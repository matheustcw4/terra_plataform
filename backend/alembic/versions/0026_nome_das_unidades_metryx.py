"""nome_das_unidades_metryx

As unidades do Metryx passam a ter o nome do cliente na descrição (a tela de integrações mostra o histórico das cargas
cliente por cliente; pedido do usuário, 10/11/2026). O adapter já grava o nome a cada carga; aqui as que já existem o
recebem agora, pelo vínculo do cliente (`core.fonte_vinculo`), sem esperar a próxima: as da API (`metryx:`) e as da
ponte do datalake do BI (`stg:`), estas com a marca do datalake. A migração roda como app_owner, que passa pelo RLS.

Revision ID: 0026
Revises: 0025
Create Date: 2026-11-10
"""

from alembic import op

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None

NOMEAR = """
    UPDATE ingest.unidade_origem u
       SET descricao = c.nome || '{marca}'
      FROM core.fonte_vinculo v
      JOIN core.cliente c ON c.id = v.entidade_id
     WHERE u.fonte = 'metryx' AND v.fonte = 'metryx' AND v.entidade = 'cliente'
       AND u.chave = '{prefixo}' || v.id_externo
"""
DESNOMEAR = """
    UPDATE ingest.unidade_origem
       SET descricao = '{descricao}' || substr(chave, length('{prefixo}') + 1)
     WHERE fonte = 'metryx' AND chave LIKE '{prefixo}%'
"""


def upgrade() -> None:
    op.execute(NOMEAR.format(marca="", prefixo="metryx:"))
    op.execute(NOMEAR.format(marca=" (datalake do BI)", prefixo="stg:"))


def downgrade() -> None:
    op.execute(DESNOMEAR.format(descricao="Metryx cliente ", prefixo="metryx:"))
    op.execute(DESNOMEAR.format(descricao="Metryx (stg) cliente ", prefixo="stg:"))
