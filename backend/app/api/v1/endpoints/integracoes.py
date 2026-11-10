"""Tela de integrações (só admin): as APIs que alimentam o painel e o histórico das cargas de cada uma, com o que
aconteceu cliente por cliente (pedido do usuário, 10/11/2026). As planilhas enviadas ficam em /importacoes."""

from fastapi import APIRouter

from app.api.deps import AdminLogado, SessaoDoUsuario
from app.core.config import get_settings
from app.schemas.integracao import CargaDaIntegracao, IntegracaoPorApi
from app.services import integracoes

router = APIRouter(prefix="/admin/integracoes", tags=["integracoes"])


@router.get("")
def listar_integracoes(admin: AdminLogado) -> list[IntegracaoPorApi]:
    return integracoes.listar(get_settings())


@router.get("/{fonte}/cargas")
def cargas_da_integracao(s: SessaoDoUsuario, admin: AdminLogado, fonte: str) -> list[CargaDaIntegracao]:
    return integracoes.cargas(s, fonte)
