"""API: login, escopo (RLS por usuário) e a página Movimentação do Gado, sobre a planilha sintética.

Números esperados da fazenda sintética (doc 01 §5.1): saldo em 30/06/2025 = 1.000 bezerros + 500 vacas; em julho
+120 nascimentos, −5 mortes, 300 desmamados (bezerro -> desmama macho); em agosto, 10 vacas vendidas em pé;
rebanho médio de julho 1.550 cab e área de 1.000 ha.
"""

from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.seguranca import hash_da_senha
from app.etl.adapters.planilha.adapter import AdapterPlanilha
from app.etl.pipeline import MotorCarga
from tests.conftest import como_usuario, criar_usuario
from tests.sinteticos import gerar_planilha

SENHA = "senha-de-teste"


@pytest.fixture
def fazenda(engine_etl, engine_super, tmp_path):
    return carregar_planilha(engine_etl, engine_super, tmp_path)


# Vendas para abate além da venda em pé padrão (10 vacas em 08/2025, 4.500 kg, R$ 30.000):
# 08/2025: 20 machos, 10.000 kg vivos, 5.400 kg de carcaça (360 @), R$ 115.200 (R$ 320/@);
# 09/2025: 10 vacas, 4.000 kg vivos, 1.950 kg de carcaça (130 @), R$ 39.000 (R$ 300/@);
# meta de 08/2025: 25 machos, 12.500 kg vivos, 6.750 kg de carcaça (450 @), R$ 139.500 (R$ 310/@).
ABATES = [["ABATE", "Frigorífico", "Desmama Macho", datetime(2025, 8, 10), 20, None, 500, None, None, None, 115200,
           10000, 5400],
          ["ABATE", "Frigorífico", "Vaca", datetime(2025, 9, 10), 10, None, 400, None, None, None, 39000, 4000, 1950]]
META_DE_ABATE = [["ABATE", "Frigorífico", "Desmama Macho", datetime(2025, 8, 1), 25, None, 500, None, None, None,
                  139500, 12500, 6750]]


@pytest.fixture
def fazenda_com_vendas(engine_etl, engine_super, tmp_path):
    return carregar_planilha(engine_etl, engine_super, tmp_path,
                             linhas={"fAbate": ABATES, "fAbatePLANEJADO": META_DE_ABATE})


# Compras: 08/2025, 50 machos de 200 kg por R$ 120.000 (R$ 12/kg, 333,3 @ a R$ 360); 09/2025, 20 vacas de 400 kg por
# R$ 72.000 (R$ 9/kg, 266,7 @ a R$ 270); meta de 08/2025: 60 machos, 12.000 kg, R$ 150.000.
COMPRAS = [["COMPRA", datetime(2025, 8, 3), "Leilão", "Desmama Macho", 50, 200, 10000, None, 120000],
           ["COMPRA", datetime(2025, 9, 3), "Leilão", "Vaca", 20, 400, 8000, None, 72000]]
META_DE_COMPRA = [["COMPRA", datetime(2025, 8, 1), "Leilão", "Desmama Macho", 60, 200, 12000, None, 150000]]


@pytest.fixture
def fazenda_com_compras(engine_etl, engine_super, tmp_path):
    return carregar_planilha(engine_etl, engine_super, tmp_path,
                             linhas={"fAbate": ABATES, "fAbatePLANEJADO": META_DE_ABATE, "fCompras": COMPRAS,
                                     "fComprasPLANEJADO": META_DE_COMPRA})


# Nascimentos, mortes e transferências além do padrão (07/2025: 120 bezerros nascidos, 5 mortos por cobra):
# 08/2025: 80 bezerras nascidas; morrem 2 vacas (raio) e 1 bezerra (" cobra ", a mesma causa); entram 30 machos
# de 200 kg por R$ 60.000 (200 @, R$ 300/@); 09/2025: saem 10 vacas de 400 kg por R$ 30.000 (133,3 @, R$ 225/@).
# Metas: 100 machos nascidos em 07/2025 e 100 fêmeas em 08/2025; 4 bezerros mortos em 07/2025.
CATEGORIAS_DE_CRIA = (("Bezerra Mamando", "BEZERRA", None),)
NASCIMENTOS = [["NASCIMENTO", datetime(2025, 7, 10), "Bezerro Mamando", 120, "25/26", 32],
               ["NASCIMENTO", datetime(2025, 8, 8), "Bezerra Mamando", 80, "25/26", 30]]
