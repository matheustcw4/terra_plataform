"""Planilha em dobro (a mesma enviada duas vezes com nomes diferentes): vale a mais recente.

Duas regras, as duas só entre ARQUIVOS (unidades com data de modificação; o histórico e o Metryx não entram):
- mesmos bytes (sha256): a cópia mais antiga é ignorada antes de ser lida; se ela já tinha carregado, saem só as linhas
  que ela gravou (como os bytes são iguais, nada se perde);
- mesma fazenda (código + FAZENDA do fUnidade): a unidade mais antiga é ignorada. O aviso diz se o conteúdo é igual ou
  diferente e alerta quando a ignorada tem mais linhas — o critério é a data de modificação, e abrir e salvar a cópia
  antiga a torna "a mais recente".
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import Engine, delete, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db.session import sessao
from app.etl import loaders
from app.etl.canonical import LoteCanonico
from app.etl.quality import Cod
from app.models.ingest import Ocorrencia as OcorrenciaDb
from app.models.ingest import UnidadeOrigem as UnidadeOrigemDb
from app.models.ingest import VersaoOrigem


class ErroUnidadeDuplicada(Exception):
    """Outro arquivo, mais recente, alimenta a mesma fazenda: este é ignorado."""


@dataclass(frozen=True)
class CopiaIdentica:
    unidade_id: UUID
    chave: str
    mais_recente: bool          # a outra cópia é mais recente que a unidade em processamento?


# --- mesmos bytes --------------------------------------------------------------------------------------------------

COPIA_IDENTICA = """
    SELECT outra.id, outra.chave,
           (outra.metadados->>'mtime')::numeric > (esta.metadados->>'mtime')::numeric
           OR ((outra.metadados->>'mtime')::numeric = (esta.metadados->>'mtime')::numeric AND outra.chave < esta.chave)
               AS outra_mais_recente
    FROM ingest.unidade_origem outra
    JOIN ingest.versao_origem versao ON versao.id = outra.ultima_versao_id
    JOIN ingest.unidade_origem esta ON esta.id = :u
    WHERE outra.fonte = :fonte AND outra.id <> :u AND outra.status = 'ativa' AND versao.sha256 = :sha
      AND outra.metadados ? 'mtime' AND esta.metadados ? 'mtime'
    ORDER BY 3 DESC LIMIT 1
