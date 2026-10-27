"""As cargas que o beat agenda e o worker executa. Cada tarefa é um invólucro fino de uma função que recebe o banco
(os testes chamam a função direto, sem fila).

O resultado detalhado de cada carga fica em `ingest.job` e nas ocorrências (aba Pendências); a tarefa devolve só um
resumo, que vai para o log do worker.
"""

import logging
from collections import Counter
from datetime import date
from uuid import UUID

from sqlalchemy import Engine, text

from app.core.config import Settings, get_settings
from app.db.session import engine_etl
from app.etl.adapters.metryx.adapter import AdapterMetryx
from app.etl.adapters.planilha.adapter import AdapterPlanilha
from app.etl.pipeline import MotorCarga, ResultadoJob
from app.tasks.fila import celery
from app.tasks.trava import trava_das_cargas

log = logging.getLogger(__name__)

RECALCULAR_TODO_O_ESTOQUE = "SELECT fato.recalcular_estoque_mensal(array_agg(id), :ate) FROM core.fazenda"


def resumo(resultado: ResultadoJob) -> dict:
    """{"status": "concluido", "job_id": "...", "unidades": {"carregada": 3, "inalterada": 227}}"""
    unidades = Counter(unidade.status for unidade in resultado.unidades)
    return {"status": resultado.status, "job_id": str(resultado.job_id), "unidades": dict(unidades)}


def executar_planilhas(engine: Engine, pasta: str, estabilidade_s: float, usuario_id: UUID | None = None) -> dict:
    """A carga das planilhas em si, sem a trava (quem chama segura a trava)."""
    adapter = AdapterPlanilha(pasta, estabilidade_s=estabilidade_s)
    return resumo(MotorCarga(engine).executar(adapter, usuario_id=usuario_id))


def executar_metryx(engine: Engine, usuario_id: UUID | None = None) -> dict:
    """A carga do Metryx em si, sem a trava (quem chama segura a trava)."""
    return resumo(MotorCarga(engine).executar(AdapterMetryx(engine), usuario_id=usuario_id))


def carga_de_planilhas(engine: Engine, pasta: str | None, estabilidade_s: float = 60) -> dict:
    """Lê a pasta das planilhas; arquivo sem mudança desde a última carga é pulado (assinatura e sha256), e arquivo
    salvo há menos de `estabilidade_s` segundos também (ainda sincronizando: entra na próxima)."""
    if not pasta:
        log.warning("carga de planilhas sem PLANILHAS_DIR configurado: nada a fazer")
        return {"status": "sem_pasta"}
    with trava_das_cargas(engine, esperar=False) as conseguiu:
        if not conseguiu:
            log.info("carga de planilhas pulada: outra carga está rodando")
            return {"status": "ocupada"}
        return executar_planilhas(engine, pasta, estabilidade_s)


def carga_do_metryx(engine: Engine) -> dict:
    """Sincroniza os clientes Metryx com credencial ativa. Só roda se AGENDA_METRYX estiver preenchida: chamar a API
    real do Metryx depende de autorização (CLAUDE.md, Segurança)."""
    with trava_das_cargas(engine, esperar=False) as conseguiu:
        if not conseguiu:
            log.info("carga do Metryx pulada: outra carga está rodando")
            return {"status": "ocupada"}
        return executar_metryx(engine)


def metryx_ligado(configuracao: Settings) -> bool:
    """A agenda do Metryx preenchida é a autorização para chamar a API real (CLAUDE.md, Segurança): o "Atualizar
    agora" segue a mesma regra da agenda."""
    return bool(configuracao.agenda_metryx.strip())


def atualizacao_agora(engine: Engine, pasta: str | None, com_metryx: bool, usuario_id: UUID | None = None,
                      estabilidade_s: float = 60) -> dict:
    """O botão "Atualizar agora" do admin: as planilhas e, se ligado, o Metryx, em seguida. A trava fica presa do
    começo ao fim: a tela acompanha pela trava, e um vão entre as duas cargas pareceria o fim."""
    with trava_das_cargas(engine, esperar=False) as conseguiu:
        if not conseguiu:
            log.info("atualização pedida pulada: outra carga está rodando")
            return {"status": "ocupada"}
        resultado = {}
        if pasta:
            resultado["planilhas"] = executar_planilhas(engine, pasta, estabilidade_s, usuario_id)
        else:
            resultado["planilhas"] = {"status": "sem_pasta"}
        if com_metryx:
            resultado["metryx"] = executar_metryx(engine, usuario_id)
        return resultado


def recalculo_do_estoque(engine: Engine, ate: date) -> dict:
    """Estende o estoque de todas as fazendas até o mês de `ate`. A carga só recalcula as fazendas cuja fonte mudou;
    sem isto, fazenda sem novidade ficaria sem o mês novo. Espera a carga que estiver rodando: não pode ser pulado."""
    with trava_das_cargas(engine, esperar=True), engine.begin() as conexao:
        linhas = conexao.execute(text(RECALCULAR_TODO_O_ESTOQUE), {"ate": ate}).scalar()
    return {"status": "concluido", "linhas": linhas}


@celery.task(name="cargas.planilhas")
def carregar_planilhas() -> dict:
    resultado = carga_de_planilhas(engine_etl(), get_settings().planilhas_dir)
    log.info("carga de planilhas: %s", resultado)
    return resultado


@celery.task(name="cargas.metryx")
def sincronizar_metryx() -> dict:
    resultado = carga_do_metryx(engine_etl())
    log.info("carga do Metryx: %s", resultado)
    return resultado


@celery.task(name="cargas.atualizar_agora")
def atualizar_agora(usuario_id: str | None = None) -> dict:
    """Pedida pelo admin na tela (POST /admin/atualizacao); o job fica com o id de quem pediu."""
    configuracao = get_settings()
    dono = None
    if usuario_id:
        dono = UUID(usuario_id)
    resultado = atualizacao_agora(engine_etl(), configuracao.planilhas_dir, metryx_ligado(configuracao), dono)
    log.info("atualização pedida pelo admin: %s", resultado)
    return resultado


@celery.task(name="cargas.estoque")
def recalcular_estoque() -> dict:
    resultado = recalculo_do_estoque(engine_etl(), date.today())
    log.info("recálculo do estoque: %s", resultado)
    return resultado
