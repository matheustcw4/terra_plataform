"""Adapter de planilhas (planilha sintética no layout do template) e teste de equivalência planilha × Metryx."""

import json
import os
import shutil
import time
from datetime import date, datetime
from datetime import time as hora
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.etl.adapters.metryx import credenciais
from app.etl.adapters.planilha.adapter import AdapterPlanilha
from app.etl.adapters.planilha.leitor import ler_planilha
from app.etl.pipeline import MotorCarga
from tests.sinteticos import CLIENTE, FAZENDA, gerar_planilha
from tests.test_metryx import carregar as carregar_metryx

HOJE, ATE = date(2025, 10, 1), date(2025, 9, 1)


def carregar(pasta, **kw):
    return MotorCarga(_engine(), hoje=HOJE, estoque_ate=ATE).executar(AdapterPlanilha(pasta, estabilidade_s=0), **kw)


_ENGINE = {}


def _engine():
    return _ENGINE["etl"]


def contar(engine_super, sql, **p):
    with engine_super.connect() as c:
        return c.execute(text(sql), p).scalar()


def estoque(engine_super, fazenda_ext: str) -> dict:
    with engine_super.connect() as c:
        linhas = c.execute(text("""
            SELECT b.nome, e.competencia, e.saldo_final, e.nascimento, e.morte, e.desmame_saida, e.desmame_entrada,
                   e.venda_em_pe
            FROM fato.estoque_mensal e JOIN dim.categoria_bi b ON b.id = e.categoria_bi_id
            JOIN core.fonte_vinculo v ON v.entidade_id = e.fazenda_id AND v.entidade = 'fazenda'
            WHERE v.id_externo = :f AND e.competencia BETWEEN '2025-07-01' AND '2025-08-01'
        """), {"f": fazenda_ext}).all()
    return {(n, comp): tuple(Decimal(x) for x in resto) for n, comp, *resto in linhas}


def test_planilha_sintetica(engine_etl, engine_super, tmp_path):
    _ENGINE["etl"] = engine_etl
    gerar_planilha(tmp_path)
    r = carregar(tmp_path)
    u = r.unidades[0]
    assert u.status == "carregada_com_avisos", u.erro
    assert contar(engine_super, "SELECT id_externo FROM core.fonte_vinculo WHERE entidade = 'fazenda'") == "85|TESTE"
    jul = estoque(engine_super, "85|TESTE")[("BEZERRO", date(2025, 7, 1))]
    assert jul[0] == 815                                     # 1.000 + 120 − 5 − 300 (doc 01 §5.1)
    # venda em pé sem cliente é carregada (com aviso), não descartada
    assert contar(engine_super, "SELECT count(*) FROM fato.mov_animal WHERE tipo = 'VENDA_EM_PE'") == 1
    assert contar(engine_super, "SELECT count(*) FROM ingest.ocorrencia WHERE codigo = 'SALE_WITHOUT_CLIENT'") == 1
    # financeiro: conta traduzida pela própria planilha; conta desconhecida = 'A classificar'; sem natureza = quarentena
    with engine_super.connect() as c:
        dre = sorted(c.execute(text("SELECT centro_custo, classificacao, natureza, valor "
                                    "FROM fato.v_lancamento_financeiro")).all())
    assert dre == [("A classificar", "A CLASSIFICAR", "C", Decimal("200.00")),
                   ("Pastagens", "D - CUSTEIO", "D", Decimal("1500.50"))]
    assert contar(engine_super, "SELECT count(*) FROM ingest.linha_quarentena WHERE codigo = 'NATURE_UNKNOWN'") == 1
    assert contar(engine_super, "SELECT sum(qtd_cab) FROM fato.rebanho_medio_mensal WHERE cenario = 'realizado'") == 1550
    assert contar(engine_super, "SELECT area_total_ha FROM fato.area_mensal") == 1000


