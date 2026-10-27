"""Códigos de ocorrência e checagens genéricas de qualidade (valem para qualquer fonte).

Política: erro de ARQUIVO/payload -> nada daquela unidade muda (a versão anterior continua valendo);
erro de LINHA -> a linha vai para a quarentena e o resto carrega. Uma unidade nunca derruba o lote.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from enum import StrEnum

from app.etl.canonical import Inventario, LancamentoFinanceiro, MovAnimal, Ocorrencia


class Cod(StrEnum):
    # unidade inteira
    EXTRACT_FAILED = "EXTRACT_FAILED"
    NORMALIZE_FAILED = "NORMALIZE_FAILED"
    CONTRACT_VIOLATION = "CONTRACT_VIOLATION"
    LOAD_FAILED = "LOAD_FAILED"
    # identidade / de-para
    FARM_CREATED = "FARM_CREATED"
    CATEGORY_UNMAPPED = "CATEGORY_UNMAPPED"
    CATEGORY_UNDECLARED = "CATEGORY_UNDECLARED"
    CATEGORY_BI_UNKNOWN = "CATEGORY_BI_UNKNOWN"
    ACCOUNT_UNCLASSIFIED = "ACCOUNT_UNCLASSIFIED"   # conta carregada como "A classificar"
    SOURCE_INACTIVE_FOR_DOMAIN = "SOURCE_INACTIVE_FOR_DOMAIN"
    SNAPSHOT_HELD = "SNAPSHOT_HELD"               # guarda de volume reteve a partição
    DUPLICATE_UNIT_FILE = "DUPLICATE_UNIT_FILE"   # outra unidade mais recente alimenta a mesma fazenda
    DUPLICATE_CONTENT = "DUPLICATE_CONTENT"       # arquivo com os mesmos bytes de outro (vale o mais recente)
    # linha
    DATE_OUT_OF_RANGE = "DATE_OUT_OF_RANGE"
    VALUE_OUT_OF_RANGE = "VALUE_OUT_OF_RANGE"
    VALUE_MISSING = "VALUE_MISSING"               # venda ou compra realizada sem valor: entra com R$ 0
    OUTLIER = "OUTLIER"


# faixas de plausibilidade (docs/01 §7: invariantes)
PESO_MEDIO_KG = (Decimal(20), Decimal(900))
RENDIMENTO_CARCACA = (Decimal("0.40"), Decimal("0.65"))
PRECO_KG_VIVO = (Decimal(4), Decimal(40))       # R$/kg vivo de compra e venda (validação, achado A11)
TIPOS_COM_PRECO = ("COMPRA", "VENDA_EM_PE", "ABATE")
DATA_MINIMA = date(2000, 1, 1)
FOLGA_REALIZADO_FUTURO = timedelta(days=31)
VALOR_MAXIMO_LANCAMENTO = Decimal(1_000_000_000)


@dataclass
class ResultadoChecagem:
    ocorrencias: list[Ocorrencia]
    rejeitar: bool = False
    motivo: str | None = None
    codigo: str | None = None


def _aviso(codigo: Cod, mensagem: str, entidade: str, linha, contexto: dict) -> Ocorrencia:
    return Ocorrencia(nivel="aviso", codigo=codigo, mensagem=mensagem, entidade=entidade,
                      origem_linha=linha.origem_linha, fazenda=linha.fazenda, contexto=contexto or None)


def numero_br(valor: Decimal, casas: int) -> str:
    """Número para mensagem lida pelo usuário: 1.234,5."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def _data_valida(data: date, realizado: bool, hoje: date) -> bool:
    """Nada antes de 2000; realizado não pode estar mais de um mês no futuro."""
    if data < DATA_MINIMA:
        return False
    no_futuro = data > hoje + FOLGA_REALIZADO_FUTURO
    return not (realizado and no_futuro)


def _rejeitar(motivo: str, codigo: Cod) -> ResultadoChecagem:
    return ResultadoChecagem([], True, motivo, codigo)


