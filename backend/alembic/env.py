"""Ambiente do Alembic.

Conecta como superusuário (URL de migração) e faz `SET ROLE app_owner`: todos os objetos ficam com o dono certo
e as migrações rodam sem privilégio de superusuário. As migrações são escritas à mão (SQL explícito), sem autogenerate.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool, text

from app.core.config import get_settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

banco = context.get_x_argument(as_dictionary=True).get("banco")
url = config.attributes.get("url") or get_settings().url_migracao(banco)


def run_migrations_offline() -> None:
    context.configure(url=url, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.execute("SET ROLE app_owner")
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        connection.execute(text("SET ROLE app_owner"))
        connection.commit()
        context.configure(connection=connection, transaction_per_migration=True)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
