"""Comandos de administração de usuários (rodam como dono do banco: servem para montar o primeiro admin).

    python -m app.comandos criar-usuario --email maria@terra.com --nome "Maria" [--admin]
    python -m app.comandos dar-acesso --email joao@cliente.com --fazenda "85|BELA VISTA" [--cliente 85]
    python -m app.comandos importar-equipe "Levantamento Clientes para Power BI.xlsx" [--aplicar]

A senha do criar-usuario vem da variável SENHA_NOVA ou é perguntada sem aparecer na tela. A fazenda pode ser o uuid
ou o identificador da fonte (planilha: "código|FAZENDA"); --cliente dá acesso a todas as fazendas do código.

O importar-equipe cria os técnicos e gerentes da planilha de levantamento com as fazendas de cada um (regras em
app/services/equipe.py). Sem --aplicar, só mostra o que faria. Pode rodar de novo: só acrescenta o que falta.
"""

import argparse
import getpass
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.core.seguranca import hash_da_senha
from app.services.equipe import (
    Equipe,
    Pessoa,
    aplicar_equipe,
    fazendas_do_painel,
    ler_levantamento,
    montar_equipe,
)


def criar_usuario(email: str, nome: str, admin: bool) -> None:
    senha = os.environ.pop("SENHA_NOVA", None) or getpass.getpass("senha (não aparece): ")
    if len(senha) < 8:
        sys.exit("a senha precisa ter pelo menos 8 caracteres")
    with create_engine(get_settings().url_migracao()).begin() as conexao:
        conexao.execute(text("""
            INSERT INTO core.usuario (email, nome, senha_hash, eh_admin)
            VALUES (lower(btrim(:email)), :nome, :hash, :admin)
            ON CONFLICT (email) DO UPDATE SET nome = excluded.nome, senha_hash = excluded.senha_hash,
                                              eh_admin = excluded.eh_admin, ativo = true, atualizado_em = now()
        """), {"email": email, "nome": nome, "hash": hash_da_senha(senha), "admin": admin})
    print(f"usuário {email} pronto{' (admin)' if admin else ''}")


def dar_acesso(email: str, fazendas: list[str], clientes: list[str]) -> None:
    with create_engine(get_settings().url_migracao()).begin() as conexao:
        usuario_id = conexao.scalar(text("SELECT id FROM core.usuario WHERE email = lower(btrim(:e))"), {"e": email})
        if usuario_id is None:
            sys.exit(f"usuário {email} não existe; rode criar-usuario antes")
        ids = []
        for fazenda in fazendas:
            ids.append(_fazenda_id(conexao, fazenda))
        for codigo in clientes:
            do_cliente = conexao.scalars(text("SELECT f.id FROM core.fazenda f JOIN core.cliente c "
                                              "ON c.id = f.cliente_id WHERE c.codigo = :c"), {"c": int(codigo)})
            ids.extend(do_cliente)
        for fazenda_id in ids:
            conexao.execute(text("INSERT INTO core.usuario_fazenda (usuario_id, fazenda_id) VALUES (:u, :f) "
                                 "ON CONFLICT DO NOTHING"), {"u": usuario_id, "f": fazenda_id})
    print(f"{email}: acesso a {len(ids)} fazenda(s)")


def _fazenda_id(conexao, fazenda: str):
    encontrada = conexao.scalar(text("""
        SELECT f.id FROM core.fazenda f
        WHERE f.id::text = :f
           OR f.id IN (SELECT entidade_id FROM core.fonte_vinculo WHERE entidade = 'fazenda' AND id_externo = :f)
        LIMIT 1"""), {"f": fazenda})
    if encontrada is None:
        sys.exit(f"fazenda {fazenda} não encontrada")
    return encontrada


def importar_equipe(caminho: Path, aplicar: bool) -> None:
    linhas = ler_levantamento(caminho)
    with create_engine(get_settings().url_migracao()).begin() as conexao:
        equipe = montar_equipe(linhas, fazendas_do_painel(conexao))
        mostrar_equipe(equipe, len(linhas))
        if not aplicar:
            print("\nsimulação: nada foi gravado (rode com --aplicar para gravar)")
            return
        resumo = aplicar_equipe(conexao, equipe)
    print(f"\ngravado: {resumo['usuarios_criados']} usuário(s) novo(s), {resumo['funcoes_completadas']} função(ões) "
          f"completada(s), {resumo['acessos_novos']} acesso(s) novo(s) a fazendas")


def mostrar_equipe(equipe: Equipe, linhas: int) -> None:
    print(f"{linhas} linha(s) na planilha, {len(equipe.pessoas)} pessoa(s)")
    for pessoa in sorted(equipe.pessoas.values(), key=ordem_da_pessoa):
        marca = ""
        if pessoa.nome_provisorio:
            marca = " (nome tirado do e-mail: confira)"
        print(f"  {pessoa.funcao:<8} {pessoa.nome:<28} {pessoa.email:<45} {len(pessoa.fazendas):>4} fazenda(s){marca}")
    print(f"\n{len(equipe.avisos)} aviso(s):")
    for aviso in equipe.avisos:
        print(f"  - {aviso}")
    print(f"\n{len(equipe.linhas_sem_fazenda)} linha(s) sem fazenda no painel (ninguém ganha acesso por elas):")
    for linha in equipe.linhas_sem_fazenda:
        print(f"  - linha {linha.numero}: {linha.codigo} | {linha.proprietario} | {linha.fazenda}")
    print(f"\n{len(equipe.clientes_metryx_fora)} cliente(s) do Metryx no painel sem linha na planilha (sem acesso):")
    for cliente in equipe.clientes_metryx_fora:
        print(f"  - {cliente}")


def ordem_da_pessoa(pessoa: Pessoa) -> tuple[str, str]:
    """Gerentes primeiro, depois técnicos; em cada grupo, pelo nome."""
    return pessoa.funcao, pessoa.nome


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.comandos", description="Usuários do Projeto Terra")
    comandos = parser.add_subparsers(dest="comando", required=True)
    criar = comandos.add_parser("criar-usuario", help="cria (ou atualiza) um usuário com senha")
    criar.add_argument("--email", required=True)
    criar.add_argument("--nome", required=True)
    criar.add_argument("--admin", action="store_true")
    acesso = comandos.add_parser("dar-acesso", help="dá acesso a fazendas (ou a todas as de um cliente)")
    acesso.add_argument("--email", required=True)
    acesso.add_argument("--fazenda", action="append", default=[])
    acesso.add_argument("--cliente", action="append", default=[], help="código do projeto")
    equipe = comandos.add_parser("importar-equipe", help="técnicos e gerentes da planilha de levantamento")
    equipe.add_argument("planilha", type=Path)
    equipe.add_argument("--aplicar", action="store_true", help="grava (sem ele, só mostra o que faria)")
    argumentos = parser.parse_args(argv)
    if argumentos.comando == "criar-usuario":
        criar_usuario(argumentos.email, argumentos.nome, argumentos.admin)
    elif argumentos.comando == "dar-acesso":
        dar_acesso(argumentos.email, argumentos.fazenda, argumentos.cliente)
    else:
        importar_equipe(argumentos.planilha, argumentos.aplicar)


if __name__ == "__main__":
    main()
