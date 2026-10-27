"""Comportamento do motor: idempotência, substituir × mesclar, quarentena, fonte ativa, pendências, reprocessamento."""

from datetime import date
from decimal import Decimal

from sqlalchemy import Engine, text

from app.etl.canonical import (
    ContaOrigem,
    LancamentoFinanceiro,
    Particao,
    RebanhoMedio,
)
from app.etl.duplicatas import mensagem_em_dobro
from app.etl.pipeline import MotorCarga
from tests.fabrica import AdapterMemoria, exemplo_doc01, lote_base, mov

HOJE = date(2025, 10, 1)


def motor(engine_etl):
    return MotorCarga(engine_etl, hoje=HOJE, estoque_ate=date(2025, 9, 1))


def contar(engine_super: Engine, sql: str, **p) -> int:
    with engine_super.connect() as c:
        return c.execute(text(sql), p).scalar()


def foto_fatos(engine_super: Engine) -> list:
    """Conteúdo dos fatos sem ids/datas técnicas (para comparar cargas)."""
    with engine_super.connect() as c:
        return sorted(c.execute(text(
            "SELECT tipo, data, qtd, categoria_map_id, categoria_destino_map_id, origem_linha FROM fato.mov_animal"
        )).all()) + sorted(c.execute(text(
            "SELECT categoria_bi_id, competencia, saldo_final, ajuste FROM fato.estoque_mensal")).all())


def test_carga_e_idempotente(engine_etl, engine_super):
    adapter = AdapterMemoria("planilha", {"u1": exemplo_doc01()})
    r1 = motor(engine_etl).executar(adapter)
    assert r1.status == "concluido" and r1.unidades[0].gravadas["mov_animal"] == 3
    foto = foto_fatos(engine_super)

    r2 = motor(engine_etl).executar(adapter)                 # mesmo conteúdo: nem recarrega
    assert r2.unidades[0].status == "inalterada"

    r3 = motor(engine_etl).executar(adapter, forcar=True)    # forçado: recarrega e dá o mesmo resultado
    assert r3.unidades[0].status == "carregada"
    assert foto_fatos(engine_super) == foto
    assert contar(engine_super, "SELECT count(*) FROM core.fazenda") == 1
    assert contar(engine_super, "SELECT count(*) FROM ingest.versao_origem") == 1


def test_substituir_remove_o_que_saiu_da_fonte(engine_etl, engine_super):
    lote = exemplo_doc01()
    motor(engine_etl).executar(AdapterMemoria("planilha", {"u1": lote}))
    lote2 = lote.model_copy(update={"mov_animal": lote.mov_animal[:1]})   # o consultor apagou 2 lançamentos
    r = motor(engine_etl).executar(AdapterMemoria("planilha", {"u1": lote2}))
    assert r.unidades[0].apagadas["mov_animal"] == 3 and r.unidades[0].gravadas["mov_animal"] == 1
    assert contar(engine_super, "SELECT count(*) FROM fato.mov_animal") == 1
    assert contar(engine_super, "SELECT count(*) FROM ingest.versao_origem WHERE status = 'substituida'") == 1


def _rebanho(lote, meses: list[date], qtd: int):
    fazenda = lote.fazendas[0].id_externo
    return [RebanhoMedio(fazenda=fazenda, cenario="realizado", competencia=m, grupo="ADULTOS", qtd_cab=Decimal(qtd),
                         origem_linha=f"fRebanhoMedio!{i}") for i, m in enumerate(meses, 2)]


