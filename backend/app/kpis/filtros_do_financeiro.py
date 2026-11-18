"""Os filtros do financeiro além do status dos títulos (pedido do usuário, 18/11/2026): o tipo de atividade, a
classificação e a conta bancária, todos de seleção múltipla; sem escolha, tudo.

- tipo de atividade (`tipo_atividade` das views: Pecuária, Agricultura…, "A classificar" para a atividade sem tipo no
  de-para e "Sem atividade" para a linha que não tem): vale no realizado e no planejado. Ao marcar Agricultura, o
  planejado de um plano todo de Pecuária fica zero, e é o certo;
- classificação (`classificacao_analitica`: a do Metryx nos dados do Metryx; sem ela, o grupo do DRE por extenso):
  vale no realizado e no planejado;
- conta bancária: só o realizado tem. O plano não é vinculado a conta (decisão do usuário), e o planejado fica
  inteiro.

Os KPIs não montam esses filtros: o realizado passa por `LANCAMENTOS_DO_FILTRO` (situacao_do_lancamento.py) e o
planejado por `ORCAMENTO_ESCOLHIDO` (previsto_financeiro.py), que já trazem as condições daqui.
"""

from dataclasses import dataclass
from uuid import UUID

DO_TIPO_DE_ATIVIDADE = """(cardinality(CAST(:tipos_de_atividade AS text[])) = 0
         OR tipo_atividade = ANY (CAST(:tipos_de_atividade AS text[])))"""
DA_CLASSIFICACAO = """(cardinality(CAST(:classificacoes AS text[])) = 0
         OR classificacao_analitica = ANY (CAST(:classificacoes AS text[])))"""
DA_CONTA_BANCARIA = """(cardinality(CAST(:contas_bancarias AS uuid[])) = 0
         OR conta_bancaria_id = ANY (CAST(:contas_bancarias AS uuid[])))"""

# as condições de cada lado, para o WHERE da view (sem apelido)
DO_REALIZADO = f"{DO_TIPO_DE_ATIVIDADE} AND {DA_CLASSIFICACAO} AND {DA_CONTA_BANCARIA}"
DO_PLANEJADO = f"{DO_TIPO_DE_ATIVIDADE} AND {DA_CLASSIFICACAO}"


@dataclass(frozen=True)
class EscolhasDoFinanceiro:
    tipos_de_atividade: tuple[str, ...] = ()
    classificacoes: tuple[str, ...] = ()
    contas_bancarias: tuple[UUID, ...] = ()

    def parametros(self) -> dict:
        return {"tipos_de_atividade": list(self.tipos_de_atividade), "classificacoes": list(self.classificacoes),
                "contas_bancarias": [str(conta) for conta in self.contas_bancarias]}


SEM_ESCOLHA = EscolhasDoFinanceiro()