def test_linha_vazia_do_modelo_e_ignorada_e_linha_com_numero_sem_data_vai_para_quarentena(engine_etl, engine_super,
                                                                                         tmp_path):
    _ENGINE["etl"] = engine_etl
    adubo = ["PASTO", "ADUBO"]
    gerar_planilha(tmp_path, linhas={
        # o template traz linhas com preço/conta pré-preenchidos e nenhuma quantidade ou valor
        "fCompras": [["COMPRA", None, None, None, None, None, None, 2500, None, None, 480, None, None]],
        "fDre": [[*adubo, 1500.5, datetime(2025, 7, 15), "D", "Pastagens", "Adubação"],
                 [*adubo, None, datetime(2025, 8, 1), "D", "Pastagens", "Adubação"],
                 [*adubo, 0, datetime(2025, 8, 1), "VERIFICAR", "Pastagens", "Adubação"],
                 [*adubo, 50, None, "D", "Pastagens", "Adubação"],               # tem valor, falta a data
                 # a planilha marcou VERIFICAR: não soma, como no BI, mesmo a conta estando no ConsultaPlanoContas
                 [*adubo, 70, datetime(2025, 7, 20), "VERIFICAR", "Pastagens", "Adubação"]],
    })
    carregar(tmp_path)
    with engine_super.connect() as c:
        quarentena = c.execute(text("SELECT origem_linha, codigo FROM ingest.linha_quarentena ORDER BY 1")).all()
    assert quarentena == [("fDre!5", "REQUIRED_MISSING"), ("fDre!6", "NATURE_UNKNOWN")]
    assert contar(engine_super, "SELECT count(*) FROM fato.lancamento_financeiro") == 1
    assert contar(engine_super, "SELECT count(*) FROM fato.mov_animal WHERE tipo = 'COMPRA'") == 0


def test_bruto_e_json_mesmo_com_celula_formatada_como_hora(tmp_path):
    """O calamine devolve datetime.time para célula de hora; o bruto vai para raw.payload (JSONB)."""
    arq = gerar_planilha(tmp_path, linhas={"fMortes": [
        ["MORTE", datetime(2025, 7, 12), "Bezerro Mamando", hora(8, 30), 5, "Cobra", "Pasto 1", 40, "25/26"]]})
    conteudo = ler_planilha(arq.read_bytes())
    json.dumps(conteudo)
    assert conteudo["abas"]["fMortes"][0]["CARIMBO_BEZ"] == "08:30:00"


def test_planilha_inalterada_nao_e_relida_e_periodo_novo_preserva_o_anterior(engine_etl, engine_super, tmp_path):
    _ENGINE["etl"] = engine_etl
    arq = gerar_planilha(tmp_path)
    carregar(tmp_path)
    assert carregar(tmp_path).unidades[0].status == "inalterada"
    # o consultor troca o PERÍODO (aqui para CIVIL 2025): novo checkpoint, o de jun/2025 continua lá
    gerar_planilha(tmp_path, periodo="CIVIL 2025", saldo_bezerro=900)
    os.utime(arq, (time.time() - 120, time.time() - 120))
    carregar(tmp_path)
    with engine_super.connect() as c:
        datas = {d for (d,) in c.execute(text("SELECT DISTINCT data FROM fato.inventario"))}
    assert datas == {date(2025, 6, 30), date(2024, 12, 31)}


