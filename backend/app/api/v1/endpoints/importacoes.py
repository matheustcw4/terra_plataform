"""Importação de planilhas pela tela, no lugar da pasta do Google Drive (pedido do usuário, 09/11/2026).

Todo usuário logado envia; o worker carrega, um arquivo por vez, e só deixa cada um alimentar as fazendas a que tem
acesso (o admin, todas, e só ele cadastra fazenda nova). A tela acompanha pela lista, que traz o resultado de cada
envio.
"""

from fastapi import APIRouter, UploadFile

from app.api.deps import SessaoDoUsuario, UsuarioLogado
from app.schemas.importacao import Importacao
from app.services import importacoes

router = APIRouter(tags=["importacao"])


@router.get("/importacoes")
def listar_importacoes(s: SessaoDoUsuario) -> list[Importacao]:
    return importacoes.listar(s)


@router.post("/importacoes", status_code=202)
def importar_planilha(s: SessaoDoUsuario, usuario: UsuarioLogado, arquivo: UploadFile) -> Importacao:
    dados = arquivo.file.read(importacoes.TAMANHO_MAXIMO + 1)      # um byte a mais: o bastante para recusar
    recebida = importacoes.receber(s, usuario, arquivo.filename, dados)
    s.commit()                                     # o worker só enxerga a importação depois do commit
    importacoes.avisar_o_worker()
    return recebida