META_DE_NASCIMENTOS = [["NASCIMENTO", datetime(2025, 7, 1), "Bezerro Mamando", 100, "25/26", None],
                       ["NASCIMENTO", datetime(2025, 8, 1), "Bezerra Mamando", 100, "25/26", None]]
MORTES = [["MORTE", datetime(2025, 7, 12), "Bezerro Mamando", None, 5, "Cobra", "Pasto 1", 40, "25/26"],
          ["MORTE", datetime(2025, 8, 15), "Vaca", None, 2, "Raio", "Pasto 2", 450, "25/26"],
          ["MORTE", datetime(2025, 8, 20), "Bezerra Mamando", None, 1, " cobra ", "Pasto 1", 35, "25/26"]]
META_DE_MORTES = [["MORTE", datetime(2025, 7, 1), "Bezerro Mamando", None, 4, None, None, None, "25/26"]]
TRANSFERENCIAS_DE_ENTRADA = [["TRANSF. ENTRADA", datetime(2025, 8, 12), "Desmama Macho", 30, 200, 6000, 60000]]
TRANSFERENCIAS_DE_SAIDA = [["TRANSF. SAIDA", datetime(2025, 9, 12), "Vaca", 10, 400, 4000, 30000]]


@pytest.fixture
def fazenda_com_rebanho_movimentado(engine_etl, engine_super, tmp_path):
    linhas = {"fNascimento": NASCIMENTOS, "fNascimentoPLANEJADO": META_DE_NASCIMENTOS, "fMortes": MORTES,
              "fMortesPLANEJADO": META_DE_MORTES, "ftranfentrada": TRANSFERENCIAS_DE_ENTRADA,
              "ftranssaida": TRANSFERENCIAS_DE_SAIDA}
    return carregar_planilha(engine_etl, engine_super, tmp_path, linhas=linhas,
                             categorias_extras=CATEGORIAS_DE_CRIA)


# DRE (classificação das contas pela dim.centro_custo): 07/2025, adubo de R$ 1.500,50 com estorno de R$ 500,50 (o
# valor negativo vira crédito e abate o desembolso e o custeio); 08/2025, venda de gado de R$ 30.000 (receita da
# pecuária), arrendamento de R$ 5.000 (outra receita) e compra de gado de R$ 50.000 (desembolso, não custeio);
# 09/2025, dividendos de R$ 3.000 (despesa, fora do desembolso). Metas: adubo de R$ 2.000 em 07/2025 e venda de gado
# de R$ 25.000 em 08/2025; rebanho planejado de 1.600 cabeças em 07/2025 (o realizado é 1.550).
DRE = [["PASTO", "ADUBO", 1500.5, datetime(2025, 7, 15), "D", "Pastagens", "Adubação"],
       ["PASTO", "ADUBO", -500.5, datetime(2025, 7, 20), "D", "Pastagens", "Adubação"],
       ["REBANHO", "VENDA", 30000, datetime(2025, 8, 5), "C", "Rebanho", "Venda de gado"],
       ["ARRENDAMENTO", "PASTO", 5000, datetime(2025, 8, 6), "C", "Arrendamento", "Arrendamento"],
       ["REBANHO INVESTIMENTO", "COMPRA", 50000, datetime(2025, 8, 7), "D", "Rebanho Investimento", "Compra"],
       ["DIVIDENDOS", "SOCIOS", 3000, datetime(2025, 9, 8), "D", "Dividendos", "Dividendos"]]
META_DO_DRE = [["PASTO", "ADUBO", 2000, datetime(2025, 7, 1), "D", "Pastagens", "Adubação"],
               ["REBANHO", "VENDA", 25000, datetime(2025, 8, 1), "C", "Rebanho", "Venda de gado"]]
REBANHO_PLANEJADO = [["Bezerros", 1100, None, datetime(2025, 7, 1)], ["Adultos", 500, None, datetime(2025, 7, 1)]]


@pytest.fixture
def fazenda_com_financeiro(engine_etl, engine_super, tmp_path):
    linhas = {"fDre": DRE, "fDrePLANEJADO": META_DO_DRE, "fRebanhoMedioPLANEJADO": REBANHO_PLANEJADO,
              "fAbate": ABATES, "fAbatePLANEJADO": META_DE_ABATE}
    return carregar_planilha(engine_etl, engine_super, tmp_path, linhas=linhas)


