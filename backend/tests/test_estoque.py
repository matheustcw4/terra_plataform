"""Estoque = checkpoints + fluxos, mesma regra para as duas fontes (docs/01 §5.1)."""

from datetime import date
from decimal import Decimal

from sqlalchemy import text

from app.etl.pipeline import MotorCarga
from tests.fabrica import AdapterMemoria, checkpoint, exemplo_doc01, lote_base, mov, particoes_pecuario

HOJE = date(2025, 10, 1)
ATE = date(2025, 9, 1)


def _carregar(engine_etl, lote, chave="u1"):
    res = MotorCarga(engine_etl, hoje=HOJE, estoque_ate=ATE).executar(AdapterMemoria(lote.fonte, {chave: lote}))
    assert res.unidades[0].status.startswith("carregada"), res.unidades[0].erro


def _estoque(engine_super, categoria: str, competencia: date) -> dict:
    with engine_super.connect() as c:
        row = c.execute(text("""
            SELECT e.* FROM fato.estoque_mensal e JOIN dim.categoria_bi b ON b.id = e.categoria_bi_id
            WHERE b.nome = :cat AND e.competencia = :comp
        """), {"cat": categoria, "comp": competencia}).mappings().one()
    return {k: (v if not isinstance(v, Decimal) else int(v)) for k, v in row.items()}


def test_exemplo_doc01_planilha(engine_etl, engine_super):
    _carregar(engine_etl, exemplo_doc01("planilha"))
    jul = _estoque(engine_super, "BEZERRO", date(2025, 7, 1))
    assert (jul["saldo_inicial"], jul["nascimento"], jul["morte"], jul["desmame_saida"]) == (1000, 120, 5, 300)
    assert (jul["ajuste"], jul["saldo_final"]) == (0, 815)
    destino = _estoque(engine_super, "MACHOS 8-12", date(2025, 7, 1))
    assert (destino["desmame_entrada"], destino["saldo_final"]) == (300, 300)
    # meses sem movimento repetem o saldo até o fim
    set_ = _estoque(engine_super, "BEZERRO", date(2025, 9, 1))
    assert (set_["saldo_inicial"], set_["saldo_final"], set_["ajuste"]) == (815, 815, 0)
    # o mês do checkpoint inicial mostra o saldo como ajuste de abertura
    jun = _estoque(engine_super, "BEZERRO", date(2025, 6, 1))
    assert (jun["saldo_inicial"], jun["ajuste"], jun["saldo_final"]) == (0, 1000, 1000)


def test_exemplo_doc01_metryx_mostra_ajuste(engine_etl, engine_super):
    lote = exemplo_doc01("metryx", com_checkpoint_julho=True, cliente="777", fazenda="777|9",
                         fonte_mapa="metryx_realizado", escopo="cliente")
    _carregar(engine_etl, lote)
    jul = _estoque(engine_super, "BEZERRO", date(2025, 7, 1))
    assert (jul["saldo_inicial"], jul["ajuste"], jul["saldo_final"]) == (1000, -3, 812)


def test_fluxos_antes_do_primeiro_checkpoint_da_fazenda_sao_ignorados(engine_etl, engine_super):
    lote = exemplo_doc01("planilha")
    bez = lote.categorias[0].chave
    lote.mov_animal.append(mov("COMPRA", date(2024, 3, 1), bez, 999, 99))   # histórico anterior ao período
    _carregar(engine_etl, lote)
    assert _estoque(engine_super, "BEZERRO", date(2025, 7, 1))["saldo_final"] == 815
    with engine_super.connect() as c:
        assert c.scalar(text("SELECT min(competencia) FROM fato.estoque_mensal")) == date(2025, 6, 1)


def test_compra_que_abre_serie_nova_conta_como_compra(engine_etl, engine_super):
    """A28: o retiro ainda não tinha touro; o balanço do Metryx só registra a série no fim do mês da compra."""
    lote = lote_base(categorias={"VACA": "MATRIZES", "TOURO NELORE": "TOUROS"})
    vaca, touro = (c.chave for c in lote.categorias)
    lote.inventario = [checkpoint(date(2025, 6, 30), vaca, 100, 1), checkpoint(date(2025, 7, 31), touro, 7, 2)]
    lote.mov_animal = [mov("COMPRA", date(2025, 7, 7), touro, 7, 1)]
    lote.particoes = particoes_pecuario()
    _carregar(engine_etl, lote)
    jul = _estoque(engine_super, "TOUROS", date(2025, 7, 1))
    assert (jul["saldo_inicial"], jul["compra"], jul["ajuste"], jul["saldo_final"]) == (0, 7, 0, 7)


