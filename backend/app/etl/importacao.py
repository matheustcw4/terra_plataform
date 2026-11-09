"""A fila das planilhas enviadas pela tela (ingest.importacao): o worker pega a mais antiga, carrega pelo motor de
sempre e grava o resultado para a tela.

Uma por vez, na ordem do envio. Antes de gravar, o motor confere se quem enviou pode alimentar a fazenda do arquivo,
com a mesma regra do RLS (app.eh_admin e app.fazendas_visiveis no contexto de quem enviou): o admin pode tudo, até
cadastrar fazenda nova; os demais, só as fazendas a que têm acesso. A fazenda só se sabe depois de ler o arquivo, por
isso a conferência é do worker, e não da API. O arquivo sai da tabela assim que é processado: o bruto lido fica em
raw.payload, o que permite reprocessar sem ele.

Quem chama segura a trava das cargas (tasks/cargas.py): com ela na mão, uma importação 'processando' é de um worker
que caiu no meio.
"""

from collections import Counter
from uuid import UUID

from sqlalchemy import Engine, select, text, union

from app.db.session import ContextoRLS, sessao
from app.etl import loaders
from app.etl.adapters.planilha.enviada import AdapterPlanilhaEnviada, PlanilhaEnviada
from app.etl.canonical import LoteCanonico
from app.etl.pipeline import ErroDePermissao, MotorCarga, ResultadoUnidade

PROXIMA_DA_FILA = """
    UPDATE ingest.importacao SET status = 'processando', iniciado_em = now()
    WHERE id = (SELECT id FROM ingest.importacao WHERE status = 'na_fila'
                ORDER BY enviado_em, id LIMIT 1 FOR UPDATE SKIP LOCKED)
    RETURNING id, usuario_id, arquivo, sha256, tamanho_bytes, conteudo, enviado_em
"""
INTERROMPIDAS = """
    UPDATE ingest.importacao
    SET status = 'erro', conteudo = NULL, finalizado_em = now(),
        mensagem = 'a carga foi interrompida no meio (o worker reiniciou); envie o arquivo de novo'
    WHERE status = 'processando'
"""
RESULTADO = """
    UPDATE ingest.importacao
    SET status = :status, mensagem = :mensagem, avisos = :avisos, quarentena = :quarentena,
        fazendas = CAST(:fazendas AS uuid[]), job_id = :job, versao_origem_id = :versao, conteudo = NULL,
        finalizado_em = now()
    WHERE id = :id
"""
ACESSO_DE_QUEM_ENVIOU = "SELECT app.eh_admin() AS eh_admin, app.fazendas_visiveis() AS fazendas"
FAZENDA_DO_ARQUIVO = """
    SELECT entidade_id FROM core.fonte_vinculo
    WHERE fonte = :fonte AND entidade = 'fazenda' AND id_externo = :id_externo
"""
JA_CARREGADA = "o mesmo arquivo já tinha sido carregado: nada mudou"


def processar_fila(engine: Engine) -> dict[str, int]:
    """Carrega todas as planilhas da fila, da mais antiga para a mais nova (inclusive as que chegam enquanto isso);
    devolve quantas ficaram em cada situação."""
    with sessao(engine) as s:
        s.execute(text(INTERROMPIDAS))
    contagem: Counter = Counter()
    enviada = proxima_da_fila(engine)
    while enviada is not None:
        contagem[importar(engine, enviada)] += 1
        enviada = proxima_da_fila(engine)
    return dict(contagem)


def proxima_da_fila(engine: Engine) -> PlanilhaEnviada | None:
    """Marca a mais antiga como 'processando' e a devolve, com o arquivo."""
    with sessao(engine) as s:
        linha = s.execute(text(PROXIMA_DA_FILA)).mappings().first()
    if linha is None:
        return None
    return PlanilhaEnviada(**linha)


def importar(engine: Engine, enviada: PlanilhaEnviada) -> str:
    """Uma planilha: o motor de sempre, com a conferência do acesso de quem enviou. Devolve a situação final."""
    acesso = AcessoDeQuemEnviou(engine, enviada.usuario_id)
    motor = MotorCarga(engine, conferir_lote=acesso.conferir)
    resultado = motor.executar(AdapterPlanilhaEnviada(enviada), usuario_id=enviada.usuario_id)
    unidade = resultado.unidades[0]
    gravar_resultado(engine, enviada.id, resultado.job_id, unidade)
    return unidade.status


class AcessoDeQuemEnviou:
    """O que o motor confere antes de gravar a planilha enviada: quem enviou pode alimentar a fazenda dela?"""

    def __init__(self, engine: Engine, usuario_id: UUID | None):
        self.engine = engine
        self.usuario_id = usuario_id

    def conferir(self, lote: LoteCanonico) -> None:
        if self.usuario_id is None:
            raise ErroDePermissao("quem enviou a planilha não está mais cadastrado")
        with sessao(self.engine, ContextoRLS(self.usuario_id)) as s:
            acesso = s.execute(text(ACESSO_DE_QUEM_ENVIOU)).mappings().one()
            if acesso["eh_admin"]:
                return
            for fazenda in lote.fazendas:
                parametros = {"fonte": lote.fonte, "id_externo": fazenda.id_externo}
                fazenda_id = s.scalar(text(FAZENDA_DO_ARQUIVO), parametros)
                conferir_fazenda(fazenda.nome, fazenda_id, acesso["fazendas"])


def conferir_fazenda(nome: str, fazenda_id: UUID | None, fazendas_visiveis: list[UUID]) -> None:
    if fazenda_id is None:
        raise ErroDePermissao(f"a fazenda '{nome}' ainda não está na plataforma: a primeira planilha dela é "
                              "importada pelo administrador")
    if fazenda_id not in fazendas_visiveis:
        raise ErroDePermissao(f"você não tem acesso à fazenda '{nome}': peça o acesso ao administrador")


def gravar_resultado(engine: Engine, importacao_id: UUID, job_id: UUID, unidade: ResultadoUnidade) -> None:
    fazendas = []
    if unidade.status != "erro":
        fazendas = fazendas_da_versao(engine, unidade.versao_id)
    parametros = {"id": importacao_id, "status": unidade.status, "mensagem": mensagem_do_resultado(unidade),
                  "avisos": unidade.avisos, "quarentena": unidade.quarentena, "fazendas": fazendas, "job": job_id,
                  "versao": unidade.versao_id}
    with sessao(engine) as s:
        s.execute(text(RESULTADO), parametros)


def fazendas_da_versao(engine: Engine, versao_id: UUID | None) -> list[UUID]:
    """As fazendas com dado gravado por esta versão do arquivo (a tela mostra quais fazendas a planilha alimentou)."""
    if versao_id is None:
        return []
    consultas = []
    for tabela in loaders.TABELAS.values():
        consultas.append(select(tabela.c.fazenda_id).where(tabela.c.origem_ref == versao_id))
    with sessao(engine) as s:
        return sorted(set(s.scalars(union(*consultas))))


def mensagem_do_resultado(unidade: ResultadoUnidade) -> str | None:
    """O motivo, quando não carregou (erro ou arquivo em dobro); carregada não precisa de mensagem."""
    if unidade.status == "inalterada":
        return JA_CARREGADA
    if unidade.erro is None:
        return None
    return unidade.erro[:2000]
