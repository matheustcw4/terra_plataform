"""A versão do planejamento que entra nas metas de animais e no rebanho médio previsto (pedido do usuário, 04/11/2026).

O Metryx guarda várias versões do plano por fazenda e safra, e a carga traz todas. Sem escolha, em cada fazenda e
safra (jul a jun) entra só a mais recente, para não somar versões do mesmo plano (o BI soma todas). A tela escolhe por
fazenda, de seleção múltipla (pedido do usuário, 10/11/2026; parâmetros `versao` e `sem_plano`, que vêm no recorte de
toda página): na fazenda com versões marcadas, entram todas as marcadas, somadas (decisão do usuário); na marcada
"nenhum planejamento", nada do planejado. Quem decide é a função `app.versoes_do_planejado` (migrações 0019 e 0025);
aqui ficam a condição que os KPIs põem no WHERE e as opções que a tela mostra, por fazenda. O orçamento segue a mesma
escolha (`app.versoes_do_orcamento`, previsto_financeiro.py).
"""

from collections import defaultdict
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.kpis.filtro import Filtro, meses_do_filtro
from app.schemas.api import EscolhaDaVersao, VersaoDoPrevisto, VersoesDaFazenda

# as versões com meta (de animais ou de rebanho médio) nos meses do filtro
VERSOES_DAS_METAS = """
    SELECT m.fazenda_id, m.versao_plano_id FROM fato.mov_animal m
    WHERE m.cenario = 'planejado' AND m.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
      AND m.competencia = ANY (CAST(:meses AS date[]))
    UNION
    SELECT r.fazenda_id, r.versao_plano_id FROM fato.rebanho_medio_mensal r
    WHERE r.cenario = 'planejado' AND r.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
      AND r.competencia = ANY (CAST(:meses AS date[]))
"""
# as versões do orçamento do planejamento nos meses do filtro (são as mesmas versões do plano de cada fazenda)
VERSOES_DO_ORCAMENTO = """
    SELECT o.fazenda_id, o.versao_plano_id FROM fato.orcamento_financeiro o
    WHERE o.tipo = 'planejamento' AND o.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
      AND o.competencia = ANY (CAST(:meses AS date[]))
"""
# Todas as fazendas do filtro, com as versões do plano de cada uma nos meses (das metas e do orçamento do
# planejamento: a escolha vale nas duas); a fazenda sem plano no período vem numa linha só, sem versão.
VERSOES_POR_FAZENDA = f"""
    SELECT f.id AS fazenda_id, f.nome AS fazenda, vp.id, vp.nome, vp.ordem
    FROM core.fazenda f
    LEFT JOIN ({VERSOES_DAS_METAS} UNION {VERSOES_DO_ORCAMENTO}) p ON p.fazenda_id = f.id
    LEFT JOIN dim.versao_plano vp ON vp.id = p.versao_plano_id
    WHERE f.id = ANY (CAST(:fazendas AS uuid[]))
    ORDER BY f.nome, vp.ordem DESC NULLS LAST, vp.nome
"""
VERSOES_EM_USO = """
    SELECT DISTINCT f.nome AS fazenda, vp.nome, vp.ordem
    FROM app.versoes_do_planejado(CAST(:fazendas AS uuid[]), CAST(:versoes_do_plano AS uuid[]),
                                  CAST(:fazendas_sem_plano AS uuid[])) v
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
            "(SELECT * FROM app.versoes_do_planejado(CAST(:fazendas AS uuid[]), "
            "CAST(:versoes_do_plano AS uuid[]), CAST(:fazendas_sem_plano AS uuid[]))))")


def escolha_da_versao(s: Session, filtro: Filtro) -> EscolhaDaVersao:
    """As versões de cada fazenda do filtro, a escolhida em cada uma e as que estão valendo nas metas."""
    return EscolhaDaVersao(fazendas=versoes_por_fazenda(s, filtro), em_uso=versoes_em_uso(s, filtro))


def versoes_por_fazenda(s: Session, filtro: Filtro) -> list[VersoesDaFazenda]:
    """Todas as fazendas do filtro, em ordem, com as versões do plano no período (da mais recente para a mais antiga;
    nenhuma = sem plano), as marcadas de cada uma e se ela foi marcada "nenhum planejamento" (pedido do usuário,
    10/11/2026). A tela lista todas, para mostrar o que vale em cada fazenda."""
    nome_da_fazenda: dict = {}
    versoes_da_fazenda: dict = defaultdict(list)
    for linha in s.execute(text(VERSOES_POR_FAZENDA), filtro.parametros()).mappings():
        nome_da_fazenda[linha["fazenda_id"]] = linha["fazenda"]
        versoes = versoes_da_fazenda[linha["fazenda_id"]]
        if linha["id"] is not None and linha["id"] not in {versao.id for versao in versoes}:
            versoes.append(VersaoDoPrevisto(id=linha["id"], rotulo=linha["nome"] or "Sem nome"))
    fazendas = []
    for fazenda_id, nome in nome_da_fazenda.items():
        versoes = versoes_da_fazenda[fazenda_id]
        marcadas = [versao.id for versao in versoes if versao.id in filtro.versoes_do_plano]
        fazendas.append(VersoesDaFazenda(fazenda_id=fazenda_id, fazenda=nome, versoes=versoes, escolhidas=marcadas,
                                         sem_plano=fazenda_id in filtro.fazendas_sem_plano))
    return fazendas


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