def checar(entidade: str, linha, hoje: date | None = None) -> ResultadoChecagem:
    """Checagens que valem para qualquer fonte. Linha fora da faixa vai para a quarentena; valor estranho só avisa."""
    hoje = hoje or date.today()
    if isinstance(linha, MovAnimal):
        return checar_mov_animal(entidade, linha, hoje)
    if isinstance(linha, LancamentoFinanceiro):
        return checar_lancamento(linha, hoje)
    if isinstance(linha, Inventario) and not _data_valida(linha.data, True, hoje):
        return _rejeitar(f"data {linha.data} fora da faixa", Cod.DATE_OUT_OF_RANGE)
    return ResultadoChecagem([])


def checar_mov_animal(entidade: str, linha: MovAnimal, hoje: date) -> ResultadoChecagem:
    if not _data_valida(linha.data, linha.cenario == "realizado", hoje):
        return _rejeitar(f"data {linha.data} fora da faixa", Cod.DATE_OUT_OF_RANGE)
    if linha.valor_total is not None and linha.valor_total >= VALOR_MAXIMO_LANCAMENTO:
        return _rejeitar(f"valor {linha.valor_total:,.2f} implausível (≥ 1 bilhão)", Cod.VALUE_OUT_OF_RANGE)
    avisos = []
    if linha.peso_vivo_total_kg and linha.qtd > 0:      # peso 0 = não informado (comum em mortes)
        medio = linha.peso_vivo_total_kg / linha.qtd
        if not PESO_MEDIO_KG[0] <= medio <= PESO_MEDIO_KG[1]:
            mensagem = f"peso médio de {numero_br(medio, 1)} kg/cab fora de 20–900"
            avisos.append(_aviso(Cod.OUTLIER, mensagem, entidade, linha,
                                 {"campo": "peso_vivo_total_kg", "peso_medio": str(round(medio, 2))}))
    if linha.tipo == "ABATE" and linha.peso_carcaca_total_kg and linha.peso_vivo_total_kg:
        rendimento = linha.peso_carcaca_total_kg / linha.peso_vivo_total_kg
        if not RENDIMENTO_CARCACA[0] <= rendimento <= RENDIMENTO_CARCACA[1]:
            mensagem = f"rendimento de carcaça de {numero_br(rendimento * 100, 1)}% fora de 40–65%"
            avisos.append(_aviso(Cod.OUTLIER, mensagem, entidade, linha,
                                 {"campo": "rendimento", "rendimento": str(round(rendimento, 4))}))
    if linha.tipo in TIPOS_COM_PRECO:
        avisos.extend(checar_preco(entidade, linha))
    return ResultadoChecagem(avisos)


def checar_preco(entidade: str, linha: MovAnimal) -> list[Ocorrencia]:
    """Compra e venda: sem valor no realizado, ou R$/kg vivo fora da faixa (erro de digitação ou de escala)."""
    if not linha.valor_total:
        if linha.cenario == "realizado" and linha.qtd > 0:
            return [_aviso(Cod.VALUE_MISSING, "sem valor: entra com R$ 0 no faturamento/custo", entidade, linha, {})]
        return []
    if not linha.peso_vivo_total_kg:
        return []
    preco = linha.valor_total / linha.peso_vivo_total_kg
    if PRECO_KG_VIVO[0] <= preco <= PRECO_KG_VIVO[1]:
        return []
    return [_aviso(Cod.OUTLIER, f"preço de R$ {numero_br(preco, 2)} por kg vivo fora de R$ 4–40", entidade, linha,
                   {"campo": "valor_total", "preco_kg": str(round(preco, 2))})]


def checar_lancamento(linha: LancamentoFinanceiro, hoje: date) -> ResultadoChecagem:
    if not _data_valida(linha.data_pagamento, True, hoje):
        return _rejeitar(f"data de pagamento {linha.data_pagamento} fora da faixa", Cod.DATE_OUT_OF_RANGE)
    if linha.valor >= VALOR_MAXIMO_LANCAMENTO:          # erro de escala na origem (ex.: 5e16 no Metryx)
        return _rejeitar(f"valor {linha.valor:,.2f} implausível (≥ 1 bilhão)", Cod.VALUE_OUT_OF_RANGE)
    return ResultadoChecagem([])