"""


def copia_identica(engine: Engine, fonte: str, unidade_id: UUID, sha256: str) -> CopiaIdentica | None:
    """Outro arquivo ativo cuja versão vigente tem exatamente os mesmos bytes (empate de data: ordem do nome)."""
    with sessao(engine) as s:
        linha = s.execute(text(COPIA_IDENTICA), {"fonte": fonte, "u": unidade_id, "sha": sha256}).first()
    if linha is None:
        return None
    return CopiaIdentica(unidade_id=linha[0], chave=linha[1], mais_recente=bool(linha[2]))


def ignorar_copia(engine: Engine, job_id: UUID | None, unidade_id: UUID, chave: str, chave_da_outra: str,
                  sha256: str) -> None:
    with sessao(engine) as s:
        s.execute(update(UnidadeOrigemDb).where(UnidadeOrigemDb.id == unidade_id).values(status="ignorada"))
        s.execute(pg_insert(OcorrenciaDb).values(
            job_id=job_id, nivel="aviso", codigo=Cod.DUPLICATE_CONTENT,
            mensagem=f"{chave}: mesmos bytes de {chave_da_outra}, que é mais recente; este arquivo é ignorado e "
                     "pode ser apagado da pasta",
            contexto={"arquivo": chave, "copia_de": chave_da_outra, "sha256": sha256}))


def aposentar_copia(engine: Engine, job_id: UUID | None, copia: CopiaIdentica, chave: str, sha256: str,
                    estoque_ate) -> None:
    """A cópia antiga carregou antes da nova. Saem só as linhas que ELA gravou (origem_ref); se ela tinha virado outra
    fazenda (ex.: código errado no nome do arquivo), essa fazenda fica sem os dados em dobro."""
    with sessao(engine) as s:
        versoes = list(s.scalars(select(VersaoOrigem.id).where(VersaoOrigem.unidade_id == copia.unidade_id)))
        fazendas: set[UUID] = set()
        for tabela in loaders.TABELAS.values():
            apagadas = s.scalars(delete(tabela).where(tabela.c.origem_ref.in_(versoes)).returning(tabela.c.fazenda_id))
            fazendas.update(apagadas)
        s.execute(update(UnidadeOrigemDb).where(UnidadeOrigemDb.id == copia.unidade_id)
                  .values(status="ignorada", ultima_versao_id=None, assinatura=None))
        s.execute(pg_insert(OcorrenciaDb).values(
            job_id=job_id, nivel="aviso", codigo=Cod.DUPLICATE_CONTENT,
            mensagem=f"{copia.chave}: mesmos bytes de {chave}, que é mais recente; o que este arquivo tinha gravado "
                     "saiu e ele pode ser apagado da pasta",
            contexto={"arquivo": copia.chave, "copia_de": chave, "sha256": sha256}))
        if fazendas:
            s.execute(text("SELECT fato.recalcular_estoque_mensal(CAST(:f AS uuid[]), CAST(:ate AS date))"),
                      {"f": list(fazendas), "ate": estoque_ate})


# --- mesma fazenda -------------------------------------------------------------------------------------------------

ARQUIVO_MAIS_RECENTE_DA_FAZENDA = """
    WITH outras AS (
        SELECT origem_ref FROM fato.mov_animal WHERE fazenda_id = ANY (CAST(:f AS uuid[])) AND fonte = :fonte
        UNION SELECT origem_ref FROM fato.inventario WHERE fazenda_id = ANY (CAST(:f AS uuid[])) AND fonte = :fonte
        UNION SELECT origem_ref FROM fato.lancamento_financeiro
              WHERE fazenda_id = ANY (CAST(:f AS uuid[])) AND fonte = :fonte
        UNION SELECT origem_ref FROM fato.rebanho_medio_mensal
              WHERE fazenda_id = ANY (CAST(:f AS uuid[])) AND fonte = :fonte
    )
    SELECT outra.chave, vigente.metadados FROM outras
    JOIN ingest.versao_origem versao ON versao.id = outras.origem_ref
    JOIN ingest.unidade_origem outra ON outra.id = versao.unidade_id
    LEFT JOIN ingest.versao_origem vigente ON vigente.id = outra.ultima_versao_id
    JOIN ingest.unidade_origem esta ON esta.id = :u
    WHERE outra.id <> :u AND outra.status = 'ativa'
      AND outra.metadados ? 'mtime' AND esta.metadados ? 'mtime'
      AND coalesce((outra.metadados->>'mtime')::numeric, 0) > coalesce((esta.metadados->>'mtime')::numeric, 0)
    LIMIT 1
"""


def conferir_arquivo_em_dobro(s: Session, lote: LoteCanonico, fazendas: list[UUID], unidade_id: UUID) -> None:
    """Se outro arquivo, mais recente, já alimenta uma destas fazendas, esta unidade não carrega."""
    if not fazendas:
        return
    linha = s.execute(text(ARQUIVO_MAIS_RECENTE_DA_FAZENDA),
                      {"f": fazendas, "fonte": lote.fonte, "u": unidade_id}).first()
    if linha is None:
        return
    chave_da_outra, metadados_da_outra = linha[0], linha[1] or {}
    raise ErroUnidadeDuplicada(mensagem_em_dobro(chave_da_outra, metadados_da_outra, lote))


def mensagem_em_dobro(chave_da_outra: str, metadados_da_outra: dict, lote: LoteCanonico) -> str:
    """Diz se o arquivo ignorado é cópia ou outra versão, e avisa quando ele parece ser o mais completo."""
    base = f"a fazenda já é alimentada por um arquivo mais recente: {chave_da_outra}"
    if metadados_da_outra.get("impressao_dados") == lote.impressao_dados():
        return f"{base} (mesmo conteúdo: este arquivo pode ser apagado)"
    linhas = lote.linhas_dados()
    linhas_da_outra = metadados_da_outra.get("linhas_dados")
    if linhas_da_outra is None:
        return f"{base} (confira e apague o antigo)"
    if linhas > linhas_da_outra:
        return (f"{base}. ATENÇÃO: este arquivo, mais antigo, tem mais linhas ({linhas}) que o mais recente "
                f"({linhas_da_outra}); confira qual é o certo antes de apagar")
    return (f"{base} (conteúdo diferente: {linhas} linhas; o mais recente tem {linhas_da_outra}); "
            "confira e apague o antigo")