def carregar_planilha(engine_etl, engine_super, pasta, linhas=None, categorias_extras=()):
    gerar_planilha(pasta, linhas=linhas, categorias_extras=categorias_extras)
    MotorCarga(engine_etl, hoje=date(2025, 10, 1), estoque_ate=date(2025, 9, 1)).executar(
        AdapterPlanilha(pasta, estabilidade_s=0))
    with engine_super.connect() as c:
        return c.execute(text("SELECT entidade_id FROM core.fonte_vinculo WHERE entidade = 'fazenda'")).scalar_one()


def usuario_com_senha(engine_super, email: str, **kw):
    usuario_id = criar_usuario(engine_super, email, **kw)
    with engine_super.begin() as c:
        c.execute(text("UPDATE core.usuario SET senha_hash = :h WHERE id = :u"),
                  {"h": hash_da_senha(SENHA), "u": usuario_id})
    return usuario_id


def entrar(api: TestClient, email: str) -> dict:
    resposta = api.post("/api/v1/auth/login", json={"email": email, "senha": SENHA})
    assert resposta.status_code == 200, resposta.text
    return {"Authorization": f"Bearer {resposta.json()['token']}"}


def test_raiz_explica_onde_esta_o_painel(api):
    resposta = api.get("/")
    assert resposta.status_code == 200
    assert "/docs" in resposta.json()["mensagem"]


def test_login(api, engine_super):
    usuario_com_senha(engine_super, "consultor@terra.test")
    assert api.post("/api/v1/auth/login", json={"email": "consultor@terra.test", "senha": "errada"}).status_code == 401
    assert api.post("/api/v1/auth/login", json={"email": "ninguem@terra.test", "senha": SENHA}).status_code == 401
    cabecalho = entrar(api, " Consultor@Terra.test ")              # e-mail sem diferenciar maiúscula/espaço
    assert api.get("/api/v1/auth/me", headers=cabecalho).json()["email"] == "consultor@terra.test"
    assert api.get("/api/v1/auth/me").status_code == 401
    assert api.get("/api/v1/auth/me", headers={"Authorization": "Bearer adulterado"}).status_code == 401


def test_usuario_desativado_perde_o_acesso_na_hora(api, engine_super):
    usuario_id = usuario_com_senha(engine_super, "consultor@terra.test")
    cabecalho = entrar(api, "consultor@terra.test")
    with engine_super.begin() as c:
        c.execute(text("UPDATE core.usuario SET ativo = false WHERE id = :u"), {"u": usuario_id})
    assert api.get("/api/v1/escopo", headers=cabecalho).status_code == 401


def test_escopo_mostra_so_as_fazendas_do_usuario(api, engine_super, fazenda):
    usuario_com_senha(engine_super, "consultor@terra.test", fazendas=[fazenda])
    usuario_com_senha(engine_super, "outro@terra.test")
    usuario_com_senha(engine_super, "admin@terra.test", admin=True)
    escopo = api.get("/api/v1/escopo", headers=entrar(api, "consultor@terra.test")).json()
    [unica] = escopo["fazendas"]
    assert unica["nome"] == "TESTE" and unica["primeiro_mes"] == "2025-06-01"
    assert unica["cliente"] == "FULANO DE TAL"                   # o PROPRIETÁRIO do fUnidade, não o projeto
    assert unica["origem"] == "planilha"                         # filtro temporário "Origem" do MENU
    assert unica["ultimo_mes"] == "2025-08-01"            # último movimento; o saldo repetido até 09/2025 não conta
    assert unica["capacidades"] == {"estoque": True, "rebanho_medio": True, "area": True, "financeiro": True,
                                    "planejado": False}
    assert api.get("/api/v1/escopo", headers=entrar(api, "outro@terra.test")).json()["fazendas"] == []
    assert len(api.get("/api/v1/escopo", headers=entrar(api, "admin@terra.test")).json()["fazendas"]) == 1


