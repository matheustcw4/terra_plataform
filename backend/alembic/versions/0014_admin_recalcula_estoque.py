"""admin_recalcula_estoque: a API (app_user) pode recalcular o estoque mensal; limpa confirmações sem categoria

Classificar uma categoria de origem na tela de admin muda o estoque por categoria BI das fazendas que usam aquele
de-para (`fato.estoque_mensal` é derivada). A API recalcula na hora, na mesma transação. A função roda com os
direitos de quem chama: o RLS só deixa o admin apagar e gravar em `fato.estoque_mensal`, então um usuário comum que
a chamasse não mudaria nada.

Limpeza: a carga das planilhas gravava `confirmado_em` também quando o CADASTROINICIAL deixava a categoria BI em
branco (de-para pendente com data de confirmação). A partir desta versão a planilha só confirma com a categoria
preenchida (`app/etl/mapping.py`); aqui, as confirmações vazias já gravadas voltam a pendente de verdade.

Revision ID: 0014
Revises: 0013
Create Date: 2026-10-15
"""

from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("GRANT EXECUTE ON FUNCTION fato.recalcular_estoque_mensal(uuid[], date) TO app_user")
    op.execute("""
        UPDATE dim.categoria_map SET confirmado_em = NULL, confirmado_por = NULL
        WHERE categoria_bi_id IS NULL AND (confirmado_em IS NOT NULL OR confirmado_por IS NOT NULL)
    """)


def downgrade() -> None:
    # a limpeza não volta: uma data de confirmação sem categoria não tem o que restaurar
    op.execute("REVOKE EXECUTE ON FUNCTION fato.recalcular_estoque_mensal(uuid[], date) FROM app_user")
