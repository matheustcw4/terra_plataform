"""Conteúdo lido do .xlsm (leitor.py) -> LoteCanonico. Função pura: reprocessável a partir do bruto guardado.

Identidade: cliente = código do projeto (fUnidade!D2, conferido com o nome do arquivo); fazenda = código|FAZENDA;
retiro = fazenda|RETIRO. O nome do proprietário é atributo, nunca chave.

Regras (docs/analises/03 §8; decisões da validação de 14/10/2026):
- categoria da fazenda -> categoria BI pelo CADASTROINICIAL (de-para confirmado pela própria planilha);
- estoque: checkpoint = SALDO INICIAL (coluna F) no fim do mês anterior ao PERÍODO, para TODA categoria (0 quando
  vazio), mais os lançamentos; trocar o PERÍODO cria um checkpoint novo e o antigo fica (estratégia mesclar);
- lançamentos (realizado e planejado) substituem só do início do PERÍODO em diante (`Particao.desde`, recuado até a
  linha mais antiga do arquivo): a planilha da safra nova começa vazia e não pode apagar a safra anterior;
- desmame, mudança de categoria e consumo/doação entram como lançamentos (antes só existiam agregados);
- venda em pé sem cliente é carregada, com aviso (Q3/A3 — o Pentaho descartava);
- financeiro: conta pela tradução da própria planilha (BASEPLANODECONTAS; colunas *_BI em cache), natureza C/D pela
  coluna OPERAÇÃO (ConsultaPlanoContas só quando ela está vazia); 'VERIFICAR' ou sem natureza -> quarentena (o BI
  também não soma); estorno inverte;
- totais (kg, R$): a coluna de total da planilha primeiro, que é o que o BI soma; quantidade × valor por cabeça só
  quando o total está vazio;
- área e rebanho médio: upsert por mês (mesclar): o histórico de períodos anteriores não se perde;
- linha do modelo sem nenhum número (sem quantidade e sem total de R$/kg; o template traz milhares delas com
  fórmulas e preços pré-preenchidos) é ignorada; quarentena é só para linha com número que não dá para somar.

Como ler este arquivo: `normalizar()` (logo abaixo das funções de conversão) chama as etapas na ordem; cada etapa é
um método curto de `MontagemPlanilha`.
"""

import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from pydantic import ValidationError

from app.etl.adapters.metryx.saldo import fim_do_mes
from app.etl.adapters.planilha.template import CATEGORIAS_BI, TIPO_DA_ABA, norm_texto
from app.etl.canonical import (
    AreaMensal,
    ChaveCategoria,
    ContaOrigem,
    Inventario,
    LancamentoFinanceiro,
    LinhaRejeitada,
    LoteCanonico,
    MovAnimal,
    Ocorrencia,
    OrcamentoFinanceiro,
    Particao,
    RebanhoMedio,
    RefCategoria,
    RefCliente,
    RefFazenda,
    RefRetiro,
    RefVersaoPlano,
)
from app.etl.quality import numero_br

VERSAO_PLANILHA = "PLANILHA"
SISTEMAS = {"CRIA": "CRIA", "RECRIA E ENGORDA": "RECRIA E ENGORDA", "CICLO COMPLETO": "CICLO COMPLETO"}
GRUPOS = {"BEZERROS": "BEZERROS", "JOVENS": "JOVENS", "ADULTOS": "ADULTOS"}
DATA_VAZIA = date(1900, 1, 1)                # o Excel grava 01/01/1900 em célula de data "vazia"
INVESTIMENTOS_INFRA = norm_texto("Investimentos em infraestrutura")
COLUNAS_DE_TOTAL = ("FATURAMENTO", "VALOR_TOTAL", "PESOVIVO_TOTAL", "TOTAL_PESO", "PESOMORTO_TOTAL")
RESIDUO = Decimal("0.01")                    # |rebanho médio| abaixo disso é resíduo de fórmula, não animal
FORMATOS_DE_DATA = ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d/%m/%y", "%d%m%Y", "%Y%m%d")
PALAVRAS_GENERICAS = {"FAZENDA", "FAZ", "SITIO", "GRUPO", "E", "DE", "DA", "DO", "DAS", "DOS", "LTDA", "AGRO",
                      "AGROPECUARIA"}
CENARIOS = (("realizado", ""), ("planejado", "PLANEJADO"))       # (cenário, sufixo do nome da aba)
EXTRAS_DO_LANCAMENTO = ("CARIMBO_BEZ", "TIPO", "VALOR_ARROBA", "RENDIMENTO")
# coluna de total -> coluna por cabeça, quando a aba tem as duas: o total vale (é o que o BI soma), a outra confere
PARES_DE_TOTAL = {"TOTAL_PESO": "PESO_VIVO", "PESOVIVO_TOTAL": "PESO_VIVO", "VALOR_TOTAL": "VALOR_CAB",
                  "FATURAMENTO": "VALOR_CAB"}
