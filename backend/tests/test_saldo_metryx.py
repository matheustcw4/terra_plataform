"""Regra de saldo do Metryx: a do SQL fSaldoGado do BI, menos onde o BI diverge do inventário do próprio Metryx
(bezerros mamando, 20/10/2026: o número tem de bater com o Metryx)."""

from datetime import date
from decimal import Decimal

from app.etl.adapters.metryx.saldo import RegistroBalanco, saldo_fim_de_mes

D = Decimal


def reg(d: str, q, *, cat="C1", owner="O1", grupo="Garrotes e Bois", nasc=None, safra=None, retiro="R1"):
    return RegistroBalanco(fazenda="F", retiro=retiro, categoria=cat, owner=owner, data=date.fromisoformat(d),
                           quantidade=D(q), grupo=grupo, nascimento=nasc, safra=safra)


def test_categoria_comum_ultimo_registro_do_mes_e_maior_no_empate():
    s = saldo_fim_de_mes([reg("2025-01-05", 10), reg("2025-01-20", 7), reg("2025-01-20", 9), reg("2025-03-02", 4)])
    assert s[("F", "R1", "C1")] == {date(2025, 1, 31): D(9), date(2025, 3, 31): D(4)}


def test_owners_somam_cada_um_com_seu_ultimo_saldo():
    s = saldo_fim_de_mes([reg("2025-01-10", 100, owner="A"), reg("2025-02-10", 50, owner="B"),
                          reg("2025-03-10", 80, owner="A")])
    assert s[("F", "R1", "C1")] == {date(2025, 1, 31): D(100), date(2025, 2, 28): D(150), date(2025, 3, 31): D(130)}


def test_registro_sem_grupo_fica_de_fora_como_no_bi():
    assert saldo_fim_de_mes([reg("2025-01-10", 5, grupo=None)]) == {}


def test_bezerros_coorte_de_um_mes_continua_no_saldo():
    """Coorte que aparece num mês só continua no saldo nos meses seguintes (o último saldo conhecido dela)."""
    b = dict(cat="BZ", grupo="Bezerros Mamando")
    s = saldo_fim_de_mes([reg("2025-01-10", 20, nasc="01/25", safra="24/25", **b),
                          reg("2025-02-10", 15, nasc="02/25", safra="24/25", **b)])
    assert s[("F", "R1", "BZ")] == {date(2025, 1, 31): D(20), date(2025, 2, 28): D(35)}


def test_bezerros_coorte_de_varios_meses_vale_o_ultimo_saldo_do_mes():
    """Cada mês vale o último saldo da coorte naquele mês, como o inventário do Metryx. O BI fazia "o maior valor
    daquele mês em diante", e fevereiro sairia 28 (U6 PARTE V, mai/2026: 32 bezerras no BI, 31 no Metryx)."""
    b = dict(cat="BZ", grupo="Bezerras Mamando", nasc="01/25", safra="24/25")
    s = saldo_fim_de_mes([reg("2025-01-10", 30, **b), reg("2025-02-10", 25, **b), reg("2025-03-10", 28, **b)])
    assert s[("F", "R1", "BZ")] == {date(2025, 1, 31): D(30), date(2025, 2, 28): D(25), date(2025, 3, 31): D(28)}


def test_lote_que_zera_e_volta_depois_fica_zerado_no_mes_em_que_zerou():
    """O caso real do U6 PARTE V: o lote zera em 20/05 (desmame) e 1 animal volta no balanço de 20/06."""
    b = dict(cat="BZ", grupo="Bezerras Mamando", nasc="10/25", safra="25/26")
    s = saldo_fim_de_mes([reg("2026-04-30", 91, **b), reg("2026-05-20", 0, **b), reg("2026-06-20", 1, **b)])
    assert s[("F", "R1", "BZ")] == {date(2026, 4, 30): D(91), date(2026, 5, 31): D(0), date(2026, 6, 30): D(1)}


def test_desempate_de_bezerros_padrao_e_o_primeiro_gravado_como_no_bi():
    """Dois saldos da mesma coorte no mesmo dia: o BI não tem regra; o padrão é o primeiro na ordem da API."""
    b = dict(cat="BZ", grupo="Bezerros Mamando", nasc="01/25", safra="24/25")
    regs = [reg("2025-01-10", 30, **b),
            RegistroBalanco(**{**reg("2025-02-28", 0, **b).__dict__, "ordem": 1}),
            RegistroBalanco(**{**reg("2025-02-28", 25, **b).__dict__, "ordem": 2})]
    fev = date(2025, 2, 28)
    assert saldo_fim_de_mes(regs)[("F", "R1", "BZ")][fev] == D(0)
    assert saldo_fim_de_mes(regs, "ultimo")[("F", "R1", "BZ")][fev] == D(25)
    assert saldo_fim_de_mes(regs, "maior")[("F", "R1", "BZ")][fev] == D(25)
    assert saldo_fim_de_mes(regs, "menor")[("F", "R1", "BZ")][fev] == D(0)
