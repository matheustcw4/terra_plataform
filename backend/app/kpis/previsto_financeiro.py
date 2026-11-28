"""Qual orçamento entra como planejado do financeiro nas páginas Previsto × Realizado e Financeiro (pedido do usuário,
29/10/2026): o planejamento, na versão escolhida na tela.

Regras:
- tipo: só 'planejamento' (o fluxo de caixa do plano do Metryx e o DRE planejado da planilha, por versão). A previsão
  financeira do Metryx (contas a pagar e a receber) não é planejado e não entra nunca (pedido do usuário, 27/11/2026:
  "planejamento é planejamento e vem dos endpoints"); até lá, era um segundo tipo, o padrão. O pedido de outro tipo
  (um link antigo com `previsto=previsao`) dá o planejamento. A lista `tipos` continua na resposta, para o caso de um
  tipo novo, e a tela só mostra o seletor quando há mais de um;
- versão: sem escolha, em cada fazenda e safra (jul a jun) entra só a mais recente (maior ordem), para não somar
  versões do mesmo plano (o BI soma todas). As versões marcadas na tela para a fazenda (as mesmas das metas de
  animais, que vêm no recorte: versao_do_plano.py) entram todas, somadas; a fazenda marcada "nenhum planejamento" fica
  sem orçamento;
- a lista de versões é a mesma das outras páginas e do MENU: todas as fazendas do filtro, com as versões do plano
  nos meses (das metas e do orçamento do planejamento), por fazenda (versao_do_plano.py).
"""

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.kpis.filtro import Filtro
from app.kpis.filtros_do_financeiro import DO_PLANEJADO
from app.kpis.versao_do_plano import rotulo_da_versao, versoes_por_fazenda
from app.schemas.api import EscolhaDoPrevisto, TipoDoPrevisto

# na ordem da escolha padrão; só o planejamento é planejado (pedido do usuário, 27/11/2026)
TIPOS = {"planejamento": "Planejamento"}

# Entra no lugar da view do orçamento: as linhas do tipo escolhido, nas versões que valem em cada fazenda e safra (as
# marcadas na tela, que somam; na fazenda sem escolha, a de maior ordem; na "sem planejamento", nenhuma), pela função
# `app.versoes_do_orcamento` (migração 0025), e só do tipo de atividade e da classificação escolhidos no filtro.
ORCAMENTO_ESCOLHIDO = f"""(
    SELECT o.*
    FROM fato.v_orcamento_financeiro o
    WHERE o.tipo = :tipo_do_previsto
      AND (o.fazenda_id, extract(year FROM o.competencia - interval '6 months')::integer, o.versao_plano_id) IN (
          SELECT * FROM app.versoes_do_orcamento(CAST(:fazendas AS uuid[]), CAST(:tipo_do_previsto AS text),
                                                 CAST(:versoes_do_plano AS uuid[]),
                                                 CAST(:fazendas_sem_plano AS uuid[])))
      AND {DO_PLANEJADO}
)"""
# O rebanho que divide o planejado do financeiro (desembolso e custeio por cabeça por mês): o da mesma versão que deu o
# dinheiro, em cada fazenda e safra (pedido do usuário, 27/11/2026). Antes era a versão das metas, escolhida à parte, e
# a fazenda sem orçamento também entrava: na Maister, o plano "Global (24.06.26 teste)" de uma fazenda sem orçamento
# quase dobrava o divisor, e o desembolso planejado de 26/27 caía de R$ 173,10 para R$ 79,04 por cabeça por mês.
# Quando a versão do dinheiro não tem rebanho previsto (o fluxo de caixa de uma versão sem a evolução do rebanho), vale
# a versão do plano escolhida para a fazenda, só nas fazendas e safras que têm o dinheiro previsto.
VERSOES_DO_REBANHO_PREVISTO = """
    WITH orcamento AS (
        SELECT * FROM app.versoes_do_orcamento(CAST(:fazendas AS uuid[]), CAST(:tipo_do_previsto AS text),
                                               CAST(:versoes_do_plano AS uuid[]), CAST(:fazendas_sem_plano AS uuid[]))
    ), com_rebanho AS (
        SELECT o.fazenda_id, o.safra, o.versao_plano_id FROM orcamento o
        WHERE EXISTS (SELECT 1 FROM fato.rebanho_medio_mensal r
                      WHERE r.cenario = 'planejado' AND r.fazenda_id = o.fazenda_id
                        AND r.versao_plano_id = o.versao_plano_id
                        AND extract(year FROM r.competencia - interval '6 months')::integer = o.safra)
    )
    SELECT c.fazenda_id, c.safra, c.versao_plano_id FROM com_rebanho c
    UNION
    SELECT p.fazenda_id, p.safra, p.versao_plano_id
    FROM app.versoes_do_planejado(CAST(:fazendas AS uuid[]), CAST(:versoes_do_plano AS uuid[]),
                                  CAST(:fazendas_sem_plano AS uuid[])) p
    WHERE (p.fazenda_id, p.safra) IN (SELECT o.fazenda_id, o.safra FROM orcamento o)
      AND (p.fazenda_id, p.safra) NOT IN (SELECT c.fazenda_id, c.safra FROM com_rebanho c)
"""
TIPOS_DAS_FAZENDAS = """
    SELECT DISTINCT o.tipo FROM fato.orcamento_financeiro o WHERE o.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
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
    em_uso = []
    if tipo is not None:
        em_uso = versoes_em_uso(s, filtro, tipo)
    # a lista de cada fazenda é a mesma das outras páginas (a escolha da versão vale em todas)
    fazendas = versoes_por_fazenda(s, filtro)
    tipos = [TipoDoPrevisto(codigo=codigo, rotulo=TIPOS[codigo]) for codigo in disponiveis]
    return PrevistoEscolhido(EscolhaDoPrevisto(tipos=tipos, tipo=tipo, fazendas=fazendas, em_uso=em_uso))


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


def versoes_em_uso(s: Session, filtro: Filtro, tipo: str) -> list[str]:
    """As versões do orçamento que entraram no planejado, nos meses do filtro."""
    parametros = filtro.parametros() | {"tipo_do_previsto": tipo}
    varias_fazendas = len(filtro.fazendas) > 1
    rotulos = []
    for linha in s.execute(text(EM_USO_DO_ORCAMENTO), parametros).mappings():
        de_uma_fazenda = varias_fazendas and linha["fazendas"] == 1
        rotulos.append(rotulo_da_versao(linha["fazenda"], linha["nome"], de_uma_fazenda))
    return rotulos