def test_mesclar_preserva_meses_fora_do_periodo(engine_etl, engine_super):
    """Planilha: trocar o PERÍODO (SAFRA 24/25 -> 25/26) não apaga o histórico de rebanho médio."""
    base = lote_base()
    p = [Particao(entidade="rebanho_medio", fazenda="85|BELA VISTA", cenario="realizado", estrategia="mesclar")]
    safra_24 = [date(2024 + (m < 7), m, 1) for m in (*range(7, 13), *range(1, 7))]
    safra_25 = [date(2025 + (m < 7), m, 1) for m in (*range(7, 13), *range(1, 7))]
    v1 = base.model_copy(update={"rebanho_medio": _rebanho(base, safra_24, 100), "particoes": p})
    v2 = base.model_copy(update={"rebanho_medio": _rebanho(base, safra_25, 200), "particoes": p})
    motor(engine_etl).executar(AdapterMemoria("planilha", {"u1": v1}))
    motor(engine_etl).executar(AdapterMemoria("planilha", {"u1": v2}))
    assert contar(engine_super, "SELECT count(*) FROM fato.rebanho_medio_mensal") == 24
    assert contar(engine_super, "SELECT qtd_cab FROM fato.rebanho_medio_mensal WHERE competencia = '2024-07-01'") == 100


def test_contrato_invalido_nao_grava_nada(engine_etl, engine_super):
    lote = exemplo_doc01()
    lote.particoes = lote.particoes[:1]   # inventário sem partição declarada
    r = motor(engine_etl).executar(AdapterMemoria("planilha", {"u1": lote}))
    assert r.status == "erro" and "contrato" in r.unidades[0].erro
    assert contar(engine_super, "SELECT count(*) FROM fato.mov_animal") == 0
    assert contar(engine_super, "SELECT count(*) FROM core.fazenda") == 0
    assert contar(engine_super, "SELECT count(*) FROM ingest.ocorrencia WHERE codigo = 'CONTRACT_VIOLATION'") == 1


def test_desde_substitui_so_a_partir_do_mes(engine_etl, engine_super):
    motor(engine_etl).executar(AdapterMemoria("planilha", {"u1": exemplo_doc01()}))          # julho/2025
    agosto = exemplo_doc01()
    fazenda, bez = agosto.fazendas[0].id_externo, agosto.categorias[0].chave
    agosto.mov_animal = [mov("NASCIMENTO", date(2025, 8, 3), bez, 7, 9, fazenda)]
    agosto.particoes = [p.model_copy(update={"desde": date(2025, 8, 1)}) if p.entidade == "mov_animal" else p
                        for p in agosto.particoes]
    r = motor(engine_etl).executar(AdapterMemoria("planilha", {"u1": agosto}))
    assert r.unidades[0].status == "carregada", r.unidades[0].erro
    assert contar(engine_super, "SELECT count(*) FROM fato.mov_animal WHERE competencia = '2025-07-01'") == 3
    assert contar(engine_super, "SELECT count(*) FROM fato.mov_animal WHERE competencia = '2025-08-01'") == 1
    # linha anterior ao 'desde' ficaria fora do recorte e duplicaria a cada recarga: erro de contrato
    agosto.mov_animal.append(mov("MORTE", date(2025, 7, 30), bez, 1, 10, fazenda))
    assert any("coberta por 0" in e for e in agosto.validar_contrato())


def test_mensagem_do_arquivo_em_dobro_diz_se_e_copia_ou_outra_versao():
    lote = exemplo_doc01()
    igual = {"impressao_dados": lote.impressao_dados(), "linhas_dados": lote.linhas_dados()}
    assert "mesmo conteúdo" in mensagem_em_dobro("novo.xlsm", igual, lote)
    maior = {"impressao_dados": "outra", "linhas_dados": lote.linhas_dados() + 10}
    assert "conteúdo diferente" in mensagem_em_dobro("novo.xlsm", maior, lote)
    menor = {"impressao_dados": "outra", "linhas_dados": 1}
    assert "ATENÇÃO" in mensagem_em_dobro("novo.xlsm", menor, lote)


