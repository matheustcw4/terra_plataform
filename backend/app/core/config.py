"""Configuração da aplicação (pydantic-settings), lida do `.env` na raiz do repositório."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ_REPO = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=RAIZ_REPO / ".env", env_file_encoding="utf-8", extra="ignore")

    ambiente: str = "dev"

    postgres_host: str = "127.0.0.1"  # "localhost" tenta ::1 antes e trava no Docker Desktop (Windows)
    postgres_port: int = 55432
    postgres_db: str = "terra"
    postgres_user: str = "postgres"
    postgres_password: str = ""
    app_user_password: str = ""
    app_etl_password: str = ""

    # Fontes
    planilhas_dir: str | None = None          # pasta dos RELATÓRIO*.xlsm (ex.: G:\Meu Drive\Relatórios)
    metryx_base_url: str = "https://web-srv.metryx.app:8444/mtxserver"
    metryx_chave_cifra: str | None = None     # chave Fernet que cifra os tokens Metryx no banco (nunca no git)
    datalake_plan_url: str | None = None      # conninfo do datalake do BI de planilhas (só leitura; carga do histórico)

    # Cargas agendadas (Celery + Redis). Agenda no formato do cron, "minuto hora dia mês dia-da-semana", no fuso
    # America/Cuiaba; vazia desliga a carga.
    redis_url: str = "redis://127.0.0.1:6379/0"
    agenda_planilhas: str = "0 */2 * * *"         # a cada 2 horas: o consultor salva a planilha a qualquer hora
    agenda_metryx: str = ""                       # desligada: chamar a API real do Metryx depende de autorização
    agenda_estoque: str = "30 0 1 * *"            # dia 1, 00:30: estende o estoque de todas as fazendas ao mês novo

    # API
    jwt_segredo: str = ""                     # chave que assina os tokens de login (nunca no git; gere uma aleatória)
    jwt_minutos: int = 480                    # validade do login: um dia de trabalho
    cors_origens: str = "http://localhost:5173"   # endereços do front que podem chamar a API (separados por vírgula)

    # Sobrescrevem as URLs montadas abaixo, se definidas.
    database_url_migracao: str | None = Field(default=None)
    database_url_api: str | None = Field(default=None)
    database_url_etl: str | None = Field(default=None)

    def _url(self, usuario: str, senha: str, banco: str | None = None) -> str:
        host = f"{self.postgres_host}:{self.postgres_port}"
        return f"postgresql+psycopg://{usuario}:{senha}@{host}/{banco or self.postgres_db}"

    def url_migracao(self, banco: str | None = None) -> str:
        """Superusuário: só para migrações (que fazem SET ROLE app_owner) e para os testes criarem bancos."""
        if self.database_url_migracao and banco is None:
            return self.database_url_migracao
        return self._url(self.postgres_user, self.postgres_password, banco)

    def url_api(self, banco: str | None = None) -> str:
        if self.database_url_api and banco is None:
            return self.database_url_api
        return self._url("app_user", self.app_user_password, banco)

    def url_etl(self, banco: str | None = None) -> str:
        if self.database_url_etl and banco is None:
            return self.database_url_etl
        return self._url("app_etl", self.app_etl_password, banco)


@lru_cache
def get_settings() -> Settings:
    return Settings()
