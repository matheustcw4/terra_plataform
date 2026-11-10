"""A tela de integrações (pedido do usuário, 10/11/2026: um lugar para ver o log das atualizações): as APIs que
alimentam o painel e o histórico das cargas de cada uma, com o que aconteceu cliente por cliente.

Só o admin vê: os jobs e as unidades das cargas não têm leitura para o usuário comum (RLS, migração 0007). As
planilhas ficam de fora daqui: cada envio aparece na própria tela de importação.

Uma API nova entra em `APIS` (a fonte das cargas, o nome na tela e o campo da agenda dela na configuração).
"""

from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.schemas.integracao import AvisoDaCarga, CargaDaIntegracao, IntegracaoPorApi, UnidadeDaCarga
from app.services.pendencias import CATALOGO


@dataclass(frozen=True)
class ApiIntegrada:
    fonte: str
    rotulo: str
    campo_da_agenda: str                    # o campo de Settings com o cron dela: preenchido = ligada


APIS = [ApiIntegrada("metryx", "Metryx", "agenda_metryx")]
LIMITE_DE_CARGAS = 30

# Os códigos da carga como um todo; os das linhas vêm do catálogo das pendências.
TEXTO_DO_CODIGO = {
    "EXTRACT_FAILED": "Não deu para buscar os dados",
    "NORMALIZE_FAILED": "Não deu para ler os dados recebidos",
    "CONTRACT_VIOLATION": "Os dados recebidos não fecham com o modelo",
    "LOAD_FAILED": "Não deu para gravar os dados",
    "PERMISSION_DENIED": "Sem permissão para alimentar a fazenda",
    "SNAPSHOT_HELD": "A guarda de volume segurou a carga (a fonte mandou bem menos dados que da outra vez)",
    "ENDPOINT_NOT_LOADED": "Parte dos dados não veio nesta carga (ficou como estava)",
    "DUPLICATE_UNIT_FILE": "Outra unidade mais recente alimenta a mesma fazenda",
    "DUPLICATE_CONTENT": "Conteúdo igual ao de outra unidade",
    "FARM_CREATED": "Fazenda nova cadastrada",
    "SOURCE_INACTIVE_FOR_DOMAIN": "Dados de uma fonte que não é a ativa da fazenda (ficaram de fora)",
    "CATEGORY_UNDECLARED": "Categoria usada sem estar no cadastro da fonte",
    "CATEGORY_BI_UNKNOWN": "Categoria BI que não existe",
    # do Metryx
    "LEGACY_RETIRO_ID": "Retiro com o id antigo (achado pelo nome na fazenda)",
    "WEIGHT_AMBIGUOUS": "Peso que não dá para saber se é total ou por cabeça",
    "TRANSFER_WITHOUT_AMOUNT": "Transferência sem quantidade (ficou de fora)",
    "CATEGORY_CHANGE_IS_WEANING": "Mudança de categoria que repetia um desmame (ficou de fora)",
    "PASTURE_FARM_UNKNOWN": "Pasto de fazenda fora do cadastro do cliente (ficou fora da área)",
    "MISSING_DATE": "Período de pasto sem data de início",
    "PLAN_VERSION_CHOSEN": "Plano com mais de uma versão na safra",
    "PLAN_NEGATIVE_STOCK": "Plano com categoria negativa em algum mês (conta zero)",
    "PLAN_MONTH_OVERLAP": "Plano com mês que outra safra já cobria (ficou de fora)",
}

CARGAS = """
    SELECT j.id, j.status, j.iniciado_em, j.finalizado_em, j.detalhe, u.nome AS pedida_por
    FROM ingest.job j
    LEFT JOIN core.usuario u ON u.id = j.usuario_id
    WHERE j.fonte = :fonte
    ORDER BY j.iniciado_em DESC NULLS LAST, j.criado_em DESC
    LIMIT :limite
"""
NOMES_DAS_UNIDADES = """
    SELECT chave, coalesce(descricao, chave) AS nome
    FROM ingest.unidade_origem
    WHERE fonte = :fonte AND chave = ANY (CAST(:chaves AS text[]))
"""
AVISOS_POR_UNIDADE = """
    SELECT v.job_id, u.chave, count(*) AS avisos
    FROM ingest.versao_origem v
    JOIN ingest.unidade_origem u ON u.id = v.unidade_id
    JOIN ingest.ocorrencia o ON o.versao_origem_id = v.id AND o.nivel = 'aviso'
    WHERE v.job_id = ANY (CAST(:cargas AS uuid[]))
    GROUP BY v.job_id, u.chave
"""
# as ocorrências da carga inteira (sem versão) e as das versões que ela gravou
AVISOS_DAS_CARGAS = """
    SELECT job_id, nivel, codigo, count(*) AS quantidade, min(mensagem) AS exemplo
    FROM (
        SELECT o.job_id, o.nivel, o.codigo, o.mensagem
        FROM ingest.ocorrencia o
        WHERE o.job_id = ANY (CAST(:cargas AS uuid[])) AND o.versao_origem_id IS NULL
        UNION ALL
        SELECT v.job_id, o.nivel, o.codigo, o.mensagem
        FROM ingest.versao_origem v
        JOIN ingest.ocorrencia o ON o.versao_origem_id = v.id
        WHERE v.job_id = ANY (CAST(:cargas AS uuid[]))
    ) ocorrencias
    WHERE nivel IN ('erro', 'aviso')
    GROUP BY job_id, nivel, codigo
"""