def test_pagina_movimentacao(api, engine_super, fazenda):
    usuario_com_senha(engine_super, "consultor@terra.test", fazendas=[fazenda])
    resposta = api.get("/api/v1/dashboards/movimentacao", headers=entrar(api, "consultor@terra.test"),
                       params={"fazendas": [str(fazenda)], "inicio": "2025-07", "fim": "2025-08"})
    assert resposta.status_code == 200, resposta.text
    pagina = resposta.json()
    assert pagina["periodo"] == {"inicio": "2025-07-01", "fim": "2025-08-01", "meses": 2}
    assert pagina["estoque_final"] == 1605
    # rebanho médio só de julho (1.050 bezerros + 500 adultos) em 1.000 ha; a planilha não informa UA
    assert (pagina["rebanho_medio_cab"], pagina["lotacao_cab_ha"]) == (1550, 1.55)
    assert (pagina["rebanho_medio_ua"], pagina["lotacao_ua_ha"]) == (None, None)
    sem_meta = {"planejado": 0, "percentual_da_meta": None}
    assert pagina["nascimentos"] == {"realizado": 120, **sem_meta}
    assert pagina["mortes"] == {"realizado": 5, **sem_meta}
    assert pagina["compras"] == {"realizado": 0, **sem_meta}
    assert pagina["vendas"] == {"realizado": 10, **sem_meta}            # 10 vacas vendidas em pé em agosto
    assert round(pagina["indice_mortalidade"], 6) == round(5 / 1550, 6)
    assert pagina["estoque_mensal"] == [{"mes": "2025-07-01", "estoque_final": 1615},
                                        {"mes": "2025-08-01", "estoque_final": 1605}]
    assert pagina["estoque_por_categoria"] == [{"categoria": "BEZERRO", "estoque_final": 815},
                                               {"categoria": "MACHOS 8-12", "estoque_final": 300},
                                               {"categoria": "MATRIZES", "estoque_final": 490}]


def test_meses_salteados_somam_so_os_meses_marcados(api, engine_super, fazenda_com_rebanho_movimentado):
    """Mês de seleção múltipla, como no BI: julho e setembro, sem agosto. As somas usam só os meses marcados; o
    estoque final é o do último mês marcado."""
    fazenda = fazenda_com_rebanho_movimentado
    usuario_com_senha(engine_super, "consultor@terra.test", fazendas=[fazenda])
    cabecalho = entrar(api, "consultor@terra.test")
    url = "/api/v1/dashboards/movimentacao"
    trimestre = {"fazendas": [str(fazenda)], "inicio": "2025-07", "fim": "2025-09"}
    pagina_do_trimestre = api.get(url, headers=cabecalho, params=trimestre).json()
    resposta = api.get(url, headers=cabecalho, params={**trimestre, "meses": ["2025-09", "2025-07"]})
    assert resposta.status_code == 200, resposta.text
    pagina = resposta.json()
    assert pagina["periodo"] == {"inicio": "2025-07-01", "fim": "2025-09-01", "meses": 2}
    assert pagina["nascimentos"]["realizado"] == 120          # sem as 80 bezerras de agosto
    assert pagina["mortes"]["realizado"] == 5                 # sem as 3 mortes de agosto
    assert pagina["vendas"]["realizado"] == 0                 # a venda em pé foi em agosto
    assert pagina["estoque_final"] == pagina_do_trimestre["estoque_final"]
    assert [mes["mes"] for mes in pagina["estoque_mensal"]] == ["2025-07-01", "2025-09-01"]

    fora_do_periodo = api.get(url, headers=cabecalho, params={**trimestre, "meses": ["2025-10"]})
    assert fora_do_periodo.status_code == 422


def test_meta_da_movimentacao(api, engine_super, fazenda_com_vendas):
    """O planejado vem das abas *PLANEJADO: a meta de 25 abates contra 20 realizados em agosto."""
    usuario_com_senha(engine_super, "consultor@terra.test", fazendas=[fazenda_com_vendas])
    pagina = api.get("/api/v1/dashboards/movimentacao", headers=entrar(api, "consultor@terra.test"),
                     params={"fazendas": [str(fazenda_com_vendas)], "inicio": "2025-08", "fim": "2025-08"}).json()
    assert pagina["vendas"] == {"realizado": 30, "planejado": 25, "percentual_da_meta": 1.2}   # 20 abate + 10 em pé


def test_fazenda_de_outro_usuario_e_recusada(api, engine_super, fazenda):
    usuario_com_senha(engine_super, "outro@terra.test")
    resposta = api.get("/api/v1/dashboards/movimentacao", headers=entrar(api, "outro@terra.test"),
                       params={"fazendas": [str(fazenda)], "inicio": "2025-07", "fim": "2025-08"})
    assert resposta.status_code == 403


