"""Monta o boletim analítico inteiro: os recortes, o semáforo e uma seção por folha do PDF."""

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.kpis.analitico.comparar import limiar_do_semaforo
from app.kpis.analitico.compras import secao_compras
from app.kpis.analitico.estoque import secao_estoque, secao_lotacao
from app.kpis.analitico.financeiro import secao_caixa, secao_financeiro
from app.kpis.analitico.mortes import secao_mortes
from app.kpis.analitico.nascimentos import secao_nascimentos
from app.kpis.analitico.placar import secao_placar, tres_recortes
from app.kpis.analitico.recortes import recortes_do_boletim
from app.kpis.analitico.transferencias import secao_transferencias
from app.kpis.analitico.ultimo_dado import aviso_do_ultimo_dado
from app.kpis.analitico.vendas import secoes_de_vendas
from app.schemas.analitico import BoletimAnalitico


def boletim_analitico(s: Session, fazendas: list[UUID], mes_referencia: date, visao: str) -> BoletimAnalitico:
    recortes = recortes_do_boletim(fazendas, mes_referencia, visao)
    limiar = limiar_do_semaforo(s)
    aviso = aviso_do_ultimo_dado(s, recortes)
    estoque = secao_estoque(s, recortes, sem_lancamento_no_mes=aviso.todas_paradas)
    valores = tres_recortes(s, recortes)
    boletim = BoletimAnalitico(
        mes_referencia=recortes.mes_referencia, inicio_do_periodo=recortes.inicio_do_periodo,
        fim_do_periodo=recortes.fim_do_periodo, visao=visao, estoque=estoque,
        lotacao=secao_lotacao(s, recortes, estoque), placar_zootecnico=secao_placar(recortes, valores, limiar),
        nascimentos=secao_nascimentos(s, recortes, valores, limiar),
        compras=secao_compras(s, recortes, valores, limiar), vendas=secoes_de_vendas(s, recortes, valores, limiar),
        transferencias=secao_transferencias(s, recortes, valores, limiar), mortes=secao_mortes(s, recortes),
        financeiro=secao_financeiro(s, recortes, limiar), caixa=secao_caixa(s, recortes))
    abrir_com_o_aviso(boletim, aviso.frase)
    return boletim


def abrir_com_o_aviso(boletim: BoletimAnalitico, aviso: str | None) -> None:
    """O aviso vai em toda folha de rebanho, porque cada folha pode sair sozinha no PDF."""
    if aviso is None:
        return
    secoes = [boletim.estoque, boletim.lotacao, boletim.placar_zootecnico, boletim.nascimentos, boletim.compras,
              boletim.transferencias, boletim.mortes]
    secoes.extend(boletim.vendas)
    for secao in secoes:
        secao.leitura = [aviso] + secao.leitura
