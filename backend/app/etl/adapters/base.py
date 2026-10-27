"""Contrato de um adapter de fonte.

Um adapter sabe tudo sobre UMA fonte e nada sobre o banco:
  descobrir()  -> o que existe na fonte (arquivos, cliente × endpoint), com uma assinatura barata para pular o que
                  não mudou sem ler o conteúdo;
  extrair()    -> o conteúdo bruto, fiel à origem, com sha256 (nunca escreve na fonte);
  normalizar() -> função pura: bruto -> LoteCanonico. É o ÚNICO lugar onde existe lógica por fonte.
"""

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, runtime_checkable

from app.etl.canonical import Fonte, LoteCanonico


@dataclass(frozen=True)
class UnidadeOrigem:
    chave: str                                # identidade estável na fonte (caminho NFC; 'idCustomer:endpoint')
    descricao: str
    assinatura: str | None = None             # ex.: 'tamanho:mtime'; None = sempre extrair
    metadados: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Bruto:
    unidade: UnidadeOrigem
    formato: Literal["json", "xlsx"]
    conteudo: Any                             # json: list/dict já decodificado (Decimal p/ números); xlsx: bytes
    sha256: str
    tamanho_bytes: int
    metadados: dict[str, Any] = field(default_factory=dict)   # http_status, endpoint, …


@runtime_checkable
class SourceAdapter(Protocol):
    fonte: Fonte

    def descobrir(self) -> Iterable[UnidadeOrigem]: ...

    def extrair(self, unidade: UnidadeOrigem) -> Bruto: ...

    def normalizar(self, bruto: Bruto) -> LoteCanonico: ...


def sha256_bytes(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def sha256_json(conteudo: Any) -> str:
    """Hash estável de um JSON (chaves ordenadas, sem espaços): o mesmo payload sempre gera o mesmo hash."""
    canonico = json.dumps(conteudo, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False)
    return sha256_bytes(canonico.encode("utf-8"))
