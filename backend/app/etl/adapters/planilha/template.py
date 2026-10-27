"""Especificação do template RELATÓRIO*.xlsm (docs/analises/03 §2): abas, colunas de entrada e apelidos.

Leitura SEMPRE pelo nome do cabeçalho (linha 1), normalizado (sem acento, maiúsculas, separadores -> "_"). Colunas
de fórmula (cache do Excel) só entram quando servem para conferência ou para reproduzir o que o BI usa.
"""

import re
import unicodedata
from dataclasses import dataclass, field

CATEGORIAS_BI = ("BEZERRO", "MACHOS 8-12", "MACHOS 13-24", "MACHOS 25-36", "MACHOS + 36", "TOUROS",
                 "TOUROS DESCARTES", "SINUELO", "BEZERRA", "NOVILHAS 8-12", "NOVILHAS 13-24", "NOVILHAS 25-36",
                 "MATRIZES", "VACA DESCARTE", "VACA LEITEIRA")

REGEX_ARQUIVO = re.compile(r"^RELAT[ÓO]RIOS?\s*[-_]\s*(\d+)\s*[-_]\s*(.+?)\s*\.xls[xm]$", re.IGNORECASE)


def norm(texto) -> str:
    """Forma normalizada para casar cabeçalhos, nomes de aba e textos de de-para."""
    if texto is None:
        return ""
    s = unicodedata.normalize("NFKD", str(texto).replace("\xa0", " "))
    s = "".join(c for c in s if not unicodedata.combining(c)).upper().strip()
    return re.sub(r"[\s_\-.]+", "_", s).strip("_")


def norm_texto(texto) -> str:
    """Texto livre de de-para (categoria da fazenda, centro de custo): sem acento, maiúsculas, espaços simples."""
    return re.sub(r"\s+", " ", norm(texto).replace("_", " ")).strip()


@dataclass(frozen=True)
class Aba:
    nome: str
    campos: tuple[str, ...]                       # colunas lidas (nomes normalizados)
    cache: tuple[str, ...] = ()                   # colunas de fórmula: lidas, mas não definem "linha com conteúdo"
    apelidos_aba: tuple[str, ...] = ()
    apelidos_coluna: dict[str, tuple[str, ...]] = field(default_factory=dict)


CATEG = {"CATEG_FAZENDA": ("CATEGORIA_FAZENDA",)}


def _par(nome: str, campos, cache=(), apelidos_aba=(), apelidos_coluna=None) -> list[Aba]:
    """Aba de realizado e a sua versão *PLANEJADO (mesmos cabeçalhos)."""
    ap = apelidos_coluna or {}
    return [Aba(nome, tuple(campos), tuple(cache), tuple(apelidos_aba), ap),
            Aba(nome + "PLANEJADO", tuple(campos), tuple(cache), tuple(a + "PLANEJADO" for a in apelidos_aba), ap)]


