"""Planejamento do Metryx -> cenário planejado do canônico: as metas mensais de compra, venda, nascimento, morte e
desmame, o rebanho médio previsto e o DRE previsto.

Regras (27/10/2026; a escolha da versão é provisória até a D7):
- versão: cada fazenda tem as suas versões do plano (o número se repete entre fazendas, e uma versão pode cobrir
  várias safras). O Metryx guarda várias por fazenda e safra (Serra Dourada 25/26 tem a 1 e a 3) e o BI soma todas,
  o que dobra as metas. Aqui entra só a mais recente (maior plVersionCode) de cada fazenda e safra, olhando todos os
  endpoints do planejamento juntos, para as metas de uma safra virem da mesma versão; as outras ficam num aviso;
- categoria: o planejamento tem catálogo próprio (idCategory de 1 a 19, o mesmo para todos os clientes, com grupo,
  idade e sexo); entra como de-para à parte ('metryx_plano'), com a sugestão de categoria BI, como no realizado (D6);
- peso e valor: `weight` é por cabeça e `totalValue` é o total; no abate, a carcaça é weight × yield/100 por cabeça
  (a coluna pesomorto_total do BI); a venda de tipo "Abate" é abate, e as outras, venda em pé;
- rebanho médio previsto: o endpoint traz a evolução do rebanho (o saldo inicial da safra, sem data, e as entradas e
  saídas de cada mês). O rebanho médio do mês é a média entre o saldo do começo e o do fim do mês, por categoria, e
  categoria negativa no mês conta zero (ver `rebanho_medio`). O BI não tem rebanho médio previsto: a fórmula fica
  para conferir contra a tela de planejamento do Metryx;
- DRE previsto: o `previsao-financeiro` não tem versão e entra numa versão própria; a natureza sai do sinal do valor
  (crédito positivo, débito negativo), e a soma fica igual à do BI (fMetasDre). É o orçamento de tipo 'previsao';
- orçamento do planejamento (29/10/2026): o `previsao-fluxo-caixa-planejamento` entra como orçamento de tipo
  'planejamento', com TODAS as versões (a tela escolhe o tipo e a versão que compara com o realizado; padrão: a mais
  recente de cada fazenda e safra). A natureza vem do `type` (o valor vem sempre positivo). Quase todo item vem com o
  subcentro genérico "Subcentro de Custo" (só o código muda): ele não é conta, e o item fica no centro de custo.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any, NamedTuple

from pydantic import ValidationError

from app.etl.adapters.metryx.categoria import sugerir_categoria_bi
from app.etl.adapters.metryx.conversao import limpar_nome, para_data, para_decimal, sem_vazios
from app.etl.canonical import (
    ChaveCategoria,
    ContaOrigem,
    MovAnimal,
    OrcamentoFinanceiro,
    RebanhoMedio,
    RefCategoria,
    RefVersaoPlano,
    proximo_mes,
)

if TYPE_CHECKING:
    from app.etl.adapters.metryx.normalizar import MontagemMetryx

VERSAO_DO_FINANCEIRO = "previsao-financeiro"
ENDPOINTS_COM_VERSAO = ("compra_plano", "venda_plano", "nascimento_plano", "morte_plano", "desmame_plano",
                        "rebanho_plano")
ENDPOINT_DO_FLUXO = "fluxo_caixa_plano"
SUBCENTRO_GENERICO = "subcentro de custo"
NATUREZA_DO_TIPO = {"crédito": "C", "credito": "C", "débito": "D", "debito": "D"}
INVERSA = {"C": "D", "D": "C"}
CAMPOS_EXTRAS_DO_FLUXO = ("className", "classificationAnalyticDescription", "classificationAnalyticDisbursement",
                          "subCenterCode")


class CategoriaDoPlano(NamedTuple):
    id: Any
    nome: Any
    grupo: Any
    idade: Any
    sexo: Any


CAMPOS_DA_CATEGORIA = ("idCategory", "categoryName", "animalGroupName", "age", "gender")
CAMPOS_DA_ORIGEM = ("oldCategoryId", "oldCategoryName", "oldAnimalGroupName", "oldAge", "oldGender")
CAMPOS_DO_DESTINO = ("newCategoryId", "newCategoryName", "newAnimalGroupName", "newAge", "newGender")


def categorias_do_item(endpoint: str, item: dict) -> list[CategoriaDoPlano]:
    """As categorias citadas num item do planejamento (o desmame cita a de origem e a de destino)."""
    conjuntos = (CAMPOS_DA_CATEGORIA,)
    if endpoint == "desmame_plano":
        conjuntos = (CAMPOS_DA_ORIGEM, CAMPOS_DO_DESTINO)
    categorias = []
    for campos in conjuntos:
        categoria = CategoriaDoPlano(*(item.get(campo) for campo in campos))
        if categoria.id not in (None, ""):
            categorias.append(categoria)
    return categorias


def safra_do_item(item: dict) -> str | None:
    return item.get("anoSafra") or item.get("harvest")


def numero_da_versao(item: dict) -> int | None:
    numero = para_decimal(item.get("plVersionCode"))
    if numero is None:
        return None
    return int(numero)


def codigo_da_versao(fazenda: str, numero: int) -> str:
    """O número da versão só é único dentro da fazenda (cada fazenda tem a sua versão 1)."""
    return f"{fazenda}|v{numero}"


def natureza_do_tipo(tipo: Any) -> str | None:
    """'Crédito' -> C e 'Débito' -> D; outro texto -> None (quarentena)."""
    texto = limpar_nome(tipo) or ""
    return NATUREZA_DO_TIPO.get(texto.casefold())


def conta_do_fluxo(item: dict) -> ContaOrigem:
    """O subcentro genérico do planejamento ("Subcentro de Custo") não é conta: o item fica no centro de custo."""
    subcentro = limpar_nome(item.get("subCenterName"))
    if subcentro and subcentro.casefold() == SUBCENTRO_GENERICO:
        subcentro = None
    return ContaOrigem(centro=limpar_nome(item.get("costCenterName")) or "(vazio)", subcentro=subcentro or None)


def eh_abate(tipo: Any) -> bool:
    return str(tipo or "").strip().upper().startswith("ABATE")


def eh_saldo_inicial(item: dict) -> bool:
    return str(item.get("originMovement") or "").strip().upper().startswith("SALDO")


def eh_saida(item: dict) -> bool:
    """Evolução do rebanho: tipo "Entrada" ou "Saída" (a saída pode vir com a quantidade negativa)."""
    return str(item.get("type") or "").strip().upper().startswith("S")


def total_das_cabecas(por_cabeca: Any, qtd: Any) -> Decimal | None:
    valor, cabecas = para_decimal(por_cabeca), para_decimal(qtd)
    if valor is None or cabecas is None:
        return None
    return valor * cabecas


def peso_de_carcaca(peso_vivo_total: Decimal | None, rendimento: Any) -> Decimal | None:
    """`yield` vem em %, como o BI usa (weight × yield/100)."""
    percentual = para_decimal(rendimento)
    if peso_vivo_total is None or percentual is None:
        return None
    return peso_vivo_total * percentual / 100


@dataclass
class Evolucao:
    """A evolução do rebanho de uma fazenda numa safra (só a versão escolhida): o saldo inicial e o que entra ou sai em
    cada mês, por categoria."""

    saldo_inicial: dict[str, Decimal] = field(default_factory=dict)
    movimento: dict[tuple[date, str], Decimal] = field(default_factory=dict)

    def somar_saldo_inicial(self, categoria: str, qtd: Decimal) -> None:
        self.saldo_inicial[categoria] = self.saldo_inicial.get(categoria, Decimal(0)) + qtd

    def somar_movimento(self, mes: date, categoria: str, qtd: Decimal) -> None:
        self.movimento[(mes, categoria)] = self.movimento.get((mes, categoria), Decimal(0)) + qtd

    def meses(self) -> list[date]:
        """Do primeiro ao último mês com movimento, sem pular os meses parados."""
        if not self.movimento:
            return []
        datas = [mes for mes, _ in self.movimento]
        meses = []
        mes = min(datas)
        while mes <= max(datas):
            meses.append(mes)
            mes = proximo_mes(mes)
        return meses

    def medias(self) -> dict[tuple[date, str], Decimal]:
        """(mês, categoria) -> média entre o saldo do começo e o do fim do mês."""
        categorias = set(self.saldo_inicial)
        for _, categoria in self.movimento:
            categorias.add(categoria)
        meses = self.meses()
        medias = {}
        for categoria in sorted(categorias):
            saldo = self.saldo_inicial.get(categoria, Decimal(0))
            for mes in meses:
                inicio = saldo
                saldo += self.movimento.get((mes, categoria), Decimal(0))
                medias[(mes, categoria)] = (inicio + saldo) / 2
        return medias


class MontagemDoPlano:
    """As etapas do planejamento, chamadas em ordem por `normalizar()` depois das do realizado (usa o cadastro de
    fazendas, a quarentena e os avisos da montagem do realizado)."""

    def __init__(self, metryx: "MontagemMetryx"):
        self.metryx = metryx
        self.lote = metryx.lote
        self.dados = metryx.dados
        self.versao_da_safra: dict[tuple[str, str], int] = {}          # (fazenda, safra) -> versão escolhida
        self.nome_da_versao: dict[tuple[str, int], str | None] = {}    # (fazenda, versão) -> plVersionName
        self.versoes_usadas: set[tuple[str, int]] = set()             # nas metas de animais
        self.versoes_do_fluxo: set[tuple[str, int]] = set()           # no orçamento do planejamento
        self.usou_o_financeiro = False

    def categoria(self, id_categoria: Any) -> ChaveCategoria:
        return ChaveCategoria(fonte_mapa="metryx_plano", escopo="cliente", escopo_id=self.metryx.cliente,
                              id_externo=str(id_categoria))

    # -- versão --

    def versoes(self) -> None:
        """A versão mais recente de cada fazenda e safra. TODO(D7): a versão ativa (a API não diz qual é)."""
        encontradas = self.versoes_encontradas()
        deixadas = {}
        for chave, numeros in encontradas.items():
            self.versao_da_safra[chave] = max(numeros)
            if len(numeros) > 1:
                deixadas[chave] = sorted(numeros)[:-1]
        if deixadas:
            self.avisar_versoes_deixadas(deixadas)

    def versoes_encontradas(self) -> dict[tuple[str, str], set[int]]:
        encontradas: dict[tuple[str, str], set[int]] = defaultdict(set)
        for endpoint in ENDPOINTS_COM_VERSAO:
            for item in self.dados.get(endpoint, []):
                fazenda = self.metryx.fazenda_pelo_id(item)
                numero = numero_da_versao(item)
                safra = safra_do_item(item)
                if fazenda is None or numero is None or not safra:
                    continue
                encontradas[(fazenda, safra)].add(numero)
                self.nome_da_versao.setdefault((fazenda, numero), item.get("plVersionName"))
        return encontradas

    def avisar_versoes_deixadas(self, deixadas: dict[tuple[str, str], list[int]]) -> None:
        nomes_das_fazendas = {fazenda.id_externo: fazenda.nome for fazenda in self.lote.fazendas}
        trechos = []
        for (fazenda, safra), numeros in sorted(deixadas.items()):
            escolhida = self.rotulo_da_versao(fazenda, self.versao_da_safra[(fazenda, safra)])
            outras = ", ".join(self.rotulo_da_versao(fazenda, numero) for numero in numeros)
            trechos.append(f"{nomes_das_fazendas.get(fazenda, fazenda)} {safra}: {escolhida} (ficou de fora: {outras})")
        self.metryx.aviso("PLAN_VERSION_CHOSEN", "plano com mais de uma versão na safra, entrou a mais recente: "
                          + "; ".join(trechos))

    def rotulo_da_versao(self, fazenda: str, numero: int) -> str:
        nome = limpar_nome(self.nome_da_versao.get((fazenda, numero)))
        if nome:
            return f"versão {numero} ({nome})"
        return f"versão {numero}"

    def versao_do_item(self, item: dict, fazenda: str) -> str | None:
        """O código da versão do item, se ela for a escolhida para a fazenda e a safra dele; senão, None."""
        numero = numero_da_versao(item)
        if numero is None or numero != self.versao_da_safra.get((fazenda, safra_do_item(item))):
            return None
        self.versoes_usadas.add((fazenda, numero))
        return codigo_da_versao(fazenda, numero)

    def declarar_versoes(self) -> None:
        """As versões das metas e as do orçamento do planejamento; oficial = a escolhida para alguma safra."""
        escolhidas = set()
        for (fazenda, _safra), numero in self.versao_da_safra.items():
            escolhidas.add((fazenda, numero))
        for fazenda, numero in sorted(self.versoes_usadas | self.versoes_do_fluxo):
            nome = limpar_nome(self.nome_da_versao.get((fazenda, numero))) or f"Versão {numero}"
            codigo = codigo_da_versao(fazenda, numero)
            self.lote.versoes.append(RefVersaoPlano(cliente=self.metryx.cliente, codigo=codigo, nome=nome,
                                                    oficial=(fazenda, numero) in escolhidas, ordem=numero))
        if self.usou_o_financeiro:
            self.lote.versoes.append(RefVersaoPlano(cliente=self.metryx.cliente, codigo=VERSAO_DO_FINANCEIRO,
                                                    nome="Previsão financeira do Metryx (sem versão)", oficial=True))

    # -- categorias --

    def categorias(self) -> None:
        """O catálogo do planejamento que aparece nos endpoints, com a sugestão de categoria BI (D6)."""
        catalogo: dict[str, CategoriaDoPlano] = {}
        for endpoint in ENDPOINTS_COM_VERSAO:
            for item in self.dados.get(endpoint, []):
                for categoria in categorias_do_item(endpoint, item):
                    catalogo.setdefault(str(categoria.id), categoria)
        for id_categoria, categoria in sorted(catalogo.items()):
            sugestao = sugerir_categoria_bi(categoria.grupo, categoria.idade, categoria.sexo)
            atributos = {"animalGroupName": categoria.grupo, "age": categoria.idade, "gender": categoria.sexo}
            self.lote.categorias.append(RefCategoria(chave=self.categoria(id_categoria),
                                                     nome=limpar_nome(categoria.nome) or id_categoria,
                                                     categoria_bi=sugestao, atributos=atributos))

    # -- metas de animais --

    def lancar(self, ref: str, item: dict, tipo: str, categoria: Any, campos: dict[str, Any]) -> None:
        """Uma meta mensal de animais, só da versão escolhida para a fazenda e a safra. Sem fazenda do cliente, sem
        versão, mês, quantidade ou categoria -> quarentena."""
        fazenda = self.metryx.fazenda_pelo_id(item)
        if fazenda is None:
            self.metryx.rejeitar("mov_animal", item, ref, "FARM_UNRESOLVED", "fazenda fora deste cliente Metryx")
            return
        mes = para_data(item.get("date"))
        qtd = para_decimal(item.get("amount"))
        if numero_da_versao(item) is None or mes is None or qtd is None or categoria in (None, ""):
            self.metryx.rejeitar("mov_animal", item, ref, "REQUIRED_MISSING",
                                 "sem versão, mês, quantidade ou categoria", fazenda)
            return
        versao = self.versao_do_item(item, fazenda)
        if versao is None:
            return                                    # outra versão do plano (está no aviso PLAN_VERSION_CHOSEN)
        try:
            mov = MovAnimal(fazenda=fazenda, cenario="planejado", versao_plano=versao, tipo=tipo, data=mes,
                            categoria=self.categoria(categoria), qtd=qtd, origem_linha=ref, **sem_vazios(campos))
        except ValidationError as exc:
            self.metryx.rejeitar("mov_animal", item, ref, "INVALID_ROW", str(exc.errors()[0]["msg"]), fazenda)
            return
        self.lote.mov_animal.append(mov)

    def compras(self) -> None:
        for numero, item in enumerate(self.dados.get("compra_plano", [])):
            campos = {"peso_vivo_total_kg": total_das_cabecas(item.get("weight"), item.get("amount")),
                      "valor_total": para_decimal(item.get("totalValue"))}
            self.lancar(f"compra_plano:{numero}", item, "COMPRA", item.get("idCategory"), campos)

    def vendas(self) -> None:
        for numero, item in enumerate(self.dados.get("venda_plano", [])):
            peso_vivo = total_das_cabecas(item.get("weight"), item.get("amount"))
            tipo = "VENDA_EM_PE"
            carcaca = None
            if eh_abate(item.get("type")):
                tipo = "ABATE"
                carcaca = peso_de_carcaca(peso_vivo, item.get("yield"))
            campos = {"peso_vivo_total_kg": peso_vivo, "peso_carcaca_total_kg": carcaca,
                      "valor_total": para_decimal(item.get("totalValue")),
                      "extra": {"type": item.get("type"), "arrobaValue": item.get("arrobaValue")}}
            self.lancar(f"venda_plano:{numero}", item, tipo, item.get("idCategory"), campos)

    def nascimentos(self) -> None:
        for numero, item in enumerate(self.dados.get("nascimento_plano", [])):
            self.lancar(f"nascimento_plano:{numero}", item, "NASCIMENTO", item.get("idCategory"),
                        {"safra": item.get("harvest")})

    def mortes(self) -> None:
        for numero, item in enumerate(self.dados.get("morte_plano", [])):
            self.lancar(f"morte_plano:{numero}", item, "MORTE", item.get("idCategory"), {})

    def desmames(self) -> None:
        for numero, item in enumerate(self.dados.get("desmame_plano", [])):
            destino = self.categoria(item["newCategoryId"]) if item.get("newCategoryId") else None
            self.lancar(f"desmame_plano:{numero}", item, "DESMAME", item.get("oldCategoryId"),
                        {"categoria_destino": destino})

    # -- rebanho médio previsto --

    def rebanho_medio(self) -> None:
        """A média entre o saldo do começo e o do fim de cada mês, por categoria.

        A evolução do plano não fecha por categoria, só no total da fazenda: o plano desmama bezerros que o saldo
        inicial não tem e vende vaca de descarte antes de a vaca mudar de categoria (Serra Dourada 25/26), e a
        categoria fica negativa por uns meses. Categoria negativa no mês conta zero (cabeça negativa não existe), e o
        aviso diz quanto ficou de fora; o total fica um pouco acima da conta do plano. Um mês que duas safras da mesma
        fazenda cobrem entra uma vez só (a primeira safra)."""
        safra_do_mes: dict[tuple[str, date], str] = {}            # (fazenda, mês) -> safra que já o gravou
        repetidos = 0
        zerados: dict[str, Decimal] = defaultdict(Decimal)        # fazenda -> soma das médias negativas
        for (fazenda, safra, versao), evolucao in sorted(self.evolucoes().items()):
            for (mes, categoria), media in evolucao.medias().items():
                ja_gravado = safra_do_mes.setdefault((fazenda, mes), safra)
                if ja_gravado != safra:
                    repetidos += 1
                elif media < 0:
                    zerados[fazenda] += -media
                elif media > 0:
                    self.gravar_rebanho_medio(fazenda, versao, mes, categoria, media)
        if repetidos:
            self.metryx.aviso("PLAN_MONTH_OVERLAP", f"{repetidos} rebanho(s) médio(s) previsto(s) num mês que outra "
                              "safra do plano já cobria ficaram de fora")
        if zerados:
            self.avisar_categorias_negativas(zerados)

    def avisar_categorias_negativas(self, zerados: dict[str, Decimal]) -> None:
        nomes_das_fazendas = {fazenda.id_externo: fazenda.nome for fazenda in self.lote.fazendas}
        trechos = []
        for fazenda, cabecas in sorted(zerados.items()):
            trechos.append(f"{nomes_das_fazendas.get(fazenda, fazenda)}: {cabecas:,.0f}".replace(",", "."))
        self.metryx.aviso("PLAN_NEGATIVE_STOCK", "a evolução do plano deixa categorias negativas em alguns meses; "
                          "elas contam zero no rebanho médio previsto (cab·mês que ficaram de fora: "
                          + "; ".join(trechos) + ")")

    def gravar_rebanho_medio(self, fazenda: str, versao: str, mes: date, categoria: str, media: Decimal) -> None:
        self.lote.rebanho_medio.append(RebanhoMedio(fazenda=fazenda, cenario="planejado", versao_plano=versao,
                                                    competencia=mes, categoria=self.categoria(categoria),
                                                    qtd_cab=media,
                                                    origem_linha=f"rebanho_plano:{versao}:{categoria}:{mes:%Y-%m}"))

    def evolucoes(self) -> dict[tuple[str, str, str], Evolucao]:
        """(fazenda, safra, versão escolhida) -> evolução do rebanho."""
        evolucoes: dict[tuple[str, str, str], Evolucao] = defaultdict(Evolucao)
        for numero, item in enumerate(self.dados.get("rebanho_plano", [])):
            ref = f"rebanho_plano:{numero}"
            fazenda = self.metryx.fazenda_pelo_id(item)
            qtd = para_decimal(item.get("amount"))
            sem_categoria = item.get("idCategory") in (None, "")
            if fazenda is None or qtd is None or sem_categoria or numero_da_versao(item) is None:
                self.metryx.rejeitar("rebanho_medio", item, ref, "REQUIRED_MISSING",
                                     "sem fazenda do cliente, versão, quantidade ou categoria", fazenda)
                continue
            versao = self.versao_do_item(item, fazenda)
            if versao is not None:
                self.somar_na_evolucao(evolucoes[(fazenda, safra_do_item(item), versao)], item, ref, fazenda, qtd)
        return evolucoes

    def somar_na_evolucao(self, evolucao: Evolucao, item: dict, ref: str, fazenda: str, qtd: Decimal) -> None:
        categoria = str(item["idCategory"])
        mes = para_data(item.get("date"))
        if eh_saldo_inicial(item):
            evolucao.somar_saldo_inicial(categoria, abs(qtd))
        elif mes is None:
            self.metryx.rejeitar("rebanho_medio", item, ref, "MISSING_DATE", "movimento do plano sem mês", fazenda)
        elif eh_saida(item):
            evolucao.somar_movimento(mes, categoria, -abs(qtd))
        else:
            evolucao.somar_movimento(mes, categoria, abs(qtd))

    # -- DRE previsto --

    def orcamento(self) -> None:
        """A natureza sai do sinal do valor previsto (o débito vem negativo), como o BI soma (fMetasDre)."""
        for numero, item in enumerate(self.dados.get("previsao_financeiro", [])):
            ref = f"previsao_financeiro:{numero}"
            fazenda = self.metryx.fazenda_pelo_id(item)
            mes = para_data(item.get("date"))
            valor = para_decimal(item.get("valorPrevisto"))
            if fazenda is None or mes is None or valor is None:
                self.metryx.rejeitar("orcamento", item, ref, "REQUIRED_MISSING",
                                     "sem fazenda do cliente, data ou valor previsto", fazenda)
                continue
            if valor == 0:
                continue
            natureza = "C"
            if valor < 0:
                natureza = "D"
            conta = ContaOrigem(centro=limpar_nome(item.get("costCenter")) or "(vazio)",
                                subcentro=limpar_nome(item.get("subCenter")) or None)
            extra = {campo: item.get(campo) for campo in ("type", "className", "activity")}
            self.lote.orcamentos.append(OrcamentoFinanceiro(
                fazenda=fazenda, versao_plano=VERSAO_DO_FINANCEIRO, tipo="previsao", conta=conta, natureza=natureza,
                competencia=mes.replace(day=1), valor=abs(valor), origem_linha=ref, extra=extra))
            self.usou_o_financeiro = True

    # -- orçamento do planejamento (fluxo de caixa) --

    def fluxo_de_caixa(self) -> None:
        """O orçamento de todas as versões do plano (a tela escolhe qual comparar com o realizado). Sem fazenda do
        cliente, versão, data, valor ou natureza -> quarentena; valor negativo seria estorno e inverte a natureza."""
        for numero, item in enumerate(self.dados.get(ENDPOINT_DO_FLUXO, [])):
            ref = f"{ENDPOINT_DO_FLUXO}:{numero}"
            fazenda = self.metryx.fazenda_pelo_id(item)
            versao = numero_da_versao(item)
            mes = para_data(item.get("date"))
            valor = para_decimal(item.get("value"))
            natureza = natureza_do_tipo(item.get("type"))
            if None in (fazenda, versao, mes, valor, natureza):
                motivo = "sem fazenda do cliente, versão, data, valor ou natureza (Crédito/Débito)"
                self.metryx.rejeitar("orcamento", item, ref, "REQUIRED_MISSING", motivo, fazenda)
                continue
            if valor == 0:
                continue
            if valor < 0:
                natureza = INVERSA[natureza]
            self.nome_da_versao.setdefault((fazenda, versao), item.get("plVersionName"))
            self.versoes_do_fluxo.add((fazenda, versao))
            extra = {campo: item.get(campo) for campo in CAMPOS_EXTRAS_DO_FLUXO}
            self.lote.orcamentos.append(OrcamentoFinanceiro(
                fazenda=fazenda, versao_plano=codigo_da_versao(fazenda, versao), tipo="planejamento",
                conta=conta_do_fluxo(item), natureza=natureza, competencia=mes.replace(day=1), valor=abs(valor),
                origem_linha=ref, extra=extra))