def indicadores_arredondados(indicadores: dict) -> tuple:
    ordem = ["cabecas", "valor", "kg_vivo", "arrobas", "preco_arroba", "preco_kg", "peso_medio_kg",
             "rendimento_carcaca"]
    valores = []
    for campo in ordem:
        valor = indicadores[campo]
        valores.append(round(valor, 4) if valor is not None else None)
    return tuple(valores)


def pedir_vendas(api: TestClient, cabecalho: dict, fazenda, tipo: str):
    return api.get("/api/v1/dashboards/vendas", headers=cabecalho,
                   params={"tipo": tipo, "fazendas": [str(fazenda)], "inicio": "2025-07", "fim": "2025-09"})


def test_pagina_vendas_abate(api, engine_super, fazenda_com_vendas):
    usuario_com_senha(engine_super, "consultor@terra.test", fazendas=[fazenda_com_vendas])
    resposta = pedir_vendas(api, entrar(api, "consultor@terra.test"), fazenda_com_vendas, "abate")
    assert resposta.status_code == 200, resposta.text
    pagina = resposta.json()
    quadro = {}
    for coluna in pagina["quadro"]:
        quadro[coluna["recorte"]] = (indicadores_arredondados(coluna["realizado"]),
                                     indicadores_arredondados(coluna["planejado"]))
    #                  cab  valor (R$)   kg vivo  @    R$/@      R$/kg    kg/cab    rendimento
    meta = (25, 139500, 12500, 450, 310, 11.16, 500, 0.54)
    sem_venda = (0, 0, 0, 0, None, None, None, None)
    assert quadro == {
        "GERAL": ((30, 154200, 14000, 490, 314.6939, 11.0143, 466.6667, 0.525), meta),
        "MACHO": ((20, 115200, 10000, 360, 320, 11.52, 500, 0.54), meta),
        "FÊMEA": ((10, 39000, 4000, 130, 300, 9.75, 400, 0.4875), sem_venda),
    }
    serie = [(mes["mes"], mes["cabecas"], mes["cabecas_planejadas"], mes["cabecas_acumuladas"], mes["valor"],
              mes["valor_planejado"]) for mes in pagina["serie_mensal"]]
    assert serie == [("2025-07-01", 0, 0, 0, 0, 0), ("2025-08-01", 20, 25, 20, 115200, 139500),
                     ("2025-09-01", 10, 0, 30, 39000, 0)]


def test_pagina_vendas_em_pe(api, engine_super, fazenda_com_vendas):
    usuario_com_senha(engine_super, "consultor@terra.test", fazendas=[fazenda_com_vendas])
    cabecalho = entrar(api, "consultor@terra.test")
    pagina = pedir_vendas(api, cabecalho, fazenda_com_vendas, "em_pe").json()
    geral = pagina["quadro"][0]
    # @ da venda em pé = kg vivo ÷ 30; sem carcaça, sem rendimento
    assert indicadores_arredondados(geral["realizado"]) == (10, 30000, 4500, 150, 200, 6.6667, 450, None)
    assert pedir_vendas(api, cabecalho, fazenda_com_vendas, "leilao").status_code == 422


# Venda em pé com três erros de lançamento: data digitada "0108/2025" (não entra), venda sem cliente e preço de
# R$ 0,10 por kg vivo (entram, para conferir).
VENDAS_COM_ERROS = [["EMPÉ", "Comprador", datetime(2025, 8, 5), "GTA1", "Vaca", 10, 450, 4500, None, None, 30000],
                    ["EMPÉ", "Comprador", "0108/2025", "GTA2", "Vaca", 5, 450, 2250, None, None, 15000],
                    ["EMPÉ", None, datetime(2025, 8, 20), "GTA3", "Vaca", 2, 450, 900, None, None, 90]]


@pytest.fixture
def fazenda_com_erros(engine_etl, engine_super, tmp_path):
    return carregar_planilha(engine_etl, engine_super, tmp_path, linhas={"fVendaemPe": VENDAS_COM_ERROS})


