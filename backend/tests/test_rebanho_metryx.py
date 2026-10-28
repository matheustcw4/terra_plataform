"""Rebanho médio realizado do Metryx: média do saldo de cada dia do balanço, como o relatório do Metryx (27/10/2026:
U6, jul–set/2026, 7.705 cab no Metryx e na plataforma; o endpoint `rebanho-medio-pecuario` do BI dava 8.505)."""

from datetime import date
from decimal import Decimal

from app.etl.adapters.metryx.normalizar import normalizar
from app.etl.adapters.metryx.rebanho import dias_em_cada_mes, rebanho_medio_mensal
from app.etl.adapters.metryx.saldo import RegistroBalanco
from tests.sinteticos import CAT_BEZ, CAT_DESM, CAT_VACA, CLIENTE, FAZENDA, payloads_metryx
from tests.test_metryx import conteudo_bruto

D = Decimal
JANEIRO, FEVEREIRO = date(2025, 1, 1), date(2025, 2, 1)


def reg(d: str, q, *, cat="C1", owner="O1", grupo="Garrotes e Bois", nasc=None, safra=None, ordem=0):
    return RegistroBalanco(fazenda="F", retiro="R1", categoria=cat, owner=owner, data=date.fromisoformat(d),
                           quantidade=D(q), grupo=grupo, nascimento=nasc, safra=safra, ordem=ordem)


def media(valor: float) -> Decimal:
    return D(valor).quantize(D("0.001"))


def test_cada_saldo_vale_os_dias_ate_o_registro_seguinte():
    """100 cab de 1º a 10/01 e 200 de 11 a 31/01; em fevereiro, sem registro, continua 200."""
    medias = rebanho_medio_mensal([reg("2025-01-01", 100), reg("2025-01-11", 200)], ate=date(2025, 2, 28))
    assert medias == {("F", "C1", JANEIRO): media((100 * 10 + 200 * 21) / 31), ("F", "C1", FEVEREIRO): D(200)}


def test_antes_do_primeiro_registro_nao_ha_animal():
    medias = rebanho_medio_mensal([reg("2025-01-21", 31)], ate=date(2025, 1, 31))
    assert medias == {("F", "C1", JANEIRO): D(11)}            # 31 cab em 11 dos 31 dias


def test_owners_e_coortes_de_bezerros_somam():
    bezerro = {"cat": "BZ", "grupo": "Bezerros Mamando", "safra": "24/25"}
    registros = [reg("2025-01-01", 10, owner="A"), reg("2025-01-01", 20, owner="B"),
                 reg("2025-01-01", 5, nasc="12/24", **bezerro), reg("2025-01-01", 7, nasc="01/25", **bezerro)]
    medias = rebanho_medio_mensal(registros, ate=date(2025, 1, 31))
    assert medias == {("F", "C1", JANEIRO): D(30), ("F", "BZ", JANEIRO): D(12)}


def test_mesmo_dia_usa_o_desempate_do_inventario():
    """Categorias comuns: o maior valor do dia; bezerros mamando: o primeiro gravado (como o saldo, saldo.py)."""
    bezerro = {"cat": "BZ", "grupo": "Bezerros Mamando", "nasc": "01/25", "safra": "24/25"}
    registros = [reg("2025-01-01", 10, ordem=1), reg("2025-01-01", 30, ordem=2),
                 reg("2025-01-01", 8, ordem=3, **bezerro), reg("2025-01-01", 4, ordem=4, **bezerro)]
    medias = rebanho_medio_mensal(registros, ate=date(2025, 1, 31))
    assert medias == {("F", "C1", JANEIRO): D(30), ("F", "BZ", JANEIRO): D(8)}


def test_sem_grupo_e_mes_sem_animal_ficam_de_fora():
    registros = [reg("2025-01-01", 5, grupo=None), reg("2025-01-01", 0, cat="C2")]
    assert rebanho_medio_mensal(registros, ate=date(2025, 1, 31)) == {}


def test_dias_de_cada_mes_no_intervalo():
    assert dias_em_cada_mes(date(2025, 1, 30), date(2025, 3, 2)) == [(JANEIRO, 2), (FEVEREIRO, 28),
                                                                    (date(2025, 3, 1), 1)]
    assert dias_em_cada_mes(date(2025, 1, 5), date(2025, 1, 5)) == []


def test_normalizador_usa_o_balanco_e_nao_o_endpoint_do_bi():
    """Julho da fazenda sintética: bezerros 1.000 até 30/07 e 815 no dia 31; garrotes 300 só no dia 31; vacas 500.
    O `rebanho-medio-pecuario` (aqui com um número absurdo) não entra."""
    absurdo = [{"idFarm": FAZENDA, "month": "7-2025", "idCategory": CAT_BEZ, "amount": 99999}]
    lote = normalizar(conteudo_bruto(payloads_metryx(rebanho_medio=absurdo)))
    julho = {linha.categoria.id_externo: linha.qtd_cab for linha in lote.rebanho_medio
             if linha.competencia == date(2025, 7, 1)}
    assert julho == {CAT_BEZ: media((1000 * 30 + 815) / 31), CAT_DESM: media(300 / 31), CAT_VACA: D(500)}
    assert {linha.competencia for linha in lote.rebanho_medio} == {date(2025, 6, 1), date(2025, 7, 1),
                                                                    date(2025, 8, 1)}
    assert ("rebanho_medio", f"{CLIENTE}|{FAZENDA}") in {(p.entidade, p.fazenda) for p in lote.particoes}


def test_sem_balanco_o_rebanho_medio_fica_como_estava():
    """Balanço proibido: nem estoque nem rebanho médio são substituídos (a partição dos dois sai junto)."""
    conteudo = conteudo_bruto(payloads_metryx())
    conteudo["endpoints"]["balanco"] = "proibido"
    lote = normalizar(conteudo)
    assert not {"inventario", "rebanho_medio"} & {p.entidade for p in lote.particoes if p.cenario == "realizado"}
