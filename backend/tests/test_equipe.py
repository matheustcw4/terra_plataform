"""Equipe a partir da planilha de levantamento (app/services/equipe.py): pessoas, funções, nomes e fazendas.

Cenário: duas fazendas de planilha do cliente 10, uma do cliente 30 (com outro nome na planilha) e as fazendas Metryx
de dois customers, um deles fora do levantamento.
"""

from openpyxl import Workbook
from sqlalchemy import text

from app.services.equipe import GERENTE, TECNICO, aplicar_equipe, fazendas_do_painel, ler_levantamento, montar_equipe

CABECALHO = ["BASE", "CÓDIGO DO CLIENTE", "PROPRIETÁRIO", "PROJETO", "FAZENDA", "TÉCNICO", "EMAIL", "EMAIL - GERENTE",
             "email- REGIONAL", "PRODUTIVO (METRYX OU EXCEL)"]
LINHAS = [
    ["GO", 10, "CLIENTE UM", "P", "FAZENDA A", "ANA SOUZA", "Ana@T.com", "ger@t.com", "reg@t.com", "EXCEL"],
    ["GO", 10, "CLIENTE UM", "P", "Fazenda B", "ANA", "ana@t.com", "ger@t.com", "reg@t.com", "EXCEL"],
    ["MT", 20, "CLIENTE DOIS", "P", "SEM PLANILHA", "BETO", "beto@t.com", "ger@t.com", "ana@t.com", "EXCEL"],
    ["MT", 30, "CLIENTE TRÊS", "P", "NOME NA PLANILHA", "ANA SOUZA", "beto@t.com", "ger@t.com", "reg@t.com", "EXCEL"],
    ["MS", 40, "Cliente Metryx", "P", "Qualquer", "CARLA DA SILVA", "carla@t.com", "ger@t.com", "reg@t.com", "METRYX"],
]


def criar_planilha(pasta) -> str:
    livro = Workbook()
    aba = livro.active
    aba.append(CABECALHO)
    for linha in LINHAS:
        aba.append(linha)
    caminho = pasta / "levantamento.xlsx"
    livro.save(caminho)
    return caminho


def criar_fazenda(conexao, fonte: str, id_externo: str, nome: str, proprietario: str):
    cliente = conexao.execute(text("INSERT INTO core.cliente (nome) VALUES (:n) RETURNING id"), {"n": proprietario})
    fazenda_id = conexao.execute(text("""
        INSERT INTO core.fazenda (cliente_id, nome, proprietario) VALUES (:c, :n, :p) RETURNING id"""),
        {"c": cliente.scalar(), "n": nome, "p": proprietario}).scalar()
    conexao.execute(text("""
        INSERT INTO core.fonte_vinculo (fonte, entidade, id_externo, entidade_id)
        VALUES (:fonte, 'fazenda', :id_externo, :id)"""), {"fonte": fonte, "id_externo": id_externo, "id": fazenda_id})
    return fazenda_id


def preparar_fazendas(engine_super) -> dict:
    with engine_super.begin() as c:
        return {
            "A": criar_fazenda(c, "planilha", "10|FAZENDA A", "FAZENDA A", "CLIENTE UM"),
            "B": criar_fazenda(c, "planilha", "10|FAZENDA B", "FAZENDA B", "CLIENTE UM"),
            "UNICA": criar_fazenda(c, "planilha", "30|OUTRO NOME", "OUTRO NOME", "CLIENTE TRÊS"),
            "M1": criar_fazenda(c, "metryx", "cust|f1", "3) Fazenda Qualquer", "Cliente Metryx"),
            "M2": criar_fazenda(c, "metryx", "outro|f2", "Sede", "Outro Cliente"),
        }


