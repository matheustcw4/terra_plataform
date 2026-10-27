"""Linha de comando do motor de carga (roda como app_etl).

    python -m app.etl planilhas [--pasta DIR] [--arquivo NOME ...] [--forcar]
    python -m app.etl planilhas-historico [--ate AAAA-MM] [--prop-faz CHAVE ...]   (carga única; depois de `planilhas`)
    python -m app.etl metryx [--cliente ID ...] [--forcar]
    python -m app.etl metryx-credencial --cliente ID --nome "Nome do cliente"   (lê o token sem ecoar)
    python -m app.etl reprocessar VERSAO_ID --fonte planilha|metryx
    python -m app.etl estoque [--ate AAAA-MM-DD]

`--forcar` recarrega mesmo sem mudança na fonte; `--ignorar-guarda` aplica uma queda de volume que a guarda reteve
(só depois de confirmar que a queda é legítima).
"""

import argparse
import getpass
import logging
import os
import sys
from datetime import date
from uuid import UUID

from sqlalchemy import text

from app.core.logging import configurar_logging
from app.db.session import engine_etl, sessao
from app.etl.pipeline import MotorCarga, ResultadoJob


def _resumo(r: ResultadoJob) -> int:
    cont: dict[str, int] = {}
    for u in r.unidades:
        cont[u.status] = cont.get(u.status, 0) + 1
    print(f"job {r.job_id}: {r.status} | " + ", ".join(f"{k}: {v}" for k, v in sorted(cont.items())))
    for u in r.unidades:
        if u.status in ("erro", "ignorada"):
            print(f"  {u.status.upper()} {u.chave}: {(u.erro or '')[:300]}")
    return 1 if r.status == "erro" else 0


def _historico(engine, motor: MotorCarga, ate: date, prop_faz: list[str] | None) -> int:
    """Carrega o histórico e devolve a palavra final às planilhas: reprocessa (do bruto guardado) a última versão de
    cada planilha ativa, o que restaura os atributos da fazenda que o snapshot possa ter sobrescrito."""
    from app.etl.adapters.planilha.adapter import AdapterPlanilha
    from app.etl.adapters.planilha.historico import AdapterHistoricoPlanilha
    status = _resumo(motor.executar(AdapterHistoricoPlanilha(engine, ate=ate, prop_faz=prop_faz), forcar=True))
    with sessao(engine) as s:
        versoes = s.scalars(text("SELECT ultima_versao_id FROM ingest.unidade_origem WHERE fonte = 'planilha' "
                                 "AND status = 'ativa' AND metadados ? 'mtime' AND ultima_versao_id IS NOT NULL")).all()
    planilhas = AdapterPlanilha(".")          # o reprocessamento usa o bruto guardado, não relê a pasta
    erros = [r for r in (motor.reprocessar(planilhas, v) for v in versoes) if r.status == "erro"]
    print(f"planilhas reprocessadas por cima do histórico: {len(versoes)} ({len(erros)} com erro)")
    for r in erros:
        print(f"  ERRO {r.chave}: {(r.erro or '')[:300]}")
    return status or (1 if erros else 0)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m app.etl", description="Cargas do Projeto Terra")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("planilhas", help="carrega os RELATÓRIO*.xlsm da pasta")
    p.add_argument("--pasta")
    p.add_argument("--arquivo", action="append")
    p.add_argument("--forcar", action="store_true")
    p.add_argument("--ignorar-guarda", action="store_true")
    h = sub.add_parser("planilhas-historico",
                       help="carga única do histórico das planilhas a partir do snapshot do datalake do BI (Q6)")
    h.add_argument("--ate", default="2026-06", help="último mês do histórico (AAAA-MM)")
    h.add_argument("--prop-faz", action="append", help="só estas fazendas (chave PROP_FAZ do BI)")
    m = sub.add_parser("metryx", help="sincroniza os clientes Metryx com credencial ativa")
    m.add_argument("--cliente", action="append")
    m.add_argument("--forcar", action="store_true")
    m.add_argument("--ignorar-guarda", action="store_true")
    c = sub.add_parser("metryx-credencial", help="cadastra/rotaciona o token de um cliente Metryx")
    c.add_argument("--cliente", required=True, help="idCustomer do Metryx")
    c.add_argument("--nome", required=True, help="nome do cliente (para o cadastro)")
    r = sub.add_parser("reprocessar", help="renormaliza uma versão a partir do bruto guardado")
    r.add_argument("versao", type=UUID)
    r.add_argument("--fonte", choices=("planilha", "metryx"), required=True)
    e = sub.add_parser("estoque", help="recalcula fato.estoque_mensal de todas as fazendas")
    e.add_argument("--ate", type=date.fromisoformat, default=date.today())
    a = ap.parse_args(argv)

    configurar_logging(logging.INFO)
    engine = engine_etl()

    if a.cmd == "metryx-credencial":
        from app.etl.adapters.metryx import credenciais
        token = os.environ.pop("METRYX_TOKEN_NOVO", None) or getpass.getpass("token do cliente (não aparece): ")
        cliente_id = credenciais.registrar(engine, a.cliente.strip(), token.strip(), a.nome)
        print(f"credencial cadastrada para o cliente Metryx {a.cliente} (cliente interno {cliente_id})")
        return 0

    if a.cmd == "estoque":
        with sessao(engine) as s:
            n = s.execute(text("SELECT fato.recalcular_estoque_mensal(array_agg(id), :ate) FROM core.fazenda"),
                          {"ate": a.ate}).scalar()
        print(f"estoque recalculado: {n} linhas")
        return 0

    motor = MotorCarga(engine, ignorar_guarda=getattr(a, "ignorar_guarda", False))
    if a.cmd == "planilhas-historico":
        return _historico(engine, motor, date.fromisoformat(a.ate + "-01"), a.prop_faz)
    if a.cmd in ("planilhas", "reprocessar") and getattr(a, "fonte", "planilha") == "planilha":
        from app.etl.adapters.planilha.adapter import AdapterPlanilha
        adapter = AdapterPlanilha(getattr(a, "pasta", None), arquivos=getattr(a, "arquivo", None))
    else:
        from app.etl.adapters.metryx.adapter import AdapterMetryx
        adapter = AdapterMetryx(engine, customers=getattr(a, "cliente", None))

    if a.cmd == "reprocessar":
        res = motor.reprocessar(adapter, a.versao)
        print(f"{res.chave}: {res.status} {dict(res.gravadas)} quarentena={res.quarentena} {res.erro or ''}")
        return 0 if res.status != "erro" else 1
    return _resumo(motor.executar(adapter, forcar=a.forcar))


if __name__ == "__main__":
    sys.exit(main())
