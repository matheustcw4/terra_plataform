"""Cliente HTTP da API Metryx (somente leitura).

- Só chama caminhos da allow-list (endpoints.py); `control-birth` é recusado mesmo se pedido.
- Repete em falha transitória (timeout, rede, 429, 5xx) com espera exponencial; NÃO repete 400/401/403/404.
- O token vai só no header `x-auth-token` e nunca aparece em log, exceção ou repr.
- A resposta tem de ser uma lista JSON (o content-type da API é `*/*`, então o header não é confiável).
"""

import json
import logging
from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from app.etl.adapters.metryx.endpoints import CAMINHOS_PERMITIDOS, CAMINHOS_PROIBIDOS

log = logging.getLogger(__name__)


class ErroMetryx(Exception):
    pass


class CredencialInvalida(ErroMetryx):      # 401: token revogado/errado — não adianta repetir
    pass


class EndpointProibido(ErroMetryx):        # 403: o cliente não tem permissão para este endpoint
    pass


class EndpointInexistente(ErroMetryx):     # 404
    pass


class RespostaInesperada(ErroMetryx):      # corpo que não é lista JSON
    pass


class _Transitorio(ErroMetryx):            # 429/5xx: repetir
    pass


@dataclass(frozen=True)
class RespostaMetryx:
    status: int
    itens: list[dict[str, Any]]
    tamanho_bytes: int


class ClienteMetryx:
    def __init__(self, base_url: str, *, tentativas: int = 5, espera_max: float = 60,
                 transport: httpx.BaseTransport | None = None, timeout: httpx.Timeout | None = None):
        self._http = httpx.Client(
            base_url=base_url, transport=transport,
            timeout=timeout or httpx.Timeout(connect=10, read=180, write=10, pool=30),
            headers={"Accept": "application/json", "User-Agent": "projeto-terra-metryx-adapter/0.1"},
        )
        self._tentativas = tentativas
        self._espera_max = espera_max

    def fechar(self) -> None:
        self._http.close()

    def get_lista(self, caminho: str, token: str) -> RespostaMetryx:
        if caminho in CAMINHOS_PROIBIDOS or caminho not in CAMINHOS_PERMITIDOS:
            raise ErroMetryx(f"caminho fora da allow-list: {caminho}")
        for tentativa in Retrying(
            stop=stop_after_attempt(self._tentativas),
            wait=wait_exponential_jitter(max=self._espera_max),
            retry=retry_if_exception_type((_Transitorio, httpx.TransportError)),
            reraise=True,
        ):
            with tentativa:
                return self._get(caminho, token)
        raise AssertionError("inalcançável")

    def _get(self, caminho: str, token: str) -> RespostaMetryx:
        try:
            r = self._http.get(caminho, headers={"x-auth-token": token})
        except httpx.TransportError as exc:
            # a mensagem do httpx não inclui headers; mesmo assim registramos só o tipo
            log.warning("metryx %s: falha de rede (%s)", caminho, type(exc).__name__)
            raise
        log.info("metryx %s: HTTP %s, %s bytes", caminho, r.status_code, len(r.content))
        if r.status_code == 401:
            raise CredencialInvalida(f"{caminho}: 401 (token inválido ou revogado)")
        if r.status_code == 403:
            raise EndpointProibido(f"{caminho}: 403 (sem permissão para este endpoint)")
        if r.status_code == 404:
            raise EndpointInexistente(f"{caminho}: 404")
        if r.status_code == 429 or r.status_code >= 500:
            raise _Transitorio(f"{caminho}: HTTP {r.status_code}")
        if r.status_code != 200:
            raise ErroMetryx(f"{caminho}: HTTP {r.status_code}")
        try:
            dados = json.loads(r.content)
        except ValueError as exc:
            raise RespostaInesperada(f"{caminho}: corpo não é JSON") from exc
        if not isinstance(dados, list):
            raise RespostaInesperada(f"{caminho}: esperado lista JSON, veio {type(dados).__name__}")
        return RespostaMetryx(r.status_code, dados, len(r.content))
