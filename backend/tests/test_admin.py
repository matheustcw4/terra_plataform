"""Telas de admin: de-paras de categoria e de contas, usuários, funções e acesso às fazendas, pela API (app_user + RLS).

Fazenda sintética (tests/sinteticos.py) com 80 bezerras nascidas em 08/2025 numa categoria que o CADASTROINICIAL não
tem ("Bezerra Mamando"): o de-para nasce pendente e as bezerras ficam fora do estoque até o admin classificar. O DRE
padrão tem uma conta fora do plano unificado ("Apicultura / Mel", R$ 200), que nasce "A classificar".
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from kombu.exceptions import OperationalError
from sqlalchemy import text

from app.services import atualizacao
from app.tasks.trava import trava_das_cargas
from tests.test_api import SENHA, carregar_planilha, entrar, usuario_com_senha

NASCIMENTOS = [["NASCIMENTO", datetime(2025, 7, 10), "Bezerro Mamando", 120, "25/26", 32],
               ["NASCIMENTO", datetime(2025, 8, 8), "Bezerra Mamando", 80, "25/26", 30]]
PERIODO = {"inicio": "2025-07", "fim": "2025-09"}


@pytest.fixture
def fazenda(engine_etl, engine_super, tmp_path):
    return carregar_planilha(engine_etl, engine_super, tmp_path, linhas={"fNascimento": NASCIMENTOS})


@pytest.fixture
def admin(api: TestClient, engine_super) -> dict:
    usuario_com_senha(engine_super, "admin@terra.test", admin=True)
    return entrar(api, "admin@terra.test")


def estoque_por_categoria(api: TestClient, cabecalho: dict, fazenda) -> dict:
    resposta = api.get("/api/v1/dashboards/movimentacao", headers=cabecalho,
                       params={"fazendas": [str(fazenda)], **PERIODO})
    assert resposta.status_code == 200, resposta.text
    estoque = {}
    for categoria in resposta.json()["estoque_por_categoria"]:
        estoque[categoria["categoria"]] = categoria["estoque_final"]
    return estoque


def test_so_o_admin_entra(api, engine_super, fazenda):
    usuario_com_senha(engine_super, "consultor@terra.test", fazendas=[fazenda])
    cabecalho = entrar(api, "consultor@terra.test")
    for rota in ("/api/v1/admin/categorias", "/api/v1/admin/contas", "/api/v1/admin/usuarios", "/api/v1/admin/funcoes",
                 "/api/v1/admin/atualizacao"):
        assert api.get(rota, headers=cabecalho).status_code == 403
    assert api.post("/api/v1/admin/funcoes", headers=cabecalho, json={"nome": "X"}).status_code == 403
    assert api.post("/api/v1/admin/atualizacao", headers=cabecalho).status_code == 403
    assert api.put(f"/api/v1/admin/usuarios/{fazenda}/fazendas", headers=cabecalho,
                   json={"fazendas": []}).status_code == 403


def test_classificar_categoria_recalcula_o_estoque(api, admin, fazenda):
    assert "BEZERRA" not in estoque_por_categoria(api, admin, fazenda)
    lista = api.get("/api/v1/admin/categorias", headers=admin).json()
    pendente = [item for item in lista["itens"] if item["nome_origem"] == "Bezerra Mamando"][0]
    # usos: o nascimento e o saldo inicial zerado que toda categoria ganha no começo do período
    assert (pendente["fazenda"], pendente["categoria_bi_id"], pendente["lancamentos"]) == ("TESTE", None, 2)
    assert lista["pendentes"] >= 1
    bezerra = [opcao["id"] for opcao in lista["opcoes"] if opcao["nome"] == "BEZERRA"][0]

    resposta = api.put(f"/api/v1/admin/categorias/{pendente['id']}", headers=admin,
                       json={"categoria_bi_id": bezerra})
    assert resposta.status_code == 204, resposta.text
    assert estoque_por_categoria(api, admin, fazenda)["BEZERRA"] == 80
    todas = api.get("/api/v1/admin/categorias", headers=admin, params={"so_pendentes": False, "busca": "bezerra"})
    classificada = [item for item in todas.json()["itens"] if item["id"] == pendente["id"]][0]
    assert (classificada["categoria_bi_id"], classificada["confirmado_por"]) == (bezerra, "admin@terra.test")

    # desfazer: volta a pendente e sai do estoque
    api.put(f"/api/v1/admin/categorias/{pendente['id']}", headers=admin, json={"categoria_bi_id": None})
    assert "BEZERRA" not in estoque_por_categoria(api, admin, fazenda)


def test_classificacao_do_admin_sobrevive_a_recarga_da_planilha(api, admin, engine_etl, engine_super, tmp_path):
    # a categoria está no CADASTROINICIAL, mas com a categoria BI em branco: o de-para nasce pendente
    em_branco = (("Bezerra Mamando", None, None),)
    fazenda = carregar_planilha(engine_etl, engine_super, tmp_path, linhas={"fNascimento": NASCIMENTOS},
                                categorias_extras=em_branco)
    lista = api.get("/api/v1/admin/categorias", headers=admin).json()
    pendente = [item for item in lista["itens"] if item["nome_origem"] == "Bezerra Mamando"][0]
    assert (pendente["categoria_bi_id"], pendente["confirmado_em"]) == (None, None)
    bezerra = [opcao["id"] for opcao in lista["opcoes"] if opcao["nome"] == "BEZERRA"][0]
    api.put(f"/api/v1/admin/categorias/{pendente['id']}", headers=admin, json={"categoria_bi_id": bezerra})

    # o consultor manda a planilha de novo (com uma morte a mais), ainda com a categoria em branco no cadastro
    morte = ["MORTE", datetime(2025, 8, 20), "Vaca", None, 1, "Raio", "Pasto 2", 450, "25/26"]
    carregar_planilha(engine_etl, engine_super, tmp_path, linhas={"fNascimento": NASCIMENTOS, "fMortes": [morte]},
                      categorias_extras=em_branco)
    assert estoque_por_categoria(api, admin, fazenda)["BEZERRA"] == 80


def test_classificar_conta_muda_o_dre(api, admin, fazenda, engine_super):
    lista = api.get("/api/v1/admin/contas", headers=admin).json()
    apicultura = [item for item in lista["itens"] if item["centro"] == "Apicultura"][0]
    assert (apicultura["centro_custo_id"], apicultura["lancamentos"], apicultura["valor"]) == (None, 1, 200)
    with engine_super.connect() as c:
        outros_animais = c.scalar(text("SELECT id FROM dim.centro_custo WHERE nome = 'Vendas outros animais'"))

    resposta = api.put(f"/api/v1/admin/contas/{apicultura['id']}", headers=admin,
                       json={"centro_custo_id": outros_animais})
    assert resposta.status_code == 204, resposta.text
    dre = api.get("/api/v1/dashboards/previsto_realizado", headers=admin,
                  params={"fazendas": [str(fazenda)], **PERIODO}).json()
    receitas = [grupo for grupo in dre["grupos"] if grupo["classificacao"] == "A - RECEITAS"][0]
    assert [(conta["nome"], conta["acumulado"]["realizado"]) for conta in receitas["contas"]] == [
        ("Vendas outros animais", 200)]
    assert api.put(f"/api/v1/admin/contas/{fazenda}", headers=admin,
                   json={"centro_custo_id": outros_animais}).status_code == 404


def criar_funcao(api: TestClient, admin: dict, nome: str) -> dict:
    resposta = api.post("/api/v1/admin/funcoes", headers=admin, json={"nome": nome})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_usuarios_e_acesso_as_fazendas(api, admin, fazenda, engine_super):
    tecnico = criar_funcao(api, admin, "Técnico de campo")
    novo = {"nome": "Técnica", "email": " Tecnica@Terra.test ", "senha": SENHA, "funcao_id": tecnico["id"]}
    criado = api.post("/api/v1/admin/usuarios", headers=admin, json=novo)
    assert criado.status_code == 201, criado.text
    tecnica = criado.json()
    assert (tecnica["email"], tecnica["funcao"], tecnica["eh_admin"], tecnica["fazendas"]) ==         ("tecnica@terra.test", "Técnico de campo", False, 0)
    with engine_super.connect() as c:                   # a senha só existe como hash argon2
        hash_gravado = c.execute(text("SELECT senha_hash FROM core.usuario WHERE email = 'tecnica@terra.test'")).scalar()
    assert hash_gravado.startswith("$argon2") and SENHA not in hash_gravado
    assert "senha_hash" not in tecnica
    assert api.post("/api/v1/admin/usuarios", headers=admin, json=novo).status_code == 409

    # sem fazenda, a técnica entra e não vê nada; com acesso, vê a fazenda
    cabecalho = entrar(api, "tecnica@terra.test")
    assert api.get("/api/v1/escopo", headers=cabecalho).json()["fazendas"] == []
    acesso = api.put(f"/api/v1/admin/usuarios/{tecnica['id']}/fazendas", headers=admin,
                     json={"fazendas": [str(fazenda)]})
    assert [(item["nome"], item["tem_acesso"]) for item in acesso.json()] == [("TESTE", True)]
    assert [item["nome"] for item in api.get("/api/v1/escopo", headers=cabecalho).json()["fazendas"]] == ["TESTE"]

    # desativada, perde a sessão na hora
    alterado = api.patch(f"/api/v1/admin/usuarios/{tecnica['id']}", headers=admin, json={"ativo": False})
    assert alterado.json()["ativo"] is False
    assert api.get("/api/v1/escopo", headers=cabecalho).status_code == 401


def test_admin_nao_se_tranca_para_fora(api, admin):
    usuarios = api.get("/api/v1/admin/usuarios", headers=admin).json()
    eu = [usuario for usuario in usuarios if usuario["email"] == "admin@terra.test"][0]
    for alteracao in ({"eh_admin": False}, {"ativo": False}):
        assert api.patch(f"/api/v1/admin/usuarios/{eu['id']}", headers=admin, json=alteracao).status_code == 422
    assert api.patch(f"/api/v1/admin/usuarios/{eu['id']}", headers=admin, json={"senha": "curta"}).status_code == 422


def test_cadastro_de_funcoes(api, admin):
    consultor = criar_funcao(api, admin, "  Consultor ")
    assert (consultor["nome"], consultor["ativo"], consultor["usuarios"]) == ("Consultor", True, 0)
    assert api.post("/api/v1/admin/funcoes", headers=admin, json={"nome": "consultor"}).status_code == 409
    assert api.post("/api/v1/admin/funcoes", headers=admin, json={"nome": "   "}).status_code == 422
    gerente = criar_funcao(api, admin, "Gerente")
    renomeada = api.patch(f"/api/v1/admin/funcoes/{gerente['id']}", headers=admin, json={"nome": "Gerente de fazenda"})
    assert renomeada.json()["nome"] == "Gerente de fazenda"
    assert api.patch(f"/api/v1/admin/funcoes/{gerente['id']}", headers=admin,
                     json={"nome": "CONSULTOR"}).status_code == 409

    # o usuário escolhe a função na lista: sem função, com função inexistente ou inativa, não cria
    novo = {"nome": "Ana", "email": "ana@terra.test", "senha": SENHA}
    assert api.post("/api/v1/admin/usuarios", headers=admin, json=novo).status_code == 422
    assert api.post("/api/v1/admin/usuarios", headers=admin, json={**novo, "funcao_id": 999}).status_code == 422
    api.patch(f"/api/v1/admin/funcoes/{gerente['id']}", headers=admin, json={"ativo": False})
    assert api.post("/api/v1/admin/usuarios", headers=admin,
                    json={**novo, "funcao_id": gerente["id"]}).status_code == 422
    ana = api.post("/api/v1/admin/usuarios", headers=admin, json={**novo, "funcao_id": consultor["id"]}).json()

    # trocar a função do usuário; função em uso não se apaga, a sem uso sim
    trocada = api.patch(f"/api/v1/admin/usuarios/{ana['id']}", headers=admin, json={"funcao_id": gerente["id"]})
    assert trocada.status_code == 422                            # inativa
    lista = {funcao["nome"]: funcao for funcao in api.get("/api/v1/admin/funcoes", headers=admin).json()}
    assert (lista["Consultor"]["usuarios"], lista["Gerente de fazenda"]["ativo"]) == (1, False)
    assert api.delete(f"/api/v1/admin/funcoes/{consultor['id']}", headers=admin).status_code == 409
    assert api.delete(f"/api/v1/admin/funcoes/{gerente['id']}", headers=admin).status_code == 204
    assert [funcao["nome"] for funcao in api.get("/api/v1/admin/funcoes", headers=admin).json()] == ["Consultor"]


@pytest.fixture
def fila(monkeypatch) -> list:
    """No lugar do Redis: guarda o que a API pôs na fila."""
    pedidos = []
    monkeypatch.setattr(atualizacao, "enviar_para_a_fila", pedidos.append)
    return pedidos


def test_atualizar_agora_poe_a_carga_na_fila(api, admin, fila, engine_super):
    situacao = api.get("/api/v1/admin/atualizacao", headers=admin).json()
    assert situacao["rodando"] is False
    assert situacao["ultima"] is None
    resposta = api.post("/api/v1/admin/atualizacao", headers=admin)
    assert resposta.status_code == 202, resposta.text
    assert resposta.json()["pedida_em"]
    with engine_super.connect() as c:
        admin_id = c.scalar(text("SELECT id FROM core.usuario WHERE email = 'admin@terra.test'"))
    assert fila == [admin_id]                                    # o job vai guardar quem pediu


def test_atualizar_agora_com_carga_rodando_espera(api, admin, fila, engine_etl):
    with trava_das_cargas(engine_etl, esperar=False):
        assert api.get("/api/v1/admin/atualizacao", headers=admin).json()["rodando"] is True
        resposta = api.post("/api/v1/admin/atualizacao", headers=admin)
    assert resposta.status_code == 409
    assert fila == []


def test_atualizar_agora_mostra_a_ultima_carga(api, admin, fazenda):
    ultima = api.get("/api/v1/admin/atualizacao", headers=admin).json()["ultima"]
    assert ultima["fonte"] == "planilha"
    assert ultima["finalizado_em"] is not None


def test_atualizar_agora_sem_redis_avisa(api, admin, monkeypatch):
    def fila_fora(usuario_id):
        raise OperationalError("Redis fora do ar")

    monkeypatch.setattr(atualizacao, "enviar_para_a_fila", fila_fora)
    resposta = api.post("/api/v1/admin/atualizacao", headers=admin)
    assert resposta.status_code == 503
    assert "Redis" in resposta.json()["detail"]