def test_erro_numa_unidade_nao_derruba_as_outras(engine_etl, engine_super):
    lotes = {"ok": exemplo_doc01(), "ruim": exemplo_doc01(cliente="2", fazenda="2|X", nome_fazenda="X"),
             "nao_json": exemplo_doc01(cliente="3", fazenda="3|Y", nome_fazenda="Y")}
    r = motor(engine_etl).executar(AdapterMemoria("planilha", lotes, falhar_extracao={"ruim"},
                                                  bruto_nao_json={"nao_json"}))
    assert {u.chave: u.status for u in r.unidades} == {"ok": "carregada", "ruim": "erro", "nao_json": "erro"}
    assert r.status == "concluido_com_avisos"
    assert contar(engine_super, "SELECT count(*) FROM fato.mov_animal") == 3


def _financeiro(lote, contas: list[ContaOrigem]):
    fazenda = lote.fazendas[0].id_externo
    lote.lancamentos = [LancamentoFinanceiro(fazenda=fazenda, conta=c, natureza="D", valor=Decimal("100.50"),
                                             data_pagamento=date(2025, 8, 5), origem_linha=f"fDre!{i}")
                        for i, c in enumerate(contas, 2)]
    lote.particoes = [Particao(entidade="lancamento", fazenda=fazenda, cenario="realizado", estrategia="substituir")]
    return lote


def _dre(engine_super) -> list[tuple]:
    with engine_super.connect() as c:
        return sorted(c.execute(text("SELECT centro_custo, classificacao, a_classificar, valor "
                                     "FROM fato.v_lancamento_financeiro")).all())


def test_conta_fora_do_plano_entra_como_a_classificar(engine_etl, engine_super):
    """Decisão Q1: nada some do caixa. A conta desconhecida carrega como 'A classificar' (o total bate com a fonte)."""
    lote = _financeiro(lote_base(), [ContaOrigem(centro="  pastagens "),          # nome canônico (sem acento/caixa)
                                     ContaOrigem(centro="Transportadora Itapajé", subcentro="Fretes")])
    r = motor(engine_etl).executar(AdapterMemoria("planilha", {"u1": lote}))
    u = r.unidades[0]
    assert (u.status, u.gravadas["lancamento"], u.quarentena) == ("carregada_com_avisos", 2, 0)
    assert _dre(engine_super) == [("A classificar", "A CLASSIFICAR", True, Decimal("100.50")),
                                  ("Pastagens", "D - CUSTEIO", False, Decimal("100.50"))]
    assert contar(engine_super, "SELECT count(*) FROM ingest.ocorrencia WHERE codigo = 'ACCOUNT_UNCLASSIFIED'") == 1
    assert contar(engine_super, "SELECT count(*) FROM dim.plano_contas_map WHERE centro_custo_id IS NULL "
                                "AND nome_centro_origem = 'Transportadora Itapajé'") == 1

    # o admin classifica a conta: o histórico é reclassificado sem recarga
    with engine_super.begin() as c:
        c.execute(text("UPDATE dim.plano_contas_map SET confirmado_em = now(), centro_custo_id = "
                       "(SELECT id FROM dim.centro_custo WHERE nome = 'Outros Débitos') WHERE centro_custo_id IS NULL"))
    assert _dre(engine_super)[0] == ("Outros Débitos", "F - OUTROS DÉBITOS", False, Decimal("100.50"))

    # recarga usa o de-para classificado (não cria pendência nova)
    r = motor(engine_etl).executar(AdapterMemoria("planilha", {"u1": lote}), forcar=True)
    assert r.unidades[0].status == "carregada"
    assert contar(engine_super, "SELECT count(*) FROM dim.plano_contas_map WHERE centro_custo_id IS NULL") == 0


