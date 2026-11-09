"""Adapter das planilhas enviadas pela tela (ingest.importacao): uma unidade só, o arquivo enviado.

A unidade é a mesma da pasta: a chave é o nome do arquivo, então o histórico de versões continua de onde a pasta
parou, e a leitura e o normalizador são os mesmos (adapter.py). A data do envio faz o papel da data de modificação
do arquivo: no aviso de arquivo em dobro (duplicatas.py), vale o último enviado. A assinatura é o sha256 dos bytes:
o mesmo arquivo enviado de novo sai 'inalterada' sem ser lido.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.etl.adapters.base import Bruto, UnidadeOrigem
from app.etl.adapters.planilha.adapter import bruto_da_planilha
from app.etl.adapters.planilha.normalizar import normalizar
from app.etl.adapters.planilha.template import REGEX_ARQUIVO
from app.etl.canonical import LoteCanonico


@dataclass(frozen=True)
class PlanilhaEnviada:
    id: UUID
    usuario_id: UUID | None
    arquivo: str
    sha256: str
    tamanho_bytes: int
    conteudo: bytes
    enviado_em: datetime


class AdapterPlanilhaEnviada:
    fonte = "planilha"

    def __init__(self, enviada: PlanilhaEnviada):
        self.enviada = enviada

    def descobrir(self) -> list[UnidadeOrigem]:
        metadados = {"tamanho": self.enviada.tamanho_bytes, "mtime": self.enviada.enviado_em.timestamp(),
                     "importacao_id": str(self.enviada.id)}
        nome = REGEX_ARQUIVO.match(self.enviada.arquivo)
        if nome is not None:
            metadados["codigo_nome"] = nome.group(1)
            metadados["rotulo"] = nome.group(2).strip()
        unidade = UnidadeOrigem(chave=self.enviada.arquivo, descricao=self.enviada.arquivo,
                                assinatura=f"sha256:{self.enviada.sha256}", metadados=metadados)
        return [unidade]

    def extrair(self, unidade: UnidadeOrigem) -> Bruto:
        return bruto_da_planilha(unidade, self.enviada.conteudo)

    def normalizar(self, bruto: Bruto) -> LoteCanonico:
        return normalizar(bruto.conteudo)
