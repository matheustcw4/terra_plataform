"""Conta mestre do Metryx: a lista de clientes (`GET /api-metryx/customers`) alimenta as credenciais a cada carga.
Cliente novo entra sozinho, token trocado é rotacionado, a conta recusada não para a carga e nenhum token aparece no
bruto, no log ou para a API do painel. A API é simulada (httpx.MockTransport): nada chama o Metryx de verdade."""

import json
from datetime import date

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.etl.adapters.metryx import contas, credenciais
from app.etl.adapters.metryx.adapter import AdapterMetryx
from app.etl.adapters.metryx.cliente import ClienteMetryx
from app.etl.adapters.metryx.endpoints import CAMINHO_DOS_CLIENTES
from app.etl.pipeline import MotorCarga
from app.services import integracoes
from tests.sinteticos import CLIENTE, payloads_metryx, transporte_metryx

BASE = "https://metryx.teste/mtxserver"
MESTRE = "token-mestre"
NOVO = "c0ffee00-0000-0000-0000-000000000002"


def lista_de_clientes(token_do_cliente: str = "token-teste") -> list[dict]:
    return [
        {"idCustomer": CLIENTE, "customer": "Cliente Teste", "listToken": [{"token": token_do_cliente}]},
        {"idCustomer": NOVO, "customer": "Cliente Novo", "listToken": [{"token": "token-do-novo"}]},
        {"idCustomer": "sem-token", "customer": "Sem Token", "listToken": []},
    ]


def transporte_com_conta(clientes: list[dict], dados: dict | None = None) -> httpx.MockTransport:
    """A lista de clientes com o token mestre; o resto, como na API de um cliente (tests/sinteticos.py)."""
    do_cliente = transporte_metryx(dados or payloads_metryx())

    def responder(pedido: httpx.Request) -> httpx.Response:
        if pedido.url.path.removeprefix("/mtxserver") != CAMINHO_DOS_CLIENTES:
            return do_cliente.handle_request(pedido)
        if pedido.headers.get("x-auth-token") != MESTRE:
            return httpx.Response(401)
        return httpx.Response(200, content=json.dumps(clientes).encode())

    return httpx.MockTransport(responder)


def cliente_http(transporte: httpx.MockTransport) -> ClienteMetryx:
    return ClienteMetryx(BASE, transport=transporte, tentativas=2, espera_max=0.01)


def tokens_ativos(engine_etl) -> dict[str, str]:
    ativos = {}
    for credencial in credenciais.credenciais_ativas(engine_etl):
        ativos[credencial.metryx_customer_id] = credencial.token
    return ativos


def test_a_lista_cadastra_o_cliente_novo_e_troca_o_token(engine_etl, engine_super, caplog):
    credenciais.registrar(engine_etl, CLIENTE, "token-antigo", "Cliente Teste")
    contas.registrar_conta(engine_etl, MESTRE, "Terra")
    descoberta = contas.descobrir_clientes(engine_etl, cliente_http(transporte_com_conta(lista_de_clientes())))
    assert (descoberta.clientes, descoberta.novos, descoberta.trocados, descoberta.sem_token) == (3, 1, 1, 1)
    assert tokens_ativos(engine_etl) == {CLIENTE: "token-teste", NOVO: "token-do-novo"}
    for token in (MESTRE, "token-teste", "token-do-novo"):
        assert token not in caplog.text
    with engine_super.connect() as c:
        conta = c.execute(text("SELECT status, clientes, ultimo_erro FROM integracao.metryx_conta")).one()
        linhas = c.scalar(text("SELECT count(*) FROM integracao.metryx_credencial"))
    assert tuple(conta) == ("ativa", 3, None)
    # a segunda leitura não muda nada: o token em uso continua na lista
    de_novo = contas.descobrir_clientes(engine_etl, cliente_http(transporte_com_conta(lista_de_clientes())))
    assert (de_novo.novos, de_novo.trocados) == (0, 0)
    with engine_super.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM integracao.metryx_credencial")) == linhas


def test_a_conta_recusada_nao_para_a_carga(engine_etl, engine_super):
    credenciais.registrar(engine_etl, CLIENTE, "token-teste", "Cliente Teste")
    contas.registrar_conta(engine_etl, "token-mestre-velho", "Terra")
    descoberta = contas.descobrir_clientes(engine_etl, cliente_http(transporte_com_conta(lista_de_clientes())))
    assert descoberta.contas_com_erro == 1
    assert tokens_ativos(engine_etl) == {CLIENTE: "token-teste"}          # o cliente já cadastrado continua
    with engine_super.connect() as c:
        status, erro = c.execute(text("SELECT status, ultimo_erro FROM integracao.metryx_conta")).one()
    assert status == "invalida" and "401" in erro
    with Session(engine_super) as s:
        [observacao, clientes] = integracoes.observacoes_do_metryx(s)
    assert "recusou o token" in observacao and clientes == "Clientes com token ativo: 1."


def test_a_carga_traz_o_cliente_que_so_a_conta_conhece(engine_etl, engine_super):
    contas.registrar_conta(engine_etl, MESTRE, "Terra")
    clientes = [{"idCustomer": CLIENTE, "customer": "Cliente Teste", "listToken": [{"token": "token-teste"}]}]
    adapter = AdapterMetryx(engine_etl, cliente_http(transporte_com_conta(clientes)))
    resultado = MotorCarga(engine_etl, hoje=date(2025, 10, 1), estoque_ate=date(2025, 9, 1)).executar(adapter)
    assert [unidade.status for unidade in resultado.unidades] == ["carregada_com_avisos"]
    with engine_super.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM core.fazenda WHERE proprietario = 'Cliente Teste'")) == 2
        bruto = c.scalar(text("SELECT string_agg(conteudo::text, '') FROM raw.payload"))
    assert MESTRE not in bruto and "token-teste" not in bruto     # a lista dos tokens nunca vai para o bruto


def test_sem_conta_mestre_a_tela_explica(engine_super):
    with Session(engine_super) as s:
        [sem_conta, clientes] = integracoes.observacoes_do_metryx(s)
    assert sem_conta.startswith("Sem conta mestre") and clientes == "Clientes com token ativo: 0."


def test_a_lista_de_clientes_esta_na_allow_list():
    transporte = transporte_com_conta(lista_de_clientes())
    resposta = cliente_http(transporte).get_lista(CAMINHO_DOS_CLIENTES, MESTRE)
    assert len(resposta.itens) == 3
