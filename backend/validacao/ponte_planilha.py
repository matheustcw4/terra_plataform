"""Ponte de validação Planilha: `stg_*` do DATALAKE_PLAN -> LoteCanonico (uma unidade por PROP_FAZ).

Faz o papel do adapter de planilhas enquanto ele não existe, partindo do que o Pentaho já gravou:
- identidade = PROP_FAZ (a mesma chave do BI; o adapter real usará código do cliente + fazenda);
- categoria de origem = a categoria BI (a stg_fmovgado só existe nesse grão);
- lançamentos das abas detalhadas (compras, abate, em pé, mortes, nascimentos, transferências);
- consumo/doação, desmame e mudança de categoria só existem agregados na stg_fmovgado (aba fMovRebanho):
  entram como lançamentos mensais, e desmame/mudança são pareados saída -> entrada dentro do mês;
- checkpoint de estoque = "Saldo Anterior" da fMovGado, no último dia do mês anterior ao PERÍODO.
"""

from collections import defaultdict
from datetime import date
from decimal import Decimal

from pydantic import ValidationError

from app.etl.adapters.base import Bruto, UnidadeOrigem, sha256_json
from app.etl.adapters.metryx.saldo import fim_do_mes
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
    Particao,
    RebanhoMedio,
    RefCategoria,
    RefCliente,
    RefFazenda,
)
from validacao.datalake import consultar, parse_data
from validacao.datalake import jsonavel as _jsonavel

BANCO = "DATALAKE_PLAN"
PROP_FAZ = """unaccent(replace(concat("proprietÁrio", fazenda), ' ', '')) AS prop_faz"""
CATEGORIAS_BI = {"BEZERRO", "MACHOS 8-12", "MACHOS 13-24", "MACHOS 25-36", "MACHOS + 36", "TOUROS",
                 "TOUROS DESCARTES", "SINUELO", "BEZERRA", "NOVILHAS 8-12", "NOVILHAS 13-24", "NOVILHAS 25-36",
                 "MATRIZES", "VACA DESCARTE", "VACA LEITEIRA"}
SEM_CATEGORIA = "(SEM CATEGORIA BI)"

CONSULTAS = {
    "unidades": f'SELECT projeto, "CÓDIGO PROJETO" AS codigo, "SISTEMA PRODUTIVO" AS sistema, ano, fazenda, '
                f'"proprietÁrio" AS proprietario, {PROP_FAZ} FROM "DATABASE".stg_unidades WHERE projeto IS NOT NULL',
    "movgado": f'SELECT "operaÇÃo" AS operacao, "DATA" AS data, qtd, categoria_bi, {PROP_FAZ} '
               f'FROM "DATABASE".stg_fmovgado',
    "compras": f'SELECT "DATA" AS data, qtd, total_peso, "VALOR TOTAL" AS valor, origem AS contraparte, '
               f'categoria_bi, categ_fazenda, {PROP_FAZ} FROM "DATABASE".stg_fcompras',
    "abate": f'SELECT "DATA" AS data, qtd, pesovivo_total, pesomorto_total, faturamento, cliente, era, categoria_bi, '
             f'categ_fazenda, {PROP_FAZ} FROM "DATABASE".stg_fvendaabate',
    "empe": f'SELECT "DATA" AS data, qtd, pesovivo_total, faturamento, cliente, documento, categoria_bi, '
            f'categ_fazenda, {PROP_FAZ} FROM "DATABASE".stg_fvendaempe',
    "mortes": f'SELECT "DATA" AS data, qtd, peso_total, causa, "LOCAL" AS local, safra, categoria_bi, categ_fazenda, '
              f'{PROP_FAZ} FROM "DATABASE".stg_fmortes',
    "nascimentos": f'SELECT "DATA" AS data, qtd, peso_nasc, safra, categoria_bi, categ_fazenda, {PROP_FAZ} '
                   f'FROM "DATABASE".stg_fnascimento',
    "transf_entrada": f'SELECT "DATA" AS data, qtd, total_peso, "VALOR TOTAL" AS valor, categoria_bi, '
                      f'categoria_fazenda AS categ_fazenda, {PROP_FAZ} FROM "DATABASE".stg_ftransfentrada',
    "transf_saida": f'SELECT "DATA" AS data, qtd, total_peso, "VALOR TOTAL" AS valor, categoria_bi, '
                    f'categoria_fazenda AS categ_fazenda, {PROP_FAZ} FROM "DATABASE".stg_ftransfsaida',
    "rebanho": f'SELECT grupo_categoria, qtd_cab, qtd_ua, "DATA" AS data, {PROP_FAZ} FROM "DATABASE".stg_frebanhomedio',
    "area": f'SELECT "DATA" AS data, "Área_pasto" AS pasto, "Área_ilp" AS ilp, "Área_total" AS total, {PROP_FAZ} '
            f'FROM "DATABASE".stg_area',
    "dre": f'SELECT centro_de_custo, sub_centro, valor, "operaÇÃo" AS operacao, centro_de_custo_bi, sub_centro_bi, '
           f'data_pag, {PROP_FAZ} FROM "DATABASE".stg_fdre',
}

