"""Telas de admin dos de-paras: categoria da fonte -> categoria BI e conta da fonte -> centro de custo.

Os fatos apontam para o de-para, nunca para a dimensão: classificar (ou corrigir) um de-para reclassifica o histórico
sem recarga. A única tabela derivada que depende disso é `fato.estoque_mensal` (estoque por categoria BI), recalculada
aqui mesmo para as fazendas que usam a categoria. O DRE lê a classificação da conta pela view, então mudar uma conta
não precisa de recálculo.

Tudo roda na sessão do admin: o RLS deixa o admin ler e gravar em todas as fazendas.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.admin import (
    CategoriaDeOrigem,
    CategoriasDeOrigem,
    ContaDeOrigem,
    ContasDeOrigem,
    OpcaoDeCategoria,
    OpcaoDeConta,
)

LIMITE_DA_LISTA = 500

# --- categorias ----------------------------------------------------------------------------------------------------

CATEGORIAS = """
    SELECT m.id, m.fonte, m.nome_origem, m.categoria_bi_id, m.categoria_bi_sugerida_id, m.confirmado_em,
           u.nome AS confirmado_por, f.nome AS fazenda,
           coalesce(nullif(btrim(f.proprietario), ''), cliente_da_fazenda.nome, cliente.nome) AS cliente,
           (SELECT count(*) FROM fato.mov_animal a WHERE a.categoria_map_id = m.id)
           + (SELECT count(*) FROM fato.mov_animal a WHERE a.categoria_destino_map_id = m.id)
           + (SELECT count(*) FROM fato.inventario i WHERE i.categoria_map_id = m.id)
           + (SELECT count(*) FROM fato.rebanho_medio_mensal r WHERE r.categoria_map_id = m.id) AS lancamentos
    FROM dim.categoria_map m
    LEFT JOIN core.fazenda f ON f.id = m.fazenda_id
    LEFT JOIN core.cliente cliente_da_fazenda ON cliente_da_fazenda.id = f.cliente_id
    LEFT JOIN core.cliente cliente ON cliente.id = m.cliente_id
    LEFT JOIN core.usuario u ON u.id = m.confirmado_por
    WHERE (NOT :so_pendentes OR m.categoria_bi_id IS NULL)
      AND concat_ws(' ', m.nome_origem, f.nome, f.proprietario, cliente.nome) ILIKE '%' || :busca || '%'
    ORDER BY m.categoria_bi_id IS NOT NULL, 9, f.nome, m.nome_origem
    LIMIT :limite
"""
OPCOES_DE_CATEGORIA = "SELECT id, nome, sexo, grupo FROM dim.categoria_bi ORDER BY id"
PENDENTES_DE_CATEGORIA = "SELECT count(*) FROM dim.categoria_map WHERE categoria_bi_id IS NULL"
CLASSIFICAR_CATEGORIA = """
    UPDATE dim.categoria_map
    SET categoria_bi_id = :categoria, confirmado_por = :usuario, confirmado_em = now(), atualizado_em = now()
    WHERE id = :id
    RETURNING fazenda_id, cliente_id
"""
DESFAZER_CATEGORIA = """
    UPDATE dim.categoria_map
    SET categoria_bi_id = NULL, confirmado_por = NULL, confirmado_em = NULL, atualizado_em = now()
    WHERE id = :id
    RETURNING fazenda_id, cliente_id
"""
FAZENDAS_DO_CLIENTE = "SELECT id FROM core.fazenda WHERE cliente_id = :cliente"
# Recalcula até o mesmo mês que o estoque já tem (a carga decide até onde o saldo se repete); sem estoque, até hoje.
RECALCULAR_ESTOQUE = """
    SELECT fato.recalcular_estoque_mensal(
        CAST(:fazendas AS uuid[]),
        coalesce((SELECT max(e.competencia) FROM fato.estoque_mensal e
                  WHERE e.fazenda_id = ANY (CAST(:fazendas AS uuid[]))), current_date))
