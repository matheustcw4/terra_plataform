"""O que o usuário pode ver: as fazendas (o RLS já filtrou), o período com dado e as capacidades de cada uma."""

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import SessaoDoUsuario, UsuarioLogado
from app.schemas.api import Capacidades, Escopo, FazendaDoEscopo, OpcoesDoFinanceiro, UsuarioResumo

router = APIRouter(tags=["escopo"])

# As opções dos filtros do financeiro de cada fazenda numa passada só pelas views (uma subconsulta por fazenda levava
# dez vezes mais): os tipos de atividade na ordem da dimensão, as classificações na ordem do DRE (pelo grupo; "A
# classificar" por último) e as contas bancárias pelo nome. O RLS das views já deixa só as fazendas do usuário.
OPCOES_DO_FINANCEIRO = """
    WITH linhas_do_financeiro AS (
        SELECT fazenda_id, tipo_atividade, classificacao_analitica, min(classificacao) AS grupo
        FROM fato.v_lancamento_financeiro GROUP BY 1, 2, 3
        UNION ALL
        SELECT fazenda_id, tipo_atividade, classificacao_analitica, min(classificacao)
        FROM fato.v_orcamento_financeiro GROUP BY 1, 2, 3
    ), tipos AS (
        SELECT tipo.fazenda_id,
               array_agg(tipo.tipo_atividade ORDER BY tipo.ordem NULLS LAST, tipo.tipo_atividade) AS tipos_de_atividade
        FROM (SELECT DISTINCT linha.fazenda_id, linha.tipo_atividade, ta.ordem
              FROM linhas_do_financeiro linha
              LEFT JOIN dim.tipo_atividade ta ON ta.nome = linha.tipo_atividade) tipo
        GROUP BY tipo.fazenda_id
    ), classificacoes AS (
        SELECT opcao.fazenda_id,
               array_agg(opcao.classificacao_analitica
                         ORDER BY opcao.grupo = 'A CLASSIFICAR', opcao.grupo, opcao.classificacao_analitica)
                   AS classificacoes
        FROM (SELECT fazenda_id, classificacao_analitica, min(grupo) AS grupo
              FROM linhas_do_financeiro GROUP BY 1, 2) opcao
        GROUP BY opcao.fazenda_id
    ), ordem_das_opcoes AS (
        -- a ordem de todas as opções, para a tela juntar as de várias fazendas sem embaralhar
        SELECT (SELECT array_agg(tipo.tipo_atividade ORDER BY tipo.ordem NULLS LAST, tipo.tipo_atividade)
                FROM (SELECT DISTINCT linha.tipo_atividade, ta.ordem
                      FROM linhas_do_financeiro linha
                      LEFT JOIN dim.tipo_atividade ta ON ta.nome = linha.tipo_atividade) tipo) AS tipos_de_atividade,
               (SELECT array_agg(opcao.classificacao_analitica
                                 ORDER BY opcao.grupo = 'A CLASSIFICAR', opcao.grupo, opcao.classificacao_analitica)
                FROM (SELECT classificacao_analitica, min(grupo) AS grupo
                      FROM linhas_do_financeiro GROUP BY 1) opcao) AS classificacoes
    ), contas AS (
        SELECT uso.fazenda_id,
               jsonb_agg(jsonb_build_object('id', cb.id, 'nome', cb.nome) ORDER BY cb.nome) AS contas_bancarias
        FROM (SELECT DISTINCT fazenda_id, conta_bancaria_id FROM fato.lancamento_financeiro
              WHERE conta_bancaria_id IS NOT NULL) uso
        JOIN dim.conta_bancaria cb ON cb.id = uso.conta_bancaria_id
        GROUP BY uso.fazenda_id
    )
"""