def test_pendencias_mostram_onde_corrigir(api, engine_super, fazenda_com_erros):
    usuario_com_senha(engine_super, "consultor@terra.test", fazendas=[fazenda_com_erros])
    resposta = api.get("/api/v1/qualidade/pendencias", headers=entrar(api, "consultor@terra.test"),
                       params={"fazendas": [str(fazenda_com_erros)]})
    assert resposta.status_code == 200, resposta.text
    itens = {}
    for item in resposta.json()["itens"]:
        itens[(item["codigo"], item["local"])] = item
    data_errada = itens[("REQUIRED_MISSING", "aba fVendaemPe, linha 3")]
    assert data_errada["situacao"] == "nao_entrou"
    assert data_errada["origem"] == "RELATÓRIO - 85 - TESTE.xlsx"
    assert "DATA: 0108/2025" in data_errada["valores"]
    # a venda sem cliente e o preço absurdo entram nos números, mas aparecem para conferir, na linha certa
    assert itens[("SALE_WITHOUT_CLIENT", "aba fVendaemPe, linha 4")]["situacao"] == "confira"
    assert "R$ 0,10 por kg vivo" in itens[("OUTLIER", "aba fVendaemPe, linha 4")]["detalhe"]
    # conta fora do plano: quem resolve é a equipe Terra, não quem preenche a planilha
    assert itens[("ACCOUNT_UNCLASSIFIED", None)]["quem_corrige"] == "equipe"


def test_pendencias_respeitam_o_rls(api, engine_super, engine_api, fazenda_com_erros):
    outro = usuario_com_senha(engine_super, "outro@terra.test")
    admin = usuario_com_senha(engine_super, "admin@terra.test", admin=True)
    resposta = api.get("/api/v1/qualidade/pendencias", headers=entrar(api, "outro@terra.test"),
                       params={"fazendas": [str(fazenda_com_erros)]})
    assert resposta.status_code == 403
    # a função do banco aplica a mesma regra mesmo chamada direto, sem passar pela rota
    contar = text("SELECT count(*) FROM app.pendencias_de_carga(CAST(:fazendas AS uuid[]))")
    parametros = {"fazendas": [str(fazenda_com_erros)]}
    with como_usuario(engine_api, outro) as s:
        assert s.scalar(contar, parametros) == 0
    with como_usuario(engine_api, admin) as s:
        assert s.scalar(contar, parametros) > 0


def test_pagina_compras(api, engine_super, fazenda_com_compras):
    usuario_com_senha(engine_super, "consultor@terra.test", fazendas=[fazenda_com_compras])
    resposta = api.get("/api/v1/dashboards/compras", headers=entrar(api, "consultor@terra.test"),
                       params={"fazendas": [str(fazenda_com_compras)], "inicio": "2025-07", "fim": "2025-09"})
    assert resposta.status_code == 200, resposta.text
    pagina = resposta.json()
    quadro = {}
    for coluna in pagina["quadro"]:
        quadro[coluna["recorte"]] = (indicadores_arredondados(coluna["realizado"]),
                                     indicadores_arredondados(coluna["planejado"]))
    #                  cab  valor (R$)  kg vivo  @         R$/@  R$/kg    kg/cab    (compra não tem rendimento)
    meta = (60, 150000, 12000, 400, 375, 12.5, 200, None)
    sem_compra = (0, 0, 0, 0, None, None, None, None)
    assert quadro == {
        "GERAL": ((70, 192000, 18000, 600, 320, 10.6667, 257.1429, None), meta),
        "MACHO": ((50, 120000, 10000, 333.3333, 360, 12, 200, None), meta),
        "FÊMEA": ((20, 72000, 8000, 266.6667, 270, 9, 400, None), sem_compra),
    }
    # @ vendida: abate R$ 154.200 em 490 @ de carcaça + em pé R$ 30.000 em 150 @ -> R$ 184.200 ÷ 640 @ = R$ 287,81
    assert round(pagina["preco_arroba_venda"], 4) == round(184200 / 640, 4)
    assert round(pagina["agio"], 4) == round((320 - 184200 / 640) / (184200 / 640), 4)
    serie = [(mes["mes"], mes["cabecas"], mes["cabecas_planejadas"], mes["cabecas_acumuladas"], mes["valor"],
              mes["valor_planejado"], mes["preco_arroba"]) for mes in pagina["serie_mensal"]]
    assert serie == [("2025-07-01", 0, 0, 0, 0, 0, None), ("2025-08-01", 50, 60, 50, 120000, 150000, 360),
                     ("2025-09-01", 20, 0, 70, 72000, 0, 270)]


def pedir_pagina(api: TestClient, engine_super, fazenda, pagina: str) -> dict:
    usuario_com_senha(engine_super, "consultor@terra.test", fazendas=[fazenda])
    resposta = api.get(f"/api/v1/dashboards/{pagina}", headers=entrar(api, "consultor@terra.test"),
                       params={"fazendas": [str(fazenda)], "inicio": "2025-07", "fim": "2025-09"})
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def arredondado(valor: float | None) -> float | None:
    if valor is None:
        return None
    return round(valor, 4)


