"""Formato do boletim analítico (o "Exportar PDF" no modo Analítico): uma fazenda ou um grupo num mês de referência,
com o mês, o acumulado do período (safra ou ano) até ele e a meta do período inteiro, e frases que explicam os
números. O backend calcula tudo, inclusive as frases; o front só desenha as folhas.
"""

from datetime import date

from pydantic import BaseModel

from app.schemas.api import PrevistoRealizado


class Comparado(BaseModel):
    """Previsto × realizado de um indicador num recorte (o mês ou o acumulado)."""
    previsto: float | None
    realizado: float | None
    variacao: float | None                  # realizado − previsto
    variacao_percentual: float | None       # (realizado − previsto) ÷ previsto; sem previsto, vazio
    status: str | None                      # verde | amarelo | vermelho; vazio quando o indicador não tem sentido


class LinhaDoPlacar(BaseModel):
    grupo: str                              # "REBANHO", "VENDAS ABATE"...
    indicador: str                          # "Rebanho médio", "R$/@"...
    unidade: str                            # cab | cab/ha | kg | @ | % | R$ | R$/@ | R$/kg | R$/cab | R$/cab/mês
    mes: Comparado
    acumulado: Comparado
    meta_periodo: float | None              # o previsto do período inteiro (safra ou ano)


class SecaoPlacar(BaseModel):
    linhas: list[LinhaDoPlacar]
    leitura: list[str]


# --- movimentação do estoque e lotação -----------------------------------------------------------------------------


class LinhaDoEstoque(BaseModel):
    """Uma categoria BI no mês de referência (a última linha é o TOTAL)."""
    categoria: str
    estoque_inicial: float
    nascimentos: float
    compras: float
    desmame_entrada: float
    transferencia_entrada: float
    mudanca_entrada: float
    mortes: float
    vendas: float                           # abate + em pé
    desmame_saida: float
    transferencia_saida: float
    consumo_doacao: float
    mudanca_saida: float
    ajuste: float                           # diferença entre o checkpoint da fonte e os fluxos
    estoque_final: float


class ResumoDoEstoque(BaseModel):
    """O período até o mês de referência, somado (o "ACUMULADO SAFRA")."""
    estoque_inicial: float                  # no começo do período
    nascimentos: float
    compras: float
    vendas: float
    mortes: float
    consumo_doacao: float
    transferencia_entrada: float
    transferencia_saida: float
    ajuste: float
    estoque_final: float                    # no fim do mês de referência


class FatiaDoRebanho(BaseModel):
    categoria: str
    cabecas: float
    participacao: float | None              # cabeças ÷ rebanho final


class SecaoEstoque(BaseModel):
    mes: list[LinhaDoEstoque]
    acumulado: ResumoDoEstoque
    distribuicao_final: list[FatiaDoRebanho]   # da maior para a menor
    leitura: list[str]


class MesDaLotacao(BaseModel):
    mes: date
    rebanho_medio_cab: float | None
    rebanho_medio_ua: float | None
    area_ha: float | None
    lotacao_cab_ha: float | None
    lotacao_ua_ha: float | None
    lotacao_cab_ha_prevista: float | None   # rebanho médio previsto ÷ área prevista


class SecaoLotacao(BaseModel):
    estoque_inicial: float
    estoque_final: float
    variacao_do_rebanho: float | None       # (final − inicial) ÷ inicial
    rebanho_medio_cab: float | None         # do período até o mês de referência
    rebanho_medio_ua: float | None
    lotacao_cab_ha: float | None
    lotacao_ua_ha: float | None
    lotacao_cab_ha_prevista: float | None
    lotacao_maxima: float | None            # cab/ha, entre os meses até o de referência
    lotacao_minima: float | None
    meses: list[MesDaLotacao]               # todos os meses do período (o realizado só até o de referência)
    leitura: list[str]


# --- lotes (nascimentos, compras, vendas e transferências) e mortes --------------------------------------------------


class LoteDoMes(BaseModel):
    """Um lançamento de lote no mês de referência (nascimento, compra, venda ou transferência)."""
    data: date
    categoria: str
    contraparte: str | None                 # cliente na venda, fornecedor na compra, a outra fazenda na transferência
    cabecas: float
    kg_vivo: float | None
    kg_carcaca: float | None
    arrobas: float | None
    rendimento_carcaca: float | None
    preco_arroba: float | None
    valor_por_cabeca: float | None
    preco_kg: float | None
    valor: float | None


class MesComparado(BaseModel):
    mes: date
    realizado: float | None                 # vazio depois do mês de referência
    previsto: float
    realizado_acumulado: float | None
    previsto_acumulado: float


class SecaoDeLotes(BaseModel):
    tipo: str                               # nascimento | compra | abate | em_pe | transf_entrada | transf_saida
    titulo: str
    lancamentos: list[LoteDoMes]
    meses: list[MesComparado]               # cabeças, mês a mês, no período inteiro
    resumo: list[LinhaDoPlacar]             # o acumulado previsto × realizado, indicador por indicador
    leitura: list[str]


class SecaoTransferencias(BaseModel):
    entradas: SecaoDeLotes
    saidas: SecaoDeLotes
    leitura: list[str]                      # entradas e saídas juntas (a das duas seções fica vazia)


class MorteDoMes(BaseModel):
    data: date
    causa: str
    local: str | None
    categoria: str
    cabecas: float
    peso_vivo_kg: float | None


class MesDaMortalidade(MesComparado):
    mortalidade: float | None               # mortes do mês ÷ rebanho médio do mês
    mortalidade_acumulada: float | None     # mortes acumuladas ÷ rebanho médio do período até o mês


class MortalidadeDoGrupo(BaseModel):
    grupo: str                              # BEZERROS | JOVENS | ADULTOS | GERAL
    previsto: float | None                  # mortes previstas ÷ rebanho médio previsto, até o mês de referência
    realizado: float | None
    meta_periodo: float | None              # o período inteiro, previsto


class CausaPorGrupo(BaseModel):
    causa: str
    bezerros: float
    jovens: float
    adultos: float
    sem_grupo: float                        # categoria ainda sem de-para
    total: float
    participacao: float | None


class SecaoMortes(BaseModel):
    lancamentos: list[MorteDoMes]
    meses: list[MesDaMortalidade]
    por_grupo: list[MortalidadeDoGrupo]
    causas: list[CausaPorGrupo]             # do período até o mês de referência
    leitura: list[str]


# --- financeiro ----------------------------------------------------------------------------------------------------


class CentroDoDesembolso(BaseModel):
    centro_custo: str
    valor_mes: float
    valor_acumulado: float
    por_cabeca_mes: float | None            # acumulado ÷ Σ rebanho médio dos meses


class SecaoFinanceiro(BaseModel):
    placar: list[LinhaDoPlacar]
    centros: list[CentroDoDesembolso]       # do maior para o menor, no acumulado
    leitura: list[str]


class SecaoCaixa(BaseModel):
    previsto_realizado: PrevistoRealizado   # o mês de referência e o acumulado, conta a conta
    leitura: list[str]


class BoletimAnalitico(BaseModel):
    mes_referencia: date
    inicio_do_periodo: date
    fim_do_periodo: date
    visao: str                              # safra | civil
    estoque: SecaoEstoque
    lotacao: SecaoLotacao
    placar_zootecnico: SecaoPlacar
    nascimentos: SecaoDeLotes
    compras: SecaoDeLotes
    vendas: list[SecaoDeLotes]              # abate e em pé
    transferencias: SecaoTransferencias
    mortes: SecaoMortes
    financeiro: SecaoFinanceiro
    caixa: SecaoCaixa
