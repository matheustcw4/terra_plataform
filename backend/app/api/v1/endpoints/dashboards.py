"""Uma chamada por página do boletim: o backend agrega, o front só mostra."""

from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text

from app.api.deps import SessaoDoUsuario
from app.kpis.analitico.boletim import boletim_analitico
from app.kpis.compras import compras
from app.kpis.filtro import Filtro
from app.kpis.financeiro import financeiro
from app.kpis.mortes import mortes
from app.kpis.movimentacao import movimentacao
from app.kpis.nascimentos import nascimentos
from app.kpis.previsto_financeiro import PedidoDoPrevisto
from app.kpis.previsto_realizado import previsto_realizado
from app.kpis.transferencias import transferencias
from app.kpis.vendas import vendas
from app.schemas.analitico import BoletimAnalitico
from app.schemas.api import (
    Compras,
    Financeiro,
    Mortes,
    Movimentacao,
    Nascimentos,
    PrevistoRealizado,
    Transferencias,
    Vendas,
)

router = APIRouter(prefix="/dashboards", tags=["dashboards"])

Fazendas = Annotated[list[UUID], Query(min_length=1)]
Mes = Annotated[str, Query(description="AAAA-MM")]
Meses = Annotated[list[str] | None, Query(description="AAAA-MM, um por mês marcado no MENU (seleção múltipla); "
                                                      "sem nenhum, valem todos os meses de inicio a fim")]
# o planejado do financeiro (Previsto × Realizado e Financeiro): o tipo do orçamento e a versão; sem eles, o padrão
TipoDoPrevisto = Annotated[Literal["previsao", "planejamento"] | None,
                           Query(description="orçamento do planejado: previsão financeira ou planejamento")]
VersaoDoPrevisto = Annotated[UUID | None, Query(description="versão do plano; sem ela, a mais recente de cada "
                                                            "fazenda e safra")]


def filtro_do_pedido(s: SessaoDoUsuario, fazendas: Fazendas, inicio: Mes, fim: Mes, meses: Meses = None) -> Filtro:
    """Confere o pedido de qualquer página: meses válidos, início antes do fim, meses marcados dentro do período e
    só fazendas que o usuário vê."""
    filtro = Filtro(fazendas=fazendas, inicio=mes(inicio), fim=mes(fim), meses_escolhidos=meses_escolhidos(meses))
    if filtro.inicio > filtro.fim:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "o início do período é depois do fim")
    for escolhido in filtro.meses_escolhidos:
        if escolhido < filtro.inicio or escolhido > filtro.fim:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"mês {escolhido:%Y-%m} fora do período")
    conferir_acesso(s, fazendas)
    return filtro


FiltroDoPedido = Annotated[Filtro, Depends(filtro_do_pedido)]


@router.get("/movimentacao")
def pagina_movimentacao(s: SessaoDoUsuario, filtro: FiltroDoPedido) -> Movimentacao:
    return movimentacao(s, filtro)


@router.get("/vendas")
def pagina_vendas(s: SessaoDoUsuario, tipo: Annotated[Literal["abate", "em_pe"], Query()],
                  filtro: FiltroDoPedido) -> Vendas:
    return vendas(s, filtro, tipo)


@router.get("/compras")
def pagina_compras(s: SessaoDoUsuario, filtro: FiltroDoPedido) -> Compras:
    return compras(s, filtro)


@router.get("/nascimentos")
def pagina_nascimentos(s: SessaoDoUsuario, filtro: FiltroDoPedido) -> Nascimentos:
    return nascimentos(s, filtro)


@router.get("/mortes")
def pagina_mortes(s: SessaoDoUsuario, filtro: FiltroDoPedido) -> Mortes:
    return mortes(s, filtro)


@router.get("/transferencias")
def pagina_transferencias(s: SessaoDoUsuario, filtro: FiltroDoPedido) -> Transferencias:
    return transferencias(s, filtro)


@router.get("/financeiro")
def pagina_financeiro(s: SessaoDoUsuario, filtro: FiltroDoPedido, previsto: TipoDoPrevisto = None,
                      versao: VersaoDoPrevisto = None) -> Financeiro:
    return financeiro(s, filtro, PedidoDoPrevisto(previsto, versao))


@router.get("/previsto_realizado")
def pagina_previsto_realizado(s: SessaoDoUsuario, filtro: FiltroDoPedido, previsto: TipoDoPrevisto = None,
                              versao: VersaoDoPrevisto = None) -> PrevistoRealizado:
    return previsto_realizado(s, filtro, PedidoDoPrevisto(previsto, versao))


@router.get("/analitico")
def boletim_do_mes(s: SessaoDoUsuario, fazendas: Fazendas, mes_referencia: Mes,
                   visao: Annotated[Literal["safra", "civil"], Query()] = "safra") -> BoletimAnalitico:
    """O "Exportar PDF" no modo Analítico: o mês de referência, o acumulado do período (safra ou ano) até ele e a meta
    do período inteiro, com as frases que explicam os números."""
    conferir_acesso(s, fazendas)
    return boletim_analitico(s, fazendas, mes(mes_referencia), visao)


def meses_escolhidos(textos: list[str] | None) -> tuple[date, ...]:
    """Os meses marcados, sem repetição e em ordem."""
    return tuple(sorted({mes(texto) for texto in textos or []}))


def mes(texto: str) -> date:
    """'AAAA-MM' -> 1º dia do mês."""
    try:
        return date.fromisoformat(f"{texto}-01")
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"mês inválido: {texto} (use AAAA-MM)") from exc


def conferir_acesso(s: SessaoDoUsuario, fazendas: list[UUID]) -> None:
    """Pedir fazenda que o usuário não vê é erro (e não um painel vazio que parece dado zerado)."""
    visiveis = s.scalar(text("SELECT count(*) FROM core.fazenda WHERE id = ANY (CAST(:ids AS uuid[]))"),
                        {"ids": [str(fazenda) for fazenda in fazendas]})
    if visiveis != len(set(fazendas)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "fazenda fora do seu acesso")