ABAS_LANCAMENTO: dict[str, Aba] = {a.nome: a for a in (
    *_par("fCompras", ("DATA", "ORIGEM", "CATEG_FAZENDA", "QTD", "PESO_VIVO", "TOTAL_PESO", "VALOR_CAB",
                       "VALOR_TOTAL"), apelidos_coluna=CATEG),
    *_par("fAbate", ("CLIENTE", "CATEG_FAZENDA", "DATA", "QTD", "ERA", "PESO_VIVO", "RENDIMENTO", "PESO_ARROBA",
                     "VALOR_ARROBA", "FATURAMENTO", "PESOVIVO_TOTAL", "PESOMORTO_TOTAL"),
          cache=("PESOVIVO_TOTAL", "PESOMORTO_TOTAL"), apelidos_coluna=CATEG),
    *_par("fVendaemPe", ("CLIENTE", "DATA", "DOCUMENTO", "CATEG_FAZENDA", "QTD", "PESO_VIVO", "PESOVIVO_TOTAL",
                         "VALOR_ARROBA", "VALOR_CAB", "FATURAMENTO"), apelidos_coluna=CATEG),
    *_par("fMortes", ("DATA", "CATEG_FAZENDA", "CARIMBO_BEZ", "QTD", "CAUSA", "LOCAL", "PESO_VIVO", "SAFRA"),
          apelidos_coluna=CATEG),
    *_par("fNascimento", ("DATA", "CATEG_FAZENDA", "QTD", "SAFRA", "PESO_NASC"), apelidos_coluna=CATEG),
    *_par("ftranfentrada", ("DATA", "CATEG_FAZENDA", "QTD", "PESO_VIVO", "TOTAL_PESO", "VALOR_TOTAL"),
          apelidos_coluna=CATEG),
    *_par("ftranssaida", ("DATA", "CATEG_FAZENDA", "QTD", "PESO_VIVO", "TOTAL_PESO", "VALOR_TOTAL"),
          apelidos_coluna=CATEG),
    Aba("fconsumodoacao", ("DATA", "CATEG_FAZENDA", "QTD", "PESO_VIVO", "VALOR_CAB", "TIPO", "DESTINO"),
        apelidos_aba=("fconsumodoação",), apelidos_coluna=CATEG),
    Aba("fmudcategoria", ("DATA", "CATEGORIA_FAZENDA_SAIDA", "CATEGORIA_FAZENDA_ENTRADA", "QTD", "PESO_VIVO",
                          "TOTAL_PESO"), apelidos_aba=("fmudançacateg",)),
    Aba("fdesmame", ("DATA", "CATEGORIA_FAZENDA_SAIDA", "CATEGORIA_FAZENDA_ENTRADA", "QTD", "PESO_VIVO")),
    *_par("fRebanhoMedio", ("GRUPO_CATEGORIA", "QTD_CAB", "QTD_UA", "DATA"), cache=("GRUPO_CATEGORIA", "DATA")),
    # ÁREA_ILP: em 3 arquivos o cabeçalho é "ILP" ou "SILAGEM" (o BI lê pela posição, como ÁREA_ILP)
    *_par("fArea", ("DATA", "AREA_PASTO", "AREA_ILP"), cache=("DATA",),
          apelidos_coluna={"AREA_ILP": ("ILP", "SILAGEM")}),
    *_par("fDre", ("CENTRO_DE_CUSTO", "SUB_CENTRO", "VALOR", "DATA_PAG", "OPERACAO", "CENTRO_DE_CUSTO_BI",
                   "SUB_CENTRO_BI"), cache=("OPERACAO", "CENTRO_DE_CUSTO_BI", "SUB_CENTRO_BI")),
)}

# aba -> (tipo de movimentação, campo de categoria, campo de categoria de destino)
TIPO_DA_ABA: dict[str, tuple[str, str, str | None]] = {
    "fCompras": ("COMPRA", "CATEG_FAZENDA", None),
    "fAbate": ("ABATE", "CATEG_FAZENDA", None),
    "fVendaemPe": ("VENDA_EM_PE", "CATEG_FAZENDA", None),
    "fMortes": ("MORTE", "CATEG_FAZENDA", None),
    "fNascimento": ("NASCIMENTO", "CATEG_FAZENDA", None),
    "ftranfentrada": ("TRANSF_ENTRADA", "CATEG_FAZENDA", None),
    "ftranssaida": ("TRANSF_SAIDA", "CATEG_FAZENDA", None),
    "fconsumodoacao": ("CONSUMO_DOACAO", "CATEG_FAZENDA", None),
    "fmudcategoria": ("MUDANCA_CATEGORIA", "CATEGORIA_FAZENDA_SAIDA", "CATEGORIA_FAZENDA_ENTRADA"),
    "fdesmame": ("DESMAME", "CATEGORIA_FAZENDA_SAIDA", "CATEGORIA_FAZENDA_ENTRADA"),
}
