"""O que o usuário pode ver: as fazendas (o RLS já filtrou), o período com dado e as capacidades de cada uma."""

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import SessaoDoUsuario, UsuarioLogado
from app.schemas.api import Capacidades, Escopo, FazendaDoEscopo, UsuarioResumo

router = APIRouter(tags=["escopo"])

# Uma linha por fazenda visível. Cada subconsulta diz se a fazenda tem aquele tipo de dado.
# O último mês vem do movimento e do rebanho informados, e não do estoque: `estoque_mensal` repete o saldo até o mês
# corrente, e um período padrão terminando ali mostraria meses zerados para quem parou de mandar dado.
FAZENDAS_VISIVEIS = """
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
           EXISTS (SELECT 1 FROM fato.orcamento_financeiro o WHERE o.fazenda_id = f.id)
             OR EXISTS (SELECT 1 FROM fato.mov_animal m WHERE m.fazenda_id = f.id AND m.cenario = 'planejado')
             AS tem_planejado
    FROM core.fazenda f
    JOIN core.cliente c ON c.id = f.cliente_id
    LEFT JOIN (SELECT fazenda_id, min(competencia) AS primeiro_mes
               FROM fato.estoque_mensal WHERE cenario = 'realizado' GROUP BY fazenda_id) estoque
           ON estoque.fazenda_id = f.id
    ORDER BY 4, f.nome
"""


@router.get("/escopo")
def escopo(s: SessaoDoUsuario, usuario: UsuarioLogado) -> Escopo:
    fazendas = []
    for linha in s.execute(text(FAZENDAS_VISIVEIS)).mappings():
        capacidades = Capacidades(estoque=linha["primeiro_mes"] is not None, rebanho_medio=linha["tem_rebanho_medio"],
                                  area=linha["tem_area"], financeiro=linha["tem_financeiro"],
                                  planejado=linha["tem_planejado"])
        fazendas.append(FazendaDoEscopo(
            id=linha["id"], nome=linha["nome"], cliente=linha["cliente"], origem=linha["origem"],
            sistema_produtivo=linha["sistema_produtivo"],
            primeiro_mes=linha["primeiro_mes"], ultimo_mes=linha["ultimo_mes"], capacidades=capacidades))
    resumo = UsuarioResumo(id=usuario.id, nome=usuario.nome, email=usuario.email, eh_admin=usuario.eh_admin)
    return Escopo(usuario=resumo, fazendas=fazendas)