def test_planilha_vazia_da_safra_nova_nao_apaga_a_safra_anterior(engine_etl, engine_super, tmp_path):
    """Na virada de safra o consultor começa a planilha do zero: o arquivo só responde do PERÍODO dele em diante."""
    _ENGINE["etl"] = engine_etl
    nasc_2408 = ["NASCIMENTO", datetime(2024, 8, 10), "Bezerro Mamando", 50, "24/25", 30]
    safra_2425 = {"fNascimento": [nasc_2408], "fMortes": [], "fdesmame": [], "fVendaemPe": [],
                  "fDre": [["PASTO", "ADUBO", 300, datetime(2024, 8, 15), "D", "Pastagens", "Adubação"]]}
    arq = gerar_planilha(tmp_path, periodo="SAFRA 24/25", linhas=safra_2425)
    os.utime(arq, (time.time() - 600, time.time() - 600))
    carregar(tmp_path)

    def nascimentos() -> dict:
        with engine_super.connect() as c:
            return dict(c.execute(text("SELECT competencia, sum(qtd) FROM fato.mov_animal WHERE tipo = 'NASCIMENTO' "
                                       "GROUP BY 1")).all())

    gerar_planilha(tmp_path)                      # SAFRA 25/26 do zero: só lançamentos de jul-ago/2025
    os.utime(arq, (time.time() - 300, time.time() - 300))
    carregar(tmp_path)
    assert nascimentos() == {date(2024, 8, 1): 50, date(2025, 7, 1): 120}
    assert contar(engine_super, "SELECT count(*) FROM fato.lancamento_financeiro WHERE competencia = '2024-08-01'") == 1

    # planilha cumulativa (traz a safra anterior de novo): substitui desde a linha mais antiga, sem duplicar
    gerar_planilha(tmp_path, linhas={"fNascimento": [
        nasc_2408, ["NASCIMENTO", datetime(2025, 7, 10), "Bezerro Mamando", 120, "25/26", 32]]})
    os.utime(arq, (time.time() - 120, time.time() - 120))
    carregar(tmp_path)
    assert nascimentos() == {date(2024, 8, 1): 50, date(2025, 7, 1): 120}


def test_codigo_do_arquivo_diferente_da_planilha_nao_carrega(engine_etl, engine_super, tmp_path):
    _ENGINE["etl"] = engine_etl
    gerar_planilha(tmp_path, nome="RELATÓRIO - 99 - TESTE.xlsx", codigo=85)
    r = carregar(tmp_path)
    assert r.unidades[0].status == "erro" and "código" in r.unidades[0].erro
    assert contar(engine_super, "SELECT count(*) FROM core.fazenda") == 0


def test_planilha_montada_a_partir_de_outra_fazenda_nao_carrega(engine_etl, engine_super, tmp_path):
    """Caso real (15 · GUARÁ 1): fUnidade sem código e com a fazenda de outra planilha."""
    _ENGINE["etl"] = engine_etl
    gerar_planilha(tmp_path, nome="RELATÓRIO - 85 - GUARÁ 1.xlsx", codigo=None, fazenda="AGRO ZAFANELLI (AZS)")
    r = carregar(tmp_path)
    assert r.unidades[0].status == "erro" and "corrija o fUnidade" in r.unidades[0].erro
    assert contar(engine_super, "SELECT count(*) FROM core.fazenda") == 0


@pytest.mark.parametrize("nome_velho, nome_novo", [
    ("RELATÓRIO - 85 - TESTE.xlsx", "RELATÓRIO - 85 - TESTE (1).xlsx"),
    ("RELATÓRIO - 85 - TESTE (1).xlsx", "RELATÓRIO - 85 - TESTE.xlsx"),     # o velho vem antes na ordem alfabética
])
def test_arquivo_em_dobro_vale_o_mais_recente(engine_etl, engine_super, tmp_path, nome_velho, nome_novo):
    _ENGINE["etl"] = engine_etl
    velho = gerar_planilha(tmp_path, nome=nome_velho, saldo_bezerro=1000)
    novo = gerar_planilha(tmp_path, nome=nome_novo, saldo_bezerro=700)
    os.utime(velho, (time.time() - 3600, time.time() - 3600))
    os.utime(novo, (time.time() - 120, time.time() - 120))
    r = carregar(tmp_path)
    assert {u.chave: u.status for u in r.unidades} == {nome_novo: "carregada_com_avisos", nome_velho: "ignorada"}
    with engine_super.connect() as c:          # o arquivo ignorado não é erro: lido, não carregado
        status = c.execute(text("SELECT u.status, v.status FROM ingest.unidade_origem u JOIN ingest.versao_origem v "
                                "ON v.unidade_id = u.id WHERE u.chave = :c"), {"c": nome_velho}).one()
    assert tuple(status) == ("ignorada", "extraida")
    assert contar(engine_super, "SELECT count(*) FROM core.fazenda") == 1
    assert estoque(engine_super, "85|TESTE")[("BEZERRO", date(2025, 7, 1))][0] == 515   # 700 + 120 − 5 − 300