TIPO_DA_ABA = {"compras": "COMPRA", "abate": "ABATE", "empe": "VENDA_EM_PE", "mortes": "MORTE",
               "nascimentos": "NASCIMENTO", "transf_entrada": "TRANSF_ENTRADA", "transf_saida": "TRANSF_SAIDA"}


def _d(v) -> Decimal | None:
    return None if v is None else Decimal(str(v))


def _categoria(nome) -> str:
    nome = (nome or "").strip().upper()
    return nome if nome in CATEGORIAS_BI else SEM_CATEGORIA


class PontePlanilha:
    fonte = "planilha"

    def __init__(self, prop_faz: list[str] | None = None):
        self._por_unidade: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
        for nome, sql in CONSULTAS.items():
            for linha in consultar(BANCO, sql):
                self._por_unidade[linha["prop_faz"]][nome].append(linha)
        # toda unidade com algum dado (há planilhas só com financeiro/área, sem fMovRebanho)
        self.unidades = prop_faz or sorted(k for k, v in self._por_unidade.items()
                                           if k and any(n != "unidades" and linhas for n, linhas in v.items()))

    def descobrir(self) -> list[UnidadeOrigem]:
        return [UnidadeOrigem(chave=f"stg:{u}", descricao=f"Planilha (stg) {u}") for u in self.unidades]

    def extrair(self, unidade: UnidadeOrigem) -> Bruto:
        pf = unidade.chave.split(":", 1)[1]
        conteudo = _jsonavel({"prop_faz": pf, **self._por_unidade[pf]})
        return Bruto(unidade, "json", conteudo, sha256_json(conteudo), len(str(conteudo)), {"endpoint": "stg_*"})

    # ------------------------------------------------------------------------------------------------------------
    def normalizar(self, bruto: Bruto) -> LoteCanonico:
        d = bruto.conteudo
        pf = d["prop_faz"]
        lote = LoteCanonico(fonte="planilha")
        un = (d.get("unidades") or [None])[0]
        codigo = str(un["codigo"]).strip().removesuffix(",0").removesuffix(".0") if un and un["codigo"] else None
        cliente = (codigo if codigo else
                   (f"PROJ:{un['projeto']}" if un else "SEM_CADASTRO"))
        nome_cliente = un["projeto"] if un else "SEM CADASTRO EM stg_unidades"
        lote.clientes = [RefCliente(id_externo=cliente, nome=nome_cliente,
                                    codigo=int(cliente) if cliente.isdigit() else None)]
        ano = (un or {}).get("ano") or ""
        lote.fazendas = [RefFazenda(
            id_externo=pf, cliente=cliente, nome=(un or {}).get("fazenda") or pf,
            proprietario=(un or {}).get("proprietario"),
            sistema_produtivo=(un or {}).get("sistema") or None,
            tipo_ano="SAFRA" if "SAFRA" in ano.upper() else ("CIVIL" if ano else None))]
        if un is None:
            lote.ocorrencias.append(Ocorrencia(nivel="aviso", codigo="UNIT_NOT_REGISTERED", fazenda=pf,
                                               mensagem="PROP_FAZ com fatos mas sem linha em stg_unidades"))

        usadas: set[str] = set()

        def cat(nome: str) -> ChaveCategoria:
            usadas.add(nome)
            return ChaveCategoria(fonte_mapa="planilha", escopo="fazenda", escopo_id=pf, id_externo=nome)

        def rejeitar(entidade, linha, codigo, motivo):
            lote.rejeitadas.append(LinhaRejeitada(entidade=entidade, origem_linha=linha.get("_n"), codigo=codigo,
                                                  motivo=motivo, dados=linha, fazenda=pf))

        # --- lançamentos das abas detalhadas ---
        for aba, tipo in TIPO_DA_ABA.items():
            for n, x in enumerate(d.get(aba, [])):
                x = {**x, "_n": f"{aba}!{n}"}
                dt, qtd = parse_data(x["data"]), _d(x["qtd"])
                if dt is None or qtd is None:
                    rejeitar("mov_animal", x, "REQUIRED_MISSING", "sem data válida ou quantidade")
                    continue
                campos = {}
                if aba in ("compras", "transf_entrada", "transf_saida"):
                    campos = {"peso_vivo_total_kg": _d(x["total_peso"]), "valor_total": _d(x["valor"])}
                elif aba == "abate":
                    campos = {"peso_vivo_total_kg": _d(x["pesovivo_total"]),
                              "peso_carcaca_total_kg": _d(x["pesomorto_total"]), "valor_total": _d(x["faturamento"]),
                              "contraparte": x["cliente"], "era": x["era"]}
                elif aba == "empe":
                    campos = {"peso_vivo_total_kg": _d(x["pesovivo_total"]), "valor_total": _d(x["faturamento"]),
                              "contraparte": x["cliente"], "documento": x["documento"]}
                elif aba == "mortes":
                    campos = {"peso_vivo_total_kg": _d(x["peso_total"]), "causa": x["causa"], "local": x["local"],
                              "safra": x["safra"]}
                elif aba == "nascimentos":
                    campos = {"peso_vivo_total_kg": _d(x["peso_nasc"] * x["qtd"]) if x["peso_nasc"] else None,
                              "safra": x["safra"]}
                if aba == "compras":
                    campos["contraparte"] = x["contraparte"]
                try:
                    lote.mov_animal.append(MovAnimal(
                        fazenda=pf, cenario="realizado", tipo=tipo, data=dt, categoria=cat(_categoria(x["categoria_bi"])),
                        qtd=qtd, origem_linha=x["_n"], extra={"categ_fazenda": x.get("categ_fazenda")},
                        **{k: v for k, v in campos.items() if v is not None and not (isinstance(v, Decimal) and v < 0)}))
                except ValidationError as exc:
                    rejeitar("mov_animal", x, "INVALID_ROW", str(exc.errors()[0]["msg"]))

        # --- fMovGado: saldo anterior (checkpoint) e operações que só existem agregadas ---
        saldo: dict[tuple[date, str], Decimal] = defaultdict(Decimal)
        consumo: dict[tuple[date, str], Decimal] = defaultdict(Decimal)
        pares: dict[tuple[str, date], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
        for x in d.get("movgado", []):
            dt, qtd, op = parse_data(x["data"]), _d(x["qtd"]) or Decimal(0), x["operacao"]
            if dt is None:
                continue
            c = _categoria(x["categoria_bi"])
            if op == "Saldo Anterior":
                saldo[(fim_do_mes(dt), c)] += qtd
            elif op.startswith("Consumo"):
                consumo[(dt, c)] += qtd
            elif op in ("DESMAME", "Mud. de Categoria") and qtd:
                pares[(op, dt)][c] += qtd
        # início do PERÍODO: data do Saldo Anterior (ou o mês anterior ao 1º mês da fMovRebanho)
        meses_mov = [parse_data(x["data"]) for x in d.get("movgado", []) if parse_data(x["data"])]
        inicio = min((dt for dt, _ in saldo), default=None) or (
            date.fromordinal(min(meses_mov).toordinal() - 1) if meses_mov else None)
        for (dt, c), q in consumo.items():
            if q > 0:
                lote.mov_animal.append(MovAnimal(fazenda=pf, cenario="realizado", tipo="CONSUMO_DOACAO", data=dt,
                                                 categoria=cat(c), qtd=q, origem_linha=f"fMovRebanho!Consumo:{c}:{dt}"))
        for (op, dt), por_cat in pares.items():
            tipo = "DESMAME" if op == "DESMAME" else "MUDANCA_CATEGORIA"
            saidas = sorted((c, -q) for c, q in por_cat.items() if q < 0)
            entradas = sorted((c, q) for c, q in por_cat.items() if q > 0)
            sobra = sum(q for _, q in entradas) - sum(q for _, q in saidas)
            if sobra:
                lote.ocorrencias.append(Ocorrencia(
                    nivel="aviso", codigo="UNPAIRED_TRANSFER_OF_CATEGORY", fazenda=pf, entidade="mov_animal",
                    mensagem=f"{op} {dt:%m/%Y}: entradas − saídas = {sobra} cab (um lado sem categoria BI na planilha)",
                    contexto={"saidas": {c: str(q) for c, q in saidas}, "entradas": {c: str(q) for c, q in entradas}}))
            i = 0
            for c_out, q_out in saidas:              # pareamento guloso: preserva o líquido de cada categoria
                while q_out > 0 and i < len(entradas):
                    c_in, q_in = entradas[i]
                    q = min(q_out, q_in)
                    lote.mov_animal.append(MovAnimal(
                        fazenda=pf, cenario="realizado", tipo=tipo, data=dt, categoria=cat(c_out),
                        categoria_destino=cat(c_in), qtd=q, origem_linha=f"fMovRebanho!{tipo}:{c_out}>{c_in}:{dt}"))
                    q_out -= q
                    entradas[i] = (c_in, q_in - q)
                    if entradas[i][1] == 0:
                        i += 1

        # --- rebanho médio (grupo × mês) e área (mês): somados quando há arquivo em dobro ---
        rm: dict[tuple, list[Decimal | None]] = defaultdict(lambda: [Decimal(0), None])
        for x in d.get("rebanho", []):
            comp, grupo = parse_data(x["data"]), (x["grupo_categoria"] or "").upper()
            if comp is None or grupo not in ("BEZERROS", "JOVENS", "ADULTOS") or x["qtd_cab"] is None:
                continue
            acc = rm[(comp.replace(day=1), grupo)]
            acc[0] += _d(x["qtd_cab"])
            if x["qtd_ua"] is not None:
                acc[1] = (acc[1] or Decimal(0)) + _d(x["qtd_ua"])
        lote.rebanho_medio = [
            RebanhoMedio(fazenda=pf, cenario="realizado", competencia=comp, grupo=g, qtd_cab=v[0],
                         qtd_ua_informada=v[1], origem_linha=f"fRebanhoMedio!{g}:{comp}")
            for (comp, g), v in rm.items() if v[0] >= 0
        ]
        ar: dict[date, list[Decimal]] = defaultdict(lambda: [Decimal(0)] * 3)
        for x in d.get("area", []):
            comp = parse_data(x["data"])
            if comp is None:
                continue
            acc = ar[comp.replace(day=1)]
            for i, k in enumerate(("pasto", "ilp", "total")):
                acc[i] += _d(x[k]) or Decimal(0)
        lote.area = [AreaMensal(fazenda=pf, cenario="realizado", competencia=comp, area_pasto_ha=v[0],
                                area_ilp_ha=v[1], area_total_ha=v[2], origem_linha=f"fArea!{comp}")
                     for comp, v in ar.items() if min(v) >= 0]

        # --- financeiro ---
        for n, x in enumerate(d.get("dre", [])):
            x = {**x, "_n": f"fDre!{n}"}
            dt, valor = parse_data(x["data_pag"]), _d(x["valor"])
            if dt is None or valor is None:
                rejeitar("lancamento", x, "REQUIRED_MISSING", "sem data de pagamento ou valor")
                continue
            if x["operacao"] not in ("C", "D"):
                rejeitar("lancamento", x, "NATURE_UNKNOWN",
                         f"operação '{x['operacao']}': sem natureza C/D, não soma em receita nem despesa (como no BI)")
                continue
            natureza = x["operacao"]
            if valor < 0:
                natureza, valor = ("D" if natureza == "C" else "C"), -valor
            lote.lancamentos.append(LancamentoFinanceiro(
                fazenda=pf, conta=ContaOrigem(centro=x["centro_de_custo_bi"] or x["centro_de_custo"] or "(vazio)",
                                              subcentro=x["sub_centro_bi"] or x["sub_centro"]),
                natureza=natureza, valor=valor, data_pagamento=dt, origem_linha=x["_n"],
                extra={"centro_local": x["centro_de_custo"], "sub_centro_local": x["sub_centro"],
                       "sinal_invertido": _d(x["valor"]) < 0}))

        # o Pentaho descarta as linhas zeradas da fMovRebanho: na planilha TODA categoria tem Saldo Anterior (0 ou não)
        if inicio is not None:
            for c in usadas:
                saldo.setdefault((inicio, c), Decimal(0))
        for (dt, c), q in saldo.items():
            if q < 0:
                rejeitar("inventario", {"categoria": c, "data": dt.isoformat(), "qtd": str(q),
                                        "_n": f"fMovRebanho!SaldoAnterior:{c}:{dt}"},
                         "NEGATIVE_STOCK", f"Saldo Anterior negativo ({q}) na planilha")
                continue
            lote.inventario.append(Inventario(fazenda=pf, categoria=cat(c), data=dt, qtd=q,
                                              origem_linha=f"fMovRebanho!SaldoAnterior:{c}:{dt}"))

        lote.categorias = [RefCategoria(chave=ChaveCategoria(fonte_mapa="planilha", escopo="fazenda", escopo_id=pf,
                                                             id_externo=c), nome=c,
                                        categoria_bi=None if c == SEM_CATEGORIA else c, confirmada=True)
                           for c in sorted(usadas)]
        lote.particoes = [
            Particao(entidade="mov_animal", fazenda=pf, cenario="realizado", estrategia="substituir"),
            Particao(entidade="inventario", fazenda=pf, cenario="realizado", estrategia="mesclar"),
            Particao(entidade="rebanho_medio", fazenda=pf, cenario="realizado", estrategia="mesclar"),
            Particao(entidade="area", fazenda=pf, cenario="realizado", estrategia="mesclar"),
            Particao(entidade="lancamento", fazenda=pf, cenario="realizado", estrategia="substituir"),
        ]
        return lote