def serie_de_contagem(pagina: dict) -> list[tuple]:
    serie = []
    for mes in pagina["serie_mensal"]:
        serie.append((mes["mes"], mes["realizado"], mes["planejado"], mes["realizado_acumulado"],
                      mes["planejado_acumulado"]))
    return serie


def test_pagina_nascimentos(api, engine_super, fazenda_com_rebanho_movimentado):
    pagina = pedir_pagina(api, engine_super, fazenda_com_rebanho_movimentado, "nascimentos")
    quadro = {}
    for coluna in pagina["quadro"]:
        quadro[coluna["recorte"]] = (coluna["realizado"], coluna["planejado"],
                                     arredondado(coluna["percentual_da_meta"]),
                                     arredondado(coluna["participacao_no_total"]))
    #                  realizado  planejado  % da meta  % do total
    assert quadro == {"GERAL": (200, 200, 1.0, 1.0), "MACHO": (120, 100, 1.2, 0.6), "FÊMEA": (80, 100, 0.8, 0.4)}
    assert serie_de_contagem(pagina) == [("2025-07-01", 120, 100, 120, 100), ("2025-08-01", 80, 100, 200, 200),
                                         ("2025-09-01", 0, 0, 200, 200)]


def test_pagina_mortes(api, engine_super, fazenda_com_rebanho_movimentado):
    pagina = pedir_pagina(api, engine_super, fazenda_com_rebanho_movimentado, "mortes")
    quadro = {}
    for coluna in pagina["quadro"]:
        quadro[coluna["recorte"]] = (coluna["realizado"], coluna["planejado"],
                                     arredondado(coluna["percentual_da_meta"]),
                                     arredondado(coluna["sobre_rebanho_medio"]),
                                     arredondado(coluna["sobre_nascimentos"]))
    # rebanho médio de 07/2025 (único mês informado): 1.050 bezerros + 500 adultos = 1.550; nascimentos: 200
    #                  realizado  planejado  % da meta  ÷ rebanho médio        ÷ nascimentos
    assert quadro == {"GERAL": (8, 4, 2.0, arredondado(8 / 1550), None),
                      "BEZERROS": (6, 4, 1.5, arredondado(6 / 1050), 0.03),
                      "JOVENS": (0, 0, None, None, None),
                      "ADULTOS": (2, 0, None, 0.004, None)}
    assert pagina["causas"] == [{"causa": "COBRA", "cabecas": 6}, {"causa": "RAIO", "cabecas": 2}]
    assert serie_de_contagem(pagina) == [("2025-07-01", 5, 4, 5, 4), ("2025-08-01", 3, 0, 8, 4),
                                         ("2025-09-01", 0, 0, 8, 4)]


def test_pagina_transferencias(api, engine_super, fazenda_com_rebanho_movimentado):
    pagina = pedir_pagina(api, engine_super, fazenda_com_rebanho_movimentado, "transferencias")
    entrada = {}
    for coluna in pagina["entrada"]:
        entrada[coluna["recorte"]] = indicadores_arredondados(coluna["realizado"])
    saida = {}
    for coluna in pagina["saida"]:
        saida[coluna["recorte"]] = indicadores_arredondados(coluna["realizado"])
    sem_transferencia = (0, 0, 0, 0, None, None, None, None)
    #                       cab  valor (R$)  kg vivo  @         R$/@  R$/kg  kg/cab
    assert entrada["MACHO"] == (30, 60000, 6000, 200, 300, 10, 200, None)
    assert entrada["FÊMEA"] == sem_transferencia
    assert saida["FÊMEA"] == (10, 30000, 4000, 133.3333, 225, 7.5, 400, None)
    assert saida["MACHO"] == sem_transferencia
    serie = [(mes["mes"], mes["entradas"], mes["saidas"]) for mes in pagina["serie_mensal"]]
    assert serie == [("2025-07-01", 0, 0), ("2025-08-01", 30, 0), ("2025-09-01", 0, 10)]


