"""Sugestão de categoria BI para uma categoria do Metryx (grupo + faixa etária + sexo).

É só sugestão: grava em categoria_bi_sugerida_id; quem confirma é o consultor (D6).
"""

import unicodedata


def _norm(texto: str | None) -> str:
    if not texto:
        return ""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.upper().split())


IDADE_MACHO = {"00-08": "BEZERRO", "08-12": "MACHOS 8-12", "12-24": "MACHOS 13-24", "24-36": "MACHOS 25-36",
               "36-00": "MACHOS + 36"}
IDADE_FEMEA = {"00-08": "BEZERRA", "08-12": "NOVILHAS 8-12", "12-24": "NOVILHAS 13-24", "24-36": "NOVILHAS 25-36",
               "36-00": "MATRIZES"}


def sugerir_categoria_bi(grupo: str | None, idade: str | None, sexo: str | None) -> str | None:
    g, i, s = _norm(grupo), (idade or "").strip(), _norm(sexo)
    femea = s.startswith("F")
    if g == "BEZERROS MAMANDO":
        return "BEZERRO"
    if g == "BEZERRAS MAMANDO":
        return "BEZERRA"
    if g == "TOUROS":
        return "TOUROS"
    if g == "MATRIZES DESCARTE":
        return "VACA DESCARTE"
    if g == "MATRIZES EM REPRODUCAO":
        return "MATRIZES"
    if g in ("GARROTES E BOIS", "NOVILHAS", "OUTROS") and s:
        return (IDADE_FEMEA if femea else IDADE_MACHO).get(i)
    return None
