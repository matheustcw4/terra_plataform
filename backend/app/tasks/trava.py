"""Uma carga por vez no banco: trava consultiva (advisory lock) do Postgres, presa a uma conexão.

O worker roda com uma tarefa por vez, mas a trava também segura duas instâncias do worker: a mesma carga rodaria duas
vezes, e o recálculo do estoque do mês concorreria com uma carga. (O motor já serializa duas cargas da mesma fazenda;
esta trava é a do conjunto.) A trava se solta sozinha se o processo cair (é da conexão).
"""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Connection, Engine, text
from sqlalchemy.orm import Session

CHAVE_DAS_CARGAS = 2026_10_15_01        # número fixo que identifica "as cargas do Terra" entre as travas do banco

# Uma trava de chave bigint aparece em pg_locks partida em duas: os 32 bits de cima em classid, os de baixo em objid,
# com objsubid = 1.
TRAVA_PRESA = """
    SELECT EXISTS (
        SELECT 1 FROM pg_locks
        WHERE locktype = 'advisory' AND granted
          AND classid = CAST(:classe AS oid) AND objid = CAST(:objeto AS oid) AND objsubid = 1
    )
"""


@contextmanager
def trava_das_cargas(engine: Engine, esperar: bool) -> Iterator[bool]:
    """Dá True com a trava na mão. `esperar=False`: se outra carga roda, dá False na hora (a agenda tenta de novo
    depois); `esperar=True`: espera a outra terminar (para o que não pode ser pulado, como o estoque do mês)."""
    with engine.connect() as conexao:
        if esperar:
            conexao.execute(text("SELECT pg_advisory_lock(:chave)"), {"chave": CHAVE_DAS_CARGAS})
            conseguiu = True
        else:
            conseguiu = conexao.scalar(text("SELECT pg_try_advisory_lock(:chave)"), {"chave": CHAVE_DAS_CARGAS})
        try:
            yield conseguiu
        finally:
            if conseguiu:
                conexao.execute(text("SELECT pg_advisory_unlock(:chave)"), {"chave": CHAVE_DAS_CARGAS})


def carga_rodando(conexao: Connection | Session) -> bool:
    """Alguma carga está com a trava agora? Só olha a lista de travas do banco: pegar a trava, mesmo por um instante,
    faria a carga que está começando ser pulada."""
    parametros = {"classe": CHAVE_DAS_CARGAS >> 32, "objeto": CHAVE_DAS_CARGAS & 0xFFFFFFFF}
    return bool(conexao.scalar(text(TRAVA_PRESA), parametros))
