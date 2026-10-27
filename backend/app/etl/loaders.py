"""Gravação transacional por partição.

substituir: DELETE do recorte (fonte + fazenda + cenário [+ tipos] [+ versão] [+ meses entre `desde` e `ate`]) e
            INSERT das linhas do lote.
            Re-executar com o mesmo conteúdo dá o mesmo resultado; leitores nunca veem o recorte vazio
            (tudo na mesma transação).
mesclar:    INSERT … ON CONFLICT (chave natural) DO UPDATE — o que não veio continua lá.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import Table, delete, func, insert, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.etl.canonical import proximo_mes
from app.models.fato import (
    AreaMensal,
    Inventario,
    LancamentoFinanceiro,
    MovAnimal,
    OrcamentoFinanceiro,
    RebanhoMedioMensal,
)

TABELAS: dict[str, Table] = {
    "mov_animal": MovAnimal.__table__,
    "inventario": Inventario.__table__,
    "rebanho_medio": RebanhoMedioMensal.__table__,
    "area": AreaMensal.__table__,
    "lancamento": LancamentoFinanceiro.__table__,
    "orcamento": OrcamentoFinanceiro.__table__,
}

# chave natural (constraint UNIQUE) das entidades que aceitam 'mesclar'
CHAVE_NATURAL: dict[str, tuple[str, tuple[str, ...]]] = {
    "inventario": ("uq_inventario", ("fazenda_id", "retiro_id", "categoria_map_id", "data")),
    "rebanho_medio": ("uq_rebanho_medio",
                      ("fazenda_id", "cenario", "versao_plano_id", "competencia", "grupo", "categoria_map_id")),
    "area": ("uq_area_mensal", ("fazenda_id", "cenario", "versao_plano_id", "competencia")),
}

NAO_ATUALIZAR = {"id", "carregado_em"}

# coluna do recorte `desde` (competencia é a data truncada no mês, gerada no banco)
COLUNA_DESDE: dict[str, str] = {"mov_animal": "competencia", "inventario": "data", "rebanho_medio": "competencia",
                                "area": "competencia", "lancamento": "competencia", "orcamento": "competencia"}


@dataclass(frozen=True)
class ParticaoDb:
    entidade: str
    fonte: str
    fazenda_id: UUID
    cenario: str
    estrategia: str
    tipos: tuple[str, ...] | None = None
    versao_plano_id: UUID | None = None
    guarda_volume: float | None = None
    desde: date | None = None
    ate: date | None = None


@dataclass(frozen=True)
class ResultadoParticao:
    apagadas: int
    gravadas: int
    retida: bool = False
    existentes: int = 0


def aplicar(s: Session, p: ParticaoDb, linhas: list[dict[str, Any]], *, ignorar_guarda: bool = False
            ) -> ResultadoParticao:
    """Aplica uma partição (ou a retém, se a guarda de volume disparar)."""
    if p.estrategia == "substituir":
        return substituir(s, p, linhas, ignorar_guarda)
    return mesclar(s, p, linhas)


def substituir(s: Session, p: ParticaoDb, linhas: list[dict[str, Any]], ignorar_guarda: bool) -> ResultadoParticao:
    """Apaga o recorte e grava as linhas do lote, na mesma transação."""
    tabela = TABELAS[p.entidade]
    recorte = condicoes_do_recorte(tabela, p)
    if p.guarda_volume and not ignorar_guarda:
        existentes = s.scalar(select(func.count()).select_from(tabela).where(*recorte))
        # a fonte trouxe bem menos do que já existe (ex.: resposta vazia da API): não apaga nada
        if existentes and len(linhas) < existentes * p.guarda_volume:
            return ResultadoParticao(0, 0, retida=True, existentes=existentes)
    apagadas = s.execute(delete(tabela).where(*recorte)).rowcount
    if linhas:
        s.execute(insert(tabela), linhas)
    return ResultadoParticao(apagadas, len(linhas))


def condicoes_do_recorte(tabela: Table, p: ParticaoDb) -> list:
    """WHERE do recorte: fonte + fazenda, e mais o que a partição limitar (cenário, tipos, versão, meses)."""
    condicoes = [tabela.c.fonte == p.fonte, tabela.c.fazenda_id == p.fazenda_id]
    if "cenario" in tabela.c:
        condicoes.append(tabela.c.cenario == p.cenario)
    if p.tipos is not None:
        condicoes.append(tabela.c.tipo.in_(p.tipos))
    if p.versao_plano_id is not None:
        condicoes.append(tabela.c.versao_plano_id == p.versao_plano_id)
    coluna_do_mes = tabela.c[COLUNA_DESDE[p.entidade]]
    if p.desde is not None:
        condicoes.append(coluna_do_mes >= p.desde)
    if p.ate is not None:
        condicoes.append(coluna_do_mes < proximo_mes(p.ate))
    return condicoes


def mesclar(s: Session, p: ParticaoDb, linhas: list[dict[str, Any]]) -> ResultadoParticao:
    """INSERT … ON CONFLICT (chave natural) DO UPDATE: o que não veio no lote continua no banco."""
    if not linhas:
        return ResultadoParticao(0, 0)
    tabela = TABELAS[p.entidade]
    restricao, chave = CHAVE_NATURAL[p.entidade]
    comando = pg_insert(tabela)
    colunas = set()
    for linha in linhas:
        colunas.update(linha)
    atualizar = {}
    for coluna in colunas:
        if coluna not in chave and coluna not in NAO_ATUALIZAR:
            atualizar[coluna] = comando.excluded[coluna]
    atualizar["carregado_em"] = comando.excluded.carregado_em
    s.execute(comando.on_conflict_do_update(constraint=restricao, set_=atualizar), linhas)
    return ResultadoParticao(0, len(linhas))
