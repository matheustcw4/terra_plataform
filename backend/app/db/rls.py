"""Gerador do SQL de RLS usado pelas migrações `rls_*` (um único padrão para todas as tabelas).

Regras:
- `app_user` (API): leitura conforme a regra da tabela; escrita só para admin.
  A escrita é uma política FOR ALL com USING e WITH CHECK, para que UPDATE/DELETE de não-admin não atinjam
  linha nenhuma (uma política de leitura FOR ALL deixaria um usuário comum apagar linhas que só deveria ver).
- `app_etl` (workers): acesso total ou só leitura, conforme a tabela.
- Sem política para um papel = nenhuma linha (RLS fecha por padrão). FORCE vale até para o dono.
- As funções `app.*` são chamadas dentro de `(SELECT ...)` para virar InitPlan
  (avaliadas 1× por consulta, não por linha).
"""

from typing import Literal

ADMIN = "(SELECT app.eh_admin())"


def por_fazenda(coluna: str = "fazenda_id") -> str:
    return f"{ADMIN} OR {coluna} = ANY ((SELECT app.fazendas_visiveis())::uuid[])"


def por_cliente(coluna: str = "cliente_id") -> str:
    return f"{ADMIN} OR {coluna} = ANY ((SELECT app.clientes_visiveis())::uuid[])"


TODOS = "true"
SO_ADMIN = ADMIN

AcessoEtl = Literal["tudo", "leitura", "nenhum"]


def habilitar(tabela: str, leitura_usuario: str | None, etl: AcessoEtl = "tudo") -> str:
    """SQL que liga o RLS (ENABLE + FORCE) e cria as políticas padrão de `tabela`.

    leitura_usuario: expressão USING para SELECT do app_user (None = usuário comum não lê; admin lê via escrita).
    """
    partes = [
        f"ALTER TABLE {tabela} ENABLE ROW LEVEL SECURITY;",
        f"ALTER TABLE {tabela} FORCE ROW LEVEL SECURITY;",
        f"CREATE POLICY usuario_escrita ON {tabela} FOR ALL TO app_user USING ({ADMIN}) WITH CHECK ({ADMIN});",
    ]
    if leitura_usuario is not None:
        partes.append(f"CREATE POLICY usuario_leitura ON {tabela} FOR SELECT TO app_user USING ({leitura_usuario});")
    if etl == "tudo":
        partes.append(f"CREATE POLICY etl_tudo ON {tabela} FOR ALL TO app_etl USING (true) WITH CHECK (true);")
    elif etl == "leitura":
        partes.append(f"CREATE POLICY etl_leitura ON {tabela} FOR SELECT TO app_etl USING (true);")
    return "\n".join(partes)


def desabilitar(tabela: str) -> str:
    return "\n".join(
        [
            *(f"DROP POLICY IF EXISTS {p} ON {tabela};" for p in ("usuario_escrita", "usuario_leitura", "etl_tudo",
                                                                     "etl_leitura")),
            f"ALTER TABLE {tabela} NO FORCE ROW LEVEL SECURITY;",
            f"ALTER TABLE {tabela} DISABLE ROW LEVEL SECURITY;",
        ]
    )