def test_pagina_financeiro(api, engine_super, fazenda_com_financeiro):
    pagina = pedir_pagina(api, engine_super, fazenda_com_financeiro, "financeiro")
    # desembolso: adubo 1.000 (1.500,50 − estorno) + compra de gado 50.000; os dividendos ficam fora
    assert (pagina["desembolso"], pagina["receitas"]) == (51000, 30000)
    velocimetros = {}
    for nome in ("desembolso_por_cabeca_mes", "custeio_por_cabeca_mes", "preco_arroba_venda"):
        velocimetro = pagina[nome]
        velocimetros[nome] = (arredondado(velocimetro["realizado"]), arredondado(velocimetro["planejado"]),
                              arredondado(velocimetro["maximo"]), velocimetro["dentro_da_meta"])
    # por cabeça por mês = valor ÷ Σ do rebanho médio dos meses (1.550 realizado, 1.600 planejado), escala = meta × 1,2;
    # @ vendida: (R$ 154.200 de abate + R$ 30.000 em pé) ÷ (490 @ + 150 @); meta R$ 139.500 ÷ 450 @; escala × 1,15
    assert velocimetros == {
        "desembolso_por_cabeca_mes": (arredondado(51000 / 1550), 1.25, 1.5, False),
        "custeio_por_cabeca_mes": (arredondado(1000 / 1550), 1.25, 1.5, True),
        "preco_arroba_venda": (arredondado(184200 / 640), 310, 356.5, False),
    }
    assert pagina["desembolso_por_centro"] == [{"centro_custo": "Rebanho Investimento", "valor": 50000},
                                               {"centro_custo": "Pastagens", "valor": 1000}]
    serie = []
    for mes in pagina["serie_mensal"]:
        serie.append((mes["mes"], mes["receitas"], mes["receitas_planejadas"], mes["despesas"], mes["saldo"],
                      mes["desembolso"], mes["desembolso_planejado"], arredondado(mes["desembolso_por_cabeca"]),
                      arredondado(mes["desembolso_por_cabeca_planejado"])))
    # saldo = receitas (inclusive o arrendamento) − despesas (inclusive os dividendos)
    assert serie == [("2025-07-01", 0, 0, 1000, -1000, 1000, 2000, arredondado(1000 / 1550), 1.25),
                     ("2025-08-01", 30000, 25000, 50000, -15000, 50000, 0, None, None),
                     ("2025-09-01", 0, 0, 3000, -3000, 0, 0, None, None)]


def comparacao_arredondada(comparacao: dict) -> tuple:
    return (comparacao["realizado"], comparacao["planejado"], arredondado(comparacao["variacao"]), comparacao["semaforo"])


def test_pagina_previsto_realizado(api, engine_super, fazenda_com_financeiro):
    pagina = pedir_pagina(api, engine_super, fazenda_com_financeiro, "previsto_realizado")
    assert pagina["ultimo_mes"] == "2025-09-01"
    grupos = {}
    for grupo in pagina["grupos"]:
        contas = {}
        for conta in grupo["contas"]:
            contas[conta["nome"]] = comparacao_arredondada(conta["acumulado"])
        grupos[grupo["classificacao"]] = (comparacao_arredondada(grupo["total"]["acumulado"]), contas)
    # acumulado de 07 a 09/2025 (mesmo DRE do teste do Financeiro): receitas acima da meta = verde; despesas acima da
    # meta = vermelho; sem meta, sem variação nem semáforo
    assert grupos == {
        "A - RECEITAS": ((35000, 25000, 0.4, "verde"), {"Arrendamento": (5000, 0, None, None),
                                                         "Rebanho": (30000, 25000, 0.2, "verde")}),
        "B - DESEMBOLSO": ((51000, 2000, 24.5, "vermelho"), {}),
        "C - INVESTIMENTOS": ((50000, 0, None, None), {"Rebanho Investimento": (50000, 0, None, None)}),
        "D - CUSTEIO": ((1000, 2000, -0.5, "verde"), {"Pastagens": (1000, 2000, -0.5, "verde")}),
        "F - OUTROS DÉBITOS": ((3000, 0, None, None), {"Dividendos": (3000, 0, None, None)}),
    }
    # resultado = receitas − (investimentos + custeio + outros débitos): 35.000 − 54.000; meta 25.000 − 2.000
    assert comparacao_arredondada(pagina["resultado"]["acumulado"]) == (-19000, 23000, arredondado(-42000 / 23000),
                                                                        "vermelho")
    # o último mês (09/2025) só tem os dividendos
    assert comparacao_arredondada(pagina["resultado"]["mensal"]) == (-3000, 0, None, None)