def test_monta_a_equipe_da_planilha(engine_super, tmp_path):
    fazendas = preparar_fazendas(engine_super)
    with engine_super.connect() as c:
        equipe = montar_equipe(ler_levantamento(criar_planilha(tmp_path)), fazendas_do_painel(c))

    ana, ger, beto, carla = (equipe.pessoas[email] for email in ("ana@t.com", "ger@t.com", "beto@t.com", "carla@t.com"))
    # o nome mais usado na coluna TÉCNICO; regional em alguma linha é gerente
    assert (ana.nome, ana.funcao, ana.nome_provisorio) == ("Ana Souza", GERENTE, False)
    assert (beto.nome, beto.funcao) == ("Beto", TECNICO)
    assert (carla.nome, carla.funcao) == ("Carla da Silva", TECNICO)
    # quem só é gerente ou regional ganha nome provisório tirado do e-mail
    assert (ger.nome, ger.funcao, ger.nome_provisorio) == ("Ger", GERENTE, True)

    # planilha pelo código e o nome; código com uma fazenda só casa mesmo com outro nome; Metryx pelo cliente
    assert ana.fazendas == {fazendas["A"], fazendas["B"]}
    assert beto.fazendas == {fazendas["UNICA"]}
    assert carla.fazendas == {fazendas["M1"]}
    assert ger.fazendas == {fazendas["A"], fazendas["B"], fazendas["UNICA"], fazendas["M1"]}

    assert [linha.fazenda for linha in equipe.linhas_sem_fazenda] == ["SEM PLANILHA"]
    assert equipe.clientes_metryx_fora == ["OUTRO CLIENTE"]
    avisos = " ".join(equipe.avisos)
    assert "linha 5" in avisos and "'Ana Souza', mas o e-mail é de Beto" in avisos      # nome de outra pessoa
    assert "casada pela única fazenda de planilha do código" in avisos
    assert "'Ana', mas" not in avisos                                                     # forma curta não é troca


def test_grava_a_equipe_so_acrescentando(engine_super, tmp_path):
    fazendas = preparar_fazendas(engine_super)
    with engine_super.begin() as c:                                     # Carla já existe, com outro nome
        c.execute(text("INSERT INTO core.usuario (email, nome) VALUES ('carla@t.com', 'Carla (já cadastrada)')"))
    linhas = ler_levantamento(criar_planilha(tmp_path))
    with engine_super.begin() as c:
        resumo = aplicar_equipe(c, montar_equipe(linhas, fazendas_do_painel(c)))
    assert (resumo["usuarios_criados"], resumo["funcoes_completadas"], resumo["acessos_novos"]) == (4, 1, 12)

    with engine_super.connect() as c:
        usuarios = {linha.email: linha for linha in c.execute(text("""
            SELECT u.email, u.nome, f.nome AS funcao, u.senha_hash, u.eh_admin,
                   (SELECT count(*) FROM core.usuario_fazenda uf WHERE uf.usuario_id = u.id) AS fazendas
            FROM core.usuario u LEFT JOIN core.funcao f ON f.id = u.funcao_id"""))}
        assert c.execute(text("SELECT nome FROM core.funcao ORDER BY nome")).scalars().all() == [GERENTE, TECNICO]
    assert (usuarios["ana@t.com"].funcao, usuarios["ana@t.com"].fazendas) == (GERENTE, 2)
    assert (usuarios["carla@t.com"].nome, usuarios["carla@t.com"].funcao) == ("Carla (já cadastrada)", TECNICO)
    assert all(usuario.senha_hash is None and not usuario.eh_admin for usuario in usuarios.values())
    with engine_super.connect() as c:                                   # o customer fora do levantamento: ninguém
        assert c.execute(text("SELECT count(*) FROM core.usuario_fazenda WHERE fazenda_id = :f"),
                         {"f": fazendas["M2"]}).scalar() == 0

    # de novo: nada a fazer
    with engine_super.begin() as c:
        resumo = aplicar_equipe(c, montar_equipe(linhas, fazendas_do_painel(c)))
    assert sum(resumo.values()) == 0
