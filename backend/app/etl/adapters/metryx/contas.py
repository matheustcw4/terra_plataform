"""Conta mestre do Metryx (pedido do usuário, 17/11/2026): um token que só lista os clientes e o token de cada um
(`GET /api-metryx/customers`, fora do Swagger; é o que o Pentaho do BI usa, análise 04 §1). Toda carga relê a lista
antes de buscar os dados: cliente novo ganha a credencial dele e token trocado é rotacionado, sem cadastro à mão.

Os tokens da resposta não vão para o bruto nem para o log: só cifrados, em integracao.metryx_credencial. Se a conta
falha (401, rede), a carga segue com os clientes já cadastrados, e o motivo fica na conta (a tela de integrações o
mostra). Cliente que some da lista não é desligado: a credencial dele pode ter sido cadastrada à mão.
"""

import logging
from dataclasses import dataclass, field
from uuid import UUID

import httpx
from sqlalchemy import Engine, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.session import sessao
from app.etl.adapters.metryx import credenciais
from app.etl.adapters.metryx.cliente import ClienteMetryx, CredencialInvalida, ErroMetryx
from app.etl.adapters.metryx.endpoints import CAMINHO_DOS_CLIENTES
from app.models.ingest import MetryxConta, MetryxCredencial

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Conta:
    id: UUID
    nome: str
    token: str = field(repr=False)

    def __repr__(self) -> str:   # nunca expor o token
        return f"Conta(nome={self.nome!r}, id={self.id})"


@dataclass
class Descoberta:
    """O que a leitura das contas fez com os clientes (vai para o log do worker)."""
    clientes: int = 0              # clientes que as contas listaram
    novos: int = 0                 # sem credencial ativa antes: entram nesta carga
    trocados: int = 0              # o token em uso saiu da lista: vale o da lista
    sem_token: int = 0             # listados sem idCustomer ou sem token: ficam de fora
    contas_com_erro: int = 0       # a carga segue com os clientes já cadastrados


def registrar_conta(engine: Engine, token: str, nome: str) -> UUID:
    """Cadastra a conta mestre (ou reativa a que tem o mesmo token)."""
    with sessao(engine) as s:
        comando = pg_insert(MetryxConta).values(nome=nome, token_cifrado=credenciais.cifrar(token),
                                                token_impressao=credenciais.impressao(token), status="ativa")
        return s.scalar(comando.on_conflict_do_update(
            constraint="uq_metryx_conta",
            set_={"nome": nome, "token_cifrado": comando.excluded.token_cifrado, "status": "ativa",
                  "ultimo_erro": None, "atualizado_em": text("now()")},
        ).returning(MetryxConta.id))


def contas_ativas(engine: Engine) -> list[Conta]:
    with sessao(engine) as s:
        consulta = select(MetryxConta).where(MetryxConta.status == "ativa").order_by(MetryxConta.criado_em)
        linhas = s.scalars(consulta).all()
    contas = []
    for linha in linhas:
        contas.append(Conta(linha.id, linha.nome, credenciais.decifrar(linha.token_cifrado)))
    return contas


@dataclass(frozen=True)
class SituacaoDaConta:
    nome: str
    status: str
    ultimo_erro: str | None


def situacao_das_contas(engine: Engine) -> list[SituacaoDaConta]:
    """Todas as contas mestres cadastradas, sem o token: o nome, a situação e o último erro."""
    with sessao(engine) as s:
        consulta = select(MetryxConta.nome, MetryxConta.status, MetryxConta.ultimo_erro).order_by(MetryxConta.criado_em)
        linhas = s.execute(consulta).all()
    situacoes = []
    for nome, situacao, erro in linhas:
        situacoes.append(SituacaoDaConta(nome, situacao, erro))
    return situacoes


NOME_DA_CONTA_DA_CONFIGURACAO = "Terra"


