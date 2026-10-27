"""Diagnóstico de uma carga: ocorrências (avisos/erros) e linhas em quarentena, gravadas por versão de origem.

O diagnóstico vale para a versão vigente: ao gravar o de uma versão nova, o das versões anteriores da mesma unidade sai.
Também monta os avisos de pendência — categoria sem categoria BI e conta "A classificar" — que dependem do banco.
"""

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.etl.canonical import LinhaRejeitada, LoteCanonico, Ocorrencia
from app.etl.mapping import Resolvido
from app.etl.quality import Cod
from app.models.ingest import LinhaQuarentena, VersaoOrigem
from app.models.ingest import Ocorrencia as OcorrenciaDb


@dataclass
class Diagnostico:
    ocorrencias: list[Ocorrencia] = field(default_factory=list)
    rejeitadas: list[LinhaRejeitada] = field(default_factory=list)

    def avisos(self) -> int:
        """Ocorrências que contam como aviso (as de nível 'info' não contam)."""
        return sum(1 for ocorrencia in self.ocorrencias if ocorrencia.nivel != "info")


def gravar(s: Session, diagnostico: Diagnostico, resolvido: Resolvido, versao_id: UUID, unidade_id: UUID | None,
           job_id: UUID | None) -> None:
    if unidade_id is not None:          # o diagnóstico das versões anteriores desta unidade sai
        anteriores = select(VersaoOrigem.id).where(VersaoOrigem.unidade_id == unidade_id)
        s.execute(LinhaQuarentena.__table__.delete().where(LinhaQuarentena.versao_origem_id.in_(anteriores)))
        s.execute(OcorrenciaDb.__table__.delete().where(OcorrenciaDb.versao_origem_id.in_(anteriores)))
    if diagnostico.ocorrencias:
        linhas = []
        for ocorrencia in diagnostico.ocorrencias:
            linhas.append({"job_id": job_id, "versao_origem_id": versao_id,
                           "fazenda_id": fazenda_id(resolvido, ocorrencia.fazenda), "nivel": ocorrencia.nivel,
                           "codigo": ocorrencia.codigo, "mensagem": ocorrencia.mensagem,
                           "entidade": ocorrencia.entidade, "origem_linha": ocorrencia.origem_linha,
                           "contexto": ocorrencia.contexto})
        s.execute(pg_insert(OcorrenciaDb), linhas)
    if diagnostico.rejeitadas:
        linhas = []
        for rejeitada in diagnostico.rejeitadas:
            linhas.append({"versao_origem_id": versao_id, "job_id": job_id,
                           "fazenda_id": fazenda_id(resolvido, rejeitada.fazenda), "entidade": rejeitada.entidade,
                           "origem_linha": rejeitada.origem_linha, "codigo": rejeitada.codigo,
                           "motivo": rejeitada.motivo, "dados": rejeitada.dados})
        s.execute(pg_insert(LinhaQuarentena), linhas)


def fazenda_id(resolvido: Resolvido, fazenda: str | None) -> UUID | None:
    """Fazenda do aviso ou da linha rejeitada. Sem fazenda própria (ex.: aviso de uma aba da planilha), vale a da
    unidade quando ela alimenta uma fazenda só, como toda planilha: o RLS mostra o diagnóstico a quem vê a fazenda, e
    sem fazenda ninguém além do admin o veria."""
    if fazenda is not None:
        return resolvido.fazendas.get(fazenda)
    if len(resolvido.fazendas) == 1:
        return next(iter(resolvido.fazendas.values()))
    return None


def pendencias_de_categoria(s: Session, resolvido: Resolvido) -> list[Ocorrencia]:
    """Categorias usadas no lote que ainda não têm categoria BI: os dados entram, mas ficam fora do estoque/KPIs."""
    if not resolvido.categorias:
        return []
    pendentes = s.execute(
        text("SELECT id, nome_origem, fonte FROM dim.categoria_map "
             "WHERE id = ANY (CAST(:ids AS uuid[])) AND categoria_bi_id IS NULL"),
        {"ids": list(set(resolvido.categorias.values()))},
    ).all()
    avisos = []
    for categoria_map_id, nome, fonte in pendentes:
        avisos.append(Ocorrencia(
            nivel="aviso", codigo=Cod.CATEGORY_UNMAPPED,
            mensagem=f"categoria '{nome}' ({fonte}) sem categoria BI confirmada: fora do estoque e dos KPIs até ser "
                     "mapeada",
            contexto={"categoria_map_id": str(categoria_map_id)}))
    return avisos


def pendencias_de_conta(s: Session, resolvido: Resolvido, lote: LoteCanonico) -> list[Ocorrencia]:
    """Contas usadas no lote ainda "A classificar": os lançamentos entram (o total bate), a classificação pendente."""
    if not resolvido.contas:
        return []
    resultado = s.execute(
        text("SELECT id FROM dim.plano_contas_map WHERE id = ANY (CAST(:ids AS uuid[])) AND centro_custo_id IS NULL"),
        {"ids": list(set(resolvido.contas.values()))})
    pendentes = {conta_map_id for (conta_map_id,) in resultado}
    uso: dict = {}                      # conta -> (linhas, valor total)
    for linha in [*lote.lancamentos, *lote.orcamentos]:
        if resolvido.contas[linha.conta] not in pendentes:
            continue
        linhas, total = uso.get(linha.conta, (0, 0))
        uso[linha.conta] = (linhas + 1, total + linha.valor)
    avisos = []
    for conta, (linhas, total) in uso.items():
        avisos.append(Ocorrencia(
            nivel="aviso", codigo=Cod.ACCOUNT_UNCLASSIFIED,
            mensagem=f"conta '{conta.centro} / {conta.subcentro or '-'}' fora do plano de contas: "
                     f"{linhas} lançamento(s), R$ {total:,.2f}, carregados como 'A classificar'",
            contexto={"plano_contas_map_id": str(resolvido.contas[conta]), "linhas": linhas, "valor": str(total)}))
    return avisos
