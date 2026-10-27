"""Quando cada carga roda: as agendas vêm da configuração (.env), no formato do cron, e viram o `beat_schedule`.

    AGENDA_PLANILHAS="0 */2 * * *"     a cada 2 horas
    AGENDA_METRYX=""                   desligada (vazia)
    AGENDA_ESTOQUE="30 0 1 * *"        dia 1 de cada mês, 00:30

Os cinco campos são os do cron: minuto, hora, dia do mês, mês e dia da semana.
"""

from celery.schedules import crontab

from app.core.config import Settings

# (nome da agenda, tarefa do Celery, campo da configuração com o horário)
CARGAS = [
    ("planilhas", "cargas.planilhas", "agenda_planilhas"),
    ("metryx", "cargas.metryx", "agenda_metryx"),
    ("estoque", "cargas.estoque", "agenda_estoque"),
]


def horario_do_cron(texto: str) -> crontab | None:
    """'0 */2 * * *' -> crontab; texto vazio -> None (carga desligada)."""
    campos = texto.split()
    if not campos:
        return None
    if len(campos) != 5:
        raise ValueError(f"agenda inválida: '{texto}' (use minuto hora dia mês dia-da-semana, como no cron)")
    minuto, hora, dia, mes, dia_da_semana = campos
    return crontab(minute=minuto, hour=hora, day_of_month=dia, month_of_year=mes, day_of_week=dia_da_semana)


def agenda_das_cargas(configuracao: Settings) -> dict:
    """O `beat_schedule` do Celery: só as cargas com horário."""
    agenda = {}
    for nome, tarefa, campo in CARGAS:
        horario = horario_do_cron(getattr(configuracao, campo))
        if horario is not None:
            agenda[nome] = {"task": tarefa, "schedule": horario}
    return agenda