def conta_da_configuracao(engine: Engine, token: str) -> None:
    """O token mestre do .env (METRYX_TOKEN_MESTRE) vira a conta mestre, a cada carga: o mesmo token só reativa a conta
    (a recusada volta a ser tentada), e um token novo entra ao lado dos que já existiam."""
    if token.strip():
        registrar_conta(engine, token.strip(), NOME_DA_CONTA_DA_CONFIGURACAO)


def descobrir_clientes(engine: Engine, cliente_http: ClienteMetryx, token_mestre: str = "") -> Descoberta:
    """Relê a lista de clientes de cada conta mestre e atualiza as credenciais. Sem conta, não chama a API."""
    conta_da_configuracao(engine, token_mestre)
    descoberta = Descoberta()
    for conta in contas_ativas(engine):
        ler_conta(engine, cliente_http, conta, descoberta)
    return descoberta


def ler_conta(engine: Engine, cliente_http: ClienteMetryx, conta: Conta, descoberta: Descoberta) -> None:
    """Uma conta: a lista dos clientes. A falha dela não para a carga, que segue com os clientes já cadastrados."""
    try:
        resposta = cliente_http.get_lista(CAMINHO_DOS_CLIENTES, conta.token)
    except CredencialInvalida as erro:
        marcar_conta(engine, conta.id, "invalida", str(erro))
        descoberta.contas_com_erro += 1
        log.warning("metryx: a conta mestre %s foi recusada (%s)", conta.nome, erro)
        return
    except (ErroMetryx, httpx.TransportError) as erro:
        marcar_conta(engine, conta.id, "ativa", f"{type(erro).__name__}: {erro}")
        descoberta.contas_com_erro += 1
        log.warning("metryx: a lista de clientes da conta %s falhou (%s)", conta.nome, type(erro).__name__)
        return
    for item in resposta.itens:
        guardar_cliente(engine, item, descoberta)
    marcar_conta(engine, conta.id, "ativa", None, clientes=len(resposta.itens))


def guardar_cliente(engine: Engine, item: dict, descoberta: Descoberta) -> None:
    """Um cliente da lista: cadastra o token dele, a não ser que o token em uso continue na lista."""
    descoberta.clientes += 1
    id_customer = texto(item.get("idCustomer"))
    tokens = tokens_do_cliente(item)
    if not id_customer or not tokens:
        descoberta.sem_token += 1
        return
    em_uso = impressao_em_uso(engine, id_customer)
    impressoes = [credenciais.impressao(token) for token in tokens]
    if em_uso in impressoes:
        return
    if em_uso is None:
        descoberta.novos += 1
    else:
        descoberta.trocados += 1
    nome = texto(item.get("customer")) or f"Metryx cliente {id_customer}"
    credenciais.registrar(engine, id_customer, tokens[0], nome)


def tokens_do_cliente(item: dict) -> list[str]:
    """Os tokens da `listToken`, na ordem da API (vale o primeiro quando o em uso não está entre eles)."""
    tokens = []
    for registro in item.get("listToken") or []:
        token = registro
        if isinstance(registro, dict):
            token = registro.get("token")
        if isinstance(token, str) and token.strip():
            tokens.append(token.strip())
    return tokens


def impressao_em_uso(engine: Engine, id_customer: str) -> str | None:
    with sessao(engine) as s:
        return s.scalar(select(MetryxCredencial.token_impressao)
                        .where(MetryxCredencial.metryx_customer_id == id_customer,
                               MetryxCredencial.status == "ativa")
                        .order_by(MetryxCredencial.criado_em.desc()).limit(1))


def marcar_conta(engine: Engine, conta_id: UUID, status: str, erro: str | None, clientes: int | None = None) -> None:
    valores = {"status": status, "ultimo_erro": erro, "ultima_validacao_em": text("now()"),
               "atualizado_em": text("now()")}
    if clientes is not None:
        valores["clientes"] = clientes
    with sessao(engine) as s:
        s.execute(update(MetryxConta).where(MetryxConta.id == conta_id).values(valores))


def texto(valor) -> str:
    if valor is None:
        return ""
    return str(valor).strip()
