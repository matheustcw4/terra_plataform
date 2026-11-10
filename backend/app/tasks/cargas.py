"""As cargas que o beat agenda e o worker executa. Cada tarefa é um invólucro fino de uma função que recebe o banco
(os testes chamam a função direto, sem fila).

As fontes são duas (pedido do usuário, 10/11/2026: o Google Drive deixou de ser fonte): as planilhas enviadas pela
tela de importação e o Metryx pela API. O resultado detalhado de cada carga fica em `ingest.job` e nas ocorrências
(aba Pendências); a tarefa devolve só um resumo, que vai para o log do worker.
"""

import logging
from collections import Counter
from datetime import date
from uuid import UUID

from sqlalchemy import Engine, text

from app.core.config import Settings, get_settings
from app.db.session import engine_etl
from app.etl.adapters.metryx.adapter import AdapterMetryx
from app.etl.importacao import processar_fila
from app.etl.pipeline import MotorCarga, ResultadoJob
from app.tasks.fila import celery
from app.tasks.trava import trava_das_cargas

log = logging.getLogger(__name__)

RECALCULAR_TODO_O_ESTOQUE = "SELECT fato.recalcular_estoque_mensal(array_agg(id), :ate) FROM core.fazenda"


def resumo(resultado: ResultadoJob) -> dict:
    """{"status": "concluido", "job_id": "...", "unidades": {"carregada": 3, "inalterada": 227}}"""
    unidades = Counter(unidade.status for unidade in resultado.unidades)
    return {"status": resultado.status, "job_id": str(resultado.job_id), "unidades": dict(unidades)}


def executar_metryx(engine: Engine, usuario_id: UUID | None = None) -> dict:
    """A carga do Metryx em si, sem a trava (quem chama segura a trava)."""
    return resumo(MotorCarga(engine).executar(AdapterMetryx(engine), usuario_id=usuario_id))


def carga_do_metryx(engine: Engine, usuario_id: UUID | None = None) -> dict:
    """Sincroniza os clientes Metryx com credencial ativa. A agenda só roda com AGENDA_METRYX preenchida: chamar a
    API real do Metryx depende de autorização (CLAUDE.md, Segurança)."""
    with trava_das_cargas(engine, esperar=False) as conseguiu:
        if not conseguiu:
            log.info("carga do Metryx pulada: outra carga está rodando")
            return {"status": "ocupada"}
        return executar_metryx(engine, usuario_id)


def atualizacao_agora(engine: Engine, configuracao: Settings, usuario_id: UUID | None = None) -> dict:
    """O botão "Atualizar agora" do admin: o Metryx, só com a agenda dele ligada (a mesma autorização da agenda).
    As planilhas não entram: chegam pela tela de importação, que carrega cada envio na hora."""
    if not configuracao.metryx_ligado:
        log.info("atualização pedida com o Metryx desligado: nada a fazer")
        return {"status": "metryx_desligado"}
    return carga_do_metryx(engine, usuario_id)


def importacoes_na_fila(engine: Engine) -> dict:
    """As planilhas enviadas pela tela, da mais antiga para a mais nova. Com outra carga rodando, ficam na fila: a API
    avisa o worker a cada envio, e a agenda (AGENDA_IMPORTACOES) tenta de novo de tempos em tempos."""
    with trava_das_cargas(engine, esperar=False) as conseguiu:
        if not conseguiu:
            log.info("importações puladas: outra carga está rodando")
            return {"status": "ocupada"}
        return {"status": "concluido", "importacoes": processar_fila(engine)}


def recalculo_do_estoque(engine: Engine, ate: date) -> dict:
    """Estende o estoque de todas as fazendas até o mês de `ate`. A carga só recalcula as fazendas cuja fonte mudou;
    sem isto, fazenda sem novidade ficaria sem o mês novo. Espera a carga que estiver rodando: não pode ser pulado."""
    with trava_das_cargas(engine, esperar=True), engine.begin() as conexao:
        linhas = conexao.execute(text(RECALCULAR_TODO_O_ESTOQUE), {"ate": ate}).scalar()
    return {"status": "concluido", "linhas": linhas}


@celery.task(name="cargas.metryx")
def sincronizar_metryx() -> dict:
    resultado = carga_do_metryx(engine_etl())
    log.info("carga do Metryx: %s", resultado)
    return resultado


@celery.task(name="cargas.atualizar_agora")
def atualizar_agora(usuario_id: str | None = None) -> dict:
    """Pedida pelo admin na tela (POST /admin/atualizacao); o job fica com o id de quem pediu."""
    dono = None
    if usuario_id:
        dono = UUID(usuario_id)
    resultado = atualizacao_agora(engine_etl(), get_settings(), dono)
    log.info("atualização pedida pelo admin: %s", resultado)
    return resultado


@celery.task(name="cargas.importacoes")
def importar_planilhas_enviadas() -> dict:
    resultado = importacoes_na_fila(engine_etl())
    log.info("planilhas enviadas pela tela: %s", resultado)
    return resultado


@celery.task(name="cargas.estoque")
def recalcular_estoque() -> dict:
    resultado = recalculo_do_estoque(engine_etl(), date.today())
    log.info("recálculo do estoque: %s", resultado)
    return resultado
