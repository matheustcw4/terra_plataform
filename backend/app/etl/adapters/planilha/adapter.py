"""Adapter de planilhas de uma pasta local: uma unidade de origem por arquivo RELATÓRIO*.xlsm (somente leitura).

No dia a dia as planilhas chegam pela tela de importação (enviada.py); a pasta serve só à carga em massa pela linha
de comando e aos testes (o Google Drive deixou de ser fonte em 10/11/2026).

descobrir(): lista a pasta (nomes em NFC — arquivos copiados do Drive vêm em NFD), casa o padrão do nome e ignora os
             temporários (~$...). A assinatura (tamanho:mtime) deixa o motor pular arquivo inalterado sem abrir.
             Ordem: mais recente primeiro.
extrair():   lê os bytes uma vez (sha256 = identidade da versão) e converte para o dict do leitor (vai para o bruto).
normalizar(): função pura em normalizar.py.
"""

import os
import unicodedata
from pathlib import Path

from app.etl.adapters.base import Bruto, UnidadeOrigem, sha256_bytes
from app.etl.adapters.planilha.leitor import ler_planilha
from app.etl.adapters.planilha.normalizar import normalizar
from app.etl.adapters.planilha.template import REGEX_ARQUIVO
from app.etl.canonical import LoteCanonico


class AdapterPlanilha:
    fonte = "planilha"

    def __init__(self, pasta: str | Path, *, arquivos: list[str] | None = None):
        self.pasta = Path(pasta)
        self.arquivos = {unicodedata.normalize("NFC", a) for a in arquivos} if arquivos else None
        self.ignorados: list[tuple[str, str]] = []

    def descobrir(self) -> list[UnidadeOrigem]:
        unidades = []
        for entrada in sorted(os.scandir(self.pasta), key=lambda e: e.name):
            nome = unicodedata.normalize("NFC", entrada.name)
            if not entrada.is_file() or nome.startswith(("~$", ".")) or not nome.lower().endswith((".xlsm", ".xlsx")):
                continue
            if self.arquivos is not None and nome not in self.arquivos:
                continue
            m = REGEX_ARQUIVO.match(nome)
            if not m:
                self.ignorados.append((nome, "FILE_NAME_UNPARSED"))
                continue
            st = entrada.stat()
            unidades.append(UnidadeOrigem(
                chave=nome, descricao=nome, assinatura=f"{st.st_size}:{st.st_mtime_ns}",
                metadados={"caminho": entrada.path, "tamanho": st.st_size, "mtime": st.st_mtime,
                           "codigo_nome": m.group(1), "rotulo": m.group(2).strip()}))
        # mais recente primeiro: com arquivo em dobro da mesma fazenda, o novo carrega e o antigo já sai ignorado
        return sorted(unidades, key=lambda unidade: unidade.metadados["mtime"], reverse=True)

    def extrair(self, unidade: UnidadeOrigem) -> Bruto:
        caminho = unidade.metadados.get("caminho") or str(self.pasta / unidade.chave)
        return bruto_da_planilha(unidade, Path(caminho).read_bytes())

    def normalizar(self, bruto: Bruto) -> LoteCanonico:
        return normalizar(bruto.conteudo)


def bruto_da_planilha(unidade: UnidadeOrigem, dados: bytes) -> Bruto:
    """Os bytes do arquivo -> o bruto: o dict do leitor, com o nome do arquivo (o código e a fazenda do nome conferem
    o fUnidade). Serve à pasta e às planilhas enviadas pela tela (enviada.py)."""
    m = REGEX_ARQUIVO.match(unidade.chave)
    conteudo = ler_planilha(dados)
    conteudo["arquivo"] = {"nome": unidade.chave, "codigo_nome": m.group(1) if m else None,
                           "rotulo": m.group(2).strip() if m else None,
                           "mtime": unidade.metadados.get("mtime")}
    return Bruto(unidade, "json", conteudo, sha256_bytes(dados), len(dados),
                 {"endpoint": "xlsm", "arquivo": unidade.chave})
