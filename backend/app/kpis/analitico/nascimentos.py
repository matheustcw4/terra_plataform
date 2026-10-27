"""Nascimentos do boletim analítico: os lançamentos do mês, as cabeças previstas × realizadas mês a mês e o resumo
por sexo (total, machos e fêmeas), com os números da página Nascimentos.
"""

from sqlalchemy.orm import Session

from app.kpis import lotes
from app.kpis.analitico import textos
from app.kpis.analitico.comparar import PrevistoERealizado, dividir, linha_do_placar
from app.kpis.analitico.lotes_do_mes import frase_da_meta, lotes_do_mes, meses_comparados
from app.kpis.analitico.placar import DoRecorte, TresRecortes
from app.kpis.analitico.recortes import Recortes
from app.schemas.analitico import LinhaDoPlacar, SecaoDeLotes

# só para listar os lançamentos e somar as cabeças do mês: nascimento não tem peso de venda nem @
NASCIMENTO = lotes.TipoDeLote(tipo_no_fato="NASCIMENTO", kg_por_arroba=30, arroba_pela_carcaca=False)
SEXOS = [("Total", "GERAL"), ("Machos", "MACHO"), ("Fêmeas", "FÊMEA")]


def secao_nascimentos(s: Session, recortes: Recortes, valores: TresRecortes, limiar: float) -> SecaoDeLotes:
    resumo = []
    for nome, sexo in SEXOS:
        meta, _ = do_sexo(valores.periodo, sexo)
        resumo.append(linha_do_placar("NASCIMENTOS", nome, "cab", "maior_melhor", do_sexo(valores.mes, sexo),
                                      do_sexo(valores.acumulado, sexo), meta, limiar))
    return SecaoDeLotes(tipo="nascimento", titulo="Nascimentos", lancamentos=lotes_do_mes(s, recortes, NASCIMENTO),
                        meses=meses_comparados(s, recortes, NASCIMENTO), resumo=resumo,
                        leitura=leitura_dos_nascimentos(recortes, resumo))


def do_sexo(recorte: DoRecorte, sexo: str) -> PrevistoERealizado:
    for quadro in recorte.nascimentos_por_sexo:
        if quadro.recorte == sexo:
            return quadro.planejado, quadro.realizado
    return None, None


def leitura_dos_nascimentos(recortes: Recortes, resumo: list[LinhaDoPlacar]) -> list[str]:
    mes = textos.mes_por_extenso(recortes.mes_referencia)
    total, machos, femeas = resumo
    realizado = total.acumulado.realizado or 0
    if realizado:
        frases = [frase_do_mes(mes, total, machos, femeas), frase_do_acumulado(mes, total, femeas)]
    else:
        frases = [f"Nenhum nascimento no período (até {mes})."]
    meta = frase_da_meta(total, realizado)
    if meta is not None:
        frases.append(meta)
    return frases


def frase_do_mes(mes: str, total: LinhaDoPlacar, machos: LinhaDoPlacar, femeas: LinhaDoPlacar) -> str:
    nascidos = total.mes.realizado or 0
    if not nascidos:
        return f"Nenhum nascimento em {mes}."
    quantos_machos = textos.contar(round(machos.mes.realizado or 0), "macho", "machos")
    quantas_femeas = textos.contar(round(femeas.mes.realizado or 0), "fêmea", "fêmeas")
    return (f"Em {mes} {textos.no_plural(nascidos, 'nasceu', 'nasceram')} {textos.cabecas(nascidos)} "
            f"({quantos_machos} e {quantas_femeas}).")


def frase_do_acumulado(mes: str, total: LinhaDoPlacar, femeas: LinhaDoPlacar) -> str:
    realizado = total.acumulado.realizado or 0
    frase = f"No acumulado até {mes}: {textos.cabecas(realizado)}"
    if total.acumulado.variacao_percentual is not None:
        frase += (f", {textos.frente_ao_previsto(total.acumulado.variacao_percentual)} "
                  f"({textos.numero(total.acumulado.previsto)})")
    parte_das_femeas = dividir(femeas.acumulado.realizado, realizado)
    if parte_das_femeas is not None:
        frase += f"; {textos.percentual(parte_das_femeas)} são fêmeas"
    return frase + "."