def listar(configuracao: Settings) -> list[IntegracaoPorApi]:
    integracoes = []
    for api in APIS:
        agenda = getattr(configuracao, api.campo_da_agenda)
        integracoes.append(IntegracaoPorApi(fonte=api.fonte, rotulo=api.rotulo, ligada=bool(agenda.strip()),
                                            quando=agenda_em_palavras(agenda),
                                            variavel_da_agenda=api.campo_da_agenda.upper()))
    return integracoes


def agenda_em_palavras(agenda: str) -> str:
    """'0 3 * * *' -> 'todo dia às 03:00, horário de Cuiabá'; outro formato do cron fica como está."""
    campos = agenda.split()
    if not campos:
        return "desligada"
    todo_dia = len(campos) == 5 and campos[2:] == ["*", "*", "*"]
    if todo_dia and campos[0].isdigit() and campos[1].isdigit():
        return f"todo dia às {int(campos[1]):02d}:{int(campos[0]):02d}, horário de Cuiabá"
    return f"no horário do cron {agenda.strip()} (Cuiabá)"


def cargas(s: Session, fonte: str) -> list[CargaDaIntegracao]:
    """As cargas mais recentes da API, da mais nova para a mais antiga."""
    if fonte not in [api.fonte for api in APIS]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"integração desconhecida: {fonte}")
    return HistoricoDasCargas(s, fonte).montar()


class HistoricoDasCargas:
    """Lê os jobs da fonte e junta, em poucas consultas, o nome de cada unidade e os avisos de cada carga."""

    def __init__(self, s: Session, fonte: str):
        self.s = s
        self.fonte = fonte
        self.jobs = []
        self.nomes: dict[str, str] = {}
        self.avisos_por_unidade: dict[tuple[UUID, str], int] = {}
        self.avisos_por_carga: dict[UUID, list[AvisoDaCarga]] = {}

    def montar(self) -> list[CargaDaIntegracao]:
        self.ler_jobs()
        self.ler_nomes_das_unidades()
        self.ler_avisos()
        return [self.carga(job) for job in self.jobs]

    def ler_jobs(self) -> None:
        parametros = {"fonte": self.fonte, "limite": LIMITE_DE_CARGAS}
        self.jobs = self.s.execute(text(CARGAS), parametros).mappings().all()

    def ler_nomes_das_unidades(self) -> None:
        chaves = set()
        for job in self.jobs:
            for unidade in unidades_do_detalhe(job["detalhe"]):
                chaves.add(unidade["chave"])
        linhas = self.s.execute(text(NOMES_DAS_UNIDADES), {"fonte": self.fonte, "chaves": sorted(chaves)})
        for chave, nome in linhas:
            self.nomes[chave] = nome

    def ler_avisos(self) -> None:
        ids = [job["id"] for job in self.jobs]
        for job_id, chave, avisos in self.s.execute(text(AVISOS_POR_UNIDADE), {"cargas": ids}):
            self.avisos_por_unidade[(job_id, chave)] = avisos
        for linha in self.s.execute(text(AVISOS_DAS_CARGAS), {"cargas": ids}).mappings():
            aviso = AvisoDaCarga(nivel=linha["nivel"], codigo=linha["codigo"], problema=problema(linha["codigo"]),
                                 quantidade=linha["quantidade"], exemplo=linha["exemplo"])
            self.avisos_por_carga.setdefault(linha["job_id"], []).append(aviso)

    def carga(self, job) -> CargaDaIntegracao:
        unidades = []
        for unidade in unidades_do_detalhe(job["detalhe"]):
            chave = unidade["chave"]
            unidades.append(UnidadeDaCarga(nome=self.nomes.get(chave, chave), status=unidade["status"],
                                           erro=unidade.get("erro"),
                                           avisos=self.avisos_por_unidade.get((job["id"], chave), 0)))
        avisos = sorted(self.avisos_por_carga.get(job["id"], []), key=ordem_do_aviso)
        return CargaDaIntegracao(id=job["id"], status=job["status"], iniciado_em=job["iniciado_em"],
                                 finalizado_em=job["finalizado_em"], pedida_por=job["pedida_por"], unidades=unidades,
                                 avisos=avisos)


def unidades_do_detalhe(detalhe: dict | None) -> list[dict]:
    """O resultado de cada unidade, gravado no fim do job (vazio enquanto ele roda)."""
    if not detalhe:
        return []
    return detalhe.get("unidades", [])


def problema(codigo: str) -> str:
    if codigo in TEXTO_DO_CODIGO:
        return TEXTO_DO_CODIGO[codigo]
    if codigo in CATALOGO:
        return CATALOGO[codigo].problema
    return "Aviso da carga"


def ordem_do_aviso(aviso: AvisoDaCarga) -> tuple:
    """Os erros primeiro; depois, o que mais apareceu."""
    return (aviso.nivel != "erro", -aviso.quantidade, aviso.codigo)
