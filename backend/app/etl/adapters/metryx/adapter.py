"""Adapter Metryx: uma unidade de origem por cliente Metryx (credencial ativa).

extrair():   chama os endpoints da allow-list com o token do cliente e devolve um único JSON
             {"idCustomer", "endpoints": {nome: status}, "dados": {nome: itens}} — guardado em raw.payload pelo motor.
             - 401: marca a credencial como inválida e falha a unidade (nada é apagado);
             - 403/404 num endpoint opcional: segue sem ele (status "proibido"/"ausente"; os dados antigos ficam);
             - endpoint obrigatório (fazenda, categoria) falhando: a unidade falha;
             - idCustomer de algum item diferente do da credencial: falha (token trocado = erro de segurança),
               exceto no endpoint marcado `confere_pela_fazenda` (A29), em que vale a fazenda do item.
normalizar(): função pura em normalizar.py (reprocessável sem chamar a API).
"""

import logging
from collections.abc import Iterable

from sqlalchemy import Engine

from app.core.config import get_settings
from app.etl.adapters.base import Bruto, UnidadeOrigem, sha256_json
from app.etl.adapters.metryx import credenciais
from app.etl.adapters.metryx.cliente import (
    ClienteMetryx,
    CredencialInvalida,
    EndpointInexistente,
    EndpointProibido,
    ErroMetryx,
    RespostaMetryx,
)
from app.etl.adapters.metryx.endpoints import ENDPOINTS, Endpoint
from app.etl.adapters.metryx.normalizar import normalizar
from app.etl.canonical import LoteCanonico

log = logging.getLogger(__name__)

PREFIXO = "metryx:"


class ErroSegurancaMetryx(ErroMetryx):
    pass


def pertence_ao_cliente(item: dict, endpoint: Endpoint, cliente_metryx: str, fazendas_do_cliente: set[str]) -> bool:
    if item.get("idCustomer") in (None, cliente_metryx):
        return True
    return endpoint.confere_pela_fazenda and item.get("idFarm") in fazendas_do_cliente


class AdapterMetryx:
    fonte = "metryx"

    def __init__(self, engine: Engine, cliente: ClienteMetryx | None = None, *,
                 customers: list[str] | None = None, endpoints: Iterable[Endpoint] | None = None):
        self.engine = engine
        self.cliente = cliente or ClienteMetryx(get_settings().metryx_base_url)
        self.customers = customers
        self.endpoints = list(endpoints or ENDPOINTS.values())
        self._credenciais: dict[str, credenciais.Credencial] = {}

    def descobrir(self) -> list[UnidadeOrigem]:
        self._credenciais = {}
        for credencial in credenciais.credenciais_ativas(self.engine, self.customers):
            self._credenciais[credencial.metryx_customer_id] = credencial
        unidades = []
        for cliente_metryx, credencial in sorted(self._credenciais.items()):
            unidades.append(UnidadeOrigem(chave=f"{PREFIXO}{cliente_metryx}",
                                          descricao=f"Metryx cliente {cliente_metryx}",
                                          metadados={"credencial_id": str(credencial.id)}))
        return unidades

    def extrair(self, unidade: UnidadeOrigem) -> Bruto:
        cliente_metryx = unidade.chave.removeprefix(PREFIXO)
        credencial = self._credencial(cliente_metryx)
        status: dict[str, str] = {}
        dados: dict[str, list] = {}
        tamanho = 0
        # o endpoint `fazenda` vem primeiro na allow-list e é conferido pelo idCustomer, sem exceção
        fazendas_do_cliente: set[str] = set()
        for endpoint in self.endpoints:
            resposta = self._ler_endpoint(endpoint, credencial, cliente_metryx, fazendas_do_cliente, status)
            if resposta is None:
                continue
            if endpoint.nome == "fazenda":
                fazendas_do_cliente = {item["idFarm"] for item in resposta.itens if item.get("idFarm")}
            status[endpoint.nome] = "ok"
            dados[endpoint.nome] = resposta.itens
            tamanho += resposta.tamanho_bytes
        credenciais.marcar(self.engine, credencial.id, "ativa")
        conteudo = {"idCustomer": cliente_metryx, "endpoints": status, "dados": dados}
        itens_por_endpoint = {nome: len(itens) for nome, itens in dados.items()}
        return Bruto(unidade, "json", conteudo, sha256_json(conteudo), tamanho,
                     {"endpoint": "*", "endpoints": status, "itens": itens_por_endpoint})

    def _credencial(self, cliente_metryx: str) -> credenciais.Credencial:
        credencial = self._credenciais.get(cliente_metryx)
        if credencial is None:
            ativas = credenciais.credenciais_ativas(self.engine, [cliente_metryx])
            credencial = ativas[0] if ativas else None
        if credencial is None:
            raise ErroMetryx(f"sem credencial ativa para o cliente Metryx {cliente_metryx}")
        return credencial

    def _ler_endpoint(self, endpoint: Endpoint, credencial: credenciais.Credencial, cliente_metryx: str,
                      fazendas_do_cliente: set[str], status: dict[str, str]) -> RespostaMetryx | None:
        """Itens de um endpoint. 401 num obrigatório invalida a credencial; 401, 403 e 404 num opcional só o deixam
        de fora."""
        try:
            resposta = self.cliente.get_lista(endpoint.caminho, credencial.token)
        except CredencialInvalida as exc:
            if endpoint.obrigatorio:
                credenciais.marcar(self.engine, credencial.id, "invalida", str(exc))
                raise
            # A API real responde 401, e não 403, ao token sem a permissão de um endpoint (U6, 20/10/2026). Os
            # obrigatórios vêm antes na allow-list e já aceitaram este token: ele vale, só este endpoint fica de fora.
            log.warning("metryx %s: 401 com o token já aceito nos obrigatórios; tratado como sem permissão",
                        endpoint.caminho)
            status[endpoint.nome] = "proibido"
            return None
        except (EndpointProibido, EndpointInexistente) as exc:
            if endpoint.obrigatorio:
                raise
            status[endpoint.nome] = "proibido" if isinstance(exc, EndpointProibido) else "ausente"
            return None
        outros_clientes = set()
        for item in resposta.itens:
            if not pertence_ao_cliente(item, endpoint, cliente_metryx, fazendas_do_cliente):
                outros_clientes.add(item.get("idCustomer"))
        if outros_clientes:          # token trocado: nunca carregar dado de outro cliente
            raise ErroSegurancaMetryx(f"{endpoint.nome}: itens de outro cliente ({sorted(outros_clientes)[:3]}) no "
                                      f"token de {cliente_metryx}")
        return resposta

    def normalizar(self, bruto: Bruto) -> LoteCanonico:
        return normalizar(bruto.conteudo)
