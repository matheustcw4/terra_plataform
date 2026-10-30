"""Formato das respostas da API (o front recebe tudo pronto: números já agregados, nada a calcular)."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

# --- login ---------------------------------------------------------------------------------------------------------


class PedidoLogin(BaseModel):
    email: str
    senha: str


class UsuarioResumo(BaseModel):
    id: UUID
    nome: str
    email: str
    eh_admin: bool


class RespostaLogin(BaseModel):
    token: str
    usuario: UsuarioResumo


# --- escopo: o que o usuário pode ver ------------------------------------------------------------------------------


class Capacidades(BaseModel):
    """Que dados a fazenda tem (o front mostra ou esconde telas por isso, nunca pela fonte)."""
    estoque: bool
    rebanho_medio: bool
    area: bool
    financeiro: bool
    planejado: bool


class FazendaDoEscopo(BaseModel):
    id: UUID
    nome: str
    cliente: str              # o 1º menu do filtro: proprietário (planilha) ou customer (Metryx)
    origem: str | None        # TEMPORÁRIO: planilha | metryx, só para o filtro "Origem" do MENU (até a Q9)
    sistema_produtivo: str | None
    primeiro_mes: date | None
    ultimo_mes: date | None   # último mês com movimento ou rebanho informado (depois dele o saldo só se repete)
    capacidades: Capacidades


class Escopo(BaseModel):
    usuario: UsuarioResumo
    fazendas: list[FazendaDoEscopo]


# --- página Movimentação do Gado ---------------------------------------------------------------------------------


class Periodo(BaseModel):
    inicio: date
    fim: date
    meses: int


class ComMeta(BaseModel):
    """Um número do período com o planejado ao lado, como os cartões "% em relação à meta" do BI."""
    realizado: float
    planejado: float
    percentual_da_meta: float | None    # realizado ÷ planejado (sem planejado, não há meta)


class EstoqueDoMes(BaseModel):
    mes: date
    estoque_final: float


class EstoqueDaCategoria(BaseModel):
    categoria: str
    estoque_final: float


class Movimentacao(BaseModel):
    periodo: Periodo
    estoque_final: float
    rebanho_medio_cab: float | None
    rebanho_medio_ua: float | None
    lotacao_cab_ha: float | None
    lotacao_ua_ha: float | None
    nascimentos: ComMeta
    mortes: ComMeta
    indice_mortalidade: float | None      # mortes ÷ rebanho médio
    compras: ComMeta
    vendas: ComMeta                       # abate + em pé
    estoque_mensal: list[EstoqueDoMes]
    estoque_por_categoria: list[EstoqueDaCategoria]


# --- páginas Vendas, Compras e Transferências (lotes de gado) ---------------------------------------------------


class IndicadoresDoLote(BaseModel):
    cabecas: float
    valor: float                    # R$: faturamento na venda, investimento na compra
    kg_vivo: float
    arrobas: float                  # abate: @ de carcaça (kg carcaça ÷ 15); em pé e compra: kg vivo ÷ 30
    preco_arroba: float | None      # R$/@
    preco_kg: float | None          # R$/kg vivo
    peso_medio_kg: float | None     # kg vivo por cabeça
    rendimento_carcaca: float | None   # kg carcaça ÷ kg vivo (só abate)


class QuadroDoLote(BaseModel):
    recorte: str                    # GERAL | MACHO | FÊMEA
    realizado: IndicadoresDoLote
    planejado: IndicadoresDoLote


class MesDoLote(BaseModel):
    mes: date
    cabecas: float
    cabecas_planejadas: float
    cabecas_acumuladas: float       # do início do período até este mês (realizado)
    valor: float
    valor_planejado: float
    preco_arroba: float | None      # do realizado do mês (a linha do gráfico de desembolso de compras)


class Vendas(BaseModel):
    periodo: Periodo
    tipo: str                       # abate | em_pe
    quadro: list[QuadroDoLote]
    serie_mensal: list[MesDoLote]


class Compras(BaseModel):
    periodo: Periodo
    quadro: list[QuadroDoLote]
    preco_arroba_compra: float | None
    preco_arroba_venda: float | None    # abate e em pé juntos, a base do ágio
    agio: float | None                  # (compra − venda) ÷ venda
    serie_mensal: list[MesDoLote]


class MesDeTransferencia(BaseModel):
    mes: date
    entradas: float                 # cabeças que chegaram de outra fazenda (realizado)
    saidas: float                   # cabeças que foram para outra fazenda (realizado)


class Transferencias(BaseModel):
    periodo: Periodo
    entrada: list[QuadroDoLote]
    saida: list[QuadroDoLote]
    serie_mensal: list[MesDeTransferencia]


# --- páginas Nascimentos e Mortes (contagens de cabeças) -----------------------------------------------------------


class ContagemDoRecorte(BaseModel):
    """Cabeças de um quadro (um sexo, um grupo ou o geral) no período, com o planejado ao lado."""
    recorte: str
    realizado: float
    planejado: float
    percentual_da_meta: float | None        # realizado ÷ planejado


class NascimentosDoSexo(ContagemDoRecorte):
    participacao_no_total: float | None     # nascimentos do recorte ÷ todos os nascimentos do período


class MortesDoGrupo(ContagemDoRecorte):
    sobre_rebanho_medio: float | None       # mortes ÷ rebanho médio do mesmo grupo
    sobre_nascimentos: float | None         # só BEZERROS: mortes ÷ nascimentos do período


class MesDaContagem(BaseModel):
    mes: date
    realizado: float
    planejado: float
    realizado_acumulado: float              # do início do período até este mês
    planejado_acumulado: float


class Nascimentos(BaseModel):
    periodo: Periodo
    quadro: list[NascimentosDoSexo]         # GERAL, MACHO, FÊMEA
    serie_mensal: list[MesDaContagem]


class CausaDeMorte(BaseModel):
    causa: str
    cabecas: float


class Mortes(BaseModel):
    periodo: Periodo
    quadro: list[MortesDoGrupo]             # GERAL, BEZERROS, JOVENS, ADULTOS
    causas: list[CausaDeMorte]              # do realizado, da maior para a menor
    serie_mensal: list[MesDaContagem]


# --- página Financeiro --------------------------------------------------------------------------------------------


class Velocimetro(BaseModel):
    """Um dos velocímetros do topo da página: o realizado, a meta e o fim da escala."""
    realizado: float | None
    planejado: float | None
    maximo: float | None            # fim da escala: a meta × o fator de dim.parametro, como no BI
    dentro_da_meta: bool | None     # desembolso e custeio: realizado ≤ meta; preço da @: realizado ≥ meta


class DesembolsoDoCentro(BaseModel):
    centro_custo: str
    valor: float


class MesDoFinanceiro(BaseModel):
    mes: date
    receitas: float                 # créditos das contas de receita da pecuária e da agricultura
    receitas_planejadas: float
    despesas: float                 # todos os débitos, menos os estornos das contas de despesa
    saldo: float                    # todas as receitas (inclusive as outras) − despesas
    desembolso: float
    desembolso_planejado: float
    desembolso_por_cabeca: float | None             # desembolso do mês ÷ rebanho médio do mês
    desembolso_por_cabeca_planejado: float | None


class TipoDoPrevisto(BaseModel):
    codigo: Literal["previsao", "planejamento"]
    rotulo: str


class VersaoDoPrevisto(BaseModel):
    id: UUID
    rotulo: str                     # o nome da versão; com mais de uma fazenda, "fazenda · nome"


class EscolhaDoPrevisto(BaseModel):
    """De qual orçamento vem o planejado do financeiro (as páginas Previsto × Realizado e Financeiro escolhem)."""
    tipos: list[TipoDoPrevisto]     # os que têm orçamento nas fazendas escolhidas
    tipo: Literal["previsao", "planejamento"] | None    # o que entrou no planejado; None = nenhum orçamento
    versoes: list[VersaoDoPrevisto]  # as do tipo em uso com orçamento no período
    versao: UUID | None             # a escolhida; None = a mais recente de cada fazenda e safra


class Financeiro(BaseModel):
    periodo: Periodo
    desembolso: float               # R$ que saíram nas contas de desembolso (DCM), já sem os estornos
    receitas: float
    desembolso_por_cabeca_mes: Velocimetro
    custeio_por_cabeca_mes: Velocimetro
    preco_arroba_venda: Velocimetro
    desembolso_por_centro: list[DesembolsoDoCentro]     # do maior para o menor
    serie_mensal: list[MesDoFinanceiro]
    previsto: EscolhaDoPrevisto


# --- página Previsto × Realizado (a matriz do DRE) -------------------------------------------------------------------


class Comparacao(BaseModel):
    realizado: float
    planejado: float
    variacao: float | None          # (realizado − planejado) ÷ planejado; sem planejado, vazio
    semaforo: str | None            # verde | amarelo | vermelho, pela regra do BI (limiar de dim.parametro)


class LinhaDoPrevisto(BaseModel):
    """Uma linha da matriz: o total de uma classificação ou uma conta (centro de custo)."""
    nome: str
    mensal: Comparacao              # o último mês do período
    acumulado: Comparacao           # do início ao fim do período


class GrupoDoPrevisto(BaseModel):
    classificacao: str              # "A - RECEITAS", "B - DESEMBOLSO" (investimentos + custeio), "C - INVESTIMENTOS"...
    total: LinhaDoPrevisto
    contas: list[LinhaDoPrevisto]   # em ordem alfabética; o desembolso é só subtotal, sem contas


class PrevistoRealizado(BaseModel):
    periodo: Periodo
    ultimo_mes: date
    grupos: list[GrupoDoPrevisto]
    resultado: LinhaDoPrevisto      # receitas + outros créditos − (investimentos + custeio + outros débitos)
    previsto: EscolhaDoPrevisto


# --- pendências de lançamento (o que corrigir na origem) -------------------------------------------------------------


class Pendencia(BaseModel):
    fazenda_id: UUID
    fazenda: str
    situacao: str                   # nao_entrou (quarentena: fora dos números) | confira (entrou, mas parece errado)
    codigo: str
    problema: str                   # título curto, em pt-BR
    detalhe: str                    # o que a carga anotou (motivo ou mensagem)
    como_corrigir: str
    quem_corrige: str               # origem (planilha ou sistema de origem) | equipe (equipe Terra, na plataforma)
    origem: str                     # nome do arquivo ou da fonte
    local: str | None               # ex.: "aba fVendaemPe, linha 18"
    valores: list[str]              # o que está na linha, ex.: "DATA: 0108/2025"
    salvo_em: datetime | None       # quando o arquivo foi salvo (só arquivo)
    carregado_em: datetime | None


class ResumoDePendencias(BaseModel):
    nao_entrou: int
    confira: int
    para_a_equipe: int


class Pendencias(BaseModel):
    resumo: ResumoDePendencias
    itens: list[Pendencia]
