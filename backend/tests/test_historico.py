"""Carga do histórico das planilhas a partir do snapshot do datalake do BI (decisão Q6) e a passagem para o arquivo.

Cenário: a planilha atual já virou para a SAFRA 25/26 (saldo em 30/06/2025, lançamentos de jul-ago/2025); o snapshot
tem a safra 24/25 (saldo em 30/06/2024) e também linhas de jul/2025, que o arquivo cobre e não podem duplicar.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import text

from app.etl.adapters.planilha.adapter import AdapterPlanilha
from app.etl.adapters.planilha.historico import AdapterHistoricoPlanilha
from app.etl.pipeline import MotorCarga
from tests.conftest import como_usuario, criar_usuario
from tests.sinteticos import gerar_planilha

PF = "FULANODETALTESTE"
ATE = date(2025, 8, 1)          # teto do histórico; a planilha cobre de jul/2025 em diante


def _linha(**kw):
    return {"prop_faz": PF, "retiro": "TESTE", **kw}


def snapshot() -> dict:
    mov = {"qtd": None, "categoria_bi": None}
    return {PF: {
        "unidades": [{"prop_faz": PF, "projeto": "PROJETO TESTE", "codigo": "85,0", "sistema": "CICLO COMPLETO",
                      "ano": "SAFRA", "fazenda": "TESTE", "proprietario": "FULANO DE TAL", "filename": "x.xlsm"}],
        "movgado": [_linha(operacao="Saldo Anterior", data="2024/06/01 00:00:00.000", qtd=800, categoria_bi="BEZERRO"),
                    _linha(operacao="Saldo Anterior", data="2024/06/01 00:00:00.000", qtd=450, categoria_bi="MATRIZES"),
                    _linha(operacao="Consumo/Doação", data="2024/09/01 00:00:00.000", qtd=2, categoria_bi="MATRIZES")],
        "nascimentos": [_linha(**mov | {"data": "2024/08/10", "qtd": 60, "categoria_bi": "BEZERRO", "peso_nasc": 30,
                                        "safra": "24/25", "categ_fazenda": "Bezerro Mamando"}),
                        _linha(**mov | {"data": "2025/07/10", "qtd": 120, "categoria_bi": "BEZERRO", "peso_nasc": 32,
                                        "safra": "25/26", "categ_fazenda": "Bezerro Mamando"})],
        "mortes": [_linha(**mov | {"data": "2025/03/05", "qtd": 3, "categoria_bi": "MATRIZES", "peso_total": None,
                                   "causa": "Raio", "local": None, "safra": "24/25", "categ_fazenda": "Vaca"})],
        "dre": [{"prop_faz": PF, "centro_de_custo": "PASTO", "sub_centro": "ADUBO", "valor": 400, "operacao": "D",
                 "centro_de_custo_bi": "Pastagens", "sub_centro_bi": "Adubação", "data_pag": "2024/09/15"},
                {"prop_faz": PF, "centro_de_custo": "PASTO", "sub_centro": "ADUBO", "valor": 1500.5, "operacao": "D",
                 "centro_de_custo_bi": "Pastagens", "sub_centro_bi": "Adubação", "data_pag": "2025/07/15"}],
        "rebanho": [{"prop_faz": PF, "grupo_categoria": "Bezerros", "qtd_cab": 850, "qtd_ua": None,
                     "data": "2024/08/01"}],
        "area": [{"prop_faz": PF, "data": "2024/08/01", "pasto": 700, "ilp": 200, "total": 900}],
        "meta_nascimentos": [_linha(**mov | {"data": "2024/09/01", "qtd": 70, "categoria_bi": "BEZERRO",
                                             "peso_nasc": None, "safra": "24/25", "categ_fazenda": None})],
        "meta_dre": [{"prop_faz": PF, "centro_de_custo": "PASTO", "sub_centro": "ADUBO", "valor": 1000,
                      "operacao": "D", "centro_de_custo_bi": "Pastagens", "sub_centro_bi": "Adubação",
                      "data_pag": "2024/10/01"}],
    }}


def motor(engine_etl):
    return MotorCarga(engine_etl, hoje=date(2025, 10, 1), estoque_ate=date(2025, 9, 1))


def planilha(engine_etl, pasta):
    return motor(engine_etl).executar(AdapterPlanilha(pasta, estabilidade_s=0), forcar=True)


def historico(engine_etl):
    adapter = AdapterHistoricoPlanilha(engine_etl, ate=ATE, linhas=snapshot())
    return motor(engine_etl).executar(adapter, forcar=True)


def foto(engine_super) -> dict:
    with engine_super.connect() as c:
        return {
            "estoque": sorted(c.execute(text(
                "SELECT b.nome, e.competencia, e.saldo_final FROM fato.estoque_mensal e "
                "JOIN dim.categoria_bi b ON b.id = e.categoria_bi_id WHERE b.nome IN ('BEZERRO', 'MATRIZES')")).all()),
            "mov": sorted(c.execute(text("SELECT cenario, tipo, competencia, sum(qtd) FROM fato.mov_animal "
                                         "GROUP BY 1, 2, 3")).all()),
            "lanc": sorted(c.execute(text("SELECT competencia, sum(valor) FROM fato.lancamento_financeiro "
                                          "GROUP BY 1")).all()),
            "orc": sorted(c.execute(text("SELECT competencia, valor FROM fato.orcamento_financeiro")).all()),
            "rebanho": sorted(c.execute(text("SELECT cenario, competencia, sum(qtd_cab) FROM fato.rebanho_medio_mensal "
                                             "GROUP BY 1, 2")).all()),
            "fazendas": c.execute(text("SELECT count(*) FROM core.fazenda")).scalar(),
        }


def test_historico_entra_antes_da_planilha_e_passa_o_bastao(engine_etl, engine_super, tmp_path):
    gerar_planilha(tmp_path)
    planilha(engine_etl, tmp_path)
    r = historico(engine_etl)
    assert r.unidades[0].status.startswith("carregada"), r.unidades[0].erro
    f = foto(engine_super)
    assert f["fazendas"] == 1                                   # mesma identidade do adapter: código + fazenda
    estoque = {(n, comp): saldo for n, comp, saldo in f["estoque"]}
    assert estoque[("BEZERRO", date(2024, 8, 1))] == 860          # 800 + 60 do histórico
    assert estoque[("MATRIZES", date(2025, 3, 1))] == 445         # 450 − 2 consumo − 3 mortes
    # 30/06/2025: o histórico fecha em 0 e vale o saldo da planilha; julho segue só a planilha (doc 01 §5.1)
    assert estoque[("BEZERRO", date(2025, 6, 1))] == 1000
    assert estoque[("BEZERRO", date(2025, 7, 1))] == 815
    assert estoque[("MATRIZES", date(2025, 8, 1))] == 490
    mov = {(cen, tipo, comp): q for cen, tipo, comp, q in f["mov"]}
    assert mov[("realizado", "NASCIMENTO", date(2024, 8, 1))] == 60
    assert mov[("realizado", "NASCIMENTO", date(2025, 7, 1))] == 120   # a linha de jul/2025 do snapshot não duplica
    assert mov[("planejado", "NASCIMENTO", date(2024, 9, 1))] == 70
    lanc = dict(f["lanc"])
    assert lanc[date(2024, 9, 1)] == Decimal("400.00")
    assert lanc[date(2025, 7, 1)] == Decimal("1700.50")      # só o que está na planilha (o R$ 99 sem natureza é quarentena)
    assert f["orc"] == [(date(2024, 10, 1), Decimal("1000.00"))]
    assert ("realizado", date(2024, 8, 1), 850) in f["rebanho"]


def test_ordem_nao_importa_se_o_historico_roda_de_novo_depois_da_planilha(engine_etl, engine_super, tmp_path):
    gerar_planilha(tmp_path)
    planilha(engine_etl, tmp_path)
    historico(engine_etl)
    certo = foto(engine_super)
    with engine_super.begin() as c:
        c.execute(text("TRUNCATE fato.mov_animal, fato.inventario, fato.lancamento_financeiro, "
                       "fato.orcamento_financeiro, fato.rebanho_medio_mensal, fato.area_mensal, fato.estoque_mensal, "
                       "ingest.versao_origem, ingest.unidade_origem, core.fonte_vinculo, core.fazenda CASCADE"))
    r = historico(engine_etl)                 # sem planilha carregada: entra tudo até o teto, com aviso
    assert r.unidades[0].status == "carregada_com_avisos"
    with engine_super.connect() as c:
        assert c.execute(text("SELECT count(*) FROM ingest.ocorrencia WHERE codigo = 'HISTORY_WITHOUT_FILE'")).scalar()
    planilha(engine_etl, tmp_path)
    historico(engine_etl)
    assert foto(engine_super) == certo


def test_historico_nao_conta_como_arquivo_em_dobro(engine_etl, engine_super, tmp_path):
    gerar_planilha(tmp_path)
    planilha(engine_etl, tmp_path)
    historico(engine_etl)
    r = planilha(engine_etl, tmp_path)        # a planilha recarrega normalmente por cima do histórico
    assert [u.status for u in r.unidades] == ["carregada_com_avisos"]
    with engine_super.connect() as c:
        assert c.execute(text("SELECT count(*) FROM ingest.ocorrencia WHERE codigo = 'DUPLICATE_UNIT_FILE'")).scalar() == 0


def test_historico_nao_entra_nas_pendencias(engine_etl, engine_super, engine_api, tmp_path):
    """O histórico é carga única: corrigir a planilha antiga não muda nada, então ele fica fora da aba Pendências
    (a linha continua guardada na quarentena para a equipe)."""
    gerar_planilha(tmp_path)
    planilha(engine_etl, tmp_path)
    linhas = snapshot()
    linhas[PF]["meta_nascimentos"].append(_linha(data="0109/2024", qtd=5, categoria_bi="BEZERRO", peso_nasc=None,
                                                 safra="24/25", categ_fazenda=None))
    motor(engine_etl).executar(AdapterHistoricoPlanilha(engine_etl, ate=ATE, linhas=linhas), forcar=True)
    admin = criar_usuario(engine_super, "admin@terra.test", admin=True)
    with engine_super.connect() as c:
        fazenda = c.execute(text("SELECT id FROM core.fazenda")).scalar_one()
        guardada = c.execute(text("SELECT count(*) FROM ingest.linha_quarentena "
                                  "WHERE origem_linha LIKE 'meta_nascimentos%'")).scalar()
    assert guardada == 1
    with como_usuario(engine_api, admin) as s:
        origens = s.scalars(text("SELECT DISTINCT origem FROM app.pendencias_de_carga(CAST(:fazendas AS uuid[]))"),
                            {"fazendas": [str(fazenda)]}).all()
    assert origens == ["RELATÓRIO - 85 - TESTE.xlsx"]
