"""Números escritos como numa conversa (pt-BR), para as frases da "Leitura do mês" do boletim analítico."""

from datetime import date

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro",
         "novembro", "dezembro"]


def numero(valor: float, casas: int = 0) -> str:
    """1234.5 -> "1.235" (casas=0) ou "1.234,50" (casas=2)."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def cabecas(valor: float) -> str:
    """"1 cabeça", "1.234 cabeças"."""
    if round(valor) == 1:
        return "1 cabeça"
    return f"{numero(valor)} cabeças"


def no_plural(quantidade: float, singular: str, plural: str) -> str:
    """A palavra que concorda com a quantidade: no_plural(1, "morreu", "morreram") -> "morreu"."""
    if round(quantidade) == 1:
        return singular
    return plural


def contar(quantidade: int, singular: str, plural: str) -> str:
    """contar(1, "indicador", "indicadores") -> "1 indicador"; com 7 -> "7 indicadores"."""
    return f"{quantidade} {no_plural(quantidade, singular, plural)}"


def percentual(valor: float, casas: int = 1) -> str:
    """0.047 -> "4,7%"."""
    return f"{numero(valor * 100, casas)}%"


def dinheiro(valor: float, casas: int = 0) -> str:
    """1234.5 -> "R$ 1.235"; negativo -> "-R$ 1.235"."""
    if valor < 0:
        return f"-R$ {numero(-valor, casas)}"
    return f"R$ {numero(valor, casas)}"


def mes_por_extenso(mes: date) -> str:
    """date(2026, 9, 1) -> "setembro/2026"."""
    return f"{MESES[mes.month - 1]}/{mes.year}"


def acima_ou_abaixo(variacao_percentual: float) -> str:
    """0.12 -> "12,0% acima"; -0.05 -> "5,0% abaixo"; perto de zero -> "igual"."""
    if abs(variacao_percentual) < 0.0005:
        return "igual"
    if variacao_percentual > 0:
        return f"{percentual(variacao_percentual)} acima"
    return f"{percentual(-variacao_percentual)} abaixo"


def frente_ao_previsto(variacao_percentual: float, feminino: bool = False) -> str:
    """"12,0% acima do previsto" ou, perto de zero, "igual ao previsto"; com `feminino`, "da prevista"/"à prevista"."""
    diferenca = acima_ou_abaixo(variacao_percentual)
    if diferenca == "igual" and feminino:
        return "igual à prevista"
    if diferenca == "igual":
        return "igual ao previsto"
    if feminino:
        return f"{diferenca} da prevista"
    return f"{diferenca} do previsto"
