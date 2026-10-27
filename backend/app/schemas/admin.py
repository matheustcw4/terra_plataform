"""Formato das telas de administração: de-paras de categoria e de contas, usuários, funções, acesso às fazendas e o
"Atualizar agora"."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# --- de-para de categorias -----------------------------------------------------------------------------------------


class OpcaoDeCategoria(BaseModel):
    id: int
    nome: str
    sexo: str
    grupo: str


class CategoriaDeOrigem(BaseModel):
    """Uma categoria como a fonte escreve, numa fazenda (planilha) ou num cliente (Metryx), e a categoria BI dela."""
    id: UUID
    fonte: str
    cliente: str | None
    fazenda: str | None                     # vazio: vale para todas as fazendas do cliente
    nome_origem: str
    categoria_bi_id: int | None             # vazio = pendente (fora do estoque e do rebanho médio)
    categoria_bi_sugerida_id: int | None    # o que a fonte sugere, quando ela não confirma
    lancamentos: int                        # movimentações, saldos e rebanho médio que usam este de-para
    confirmado_por: str | None
    confirmado_em: datetime | None


class CategoriasDeOrigem(BaseModel):
    pendentes: int                          # no banco inteiro, não só na lista
    opcoes: list[OpcaoDeCategoria]
    itens: list[CategoriaDeOrigem]          # até 500: pendentes primeiro


class PedidoDeCategoria(BaseModel):
    categoria_bi_id: int | None             # vazio volta o de-para para pendente


# --- de-para de contas ---------------------------------------------------------------------------------------------


class OpcaoDeConta(BaseModel):
    id: int
    nome: str
    classificacao: str


class ContaDeOrigem(BaseModel):
    """Uma conta (centro e subcentro) como a fonte escreve, e o centro de custo do plano unificado."""
    id: UUID
    fonte: str
    centro: str
    subcentro: str | None
    centro_custo_id: int | None             # vazio = "A classificar" no DRE
    lancamentos: int                        # lançamentos realizados com esta conta
    orcamentos: int                         # linhas de orçamento com esta conta
    valor: float                            # R$ dos lançamentos realizados
    fazendas: int                           # em quantas fazendas a conta aparece
    confirmado_por: str | None
    confirmado_em: datetime | None


class ContasDeOrigem(BaseModel):
    pendentes: int
    opcoes: list[OpcaoDeConta]
    itens: list[ContaDeOrigem]              # até 500: "A classificar" primeiro, depois as de maior valor


class PedidoDeConta(BaseModel):
    centro_custo_id: int | None             # vazio volta a conta para "A classificar"


# --- usuários e acesso -------------------------------------------------------------------------------------------


class UsuarioDoAdmin(BaseModel):
    id: UUID
    nome: str
    email: str
    funcao_id: int | None                   # usuário criado antes do cadastro de funções fica sem até o admin escolher
    funcao: str | None
    eh_admin: bool
    ativo: bool
    fazendas: int                           # quantas fazendas o usuário vê (o admin vê todas)
    criado_em: datetime


class NovoUsuario(BaseModel):
    nome: str = Field(min_length=1)
    email: str = Field(min_length=3)
    senha: str = Field(min_length=8)       # só o hash (argon2) é gravado
    funcao_id: int                          # uma função ativa do cadastro de funções
    eh_admin: bool = False


class AlteracaoDeUsuario(BaseModel):
    """Só os campos enviados mudam."""
    nome: str | None = Field(default=None, min_length=1)
    funcao_id: int | None = None
    eh_admin: bool | None = None
    ativo: bool | None = None
    senha: str | None = Field(default=None, min_length=8)


class FazendaDoAcesso(BaseModel):
    id: UUID
    nome: str
    cliente: str
    origem: str | None                      # TEMPORÁRIO, como no escopo: planilha | metryx (até a Q9)
    tem_acesso: bool


class PedidoDeAcesso(BaseModel):
    fazendas: list[UUID]                    # a lista completa: o que não estiver nela perde o acesso


# --- cadastro de funções -------------------------------------------------------------------------------------------


class Funcao(BaseModel):
    id: int
    nome: str
    ativo: bool                             # inativa: some do cadastro de usuário novo, fica em quem já a tem
    usuarios: int                           # quantos usuários têm esta função (com algum, não se apaga)


class NovaFuncao(BaseModel):
    nome: str = Field(min_length=1, max_length=80)


class AlteracaoDeFuncao(BaseModel):
    """Só os campos enviados mudam."""
    nome: str | None = Field(default=None, min_length=1, max_length=80)
    ativo: bool | None = None


# --- atualizar agora -----------------------------------------------------------------------------------------------


class CargaRecente(BaseModel):
    fonte: str                              # "planilha" ou "metryx"
    status: str                             # processando, concluido, concluido_com_avisos...
    iniciado_em: datetime | None
    finalizado_em: datetime | None


class SituacaoDaAtualizacao(BaseModel):
    rodando: bool                           # alguma carga está com a trava agora (da agenda ou pedida)
    agora: datetime                         # o relógio do banco, para a tela comparar com o pedido
    ultima: CargaRecente | None             # a carga mais recente, de qualquer fonte


class PedidoDeAtualizacao(BaseModel):
    pedida_em: datetime                     # relógio do banco: a carga que começar depois disto é a pedida