"""


def listar_categorias(s: Session, so_pendentes: bool, busca: str) -> CategoriasDeOrigem:
    itens = []
    parametros = {"so_pendentes": so_pendentes, "busca": busca.strip(), "limite": LIMITE_DA_LISTA}
    for linha in s.execute(text(CATEGORIAS), parametros).mappings():
        itens.append(CategoriaDeOrigem(**linha))
    opcoes = []
    for linha in s.execute(text(OPCOES_DE_CATEGORIA)).mappings():
        opcoes.append(OpcaoDeCategoria(**linha))
    return CategoriasDeOrigem(pendentes=s.scalar(text(PENDENTES_DE_CATEGORIA)), opcoes=opcoes, itens=itens)


def classificar_categoria(s: Session, mapa_id: UUID, categoria_bi_id: int | None, usuario_id: UUID) -> None:
    """Grava a categoria BI (ou volta para pendente) e recalcula o estoque das fazendas que usam o de-para."""
    if categoria_bi_id is None:
        escopo = s.execute(text(DESFAZER_CATEGORIA), {"id": mapa_id}).first()
    else:
        escopo = s.execute(text(CLASSIFICAR_CATEGORIA),
                           {"id": mapa_id, "categoria": categoria_bi_id, "usuario": usuario_id}).first()
    if escopo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "de-para de categoria não encontrado")
    fazendas = fazendas_do_mapa(s, escopo.fazenda_id, escopo.cliente_id)
    if fazendas:
        s.execute(text(RECALCULAR_ESTOQUE), {"fazendas": fazendas})


def fazendas_do_mapa(s: Session, fazenda_id: UUID | None, cliente_id: UUID | None) -> list[str]:
    """O de-para da planilha é por fazenda; o do Metryx, por cliente (vale para todas as fazendas dele)."""
    if fazenda_id is not None:
        return [str(fazenda_id)]
    return [str(fazenda) for fazenda in s.scalars(text(FAZENDAS_DO_CLIENTE), {"cliente": cliente_id})]


# --- contas --------------------------------------------------------------------------------------------------------

CONTAS = """
    SELECT m.id, m.fonte, coalesce(m.nome_centro_origem, m.centro_origem) AS centro,
           coalesce(m.nome_subcentro_origem, nullif(m.subcentro_origem, '')) AS subcentro,
           m.centro_custo_id, m.confirmado_em, u.nome AS confirmado_por,
           coalesce(uso.lancamentos, 0) AS lancamentos, coalesce(uso.valor, 0) AS valor,
           coalesce(planejado.orcamentos, 0) AS orcamentos,
           (SELECT count(DISTINCT fazenda_id) FROM (
                SELECT l.fazenda_id FROM fato.lancamento_financeiro l WHERE l.plano_contas_map_id = m.id
                UNION
                SELECT o.fazenda_id FROM fato.orcamento_financeiro o WHERE o.plano_contas_map_id = m.id) f
           ) AS fazendas
    FROM dim.plano_contas_map m
    LEFT JOIN core.usuario u ON u.id = m.confirmado_por
    LEFT JOIN LATERAL (SELECT count(*) AS lancamentos, sum(l.valor) AS valor
                       FROM fato.lancamento_financeiro l WHERE l.plano_contas_map_id = m.id) uso ON true
    LEFT JOIN LATERAL (SELECT count(*) AS orcamentos
                       FROM fato.orcamento_financeiro o WHERE o.plano_contas_map_id = m.id) planejado ON true
    WHERE (NOT :so_pendentes OR m.centro_custo_id IS NULL)
      AND concat_ws(' ', m.nome_centro_origem, m.nome_subcentro_origem, m.centro_origem) ILIKE '%' || :busca || '%'
    ORDER BY m.centro_custo_id IS NOT NULL, coalesce(uso.valor, 0) DESC, 3, 4
    LIMIT :limite
"""
OPCOES_DE_CONTA = "SELECT id, nome, classificacao FROM dim.centro_custo WHERE ativo ORDER BY classificacao, nome"
PENDENTES_DE_CONTA = "SELECT count(*) FROM dim.plano_contas_map WHERE centro_custo_id IS NULL"
# O subcentro pertence ao centro: trocar o centro limpa o subcentro (hoje a dim.subcentro ainda está vazia).
CLASSIFICAR_CONTA = """
    UPDATE dim.plano_contas_map
    SET centro_custo_id = :centro, subcentro_id = NULL, confirmado_por = :usuario, confirmado_em = now(),
        atualizado_em = now()
    WHERE id = :id
    RETURNING id
"""
DESFAZER_CONTA = """
    UPDATE dim.plano_contas_map
    SET centro_custo_id = NULL, subcentro_id = NULL, confirmado_por = NULL, confirmado_em = NULL,
        atualizado_em = now()
    WHERE id = :id
    RETURNING id
"""


def listar_contas(s: Session, so_pendentes: bool, busca: str) -> ContasDeOrigem:
    itens = []
    parametros = {"so_pendentes": so_pendentes, "busca": busca.strip(), "limite": LIMITE_DA_LISTA}
    for linha in s.execute(text(CONTAS), parametros).mappings():
        itens.append(ContaDeOrigem(**linha))
    opcoes = []
    for linha in s.execute(text(OPCOES_DE_CONTA)).mappings():
        opcoes.append(OpcaoDeConta(**linha))
    return ContasDeOrigem(pendentes=s.scalar(text(PENDENTES_DE_CONTA)), opcoes=opcoes, itens=itens)


def classificar_conta(s: Session, mapa_id: UUID, centro_custo_id: int | None, usuario_id: UUID) -> None:
    """Grava o centro de custo (ou volta para "A classificar"). O DRE lê pela view: nada a recalcular."""
    if centro_custo_id is None:
        alterada = s.execute(text(DESFAZER_CONTA), {"id": mapa_id}).first()
    else:
        alterada = s.execute(text(CLASSIFICAR_CONTA),
                             {"id": mapa_id, "centro": centro_custo_id, "usuario": usuario_id}).first()
    if alterada is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "de-para de conta não encontrado")
