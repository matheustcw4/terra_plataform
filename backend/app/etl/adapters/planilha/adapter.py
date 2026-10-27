"""Adapter de planilhas: uma unidade de origem por arquivo RELATÓRIO*.xlsm da pasta configurada (somente leitura).

descobrir(): lista a pasta (nomes em NFC — há arquivos em NFD no Drive), casa o padrão do nome, ignora temporários
             (~$...) e arquivo alterado há menos de `estabilidade_s` (ainda sincronizando). A assinatura
             (tamanho:mtime) deixa o motor pular arquivo inalterado sem abrir. Ordem: mais recente primeiro.
extrair():   lê os bytes uma vez (sha256 = identidade da versão) e converte para o dict do leitor (vai para o bruto).
normalizar(): função pura em normalizar.py.
"""

import os
import time
import unicodedata
from pathlib import Path

from app.core.config import get_settings
from app.etl.adapters.base import Bruto, UnidadeOrigem, sha256_bytes
from app.etl.adapters.planilha.leitor import ler_planilha
from app.etl.adapters.planilha.normalizar import normalizar
from app.etl.adapters.planilha.template import REGEX_ARQUIVO
from app.etl.canonical import LoteCanonico


class AdapterPlanilha:
    fonte = "planilha"

    def __init__(self, pasta: str | Path | None = None, *, arquivos: list[str] | None = None,
                 estabilidade_s: float = 60):
        pasta = pasta or get_settings().planilhas_dir
        if not pasta:
            raise ValueError("defina PLANILHAS_DIR no .env ou passe a pasta")
        self.pasta = Path(pasta)
        self.arquivos = {unicodedata.normalize("NFC", a) for a in arquivos} if arquivos else None
        self.estabilidade_s = estabilidade_s
        self.ignorados: list[tuple[str, str]] = []

    def descobrir(self) -> list[UnidadeOrigem]:
        unidades, agora = [], time.time()
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
            if agora - st.st_mtime < self.estabilidade_s:
                self.ignorados.append((nome, "FILE_UNSTABLE"))
                continue
            unidades.append(UnidadeOrigem(
                chave=nome, descricao=nome, assinatura=f"{st.st_size}:{st.st_mtime_ns}",
                metadados={"caminho": entrada.path, "tamanho": st.st_size, "mtime": st.st_mtime,
                           "codigo_nome": m.group(1), "rotulo": m.group(2).strip()}))
        # mais recente primeiro: com arquivo em dobro da mesma fazenda, o novo carrega e o antigo já sai ignorado
        return sorted(unidades, key=lambda unidade: unidade.metadados["mtime"], reverse=True)

    def extrair(self, unidade: UnidadeOrigem) -> Bruto:
        caminho = unidade.metadados.get("caminho") or str(self.pasta / unidade.chave)
        dados = Path(caminho).read_bytes()
        m = REGEX_ARQUIVO.match(unidade.chave)
        conteudo = ler_planilha(dados)
        conteudo["arquivo"] = {"nome": unidade.chave, "codigo_nome": m.group(1) if m else None,
                               "rotulo": m.group(2).strip() if m else None,
                               "mtime": unidade.metadados.get("mtime")}
        return Bruto(unidade, "json", conteudo, sha256_bytes(dados), len(dados),
                     {"endpoint": "xlsm", "arquivo": unidade.chave})

    def normalizar(self, bruto: Bruto) -> LoteCanonico:
        return normalizar(bruto.conteudo)