def test_copia_identica_com_outro_nome_vale_so_a_mais_recente(engine_etl, engine_super, tmp_path):
    """Planilha enviada duas vezes com nomes diferentes. Aqui o pior caso: fUnidade sem código e a cópia antiga com
    outro código no nome, o que faria dela uma segunda fazenda com os mesmos dados."""
    _ENGINE["etl"] = engine_etl
    velho = gerar_planilha(tmp_path, nome="RELATÓRIO - 58 - TESTE.xlsx", codigo=None)
    os.utime(velho, (time.time() - 3600, time.time() - 3600))
    carregar(tmp_path)                               # a cópia antiga chegou primeiro e virou a fazenda 58|TESTE
    movs = contar(engine_super, "SELECT count(*) FROM fato.mov_animal")
    novo = tmp_path / "RELATÓRIO - 85 - TESTE (1).xlsx"
    shutil.copyfile(velho, novo)                     # mesmos bytes, outro nome
    os.utime(novo, (time.time() - 120, time.time() - 120))

    def status(r):
        return {u.chave: u.status for u in r.unidades}

    def movs_por_fazenda():
        with engine_super.connect() as c:
            return dict(c.execute(text(
                "SELECT v.id_externo, count(m.id) FROM core.fonte_vinculo v "
                "LEFT JOIN fato.mov_animal m ON m.fazenda_id = v.entidade_id WHERE v.entidade = 'fazenda' "
                "GROUP BY 1")).all())

    assert status(carregar(tmp_path)) == {novo.name: "carregada_com_avisos", velho.name: "ignorada"}
    assert movs_por_fazenda() == {"85|TESTE": movs, "58|TESTE": 0}           # nada em dobro
    assert contar(engine_super, "SELECT count(*) FROM ingest.ocorrencia WHERE codigo = 'DUPLICATE_CONTENT'") >= 1
    # nas cargas seguintes a cópia continua ignorada, sem nem ser normalizada
    assert status(carregar(tmp_path)) == {novo.name: "inalterada", velho.name: "ignorada"}
    assert movs_por_fazenda() == {"85|TESTE": movs, "58|TESTE": 0}


def test_arquivo_em_dobro_avisa_quando_o_ignorado_tem_mais_dados(engine_etl, engine_super, tmp_path):
    """O critério é a data de modificação: se a versão ignorada é a mais completa, o aviso diz para conferir."""
    _ENGINE["etl"] = engine_etl
    nascimentos = [["NASCIMENTO", datetime(2025, 7, 10), "Bezerro Mamando", 120, "25/26", 32],
                   ["NASCIMENTO", datetime(2025, 7, 11), "Bezerro Mamando", 3, "25/26", 32]]
    velho = gerar_planilha(tmp_path, nome="RELATÓRIO - 85 - TESTE.xlsx", linhas={"fNascimento": nascimentos})
    novo = gerar_planilha(tmp_path, nome="RELATÓRIO - 85 - TESTE (1).xlsx")
    os.utime(velho, (time.time() - 3600, time.time() - 3600))
    os.utime(novo, (time.time() - 120, time.time() - 120))
    carregar(tmp_path)
    mensagem = contar(engine_super, "SELECT mensagem FROM ingest.ocorrencia WHERE codigo = 'DUPLICATE_UNIT_FILE'")
    assert "ATENÇÃO" in mensagem and "mais linhas" in mensagem


