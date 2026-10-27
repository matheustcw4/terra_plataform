"""A aplicação Celery do Terra: o Redis é só a fila (o resultado de cada carga fica em `ingest.job`).

    celery -A app.tasks.fila worker --concurrency 1     executa as cargas, uma por vez
    celery -A app.tasks.fila beat                       dispara as cargas no horário de `agenda.py`
"""

from celery import Celery

from app.core.config import get_settings
from app.tasks.agenda import agenda_das_cargas

configuracao = get_settings()

celery = Celery("terra", broker=configuracao.redis_url, include=["app.tasks.cargas"])
celery.conf.update(
    timezone="America/Cuiaba",               # as agendas são no horário de Cuiabá, o da equipe
    task_default_queue="terra",              # fila com nome próprio: num Redis compartilhado, só o worker da Terra pega
    task_ignore_result=True,                 # nada a guardar no Redis: o job fica no banco
    worker_prefetch_multiplier=1,            # carga é longa: o worker pega uma de cada vez
    broker_connection_retry_on_startup=True,
    beat_schedule=agenda_das_cargas(configuracao),
)
