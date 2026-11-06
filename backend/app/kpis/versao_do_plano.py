"""A versão do planejamento que entra nas metas de animais e no rebanho médio previsto (pedido do usuário, 04/11/2026).

O Metryx guarda várias versões do plano por fazenda e safra, e a carga traz todas. Em cada fazenda e safra (jul a jun)
entra uma só, para não somar versões do mesmo plano (o BI soma todas): a escolhida na tela (parâmetro `versao`, que
vem no recorte de toda página), se ela tem planejado ali; senão, a mais recente. Quem decide é a função
`app.versoes_do_planejado` (migração 0019); aqui ficam a condição que os KPIs põem no WHERE e as opções que a tela
mostra. O orçamento do planejamento segue a mesma escolha (previsto_financeiro.py).
"""

from collections import defaultdict
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.kpis.filtro import Filtro, meses_do_filtro
from app.schemas.api import EscolhaDaVersao, VersaoDoPrevisto

VERSOES_COM_PLANEJADO = """
    SELECT p.fazenda_id, f.nome AS fazenda, p.versao_plano_id AS id, vp.nome, vp.ordem
    FROM (
        SELECT m.fazenda_id, m.versao_plano_id FROM fato.mov_animal m
        WHERE m.cenario = 'planejado' AND m.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
          AND m.competencia = ANY (CAST(:meses AS date[]))
        UNION
        SELECT r.fazenda_id, r.versao_plano_id FROM fato.rebanho_medio_mensal r
        WHERE r.cenario = 'planejado' AND r.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
          AND r.competencia = ANY (CAST(:meses AS date[]))
    ) p
    JOIN dim.versao_plano vp ON vp.id = p.versao_plano_id
    JOIN core.fazenda f ON f.id = p.fazenda_id
    ORDER BY f.nome, vp.ordem DESC NULLS LAST, vp.nome
"""
VERSOES_EM_USO = """
    SELECT DISTINCT f.nome AS fazenda, vp.nome, vp.ordem
    FROM app.versoes_do_planejado(CAST(:fazendas AS uuid[]), CAST(:versao_do_plano AS uuid)) v
    JOIN dim.versao_plano vp ON vp.id = v.versao_plano_id
    JOIN core.fazenda f ON f.id = v.fazenda_id
    WHERE v.safra = ANY (CAST(:safras AS integer[]))
    ORDER BY f.nome, vp.ordem DESC NULLS LAST, vp.nome
"""


def so_a_versao_que_vale(apelido: str) -> str:
    """Condição de WHERE para `fato.mov_animal` ou `fato.rebanho_medio_mensal` com o apelido dado: o realizado passa
    inteiro; do planejado, só a versão que vale na fazenda e na safra da linha."""
    return (f"({apelido}.cenario = 'realizado' OR ({apelido}.fazenda_id, "
            f"extract(year FROM {apelido}.competencia - interval '6 months')::integer, {apelido}.versao_plano_id) IN "
            "(SELECT * FROM app.versoes_do_planejado(CAST(:fazendas AS uuid[]), CAST(:versao_do_plano AS uuid))))")


def escolha_da_versao(s: Session, filtro: Filtro) -> EscolhaDaVersao:
    """As versões com meta nos meses do filtro, a escolhida e as que estão valendo."""
    linhas = list(s.execute(text(VERSOES_COM_PLANEJADO), filtro.parametros()).mappings())
    versoes = versoes_para_escolher(linhas, len(filtro.fazendas) > 1)
    versao = None
    if filtro.versao_do_plano in {versao_da_lista.id for versao_da_lista in versoes}:
        versao = filtro.versao_do_plano
    return EscolhaDaVersao(versoes=versoes, versao=versao, em_uso=versoes_em_uso(s, filtro))


def versoes_para_escolher(linhas: list, varias_fazendas: bool) -> list[VersaoDoPrevisto]:
    """Das linhas (fazenda_id, fazenda, id, nome), em ordem, as versões das fazendas que têm mais de uma: nas outras
    não há o que escolher."""
    por_fazenda: dict = defaultdict(set)
    for linha in linhas:
        por_fazenda[linha["fazenda_id"]].add(linha["id"])
    versoes = []
    vistas = set()
    for linha in linhas:
        if len(por_fazenda[linha["fazenda_id"]]) < 2 or linha["id"] in vistas:
            continue
        vistas.add(linha["id"])
        rotulo = rotulo_da_versao(linha["fazenda"], linha["nome"], varias_fazendas)
        versoes.append(VersaoDoPrevisto(id=linha["id"], rotulo=rotulo))
    return versoes


def versoes_em_uso(s: Session, filtro: Filtro) -> list[str]:
    parametros = filtro.parametros() | {"safras": safras_do_filtro(filtro)}
    varias_fazendas = len(filtro.fazendas) > 1
    rotulos = []
    for linha in s.execute(text(VERSOES_EM_USO), parametros).mappings():
        rotulo = rotulo_da_versao(linha["fazenda"], linha["nome"], varias_fazendas)
        if rotulo not in rotulos:
            rotulos.append(rotulo)
    return rotulos


def safras_do_filtro(filtro: Filtro) -> list[int]:
    """As safras (ano em que começam) que os meses do filtro tocam."""
    safras = []
    for mes in meses_do_filtro(filtro):
        safra = safra_do_mes(mes)
        if safra not in safras:
            safras.append(safra)
    return safras


def safra_do_mes(mes: date) -> int:
    if mes.month >= 7:
        return mes.year
    return mes.year - 1


def rotulo_da_versao(fazenda: str, nome: str | None, varias_fazendas: bool) -> str:
    """O nome da versão; com mais de uma fazenda no filtro, "fazenda · nome" (o número da versão é de cada fazenda)."""
    rotulo = nome or "Sem nome"
    if varias_fazendas:
        return f"{fazenda} · {rotulo}"
    return rotulo
