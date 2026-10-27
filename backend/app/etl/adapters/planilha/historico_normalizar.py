"""Histórico das planilhas (linhas do snapshot do datalake do BI) -> LoteCanonico. Função pura.

O que entra e por quê está no docstring de `historico.py`. Resumo das regras aplicadas aqui:
- só entram linhas ANTES da fronteira (o primeiro mês que os arquivos já carregados cobrem, por entidade) e até `ate`;
- o estoque usa categorias próprias "BI:<categoria>" e fecha em 0 no dia do saldo inicial do arquivo;
- lançamentos detalhados, consumo/desmame/mudança da fMovRebanho e financeiro seguem a ponte validada em
  `backend/validacao/ponte_planilha.py`; o planejado vem das `stg_fmetas*`.

Como ler: `normalizar_historico()` chama as etapas na ordem; cada etapa é um método de `MontagemHistorico`.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from pydantic import ValidationError

from app.etl.adapters.metryx.saldo import fim_do_mes
from app.etl.adapters.planilha.normalizar import SISTEMAS, VERSAO_PLANILHA, ErroIdentidade, para_data
from app.etl.adapters.planilha.template import norm_texto
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
    proximo_mes,
)

CATEGORIAS_BI = {"BEZERRO", "MACHOS 8-12", "MACHOS 13-24", "MACHOS 25-36", "MACHOS + 36", "TOUROS",
                 "TOUROS DESCARTES", "SINUELO", "BEZERRA", "NOVILHAS 8-12", "NOVILHAS 13-24", "NOVILHAS 25-36",
                 "MATRIZES", "VACA DESCARTE", "VACA LEITEIRA"}
SEM_CATEGORIA = "(SEM CATEGORIA BI)"
GRUPOS = ("BEZERROS", "JOVENS", "ADULTOS")
# chaves da fronteira, na ordem em que aparecem no aviso HISTORY_WINDOW
ENTIDADES_DA_FRONTEIRA = ("mov_realizado", "mov_planejado", "lancamento", "orcamento", "rebanho_realizado",
                          "rebanho_planejado", "area_realizado", "area_planejado")
# abas detalhadas: nome no bruto -> tipo de lançamento
TIPO_DA_ABA = {"compras": "COMPRA", "abate": "ABATE", "empe": "VENDA_EM_PE", "mortes": "MORTE",
               "nascimentos": "NASCIMENTO", "transf_entrada": "TRANSF_ENTRADA", "transf_saida": "TRANSF_SAIDA"}


def numero(valor: Any) -> Decimal | None:
    """Número de uma coluna do datalake (já vem como número ou None)."""
    if valor is None:
        return None
    return Decimal(str(valor))


def identidade(unidade: dict | None) -> tuple[str, str]:
    """(código do cliente, id externo da fazenda) — a mesma regra do adapter de planilhas."""
    unidade = unidade or {}
    codigo = str(unidade.get("codigo") or "").strip().removesuffix(",0").removesuffix(".0")
    nome = str(unidade.get("fazenda") or "").strip()
    if not codigo or not nome:
        raise ErroIdentidade("sem código do projeto ou fazenda em stg_unidades: não dá para casar com a planilha")
    return codigo, f"{codigo}|{norm_texto(nome)}"


def mes_anterior(mes: date) -> date:
    if mes.month == 1:
        return date(mes.year - 1, 12, 1)
    return date(mes.year, mes.month - 1, 1)


def limites(fronteira: dict, ate: date) -> dict[str, date]:
    """Primeiro mês que NÃO é do histórico, por entidade: o menor entre o início do PERÍODO do arquivo, o mês mais
    antigo que o arquivo traz naquela entidade e o mês seguinte a `ate`."""
    fim = proximo_mes(ate)
    inicio_arquivo = _data_iso(fronteira.get("inicio_arquivo"))
    resultado = {}
    for entidade in ENTIDADES_DA_FRONTEIRA:
        candidatos = [fim]
        if inicio_arquivo:
            candidatos.append(inicio_arquivo.replace(day=1))
        primeiro_mes_do_arquivo = _data_iso(fronteira.get(entidade))
        if primeiro_mes_do_arquivo:
            candidatos.append(primeiro_mes_do_arquivo.replace(day=1))
        resultado[entidade] = min(candidatos)
    return resultado


def _data_iso(texto: str | None) -> date | None:
    return date.fromisoformat(texto) if texto else None


def categoria_bi(nome: Any) -> str:
    texto = str(nome or "").strip().upper()
    if texto in CATEGORIAS_BI:
        return texto
    return SEM_CATEGORIA


def parear(por_categoria: dict[str, Decimal]) -> list[tuple[str, str, Decimal]]:
    """Desmame/mudança só existem agregados por categoria (saídas negativas, entradas positivas). Casa cada saída com
    as entradas em ordem alfabética, preservando o líquido de cada categoria: [(saída, entrada, qtd), ...]."""
    saidas = sorted((categoria, -qtd) for categoria, qtd in por_categoria.items() if qtd < 0)
    entradas = sorted((categoria, qtd) for categoria, qtd in por_categoria.items() if qtd > 0)
    pares = []
    proxima = 0
    for categoria_saida, falta in saidas:
        while falta > 0 and proxima < len(entradas):
            categoria_entrada, disponivel = entradas[proxima]
            qtd = min(falta, disponivel)
            pares.append((categoria_saida, categoria_entrada, qtd))
            falta -= qtd
            entradas[proxima] = (categoria_entrada, disponivel - qtd)
            if entradas[proxima][1] == 0:
                proxima += 1
    return pares


def sem_vazios_nem_negativos(campos: dict[str, Any]) -> dict[str, Any]:
    validos = {}
    for nome, valor in campos.items():
        if valor is None:
            continue
        if isinstance(valor, Decimal) and valor < 0:
            continue
        validos[nome] = valor
    return validos


# --- campos de cada aba detalhada (as colunas do datalake já são os totais que o BI soma) ----------------------------

def campos_da_linha(aba: str, linha: dict, qtd: Decimal) -> dict[str, Any]:
    if aba == "compras":
        return {"peso_vivo_total_kg": numero(linha["total_peso"]), "valor_total": numero(linha["valor"]),
                "contraparte": linha["contraparte"]}
    if aba in ("transf_entrada", "transf_saida"):
        return {"peso_vivo_total_kg": numero(linha["total_peso"]), "valor_total": numero(linha["valor"])}
    if aba == "abate":
        return {"peso_vivo_total_kg": numero(linha["pesovivo_total"]),
                "peso_carcaca_total_kg": numero(linha["pesomorto_total"]), "valor_total": numero(linha["faturamento"]),
                "contraparte": linha["cliente"], "era": linha["era"]}
    if aba == "empe":
        return {"peso_vivo_total_kg": numero(linha["pesovivo_total"]), "valor_total": numero(linha["faturamento"]),
                "contraparte": linha["cliente"], "documento": linha["documento"]}
    if aba == "mortes":
        return {"peso_vivo_total_kg": numero(linha["peso_total"]), "causa": linha["causa"], "local": linha["local"],
                "safra": linha["safra"]}
    # nascimentos: o peso vem por cabeça
    peso_total = numero(linha["peso_nasc"]) * qtd if linha["peso_nasc"] else None
    return {"peso_vivo_total_kg": peso_total, "safra": linha["safra"]}


# --- montagem do lote ----------------------------------------------------------------------------------------------

def normalizar_historico(conteudo: dict[str, Any]) -> LoteCanonico:
    historico = MontagemHistorico(conteudo)
    historico.aviso_se_nao_ha_planilha()
    historico.identidade()
    historico.lancamentos_detalhados()
    historico.fmovrebanho()
    historico.saldos()
    historico.rebanho_medio_e_area()
    historico.financeiro()
    historico.fechar()
    return historico.lote


class MontagemHistorico:
    def __init__(self, conteudo: dict[str, Any]):
        self.conteudo = conteudo
        self.prop_faz = conteudo["prop_faz"]
        self.unidade = (conteudo.get("unidades") or [None])[0]
        self.codigo, self.fazenda = identidade(self.unidade)
        self.nome_fazenda = str(self.unidade["fazenda"]).strip()
        self.ate = date.fromisoformat(conteudo["ate"])
        self.fronteira = conteudo.get("fronteira") or {}
        self.limite = limites(self.fronteira, self.ate)
        self.inicio_arquivo = _data_iso(self.fronteira.get("inicio_arquivo"))
        self.lote = LoteCanonico(fonte="planilha")
        self.retiros: dict[str, str] = {}                           # id -> nome
        self.usadas: set[tuple[str, str]] = set()                    # (retiro, categoria BI) com dado
        self.saldo: dict[tuple[date, str, str], Decimal] = {}       # (data, retiro, categoria) -> saldo anterior

    # -- apoio --

    def retiro(self, nome: Any) -> str:
        nome = str(nome or self.nome_fazenda).strip()
        retiro_id = f"{self.fazenda}|{norm_texto(nome)}"
        if retiro_id not in self.retiros:
            self.retiros[retiro_id] = nome
        return retiro_id

    def chave(self, categoria: str) -> ChaveCategoria:
        return ChaveCategoria(fonte_mapa="planilha", escopo="fazenda", escopo_id=self.fazenda,
                              id_externo=f"BI:{categoria}")

    def rejeitar(self, entidade: str, linha: dict, codigo: str, motivo: str) -> None:
        self.lote.rejeitadas.append(LinhaRejeitada(entidade=entidade, origem_linha=linha.get("_n"), codigo=codigo,
                                                   motivo=motivo, dados=linha, fazenda=self.fazenda))

    def aviso(self, codigo: str, mensagem: str, nivel: str = "aviso", entidade: str | None = None) -> None:
        self.lote.ocorrencias.append(Ocorrencia(nivel=nivel, codigo=codigo, fazenda=self.fazenda, entidade=entidade,
                                                mensagem=mensagem))

    # -- etapas --

    def aviso_se_nao_ha_planilha(self) -> None:
        if any(self.fronteira.values()):
            return
        self.aviso("HISTORY_WITHOUT_FILE", "fazenda sem planilha carregada: histórico inteiro até "
                   f"{self.ate:%m/%Y}; carregue a planilha antes (ou confira se o arquivo foi renomeado)")

    def identidade(self) -> None:
        un = self.unidade
        ano = norm_texto(un.get("ano"))
        tipo_ano = None
        if ano.startswith("SAFRA"):
            tipo_ano = "SAFRA"
        elif ano:
            tipo_ano = "CIVIL"
        nome_cliente = str(un.get("projeto") or f"Cliente {self.codigo}").strip()
        codigo_numerico = int(self.codigo) if self.codigo.isdigit() else None
        self.lote.clientes = [RefCliente(id_externo=self.codigo, nome=nome_cliente, codigo=codigo_numerico)]
        self.lote.fazendas = [RefFazenda(id_externo=self.fazenda, cliente=self.codigo,
                                         nome=self.nome_fazenda, proprietario=un.get("proprietario"),
                                         sistema_produtivo=SISTEMAS.get(norm_texto(un.get("sistema"))),
                                         tipo_ano=tipo_ano)]
        self.lote.versoes = [RefVersaoPlano(cliente=self.codigo, codigo=VERSAO_PLANILHA,
                                            nome="Planejamento da planilha", oficial=True)]

    def lancamentos_detalhados(self) -> None:
        for aba, tipo in TIPO_DA_ABA.items():
            self._aba_detalhada(aba, aba, tipo, "realizado", self.limite["mov_realizado"])
            self._aba_detalhada(aba, f"meta_{aba}", tipo, "planejado", self.limite["mov_planejado"])

    def _aba_detalhada(self, aba: str, nome: str, tipo: str, cenario: str, limite: date) -> None:
        for numero_linha, linha in enumerate(self.conteudo.get(nome, [])):
            linha = {**linha, "_n": f"{nome}!{numero_linha}"}
            data = para_data(linha["data"])
            qtd = numero(linha["qtd"])
            if data is not None and data >= limite:
                continue                                  # o arquivo já cobre este mês
            if not qtd:
                continue
            if data is None:
                self.rejeitar("mov_animal", linha, "REQUIRED_MISSING", "sem data válida")
                continue
            categoria = categoria_bi(linha["categoria_bi"])
            retiro = self.retiro(linha["retiro"])
            self.usadas.add((retiro, categoria))
            versao = VERSAO_PLANILHA if cenario == "planejado" else None
            campos = sem_vazios_nem_negativos(campos_da_linha(aba, linha, qtd))
            try:
                mov = MovAnimal(fazenda=self.fazenda, retiro=retiro, cenario=cenario, tipo=tipo, data=data,
                                categoria=self.chave(categoria), qtd=qtd, origem_linha=linha["_n"],
                                versao_plano=versao, extra={"categ_fazenda": linha.get("categ_fazenda"),
                                                            "historico": True}, **campos)
            except ValidationError as exc:
                self.rejeitar("mov_animal", linha, "INVALID_ROW", str(exc.errors()[0]["msg"]))
                continue
            self.lote.mov_animal.append(mov)

    def fmovrebanho(self) -> None:
        """Aba fMovRebanho: guarda o Saldo Anterior (vira checkpoint em `saldos`) e lança consumo, desmame e mudança,
        que no datalake só existem agregados por categoria e mês."""
        consumo: dict[tuple[date, str, str], Decimal] = {}
        desmame_e_mudanca: dict[tuple[str, date, str], dict[str, Decimal]] = {}
        for linha in self.conteudo.get("movgado", []):
            data = para_data(linha["data"])
            if data is None:
                continue
            qtd = numero(linha["qtd"]) or Decimal(0)
            operacao = linha["operacao"]
            categoria = categoria_bi(linha["categoria_bi"])
            retiro = self.retiro(linha["retiro"])
            if operacao == "Saldo Anterior":
                chave = (fim_do_mes(data), retiro, categoria)
                self.saldo[chave] = self.saldo.get(chave, Decimal(0)) + qtd
            elif data >= self.limite["mov_realizado"]:
                continue
            elif operacao.startswith("Consumo"):
                chave = (data, retiro, categoria)
                consumo[chave] = consumo.get(chave, Decimal(0)) + qtd
            elif operacao in ("DESMAME", "Mud. de Categoria") and qtd:
                por_categoria = desmame_e_mudanca.setdefault((operacao, data, retiro), {})
                por_categoria[categoria] = por_categoria.get(categoria, Decimal(0)) + qtd
        self._lancar_consumo(consumo)
        for (operacao, data, retiro), por_categoria in desmame_e_mudanca.items():
            self._lancar_desmame_ou_mudanca(operacao, data, retiro, por_categoria)

    def _lancar_consumo(self, consumo: dict[tuple[date, str, str], Decimal]) -> None:
        for (data, retiro, categoria), qtd in consumo.items():
            if qtd <= 0:
                continue
            self.usadas.add((retiro, categoria))
            self.lote.mov_animal.append(MovAnimal(
                fazenda=self.fazenda, retiro=retiro, cenario="realizado", tipo="CONSUMO_DOACAO", data=data,
                categoria=self.chave(categoria), qtd=qtd, origem_linha=f"fMovRebanho!Consumo:{categoria}:{data}",
                extra={"historico": True}))

    def _lancar_desmame_ou_mudanca(self, operacao: str, data: date, retiro: str,
                                   por_categoria: dict[str, Decimal]) -> None:
        tipo = "DESMAME" if operacao == "DESMAME" else "MUDANCA_CATEGORIA"
        entradas = sum(qtd for qtd in por_categoria.values() if qtd > 0)
        saidas = sum(-qtd for qtd in por_categoria.values() if qtd < 0)
        sobra = entradas - saidas
        if sobra:
            mensagem = (f"{operacao} {data:%m/%Y}: entradas − saídas = {sobra} cab "
                        "(um lado sem categoria BI na planilha)")
            self.aviso("UNPAIRED_TRANSFER_OF_CATEGORY", mensagem, entidade="mov_animal")
        for categoria_saida, categoria_entrada, qtd in parear(por_categoria):
            self.usadas.add((retiro, categoria_saida))
            self.usadas.add((retiro, categoria_entrada))
            self.lote.mov_animal.append(MovAnimal(
                fazenda=self.fazenda, retiro=retiro, cenario="realizado", tipo=tipo, data=data,
                categoria=self.chave(categoria_saida), categoria_destino=self.chave(categoria_entrada), qtd=qtd,
                origem_linha=f"fMovRebanho!{tipo}:{categoria_saida}>{categoria_entrada}:{data}",
                extra={"historico": True}))

    def saldos(self) -> None:
        """Checkpoints: o Saldo Anterior do snapshot (antes do arquivo) e, no dia do saldo inicial do arquivo, 0 para
        toda categoria do histórico — dali em diante vale o saldo da planilha."""
        fechamento = self.inicio_arquivo - timedelta(days=1) if self.inicio_arquivo else None
        self._completar_saldos_zerados()
        if self._saldo_do_snapshot_serve():
            for (data, retiro, categoria), qtd in sorted(self.saldo.items()):
                if data >= proximo_mes(self.ate):
                    continue
                if fechamento and data >= fechamento:
                    continue
                self._checkpoint(data, retiro, categoria, qtd)
        if fechamento:
            for retiro, categoria in sorted(self.usadas):
                self.lote.inventario.append(Inventario(
                    fazenda=self.fazenda, retiro=retiro, categoria=self.chave(categoria), data=fechamento, qtd=0,
                    origem_linha=f"historico!fechamento:{categoria}:{fechamento}"))

    def _completar_saldos_zerados(self) -> None:
        """O Pentaho descarta os zeros: toda categoria com dado tem saldo no início (0 se não veio)."""
        if not self.saldo:
            return
        primeira_data = min(data for data, _, _ in self.saldo)
        for retiro, categoria in self.usadas:
            self.saldo.setdefault((primeira_data, retiro, categoria), Decimal(0))

    def _saldo_do_snapshot_serve(self) -> bool:
        """Se o arquivo traz lançamentos anteriores ao próprio PERÍODO, o saldo do histórico não fecharia com eles."""
        if not self.inicio_arquivo:
            return True
        return self.limite["mov_realizado"] >= self.inicio_arquivo.replace(day=1)

    def _checkpoint(self, data: date, retiro: str, categoria: str, qtd: Decimal) -> None:
        origem = f"fMovRebanho!SaldoAnterior:{categoria}:{data}"
        if qtd < 0:
            self.rejeitar("inventario", {"categoria": categoria, "data": data.isoformat(), "qtd": str(qtd),
                                         "_n": origem},
                          "NEGATIVE_STOCK", f"Saldo Anterior negativo ({qtd}) na planilha")
            return
        self.usadas.add((retiro, categoria))
        self.lote.inventario.append(Inventario(fazenda=self.fazenda, retiro=retiro, categoria=self.chave(categoria),
                                               data=data, qtd=qtd, origem_linha=origem))

    def rebanho_medio_e_area(self) -> None:
        self._rebanho_medio("realizado", "rebanho", None)
        self._area("realizado", "area", None)
        self._rebanho_medio("planejado", "meta_rebanho", VERSAO_PLANILHA)
        self._area("planejado", "meta_area", VERSAO_PLANILHA)

    def _rebanho_medio(self, cenario: str, nome: str, versao: str | None) -> None:
        limite = self.limite[f"rebanho_{cenario}"]
        somas: dict[tuple[date, str], dict] = {}          # (mês, grupo) -> {cab, ua}
        for linha in self.conteudo.get(nome, []):
            mes = para_data(linha["data"])
            grupo = str(linha["grupo_categoria"] or "").upper()
            if mes is None or mes >= limite or grupo not in GRUPOS or linha["qtd_cab"] is None:
                continue
            chave = (mes.replace(day=1), grupo)
            if chave not in somas:
                somas[chave] = {"cab": Decimal(0), "ua": None}
            somas[chave]["cab"] += numero(linha["qtd_cab"])
            if linha["qtd_ua"] is not None:
                somas[chave]["ua"] = (somas[chave]["ua"] or Decimal(0)) + numero(linha["qtd_ua"])
        prefixo = "meta_" if cenario == "planejado" else ""
        for (mes, grupo), soma in somas.items():
            if soma["cab"] < 0:
                continue
            self.lote.rebanho_medio.append(RebanhoMedio(
                fazenda=self.fazenda, cenario=cenario, versao_plano=versao, competencia=mes, grupo=grupo,
                qtd_cab=soma["cab"], qtd_ua_informada=soma["ua"], origem_linha=f"{prefixo}fRebanhoMedio!{grupo}:{mes}"))

    def _area(self, cenario: str, nome: str, versao: str | None) -> None:
        limite = self.limite[f"area_{cenario}"]
        somas: dict[date, dict] = {}                      # mês -> {pasto, ilp, total}
        for linha in self.conteudo.get(nome, []):
            mes = para_data(linha["data"])
            if mes is None or mes >= limite:
                continue
            mes = mes.replace(day=1)
            if mes not in somas:
                somas[mes] = {"pasto": Decimal(0), "ilp": Decimal(0), "total": Decimal(0)}
            for coluna in ("pasto", "ilp", "total"):
                somas[mes][coluna] += numero(linha[coluna]) or Decimal(0)
        prefixo = "meta_" if cenario == "planejado" else ""
        for mes, soma in somas.items():
            if min(soma.values()) < 0:
                continue
            self.lote.area.append(AreaMensal(
                fazenda=self.fazenda, cenario=cenario, versao_plano=versao, competencia=mes,
                area_pasto_ha=soma["pasto"], area_ilp_ha=soma["ilp"], area_total_ha=soma["total"],
                origem_linha=f"{prefixo}fArea!{mes}"))

    def financeiro(self) -> None:
        """stg_fdre vira lançamento; stg_fmetasdre vira orçamento somado por conta × natureza × mês."""
        orcado: dict[tuple, Decimal] = {}
        self._dre("realizado", "dre", self.limite["lancamento"], orcado)
        self._dre("planejado", "meta_dre", self.limite["orcamento"], orcado)
        for (conta, natureza, mes), valor in orcado.items():
            self.lote.orcamentos.append(OrcamentoFinanceiro(
                fazenda=self.fazenda, versao_plano=VERSAO_PLANILHA, conta=conta, natureza=natureza, competencia=mes,
                valor=valor, origem_linha=f"meta_dre!{conta.centro}:{mes}"))

    def _dre(self, cenario: str, nome: str, limite: date, orcado: dict) -> None:
        for numero_linha, linha in enumerate(self.conteudo.get(nome, [])):
            linha = {**linha, "_n": f"{nome}!{numero_linha}"}
            data = para_data(linha["data_pag"])
            valor = numero(linha["valor"])
            if not valor:
                continue
            if data is not None and data >= limite:
                continue
            if data is None:
                self.rejeitar("lancamento", linha, "REQUIRED_MISSING", "valor sem data de pagamento")
                continue
            if linha["operacao"] not in ("C", "D"):
                self.rejeitar("lancamento", linha, "NATURE_UNKNOWN", f"operação '{linha['operacao']}': sem natureza "
                              "C/D, não soma em receita nem despesa (como no BI)")
                continue
            natureza = linha["operacao"]
            invertido = valor < 0                         # estorno: valor negativo vira a natureza oposta
            if invertido:
                natureza = "D" if natureza == "C" else "C"
                valor = -valor
            conta = ContaOrigem(centro=linha["centro_de_custo_bi"] or linha["centro_de_custo"] or "(vazio)",
                                subcentro=linha["sub_centro_bi"] or linha["sub_centro"])
            if cenario == "realizado":
                self.lote.lancamentos.append(LancamentoFinanceiro(
                    fazenda=self.fazenda, conta=conta, natureza=natureza, valor=valor, data_pagamento=data,
                    origem_linha=linha["_n"], extra={"centro_local": linha["centro_de_custo"],
                                                     "sub_centro_local": linha["sub_centro"],
                                                     "sinal_invertido": invertido, "historico": True}))
                continue
            chave = (conta, natureza, data.replace(day=1))
            orcado[chave] = orcado.get(chave, Decimal(0)) + valor

    def fechar(self) -> None:
        """Retiros, categorias, partições e o aviso com a janela do histórico."""
        self.lote.retiros = [RefRetiro(id_externo=retiro_id, fazenda=self.fazenda, nome=nome)
                             for retiro_id, nome in self.retiros.items()]
        categorias = sorted({categoria for _, categoria in self.usadas})
        for categoria in categorias:
            destino = None if categoria == SEM_CATEGORIA else categoria
            self.lote.categorias.append(RefCategoria(chave=self.chave(categoria), nome=f"{categoria} (histórico)",
                                                     categoria_bi=destino, confirmada=True))
        self.lote.particoes = [
            self._substituir_ate("mov_animal", "realizado", "mov_realizado"),
            self._substituir_ate("lancamento", "realizado", "lancamento"),
            self._substituir_ate("mov_animal", "planejado", "mov_planejado"),
            self._substituir_ate("orcamento", "planejado", "orcamento"),
            self._mesclar("inventario", "realizado"),
            self._mesclar("rebanho_medio", "realizado"),
            self._mesclar("area", "realizado"),
            self._mesclar("rebanho_medio", "planejado"),
            self._mesclar("area", "planejado"),
        ]
        janela = ", ".join(f"{entidade} {mes_anterior(mes):%m/%Y}" for entidade, mes in self.limite.items())
        self.aviso("HISTORY_WINDOW", f"histórico (snapshot {self.prop_faz}) até: {janela}", nivel="info")

    def _substituir_ate(self, entidade: str, cenario: str, chave_do_limite: str) -> Particao:
        versao = VERSAO_PLANILHA if cenario == "planejado" else None
        return Particao(entidade=entidade, fazenda=self.fazenda, cenario=cenario, estrategia="substituir",
                        versao_plano=versao, ate=mes_anterior(self.limite[chave_do_limite]))

    def _mesclar(self, entidade: str, cenario: str) -> Particao:
        versao = VERSAO_PLANILHA if cenario == "planejado" else None
        return Particao(entidade=entidade, fazenda=self.fazenda, cenario=cenario, estrategia="mesclar",
                        versao_plano=versao)
