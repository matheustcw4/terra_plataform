"""Qualidade dos dados para quem lança: o que corrigir na origem."""

from fastapi import APIRouter

from app.api.deps import SessaoDoUsuario
from app.api.v1.endpoints.dashboards import Fazendas, conferir_acesso
from app.schemas.api import Pendencias
from app.services.pendencias import pendencias

router = APIRouter(prefix="/qualidade", tags=["qualidade"])


@router.get("/pendencias")
def pendencias_de_lancamento(s: SessaoDoUsuario, fazendas: Fazendas) -> Pendencias:
    """Linhas que a última carga deixou fora dos números (quarentena) ou marcou para conferir, das fazendas pedidas.
    Não tem período: data errada é justamente um dos problemas."""
    conferir_acesso(s, fazendas)
    return pendencias(s, fazendas)
