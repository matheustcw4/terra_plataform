from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.deps import EngineDaApi
from app.api.v1.endpoints import admin, auth, dashboards, escopo, qualidade
from app.core.config import get_settings
from app.core.logging import configurar_logging

configurar_logging()

app = FastAPI(title="Projeto Terra API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origens.split(","), allow_methods=["*"],
                   allow_headers=["*"])

api_v1 = APIRouter(prefix="/api/v1")


@app.get("/", include_in_schema=False)
def raiz() -> dict[str, str]:
    """Quem abre o endereço da API no navegador cai aqui: o painel é o front, não a API."""
    return {"mensagem": "Esta é a API do Projeto Terra. O painel abre pelo front (em frontend/: npm run dev, "
                        "http://localhost:5173). A documentação da API está em /docs."}


@api_v1.get("/health", tags=["saude"])
def health(engine: EngineDaApi) -> dict[str, str]:
    with engine.connect() as conexao:
        conexao.execute(text("SELECT 1"))
    return {"status": "ok", "banco": "ok"}


api_v1.include_router(auth.router)
api_v1.include_router(escopo.router)
api_v1.include_router(dashboards.router)
api_v1.include_router(qualidade.router)
api_v1.include_router(admin.router)
app.include_router(api_v1)