# Uma linha por fazenda visível. Cada subconsulta diz se a fazenda tem aquele tipo de dado.
# O último mês vem do movimento e do rebanho informados, e não do estoque: `estoque_mensal` repete o saldo até o mês
# corrente, e um período padrão terminando ali mostraria meses zerados para quem parou de mandar dado.
FAZENDAS_VISIVEIS = OPCOES_DO_FINANCEIRO + """
    SELECT f.id, f.nome, f.sistema_produtivo,
           -- o cliente que o usuário escolhe no menu: o proprietário da fazenda (na planilha, a coluna PROPRIETÁRIO;
           -- no Metryx, o customer); sem proprietário informado, o nome do cliente no cadastro
           coalesce(nullif(btrim(f.proprietario), ''), c.nome) AS cliente,
           -- TEMPORÁRIO (pedido do usuário, 15/10/2026): a fonte que alimenta o rebanho da fazenda, só para o filtro
           -- "Origem" do MENU enquanto o mesmo cliente nas duas fontes não tem de-para (Q9). Nenhum cálculo usa isto.
           (SELECT ff.fonte FROM core.fazenda_fonte ff
            WHERE ff.fazenda_id = f.id AND ff.dominio = 'pecuario_realizado') AS origem,
           estoque.primeiro_mes,
           GREATEST((SELECT max(m.competencia) FROM fato.mov_animal m
                     WHERE m.fazenda_id = f.id AND m.cenario = 'realizado'),
                    (SELECT max(r.competencia) FROM fato.rebanho_medio_mensal r
                     WHERE r.fazenda_id = f.id AND r.cenario = 'realizado' AND r.qtd_cab > 0)) AS ultimo_mes,
           EXISTS (SELECT 1 FROM fato.rebanho_medio_mensal r
                   WHERE r.fazenda_id = f.id AND r.cenario = 'realizado') AS tem_rebanho_medio,
           EXISTS (SELECT 1 FROM fato.area_mensal a WHERE a.fazenda_id = f.id AND a.cenario = 'realizado') AS tem_area,
           EXISTS (SELECT 1 FROM fato.lancamento_financeiro l WHERE l.fazenda_id = f.id) AS tem_financeiro,
           -- as situações dos títulos que a fazenda tem (o MENU só mostra o filtro de status quando há o que escolher)
           ARRAY(SELECT DISTINCT l.situacao FROM fato.lancamento_financeiro l WHERE l.fazenda_id = f.id
                 ORDER BY 1) AS situacoes,
           coalesce(tipos.tipos_de_atividade, '{}') AS tipos_de_atividade,
           coalesce(classificacoes.classificacoes, '{}') AS classificacoes,
           coalesce(contas.contas_bancarias, '[]'::jsonb) AS contas_bancarias,
           coalesce(ordem_das_opcoes.tipos_de_atividade, '{}') AS ordem_dos_tipos,
           coalesce(ordem_das_opcoes.classificacoes, '{}') AS ordem_das_classificacoes,
           EXISTS (SELECT 1 FROM fato.orcamento_financeiro o WHERE o.fazenda_id = f.id)
             OR EXISTS (SELECT 1 FROM fato.mov_animal m WHERE m.fazenda_id = f.id AND m.cenario = 'planejado')
             AS tem_planejado
    FROM core.fazenda f
    JOIN core.cliente c ON c.id = f.cliente_id
    LEFT JOIN (SELECT fazenda_id, min(competencia) AS primeiro_mes
               FROM fato.estoque_mensal WHERE cenario = 'realizado' GROUP BY fazenda_id) estoque
           ON estoque.fazenda_id = f.id
    LEFT JOIN tipos ON tipos.fazenda_id = f.id
    LEFT JOIN classificacoes ON classificacoes.fazenda_id = f.id
    LEFT JOIN contas ON contas.fazenda_id = f.id
    CROSS JOIN ordem_das_opcoes
    ORDER BY 4, f.nome
"""


@router.get("/escopo")
def escopo(s: SessaoDoUsuario, usuario: UsuarioLogado) -> Escopo:
    fazendas = []
    linhas = s.execute(text(FAZENDAS_VISIVEIS)).mappings().all()
    for linha in linhas:
        capacidades = Capacidades(estoque=linha["primeiro_mes"] is not None, rebanho_medio=linha["tem_rebanho_medio"],
                                  area=linha["tem_area"], financeiro=linha["tem_financeiro"],
                                  planejado=linha["tem_planejado"], situacoes=linha["situacoes"],
                                  tipos_de_atividade=linha["tipos_de_atividade"],
                                  classificacoes=linha["classificacoes"], contas_bancarias=linha["contas_bancarias"])
        fazendas.append(FazendaDoEscopo(
            id=linha["id"], nome=linha["nome"], cliente=linha["cliente"], origem=linha["origem"],
            sistema_produtivo=linha["sistema_produtivo"],
            primeiro_mes=linha["primeiro_mes"], ultimo_mes=linha["ultimo_mes"], capacidades=capacidades))
    resumo = UsuarioResumo(id=usuario.id, nome=usuario.nome, email=usuario.email, eh_admin=usuario.eh_admin)
    return Escopo(usuario=resumo, fazendas=fazendas, opcoes_do_financeiro=ordem_das_opcoes(linhas))


def ordem_das_opcoes(linhas: list) -> OpcoesDoFinanceiro:
    """A mesma em todas as linhas; sem fazenda visível, nenhuma opção."""
    if not linhas:
        return OpcoesDoFinanceiro()
    primeira = linhas[0]
    return OpcoesDoFinanceiro(tipos_de_atividade=primeira["ordem_dos_tipos"],
                              classificacoes=primeira["ordem_das_classificacoes"])