def test_serie_que_nao_esta_no_inicio_da_fazenda_comeca_em_zero(engine_etl, engine_super):
    """Os meses até o 1º checkpoint da série somam os fluxos desde zero; o checkpoint corrige o que não fechar.

    É o caso da categoria do histórico sem saldo anterior, que recebe checkpoint 0 na virada para o arquivo.
    """
    lote = lote_base()
    bezerro, desmama = (c.chave for c in lote.categorias)
    lote.inventario = [checkpoint(date(2025, 6, 30), desmama, 50, 1), checkpoint(date(2025, 9, 30), bezerro, 0, 2)]
    lote.mov_animal = [
        mov("NASCIMENTO", date(2025, 5, 10), bezerro, 99, 1),   # antes do início da fazenda: já está no retrato
        mov("NASCIMENTO", date(2025, 7, 10), bezerro, 20, 2),
        mov("MORTE", date(2025, 8, 5), bezerro, 2, 3),
    ]
    lote.particoes = particoes_pecuario()
    _carregar(engine_etl, lote)
    jul = _estoque(engine_super, "BEZERRO", date(2025, 7, 1))
    assert (jul["saldo_inicial"], jul["nascimento"], jul["ajuste"], jul["saldo_final"]) == (0, 20, 0, 20)
    ago = _estoque(engine_super, "BEZERRO", date(2025, 8, 1))
    assert (ago["saldo_inicial"], ago["morte"], ago["ajuste"], ago["saldo_final"]) == (20, 2, 0, 18)
    set_ = _estoque(engine_super, "BEZERRO", date(2025, 9, 1))
    assert (set_["saldo_inicial"], set_["ajuste"], set_["saldo_final"]) == (18, -18, 0)


def test_categorias_de_origem_somam_sem_misturar_checkpoints(engine_etl, engine_super):
    """Duas categorias da fonte caem em MATRIZES com checkpoints em datas diferentes: cada uma segue o seu."""
    lote = lote_base(categorias={"VACA PARIDA": "MATRIZES", "VACA SOLTEIRA": "MATRIZES"})
    parida, solteira = (c.chave for c in lote.categorias)
    lote.inventario = [checkpoint(date(2025, 3, 10), parida, 50, 1), checkpoint(date(2025, 3, 20), solteira, 30, 2)]
    lote.mov_animal = [mov("MORTE", date(2025, 3, 15), parida, 2, 1), mov("COMPRA", date(2025, 4, 5), solteira, 10, 2)]
    lote.particoes = particoes_pecuario()
    _carregar(engine_etl, lote)
    assert _estoque(engine_super, "MATRIZES", date(2025, 3, 1))["saldo_final"] == 48 + 30
    abr = _estoque(engine_super, "MATRIZES", date(2025, 4, 1))
    assert (abr["saldo_inicial"], abr["compra"], abr["saldo_final"]) == (78, 10, 88)


def test_mesmo_dia_checkpoint_ja_contem_os_fluxos(engine_etl, engine_super):
    lote = lote_base(categorias={"BOI": "MACHOS + 36"})
    boi = lote.categorias[0].chave
    lote.inventario = [checkpoint(date(2025, 5, 1), boi, 100, 1), checkpoint(date(2025, 5, 20), boi, 90, 2)]
    lote.mov_animal = [mov("ABATE", date(2025, 5, 20), boi, 10, 1)]   # já refletido no checkpoint de 20/05
    lote.particoes = particoes_pecuario()
    _carregar(engine_etl, lote)
    mai = _estoque(engine_super, "MACHOS + 36", date(2025, 5, 1))
    assert (mai["abate"], mai["ajuste"], mai["saldo_final"]) == (10, 100, 90)   # abertura 100, sem ajuste extra