def test_equivalencia_planilha_e_metryx(engine_etl, engine_super, tmp_path):
    """docs/01 §7: a mesma fazenda escrita como planilha e como JSON do Metryx gera o mesmo estoque e os mesmos fluxos."""
    _ENGINE["etl"] = engine_etl
    gerar_planilha(tmp_path)
    carregar(tmp_path)
    credenciais.registrar(engine_etl, CLIENTE, "token-teste", "Cliente Teste")
    carregar_metryx(engine_etl)
    with engine_super.begin() as c:     # consultor confirma as sugestões de categoria do Metryx
        c.execute(text("UPDATE dim.categoria_map SET categoria_bi_id = categoria_bi_sugerida_id "
                       "WHERE categoria_bi_id IS NULL"))
    with engine_etl.begin() as c:
        c.execute(text("SELECT fato.recalcular_estoque_mensal(array_agg(id), '2025-09-01') FROM core.fazenda"))
    planilha = estoque(engine_super, "85|TESTE")
    metryx = estoque(engine_super, f"{CLIENTE}|fa000000-0000-0000-0000-000000000001")
    assert planilha and planilha == metryx
    # a mesma área de pasto em julho (planilha: pasto 800 + ILP 200; Metryx: duas pastagens de uso Pecuária)
    with engine_super.connect() as c:
        areas = c.execute(text("""
            SELECT v.id_externo, a.area_total_ha FROM fato.area_mensal a
            JOIN core.fonte_vinculo v ON v.entidade_id = a.fazenda_id AND v.entidade = 'fazenda'
            WHERE a.cenario = 'realizado' AND a.competencia = '2025-07-01'""")).all()
    assert {externo: float(area) for externo, area in areas} == {"85|TESTE": 1000.0, f"{CLIENTE}|{FAZENDA}": 1000.0}


def test_data_tem_de_ser_o_texto_inteiro():
    """Digitação errada não vira outra data (o BI também descarta a linha; aqui ela vai para a quarentena)."""
    from app.etl.adapters.planilha.normalizar import para_data as _data
    assert _data("05/11/225") is None and _data("24/11/250") is None
    assert _data("2025-07-01T04:00:00") == date(2025, 7, 1)
    assert _data("2025/07/01 00:00:00.000") == date(2025, 7, 1)
    assert _data("5/11/2025") == _data("05/11/25") == date(2025, 11, 5)
    assert _data("11/2025") == date(2025, 11, 1)
    assert _data(45658) == date(2025, 1, 1)


def test_total_que_nao_bate_com_o_valor_por_cabeca_vira_aviso_na_linha(engine_etl, engine_super, tmp_path):
    """TOTAL_PESO dobrado (500 cab × 270 kg = 135.000, mas o total diz 270.000): o total entra, como no BI, e o aviso
    aponta a linha para alguém corrigir a planilha."""
    compras = [["COMPRA", datetime(2025, 7, 5), "Leilão", "Bezerro Mamando", 500, 270, 270000, None, 1442695]]
    gerar_planilha(tmp_path, linhas={"fCompras": compras})
    MotorCarga(engine_etl, hoje=date(2025, 10, 1)).executar(AdapterPlanilha(tmp_path, estabilidade_s=0))
    with engine_super.connect() as c:
        aviso = c.execute(text("SELECT origem_linha, mensagem FROM ingest.ocorrencia "
                               "WHERE codigo = 'TOTAL_INCONSISTENT'")).one()
        peso = c.execute(text("SELECT peso_vivo_total_kg FROM fato.mov_animal WHERE tipo = 'COMPRA'")).scalar_one()
    assert aviso.origem_linha == "fCompras!2"
    assert "TOTAL_PESO = 270.000,00" in aviso.mensagem and "135.000,00" in aviso.mensagem
    assert peso == 270000
