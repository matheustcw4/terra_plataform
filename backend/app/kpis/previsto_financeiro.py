"""Qual orçamento entra como planejado do financeiro nas páginas Previsto × Realizado e Financeiro (pedido do usuário,
29/10/2026): a tela escolhe o tipo do orçamento e, quando ele tem mais de uma versão, a versão.

Regras:
- tipos: 'previsao' (previsão financeira, o DRE previsto) e 'planejamento' (o orçamento do plano, por versão). A tela
  só oferece os tipos que têm orçamento nas fazendas escolhidas. Sem pedido (ou pedido de um tipo que elas não têm),
  vale o primeiro da lista que existir: a previsão financeira, que é o que o BI compara;
- versão: em cada fazenda e safra (jul a jun) entra uma versão só, para não somar versões do mesmo plano (o BI soma
  todas). Padrão: a mais recente (maior ordem). A versão escolhida na tela (a mesma das metas de animais, que vem no
  recorte: versao_do_plano.py) substitui a mais recente na fazenda e nas safras que ela cobre; as outras fazendas e
  safras seguem com a mais recente;
- a lista de versões é a do tipo em uso com orçamento nos meses do filtro, só das fazendas com mais de uma versão
  nesses meses (nas outras não há o que escolher).
"""

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.kpis.filtro import Filtro
from app.kpis.versao_do_plano import rotulo_da_versao, versoes_para_escolher
from app.schemas.api import EscolhaDoPrevisto, TipoDoPrevisto, VersaoDoPrevisto

# na ordem da escolha padrão
TIPOS = {"previsao": "Previsão financeira", "planejamento": "Planejamento (fluxo de caixa)"}

# Entra no lugar da view do orçamento: as linhas do tipo escolhido, na versão que vale em cada fazenda e safra (a
# escolhida, se ela cobre aquela fazenda e safra; senão, a de maior ordem).
ORCAMENTO_ESCOLHIDO = """(
    SELECT o.*
    FROM fato.v_orcamento_financeiro o
    JOIN (
        SELECT DISTINCT ON (d.fazenda_id, d.safra) d.fazenda_id, d.safra, d.versao_plano_id
        FROM (
            SELECT x.fazenda_id, x.versao_plano_id, vp.ordem,
                   extract(year FROM x.competencia - interval '6 months') AS safra
            FROM fato.orcamento_financeiro x
            JOIN dim.versao_plano vp ON vp.id = x.versao_plano_id
            WHERE x.tipo = :tipo_do_previsto AND x.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
            GROUP BY 1, 2, 3, 4
        ) d
        ORDER BY d.fazenda_id, d.safra, d.versao_plano_id = CAST(:versao_do_plano AS uuid) DESC NULLS LAST,
                 d.ordem DESC NULLS LAST
    ) vale ON vale.fazenda_id = o.fazenda_id AND vale.versao_plano_id = o.versao_plano_id
          AND vale.safra = extract(year FROM o.competencia - interval '6 months')
    WHERE o.tipo = :tipo_do_previsto
)"""
TIPOS_DAS_FAZENDAS = """
    SELECT DISTINCT o.tipo FROM fato.orcamento_financeiro o WHERE o.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
"""
VERSOES_DO_TIPO = """
    SELECT DISTINCT o.fazenda_id, f.nome AS fazenda, vp.id, vp.nome, vp.ordem
    FROM fato.orcamento_financeiro o
    JOIN dim.versao_plano vp ON vp.id = o.versao_plano_id
    JOIN core.fazenda f ON f.id = o.fazenda_id
    WHERE o.tipo = :tipo AND o.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
      AND o.competencia = ANY (CAST(:meses AS date[]))
    ORDER BY f.nome, vp.ordem DESC NULLS LAST, vp.nome
"""
EM_USO_DO_ORCAMENTO = f"""
    SELECT vp.nome, min(f.nome) AS fazenda, count(DISTINCT f.id) AS fazendas, max(vp.ordem) AS ordem
    FROM {ORCAMENTO_ESCOLHIDO} o
    JOIN dim.versao_plano vp ON vp.id = o.versao_plano_id
    JOIN core.fazenda f ON f.id = o.fazenda_id
    WHERE o.competencia = ANY (CAST(:meses AS date[]))
    GROUP BY vp.id, vp.nome
    ORDER BY min(f.nome), max(vp.ordem) DESC NULLS LAST, vp.nome
"""


@dataclass(frozen=True)
class PedidoDoPrevisto:
    """O tipo de orçamento que a tela pediu; vazio = a escolha padrão (a versão vem no recorte)."""
    tipo: str | None = None


PEDIDO_PADRAO = PedidoDoPrevisto()


@dataclass(frozen=True)
class PrevistoEscolhido:
    opcoes: EscolhaDoPrevisto

    def parametros(self) -> dict:
        """Os parâmetros do `ORCAMENTO_ESCOLHIDO` além dos do recorte."""
        return {"tipo_do_previsto": self.opcoes.tipo}


def escolher_o_previsto(s: Session, filtro: Filtro, pedido: PedidoDoPrevisto) -> PrevistoEscolhido:
    disponiveis = tipos_disponiveis(s, filtro)
    tipo = tipo_em_uso(disponiveis, pedido.tipo)
    versoes = []
    if tipo is not None:
        versoes = versoes_do_tipo(s, filtro, tipo)
    versao = None
    if filtro.versao_do_plano in {versao_da_lista.id for versao_da_lista in versoes}:
        versao = filtro.versao_do_plano
    tipos = [TipoDoPrevisto(codigo=codigo, rotulo=TIPOS[codigo]) for codigo in disponiveis]
    em_uso = []
    if tipo is not None:
        em_uso = versoes_em_uso(s, filtro, tipo)
    return PrevistoEscolhido(EscolhaDoPrevisto(tipos=tipos, tipo=tipo, versoes=versoes, versao=versao, em_uso=em_uso))


def tipos_disponiveis(s: Session, filtro: Filtro) -> list[str]:
    """Os tipos com orçamento nas fazendas escolhidas, na ordem de `TIPOS`."""
    existentes = set(s.scalars(text(TIPOS_DAS_FAZENDAS), filtro.parametros()))
    return [codigo for codigo in TIPOS if codigo in existentes]


def tipo_em_uso(disponiveis: list[str], pedido: str | None) -> str | None:
    if pedido in disponiveis:
        return pedido
    if disponiveis:
        return disponiveis[0]
    return None


def versoes_do_tipo(s: Session, filtro: Filtro, tipo: str) -> list[VersaoDoPrevisto]:
    """As versões do tipo com orçamento nos meses do filtro, das fazendas que têm mais de uma."""
    linhas = list(s.execute(text(VERSOES_DO_TIPO), filtro.parametros() | {"tipo": tipo}).mappings())
    return versoes_para_escolher(linhas, len(filtro.fazendas) > 1)


def versoes_em_uso(s: Session, filtro: Filtro, tipo: str) -> list[str]:
    """As versões do orçamento que entraram no planejado, nos meses do filtro."""
    parametros = filtro.parametros() | {"tipo_do_previsto": tipo}
    varias_fazendas = len(filtro.fazendas) > 1
    rotulos = []
    for linha in s.execute(text(EM_USO_DO_ORCAMENTO), parametros).mappings():
        de_uma_fazenda = varias_fazendas and linha["fazendas"] == 1
        rotulos.append(rotulo_da_versao(linha["fazenda"], linha["nome"], de_uma_fazenda))
    return rotulos