def test_fonte_inativa_no_dominio_e_ignorada(engine_etl, engine_super):
    motor(engine_etl).executar(AdapterMemoria("planilha", {"u1": exemplo_doc01()}))
    with engine_super.begin() as c:   # cliente híbrido: o financeiro desta fazenda vem do Metryx
        c.execute(text("UPDATE core.fazenda_fonte SET fonte = 'metryx' WHERE dominio = 'financeiro_realizado'"))
    lote = _financeiro(lote_base(), [ContaOrigem(centro="Pastagens")])
    r = motor(engine_etl).executar(AdapterMemoria("planilha", {"u2": lote}))
    assert r.unidades[0].gravadas["lancamento"] == 0
    assert contar(engine_super, "SELECT count(*) FROM fato.lancamento_financeiro") == 0
    assert contar(engine_super,
                  "SELECT count(*) FROM ingest.ocorrencia WHERE codigo = 'SOURCE_INACTIVE_FOR_DOMAIN'") == 1


def test_categoria_pendente_entra_mas_fica_fora_do_estoque_ate_confirmar(engine_etl, engine_super):
    """Metryx: a fonte só sugere a categoria BI; o consultor confirma (D6). Confirmar reclassifica sem recarga."""
    lote = exemplo_doc01("metryx", cliente="777", fazenda="777|9", fonte_mapa="metryx_realizado", escopo="cliente",
                         confirmadas=False)
    r = motor(engine_etl).executar(AdapterMemoria("metryx", {"777:balanco": lote}))
    assert r.unidades[0].status == "carregada_com_avisos"
    assert contar(engine_super, "SELECT count(*) FROM fato.mov_animal") == 3
    assert contar(engine_super, "SELECT count(*) FROM fato.estoque_mensal") == 0
    assert contar(engine_super, "SELECT count(*) FROM ingest.ocorrencia WHERE codigo = 'CATEGORY_UNMAPPED'") == 2

    with engine_super.begin() as c:   # consultor aceita as sugestões
        c.execute(text("UPDATE dim.categoria_map SET categoria_bi_id = categoria_bi_sugerida_id, "
                       "confirmado_em = now()"))
        fazenda = c.execute(text("SELECT id FROM core.fazenda")).scalar()
    with engine_etl.begin() as c:
        c.execute(text("SELECT fato.recalcular_estoque_mensal(ARRAY[CAST(:f AS uuid)], '2025-09-01')"), {"f": fazenda})
    assert contar(engine_super, "SELECT saldo_final FROM fato.estoque_mensal e JOIN dim.categoria_bi b "
                                "ON b.id = e.categoria_bi_id WHERE b.nome = 'BEZERRO' AND competencia = '2025-07-01'") \
        == 815

    # nova carga com sugestão diferente não desfaz a confirmação
    motor(engine_etl).executar(AdapterMemoria("metryx", {"777:balanco": lote}), forcar=True)
    assert contar(engine_super, "SELECT count(*) FROM dim.categoria_map WHERE categoria_bi_id IS NULL") == 0


def test_reprocessa_a_partir_do_bruto_guardado(engine_etl, engine_super):
    adapter = AdapterMemoria("metryx", {"777:x": exemplo_doc01("metryx", cliente="777", fazenda="777|9")})
    r = motor(engine_etl).executar(adapter)
    versao = r.unidades[0].versao_id
    assert contar(engine_super, "SELECT count(*) FROM raw.payload WHERE versao_origem_id = :v", v=versao) == 1
    adapter.lotes.clear()   # a fonte "sumiu": o reprocessamento usa só o bruto
    r2 = motor(engine_etl).reprocessar(adapter, versao)
    assert r2.status == "carregada" and r2.gravadas["mov_animal"] == 3


def test_data_absurda_vai_para_quarentena(engine_etl, engine_super):
    lote = exemplo_doc01()
    lote.mov_animal[0] = lote.mov_animal[0].model_copy(update={"data": date(2031, 1, 1)})
    r = motor(engine_etl).executar(AdapterMemoria("planilha", {"u1": lote}))
    assert (r.unidades[0].gravadas["mov_animal"], r.unidades[0].quarentena) == (2, 1)
    assert contar(engine_super, "SELECT count(*) FROM ingest.linha_quarentena WHERE codigo = 'DATE_OUT_OF_RANGE'") == 1