DIFERENCA_TOLERADA = Decimal("0.05")         # acima de 5%, o total e o valor por cabeça × QTD não são a mesma conta


class ErroIdentidade(ValueError):
    """Arquivo cuja identidade não fecha (ex.: código da planilha ≠ código do nome do arquivo): não carrega."""


# --- conversão de células -------------------------------------------------------------------------------------------

def para_decimal(valor: Any) -> Decimal | None:
    """Número de uma célula (aceita texto como "R$ 1.234,56"). Vazio, booleano ou texto inválido -> None."""
    if valor is None or valor == "" or isinstance(valor, bool):
        return None
    if isinstance(valor, int | float | Decimal):
        return Decimal(str(valor))
    texto = str(valor).strip().replace("R$", "").replace(" ", "")
    if not texto or texto == "-":
        return None
    virgula_decimal = "," in texto and texto.rfind(",") > texto.rfind(".")      # 1.234,56
    if virgula_decimal:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return Decimal(texto.replace(",", ""))
    except Exception:  # noqa: BLE001
        return None


def para_data(valor: Any) -> date | None:
    """Data de uma célula. O texto inteiro tem de ser a data (só a hora é descartada): "05/11/225" é erro de
    digitação e vira None, não 05/11/2022."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, int | float):
        return _data_serial_do_excel(valor)
    texto = str(valor).strip().split("T")[0].split(" ")[0]
    for formato in FORMATOS_DE_DATA:
        try:
            data = datetime.strptime(texto, formato).date()
        except ValueError:
            continue
        if data == DATA_VAZIA:
            return None
        return data
    return _mes_barra_ano(texto)


def _data_serial_do_excel(numero: int | float) -> date | None:
    if not 30000 < numero < 60000:          # fora de ~1982..2064: não é data
        return None
    return date.fromordinal(date(1899, 12, 30).toordinal() + int(numero))


def _mes_barra_ano(texto: str) -> date | None:
    """'MM/AAAA' -> dia 1 do mês."""
    if len(texto) == 7 and texto[2] == "/" and texto[:2].isdigit() and texto[3:].isdigit():
        return date(int(texto[3:]), int(texto[:2]), 1)
    return None


def para_texto(valor: Any) -> str | None:
    """Texto aparado; '85.0' (número lido como texto) vira '85'; vazio -> None."""
    if valor is None:
        return None
    texto = str(valor).strip()
    if texto.endswith(".0") and texto[:-2].isdigit():
        texto = texto[:-2]
    return texto or None


def palavras_do_nome(nome: str | None) -> set[str]:
    """Palavras que identificam a fazenda num nome (para conferir o fUnidade com o nome do arquivo)."""
    palavras = set()
    for palavra in re.split(r"[^A-Z0-9]+", norm_texto(nome or "")):
        if palavra and palavra not in PALAVRAS_GENERICAS:
            palavras.add(palavra)
    return palavras


def total_ou_por_cabeca(linha: dict, coluna_total: str, coluna_por_cabeca: str, qtd: Decimal) -> Decimal | None:
    """A coluna de total vale (é o que o BI soma); vazia ou zero -> quantidade × valor por cabeça."""
    total = para_decimal(linha.get(coluna_total))
    if total:
        return total
    return por_cabeca_vezes_qtd(linha, coluna_por_cabeca, qtd)


def por_cabeca_vezes_qtd(linha: dict, coluna_por_cabeca: str, qtd: Decimal) -> Decimal | None:
    por_cabeca = para_decimal(linha.get(coluna_por_cabeca))
    if not por_cabeca:
        return None
    return por_cabeca * qtd


# --- campos de cada tipo de lançamento de animais --------------------------------------------------------------------

def campos_compra_ou_transferencia(linha: dict, qtd: Decimal) -> dict[str, Any]:
    return {"peso_vivo_total_kg": total_ou_por_cabeca(linha, "TOTAL_PESO", "PESO_VIVO", qtd),
            "valor_total": total_ou_por_cabeca(linha, "VALOR_TOTAL", "VALOR_CAB", qtd),
            "contraparte": para_texto(linha.get("ORIGEM"))}


def campos_abate(linha: dict, qtd: Decimal) -> dict[str, Any]:
    peso_carcaca = para_decimal(linha.get("PESOMORTO_TOTAL"))
    if not peso_carcaca:
        arrobas_por_cabeca = para_decimal(linha.get("PESO_ARROBA"))
        peso_carcaca = arrobas_por_cabeca * 15 * qtd if arrobas_por_cabeca else None
    return {"peso_vivo_total_kg": total_ou_por_cabeca(linha, "PESOVIVO_TOTAL", "PESO_VIVO", qtd),
            "peso_carcaca_total_kg": peso_carcaca,
            "valor_total": para_decimal(linha.get("FATURAMENTO")),
            "contraparte": para_texto(linha.get("CLIENTE")),
            "era": para_texto(linha.get("ERA"))}


def campos_venda_em_pe(linha: dict, qtd: Decimal) -> dict[str, Any]:
    return {"peso_vivo_total_kg": total_ou_por_cabeca(linha, "PESOVIVO_TOTAL", "PESO_VIVO", qtd),
            "valor_total": total_ou_por_cabeca(linha, "FATURAMENTO", "VALOR_CAB", qtd),
            "contraparte": para_texto(linha.get("CLIENTE")),
            "documento": para_texto(linha.get("DOCUMENTO"))}


def campos_morte(linha: dict, qtd: Decimal) -> dict[str, Any]:
    return {"peso_vivo_total_kg": por_cabeca_vezes_qtd(linha, "PESO_VIVO", qtd),
            "causa": para_texto(linha.get("CAUSA")),
            "local": para_texto(linha.get("LOCAL")),
            "safra": para_texto(linha.get("SAFRA"))}


def campos_nascimento(linha: dict, qtd: Decimal) -> dict[str, Any]:
    return {"peso_vivo_total_kg": por_cabeca_vezes_qtd(linha, "PESO_NASC", qtd),
            "safra": para_texto(linha.get("SAFRA"))}


def campos_consumo(linha: dict, qtd: Decimal) -> dict[str, Any]:
    return {"peso_vivo_total_kg": por_cabeca_vezes_qtd(linha, "PESO_VIVO", qtd),
            "valor_total": por_cabeca_vezes_qtd(linha, "VALOR_CAB", qtd),
            "contraparte": para_texto(linha.get("DESTINO"))}


def campos_desmame_ou_mudanca(linha: dict, qtd: Decimal) -> dict[str, Any]:
    return {"peso_vivo_total_kg": total_ou_por_cabeca(linha, "TOTAL_PESO", "PESO_VIVO", qtd)}


CAMPOS_POR_TIPO = {
    "COMPRA": campos_compra_ou_transferencia,
    "TRANSF_ENTRADA": campos_compra_ou_transferencia,
    "TRANSF_SAIDA": campos_compra_ou_transferencia,
    "ABATE": campos_abate,
    "VENDA_EM_PE": campos_venda_em_pe,
    "MORTE": campos_morte,
    "NASCIMENTO": campos_nascimento,
    "CONSUMO_DOACAO": campos_consumo,
    "DESMAME": campos_desmame_ou_mudanca,
    "MUDANCA_CATEGORIA": campos_desmame_ou_mudanca,
}


def sem_vazios_nem_negativos(campos: dict[str, Any]) -> dict[str, Any]:
    """Campo vazio fica de fora; total negativo também (é erro da planilha, e o lançamento ainda vale)."""
    validos = {}
    for nome, valor in campos.items():
        if valor is None:
            continue
        if isinstance(valor, Decimal) and valor < 0:
            continue
        validos[nome] = valor
    return validos


# --- montagem do lote ----------------------------------------------------------------------------------------------

def normalizar(conteudo: dict[str, Any]) -> LoteCanonico:
    planilha = MontagemPlanilha(conteudo)
    planilha.avisos_da_leitura()
    planilha.identidade()
    planilha.categorias_do_cadastro()
    planilha.lancamentos_de_animais()
    planilha.saldo_inicial()
    planilha.rebanho_medio_e_area()
    planilha.financeiro()
    planilha.particoes()
    return planilha.lote


class MontagemPlanilha:
    """Guarda o lote em construção e o que as etapas compartilham (identidade, categorias, data do saldo)."""

    def __init__(self, conteudo: dict[str, Any]):
        self.conteudo = conteudo
        self.abas = conteudo.get("abas", {})
        self.cadastro = conteudo.get("cadastro", {})
        self.lote = LoteCanonico(fonte="planilha")
        self.fazenda = ""
        self.retiro = ""
        self.categorias: dict[str, RefCategoria] = {}     # nome normalizado -> categoria
        self.data_saldo: date | None = None               # fim do mês anterior ao PERÍODO

    # -- ocorrências --

    def conferir_totais(self, linha: dict, aba: str, qtd: Decimal) -> None:
        """Total que não bate com o valor por cabeça × QTD (ex.: TOTAL_PESO dobrado): o total entra, como no BI, e o
        aviso aparece em Pendências para alguém corrigir a planilha."""
        for coluna_total, coluna_por_cabeca in PARES_DE_TOTAL.items():
            total = para_decimal(linha.get(coluna_total))
            por_cabeca = para_decimal(linha.get(coluna_por_cabeca))
            if not total or not por_cabeca:
                continue
            esperado = por_cabeca * qtd
            if abs(total - esperado) > DIFERENCA_TOLERADA * abs(total):
                mensagem = (f"{coluna_total} = {numero_br(total, 2)}, mas {coluna_por_cabeca} × QTD = "
                            f"{numero_br(esperado, 2)}")
                self.aviso("TOTAL_INCONSISTENT", mensagem, origem_linha=f"{aba}!{linha.get('_linha')}")

    def aviso(self, codigo: str, mensagem: str, contexto: dict | None = None, origem_linha: str | None = None) -> None:
        self.lote.ocorrencias.append(Ocorrencia(nivel="aviso", codigo=codigo, mensagem=mensagem,
                                                origem_linha=origem_linha, contexto=contexto or None))

    def rejeitar(self, entidade: str, linha: dict, aba: str, codigo: str, motivo: str) -> None:
        self.lote.rejeitadas.append(LinhaRejeitada(
            entidade=entidade, origem_linha=f"{aba}!{linha.get('_linha')}", codigo=codigo, motivo=motivo,
            dados=linha, fazenda=self.fazenda))

    def avisos_da_leitura(self) -> None:
        for aviso in self.conteudo.get("avisos_leitura", []):
            detalhe = aviso.get("campos") or aviso.get("cabecalho") or "aba ausente"
            contexto = {chave: valor for chave, valor in aviso.items() if chave != "codigo"}
            self.aviso(aviso["codigo"], f"{aviso.get('aba')}: {detalhe}", contexto)

    # -- identidade --

    def identidade(self) -> None:
        arquivo = self.conteudo.get("arquivo", {})
        unidade = self.conteudo.get("unidade", {})
        codigo_planilha = para_texto(unidade.get("codigo"))
        codigo_nome = para_texto(arquivo.get("codigo_nome"))
        if codigo_planilha and codigo_nome and codigo_planilha != codigo_nome:
            raise ErroIdentidade(f"código na planilha ({codigo_planilha}) ≠ código no nome do arquivo "
                                 f"({codigo_nome})")
        codigo = codigo_planilha or codigo_nome
        if not codigo:
            raise ErroIdentidade("sem código do projeto (fUnidade!D2) nem no nome do arquivo")

        nome_fazenda = para_texto(unidade.get("fazenda")) or arquivo.get("rotulo") or codigo
        self._conferir_nome_com_o_arquivo(nome_fazenda, arquivo.get("rotulo"), codigo_planilha)
        if not codigo_planilha:
            self.aviso("CODE_MISSING_IN_SHEET", f"fUnidade!D2 vazio; usado o código do nome do arquivo ({codigo})")

        nome_retiro = para_texto(unidade.get("retiro")) or nome_fazenda
        self.fazenda = f"{codigo}|{norm_texto(nome_fazenda)}"
        self.retiro = f"{self.fazenda}|{norm_texto(nome_retiro)}"
        ano = norm_texto(unidade.get("ano"))
        tipo_ano = None
        if ano.startswith("SAFRA"):
            tipo_ano = "SAFRA"
        elif ano:
            tipo_ano = "CIVIL"
        nome_cliente = para_texto(unidade.get("projeto")) or f"Cliente {codigo}"
        codigo_numerico = int(codigo) if codigo.isdigit() else None
        self.lote.clientes = [RefCliente(id_externo=codigo, nome=nome_cliente, codigo=codigo_numerico)]
        self.lote.fazendas = [RefFazenda(id_externo=self.fazenda, cliente=codigo, nome=nome_fazenda,
                                         proprietario=para_texto(unidade.get("proprietario")),
                                         sistema_produtivo=SISTEMAS.get(norm_texto(unidade.get("sistema"))),
                                         tipo_ano=tipo_ano)]
        self.lote.retiros = [RefRetiro(id_externo=self.retiro, fazenda=self.fazenda, nome=nome_retiro)]
        self.lote.versoes = [RefVersaoPlano(cliente=codigo, codigo=VERSAO_PLANILHA, nome="Planejamento da planilha",
                                            oficial=True)]

    def _conferir_nome_com_o_arquivo(self, nome_fazenda: str, rotulo: str | None, codigo_planilha: str | None) -> None:
        """Nome da fazenda sem nenhuma palavra em comum com o nome do arquivo: com código no fUnidade é só aviso;
        sem código, é planilha montada a partir da de outra fazenda e não carrega."""
        if not rotulo:
            return
        if palavras_do_nome(rotulo) & palavras_do_nome(nome_fazenda):
            return
        if not codigo_planilha:
            raise ErroIdentidade(f"fUnidade sem código e com a fazenda '{nome_fazenda}', que não é a do nome do "
                                 f"arquivo ('{rotulo}'): corrija o fUnidade")
        self.aviso("FARM_LABEL_MISMATCH", f"fazenda do fUnidade ('{nome_fazenda}') ≠ nome do arquivo ('{rotulo}')")

    # -- categorias --

    def categorias_do_cadastro(self) -> None:
        """CADASTROINICIAL A11:B74: categoria da fazenda -> categoria BI (de-para confirmado pela planilha)."""
        for item in self.cadastro.get("categorias", []):
            nome = norm_texto(item["categoria"])
            if not nome or nome in self.categorias:
                continue
            self.categorias[nome] = self._nova_categoria(nome, item["categoria"].strip(),
                                                         _categoria_bi(item.get("categoria_bi")))

    def chave_categoria(self, texto: Any) -> ChaveCategoria | None:
        """Chave da categoria usada num lançamento. Fora do CADASTROINICIAL ela entra pendente (como no BI)."""
        nome = norm_texto(texto)
        if not nome:
            return None
        if nome not in self.categorias:
            nome_original = str(texto).strip()
            self.categorias[nome] = self._nova_categoria(nome, nome_original, None)
            self.aviso("CATEGORY_NOT_IN_CADASTRO", f"categoria '{nome_original}' usada sem estar no CADASTROINICIAL")
        return self.categorias[nome].chave

    def _nova_categoria(self, nome: str, nome_original: str, categoria_bi: str | None) -> RefCategoria:
        chave = ChaveCategoria(fonte_mapa="planilha", escopo="fazenda", escopo_id=self.fazenda, id_externo=nome)
        return RefCategoria(chave=chave, nome=nome_original, categoria_bi=categoria_bi, confirmada=True)

    # -- lançamentos de animais --

    def lancamentos_de_animais(self) -> None:
        for nome_aba, (tipo, campo_categoria, campo_destino) in TIPO_DA_ABA.items():
            for cenario, sufixo in CENARIOS:
                aba = nome_aba + sufixo
                for linha in self.abas.get(aba, []):
                    self._lancamento(linha, aba, tipo, cenario, campo_categoria, campo_destino)

    def _lancamento(self, linha: dict, aba: str, tipo: str, cenario: str, campo_categoria: str,
                    campo_destino: str | None) -> None:
        data = para_data(linha.get("DATA"))
        qtd = para_decimal(linha.get("QTD"))
        if not qtd and not _tem_algum_total(linha):
            return                                        # linha do modelo, sem dado
        if data is None or not qtd:
            self.rejeitar("mov_animal", linha, aba, "REQUIRED_MISSING", "sem data válida ou quantidade")
            return
        if qtd < 0:
            self.rejeitar("mov_animal", linha, aba, "NEGATIVE_VALUE", "quantidade negativa")
            return
        categoria = self.chave_categoria(linha.get(campo_categoria))
        if categoria is None:
            self.rejeitar("mov_animal", linha, aba, "REQUIRED_MISSING", "sem categoria da fazenda")
            return

        campos = CAMPOS_POR_TIPO[tipo](linha, qtd)
        self.conferir_totais(linha, aba, qtd)
        if tipo == "VENDA_EM_PE" and campos["contraparte"] is None and cenario == "realizado":
            self.aviso("SALE_WITHOUT_CLIENT", "venda em pé sem cliente (carregada)",
                       origem_linha=f"{aba}!{linha.get('_linha')}")
        if tipo in ("DESMAME", "MUDANCA_CATEGORIA"):
            campos["categoria_destino"] = self.chave_categoria(linha.get(campo_destino))

        extra = {}
        for coluna in EXTRAS_DO_LANCAMENTO:
            if linha.get(coluna) is not None:
                extra[coluna] = linha.get(coluna)
        versao = VERSAO_PLANILHA if cenario == "planejado" else None
        try:
            mov = MovAnimal(fazenda=self.fazenda, retiro=self.retiro, cenario=cenario, versao_plano=versao, tipo=tipo,
                            data=data, categoria=categoria, qtd=qtd, origem_linha=f"{aba}!{linha.get('_linha')}",
                            extra=extra or None, **sem_vazios_nem_negativos(campos))
        except ValidationError as exc:
            self.rejeitar("mov_animal", linha, aba, "INVALID_ROW", str(exc.errors()[0]["msg"]))
            return
        self.lote.mov_animal.append(mov)

    # -- saldo inicial (checkpoint de estoque) --

    def saldo_inicial(self) -> None:
        """SALDO INICIAL do CADASTROINICIAL no fim do mês anterior ao PERÍODO, para toda categoria da fazenda."""
        self.data_saldo = self._data_do_saldo()
        if self.data_saldo is None:
            return
        for item in self.cadastro.get("categorias", []):
            self._saldo_da_categoria(item)
        # toda categoria tem saldo no início do período (0 se não informado), como na fMovRebanho
        categorias_com_saldo = {inv.categoria for inv in self.lote.inventario}
        for categoria in list(self.categorias.values()):
            if categoria.chave in categorias_com_saldo:
                continue
            self.lote.inventario.append(Inventario(
                fazenda=self.fazenda, retiro=self.retiro, categoria=categoria.chave, data=self.data_saldo,
                qtd=Decimal(0), origem_linha=f"CADASTROINICIAL!sem-saldo:{categoria.chave.id_externo}"))
        self.lote.inventario = _somar_repetidos(self.lote.inventario)

    def _data_do_saldo(self) -> date | None:
        periodo = para_texto(self.cadastro.get("periodo"))
        datas_do_periodo = (self.cadastro.get("periodos") or {}).get(periodo or "")
        mes_anterior = para_data(datas_do_periodo.get("anterior")) if datas_do_periodo else None
        if mes_anterior is None:
            self.aviso("PERIOD_UNKNOWN", f"PERÍODO '{periodo}' sem datas no CADASTROINICIAL: sem saldo inicial")
            return None
        return fim_do_mes(mes_anterior)

    def _saldo_da_categoria(self, item: dict) -> None:
        qtd = para_decimal(item.get("saldo")) or Decimal(0)
        categoria = self.chave_categoria(item["categoria"])
        if categoria is None:
            return
        if qtd < 0:
            self.rejeitar("inventario", {**item, "_linha": item.get("linha")}, "CADASTROINICIAL", "NEGATIVE_STOCK",
                          f"saldo inicial negativo ({qtd})")
            return
        self.lote.inventario.append(Inventario(
            fazenda=self.fazenda, retiro=self.retiro, categoria=categoria, data=self.data_saldo, qtd=qtd,
            origem_linha=f"CADASTROINICIAL!F{item.get('linha')}"))

    # -- rebanho médio e área (mensais) --

    def rebanho_medio_e_area(self) -> None:
        for cenario, sufixo in CENARIOS:
            versao = VERSAO_PLANILHA if cenario == "planejado" else None
            self._rebanho_medio(cenario, sufixo, versao)
            self._area(cenario, sufixo, versao)

    def _rebanho_medio(self, cenario: str, sufixo: str, versao: str | None) -> None:
        aba = "fRebanhoMedio" + sufixo
        somas: dict[tuple[date, str], dict] = {}          # (mês, grupo) -> {cab, ua, primeira linha}
        for linha in self.abas.get(aba, []):
            mes = para_data(linha.get("DATA"))
            grupo = GRUPOS.get(norm_texto(linha.get("GRUPO_CATEGORIA")))
            cabecas = para_decimal(linha.get("QTD_CAB"))
            if mes is None or grupo is None or cabecas is None:
                continue
            if -RESIDUO < cabecas < 0:
                continue
            if cabecas < 0:
                self.rejeitar("rebanho_medio", linha, aba, "NEGATIVE_VALUE", "rebanho médio negativo")
                continue
            chave = (mes.replace(day=1), grupo)
            if chave not in somas:
                somas[chave] = {"cab": Decimal(0), "ua": None, "linha": linha}
            somas[chave]["cab"] += cabecas
            ua = para_decimal(linha.get("QTD_UA"))
            if ua is not None:
                somas[chave]["ua"] = (somas[chave]["ua"] or Decimal(0)) + ua
        for (mes, grupo), soma in somas.items():
            self.lote.rebanho_medio.append(RebanhoMedio(
                fazenda=self.fazenda, cenario=cenario, versao_plano=versao, competencia=mes, grupo=grupo,
                qtd_cab=soma["cab"], qtd_ua_informada=soma["ua"], origem_linha=f"{aba}!{soma['linha'].get('_linha')}"))

    def _area(self, cenario: str, sufixo: str, versao: str | None) -> None:
        aba = "fArea" + sufixo
        somas: dict[date, dict] = {}                      # mês -> {pasto, ilp, primeira linha}
        for linha in self.abas.get(aba, []):
            mes = para_data(linha.get("DATA"))
            pasto = para_decimal(linha.get("AREA_PASTO"))
            ilp = para_decimal(linha.get("AREA_ILP"))
            if mes is None or (pasto is None and ilp is None):
                continue
            mes = mes.replace(day=1)
            if mes not in somas:
                somas[mes] = {"pasto": Decimal(0), "ilp": Decimal(0), "linha": linha}
            somas[mes]["pasto"] += pasto or 0
            somas[mes]["ilp"] += ilp or 0
        for mes, soma in somas.items():
            if soma["pasto"] < 0 or soma["ilp"] < 0:
                continue
            self.lote.area.append(AreaMensal(
                fazenda=self.fazenda, cenario=cenario, versao_plano=versao, competencia=mes,
                area_pasto_ha=soma["pasto"], area_ilp_ha=soma["ilp"], area_total_ha=soma["pasto"] + soma["ilp"],
                origem_linha=f"{aba}!{soma['linha'].get('_linha')}"))

    # -- financeiro --

    def financeiro(self) -> None:
        """fDre (realizado) vira lançamento; fDrePLANEJADO vira orçamento somado por conta × natureza × mês."""
        plano = PlanoDeContas(self.conteudo.get("plano", {}))
        orcado: dict[tuple, dict] = {}                    # (conta, natureza, mês) -> {valor, linhas}
        for cenario, sufixo in CENARIOS:
            aba = "fDre" + sufixo
            for linha in self.abas.get(aba, []):
                self._linha_financeira(linha, aba, cenario, plano, orcado)
        for (conta, natureza, mes), soma in orcado.items():
            self.lote.orcamentos.append(OrcamentoFinanceiro(
                fazenda=self.fazenda, versao_plano=VERSAO_PLANILHA, conta=conta, natureza=natureza, competencia=mes,
                valor=soma["valor"], origem_linha=f"fDrePLANEJADO!{min(soma['linhas'])}",
                extra={"linhas": soma["linhas"]}))

    def _linha_financeira(self, linha: dict, aba: str, cenario: str, plano: "PlanoDeContas", orcado: dict) -> None:
        data = para_data(linha.get("DATA_PAG"))
        valor = para_decimal(linha.get("VALOR"))
        if not valor:
            return                                        # vazio ou zero: linha do modelo sem lançamento
        if data is None:
            self.rejeitar("lancamento", linha, aba, "REQUIRED_MISSING", "valor sem data de pagamento")
            return
        conta = plano.conta_da_linha(linha)
        natureza = plano.natureza_da_linha(linha)
        if natureza not in ("C", "D"):
            self.rejeitar("lancamento", linha, aba, "NATURE_UNKNOWN",
                          f"conta '{conta.centro} / {conta.subcentro}' sem natureza C/D (VERIFICAR): "
                          "não soma, como no BI")
            return
        invertido = valor < 0                             # estorno: valor negativo vira a natureza oposta
        if invertido:
            natureza = "D" if natureza == "C" else "C"
            valor = -valor
        if cenario == "realizado":
            self.lote.lancamentos.append(LancamentoFinanceiro(
                fazenda=self.fazenda, conta=conta, natureza=natureza, valor=valor, data_pagamento=data,
                origem_linha=f"{aba}!{linha.get('_linha')}",
                extra={"centro_local": linha.get("CENTRO_DE_CUSTO"), "sub_centro_local": linha.get("SUB_CENTRO"),
                       "sinal_invertido": invertido}))
            return
        chave = (conta, natureza, data.replace(day=1))
        if chave not in orcado:
            orcado[chave] = {"valor": Decimal(0), "linhas": []}
        orcado[chave]["valor"] += valor
        orcado[chave]["linhas"].append(linha.get("_linha"))

    # -- partições --

    def particoes(self) -> None:
        """Por qual recorte do banco este arquivo responde. Lançamentos: do início do PERÍODO em diante (e pelo que o
        arquivo ainda traz de antes) — substituir a fazenda inteira apagaria a safra anterior já carregada."""
        self.lote.categorias = list(self.categorias.values())
        mov_realizado = [mov.data for mov in self.lote.mov_animal if mov.cenario == "realizado"]
        mov_planejado = [mov.data for mov in self.lote.mov_animal if mov.cenario == "planejado"]
        lancamentos = [lanc.data_pagamento for lanc in self.lote.lancamentos]
        orcamentos = [orc.competencia for orc in self.lote.orcamentos]
        particoes = [
            self._substituir_desde("mov_animal", "realizado", mov_realizado),
            self._mesclar("inventario", "realizado"),
            self._mesclar("rebanho_medio", "realizado"),
            self._mesclar("area", "realizado"),
            self._substituir_desde("lancamento", "realizado", lancamentos),
            self._substituir_desde("mov_animal", "planejado", mov_planejado),
            self._mesclar("rebanho_medio", "planejado"),
            self._mesclar("area", "planejado"),
            self._substituir_desde("orcamento", "planejado", orcamentos),
        ]
        self.lote.particoes = [particao for particao in particoes if particao is not None]

    def _substituir_desde(self, entidade: str, cenario: str, datas: list[date]) -> Particao | None:
        meses = [data.replace(day=1) for data in datas]
        if self.data_saldo:
            meses.append(self.data_saldo + timedelta(days=1))          # início do PERÍODO
        if not meses:
            return None                                   # sem período e sem linhas: nada a substituir
        versao = VERSAO_PLANILHA if cenario == "planejado" else None
        return Particao(entidade=entidade, fazenda=self.fazenda, cenario=cenario, estrategia="substituir",
                        versao_plano=versao, desde=min(meses))

    def _mesclar(self, entidade: str, cenario: str) -> Particao:
        versao = VERSAO_PLANILHA if cenario == "planejado" else None
        return Particao(entidade=entidade, fazenda=self.fazenda, cenario=cenario, estrategia="mesclar",
                        versao_plano=versao)


class PlanoDeContas:
    """Tradução das contas da própria planilha (BASEPLANODECONTAS e ConsultaPlanoContas)."""

    def __init__(self, plano: dict):
        self.centros = {norm_texto(nome): valor for nome, valor in plano.get("centros", {}).items()}
        self.subcentros = {norm_texto(nome): valor for nome, valor in plano.get("subcentros", {}).items()}
        self.contas = {norm_texto(nome): valor for nome, valor in plano.get("contas", {}).items()}

    def centro_traduzido(self, linha: dict) -> str | None:
        """Coluna CENTRO_DE_CUSTO_BI (cache da planilha); senão, a tradução do BASEPLANODECONTAS."""
        centro = para_texto(linha.get("CENTRO_DE_CUSTO_BI"))
        if centro:
            return centro
        return self.centros.get(norm_texto(linha.get("CENTRO_DE_CUSTO")))

    def subcentro_traduzido(self, linha: dict, centro: str | None) -> str | None:
        subcentro = para_texto(linha.get("SUB_CENTRO_BI"))
        if subcentro is not None or not linha.get("SUB_CENTRO"):
            return subcentro
        par = self.subcentros.get(norm_texto(linha.get("SUB_CENTRO")))
        if not par:
            return None
        # o subcentro tem tradução diferente quando o centro é de investimentos em infraestrutura
        if norm_texto(centro) == INVESTIMENTOS_INFRA:
            return par[0]
        return par[1]

    def conta_da_linha(self, linha: dict) -> ContaOrigem:
        """Conta traduzida; o que não tem tradução fica com o nome local da planilha."""
        centro = self.centro_traduzido(linha)
        subcentro = self.subcentro_traduzido(linha, centro)
        return ContaOrigem(centro=centro or para_texto(linha.get("CENTRO_DE_CUSTO")) or "(vazio)",
                           subcentro=subcentro or para_texto(linha.get("SUB_CENTRO")))

    def natureza_da_linha(self, linha: dict) -> str | None:
        """C/D da coluna OPERAÇÃO. Vazia: plano de contas da planilha (pelo subcentro traduzido). 'VERIFICAR': conta
        fora do plano, e o BI não soma."""
        operacao = para_texto(linha.get("OPERACAO"))
        if operacao in ("C", "D"):
            return operacao
        if operacao is not None:
            return None
        subcentro = self.subcentro_traduzido(linha, self.centro_traduzido(linha))
        conta_do_plano = self.contas.get(norm_texto(subcentro)) or {}
        return conta_do_plano.get("natureza")


def _categoria_bi(texto: Any) -> str | None:
    """Categoria BI escrita na planilha -> uma das 15 oficiais ('MACHOS 36' é grafia antiga de 'MACHOS + 36')."""
    escrita = norm_texto(texto).replace("MACHOS 36", "MACHOS + 36")
    for oficial in CATEGORIAS_BI:
        if norm_texto(oficial) == escrita:
            return oficial
    return None


def _tem_algum_total(linha: dict) -> bool:
    return any(para_decimal(linha.get(coluna)) for coluna in COLUNAS_DE_TOTAL)


def _somar_repetidos(saldos: list[Inventario]) -> list[Inventario]:
    """Mesma categoria repetida no CADASTROINICIAL: os saldos se somam (mantém a ordem da 1ª aparição)."""
    por_chave: dict[tuple, Inventario] = {}
    for saldo in saldos:
        chave = (saldo.categoria, saldo.data)
        if chave in por_chave:
            anterior = por_chave[chave]
            por_chave[chave] = anterior.model_copy(update={"qtd": anterior.qtd + saldo.qtd})
        else:
            por_chave[chave] = saldo
    return list(por_chave.values())
