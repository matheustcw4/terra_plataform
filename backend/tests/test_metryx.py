"""Adapter Metryx: cliente HTTP (allow-list, repetição, erros), credenciais cifradas e carga pelo motor (API simulada)."""

import logging
from datetime import date

import httpx
import pytest
from sqlalchemy import text

from app.etl.adapters.metryx import credenciais
from app.etl.adapters.metryx.adapter import AdapterMetryx, ErroSegurancaMetryx
from app.etl.adapters.metryx.cliente import (
    ClienteMetryx,
    CredencialInvalida,
    EndpointProibido,
    ErroMetryx,
    RespostaInesperada,
)
from app.etl.adapters.metryx.normalizar import normalizar
from app.etl.adapters.metryx.pasto import PeriodoDePasto, area_no_dia, eh_uso_pecuario
from app.etl.pipeline import MotorCarga
from tests.sinteticos import (
    CAT_DESM,
    CAT_VACA,
    CLIENTE,
    FAZENDA,
    RETIRO,
    pastagem,
    payloads_metryx,
    transporte_metryx,
)

BASE = "https://metryx.teste/mtxserver"


def cliente(transport, tentativas=3) -> ClienteMetryx:
    return ClienteMetryx(BASE, transport=transport, tentativas=tentativas, espera_max=0.01)


# --- cliente HTTP ----------------------------------------------------------------------------------------------------

def test_allow_list_recusa_control_birth_sem_chamar_a_api():
    chamadas = []
    c = cliente(transporte_metryx({}, chamadas=chamadas))
    for caminho in ("/api-metryx/control-birth", "/api-metryx/qualquer-coisa"):
        with pytest.raises(ErroMetryx, match="allow-list"):
            c.get_lista(caminho, "token-teste")
    assert chamadas == []


def test_repete_falha_transitoria_e_nao_repete_401():
    respostas = iter([httpx.Response(503), httpx.Response(429), httpx.Response(200, content=b'[{"a": 1}]')])
    c = cliente(httpx.MockTransport(lambda req: next(respostas)))
    assert c.get_lista("/api-metryx/fazenda", "t").itens == [{"a": 1}]

    chamadas = []
    c = cliente(transporte_metryx({}, chamadas=chamadas, token="outro"))
    with pytest.raises(CredencialInvalida):
        c.get_lista("/api-metryx/fazenda", "token-errado")
    assert len(chamadas) == 1                       # 401 não é repetido


def test_403_e_corpo_inesperado():
    c = cliente(httpx.MockTransport(lambda req: httpx.Response(403)))
    with pytest.raises(EndpointProibido):
        c.get_lista("/api-metryx/venda-pecuario", "t")
    c = cliente(httpx.MockTransport(lambda req: httpx.Response(200, content=b'{"erro": "x"}')))
    with pytest.raises(RespostaInesperada):
        c.get_lista("/api-metryx/venda-pecuario", "t")


def test_token_nunca_aparece_no_log(caplog):
    caplog.set_level(logging.DEBUG)
    c = cliente(transporte_metryx({"fazenda": []}, token="segredo-123"))
    c.get_lista("/api-metryx/fazenda", "segredo-123")
    assert "segredo-123" not in caplog.text


# --- credenciais ----------------------------------------------------------------------------------------------------

def test_token_cifrado_no_banco(engine_etl, engine_super):
    credenciais.registrar(engine_etl, CLIENTE, "token-teste", "Cliente Teste")
    with engine_super.connect() as c:
        cifrado = c.execute(text("SELECT token_cifrado FROM integracao.metryx_credencial")).scalar()
    assert b"token-teste" not in bytes(cifrado)
    [cred] = credenciais.credenciais_ativas(engine_etl)
    assert cred.token == "token-teste" and "token-teste" not in repr(cred)
    credenciais.registrar(engine_etl, CLIENTE, "token-novo", "Cliente Teste")      # rotação
    assert [c.token for c in credenciais.credenciais_ativas(engine_etl)] == ["token-novo"]


# --- carga pelo motor ------------------------------------------------------------------------------------------------

def carregar(engine_etl, dados=None, status=None, token="token-teste", **kw):
    adapter = AdapterMetryx(engine_etl, cliente(transporte_metryx(dados or payloads_metryx(), status, token=token)))
    return MotorCarga(engine_etl, hoje=date(2025, 10, 1), estoque_ate=date(2025, 9, 1)).executar(adapter, **kw)


def contar(engine_super, sql, **p):
    with engine_super.connect() as c:
        return c.execute(text(sql), p).scalar()


def test_carga_da_api(engine_etl, engine_super):
    credenciais.registrar(engine_etl, CLIENTE, "token-teste", "Cliente Teste")
    r = carregar(engine_etl)
    assert r.unidades[0].status == "carregada_com_avisos", r.unidades[0].erro
    assert contar(engine_super, "SELECT count(*) FROM core.fazenda") == 2
    # o "cliente" do menu do painel: no Metryx é o customer (na planilha, o PROPRIETÁRIO)
    assert contar(engine_super, "SELECT count(*) FROM core.fazenda WHERE proprietario = 'Cliente Teste'") == 2
    # transferência entre fazendas do cliente: 1 registro -> saída na origem e entrada no destino
    assert contar(engine_super, "SELECT count(*) FROM fato.mov_animal WHERE tipo IN ('TRANSF_SAIDA','TRANSF_ENTRADA')") == 2
    # morte com idRetiro legado vai para o retiro certo (uuid), não para um retiro fantasma
    assert contar(engine_super, "SELECT count(*) FROM core.retiro") == 1
    # lançamento não pago não é realizado
    assert contar(engine_super, "SELECT count(*) FROM fato.lancamento_financeiro") == 1
    assert contar(engine_super, "SELECT count(*) FROM raw.payload") == 1
    assert contar(engine_super, "SELECT count(*) FROM integracao.metryx_credencial WHERE ultima_validacao_em IS NOT NULL") == 1


def test_endpoint_proibido_mantem_os_dados_dele(engine_etl, engine_super):
    credenciais.registrar(engine_etl, CLIENTE, "token-teste", "Cliente Teste")
    carregar(engine_etl)
    vendas = contar(engine_super, "SELECT count(*) FROM fato.mov_animal WHERE tipo = 'VENDA_EM_PE'")
    r = carregar(engine_etl, status={"venda": 403})
    assert r.unidades[0].status.startswith("carregada")
    assert contar(engine_super, "SELECT count(*) FROM fato.mov_animal WHERE tipo = 'VENDA_EM_PE'") == vendas == 1


def test_401_num_endpoint_opcional_e_falta_de_permissao(engine_etl, engine_super):
    """A API real responde 401 ao token sem a permissão de um endpoint (U6, 20/10/2026). Se os obrigatórios já
    aceitaram o token, ele vale: só aquele endpoint fica de fora, os dados dele ficam como estavam e a credencial
    continua ativa."""
    credenciais.registrar(engine_etl, CLIENTE, "token-teste", "Cliente Teste")
    carregar(engine_etl)
    transferencias = "SELECT count(*) FROM fato.mov_animal WHERE tipo IN ('TRANSF_ENTRADA', 'TRANSF_SAIDA')"
    antes = contar(engine_super, transferencias)
    r = carregar(engine_etl, status={"transferencia": 401})
    assert r.unidades[0].status.startswith("carregada")
    assert contar(engine_super, transferencias) == antes > 0
    assert contar(engine_super, "SELECT status FROM integracao.metryx_credencial") == "ativa"


def test_guarda_de_volume_retem_resposta_vazia(engine_etl, engine_super):
    credenciais.registrar(engine_etl, CLIENTE, "token-teste", "Cliente Teste")
    carregar(engine_etl)
    nasc = contar(engine_super, "SELECT count(*) FROM fato.mov_animal WHERE tipo = 'NASCIMENTO'")
    r = carregar(engine_etl, payloads_metryx(nascimento=[]))
    assert contar(engine_super, "SELECT count(*) FROM fato.mov_animal WHERE tipo = 'NASCIMENTO'") == nasc == 1
    assert contar(engine_super, "SELECT count(*) FROM ingest.ocorrencia WHERE codigo = 'SNAPSHOT_HELD'") >= 1
    assert r.unidades[0].status == "carregada_com_avisos"


def test_401_marca_credencial_invalida_e_nao_apaga_nada(engine_etl, engine_super):
    credenciais.registrar(engine_etl, CLIENTE, "token-teste", "Cliente Teste")
    carregar(engine_etl)
    antes = contar(engine_super, "SELECT count(*) FROM fato.mov_animal")
    credenciais.registrar(engine_etl, CLIENTE, "token-revogado", "Cliente Teste")
    r = carregar(engine_etl, token="token-teste")            # a API só aceita o token antigo
    assert r.unidades[0].status == "erro"
    assert contar(engine_super, "SELECT count(*) FROM fato.mov_animal") == antes
    assert contar(engine_super, "SELECT status FROM integracao.metryx_credencial WHERE ultimo_erro IS NOT NULL") \
        == "invalida"


def test_item_de_outro_cliente_bloqueia_a_carga(engine_etl):
    credenciais.registrar(engine_etl, CLIENTE, "token-teste", "Cliente Teste")
    dados = payloads_metryx()
    dados["venda"] = [{**dados["venda"][0], "idCustomer": "outro-cliente"}]
    adapter = AdapterMetryx(engine_etl, cliente(transporte_metryx(dados)))
    with pytest.raises(ErroSegurancaMetryx):
        adapter.extrair(adapter.descobrir()[0])


# --- formato real da API (primeira consulta, 15/10/2026: achados A29–A31) ------------------------------------------

def conteudo_bruto(dados: dict) -> dict:
    return {"idCustomer": CLIENTE, "endpoints": dict.fromkeys(dados, "ok"), "dados": dados}


def test_mudanca_de_categoria_com_idcustomer_errado_vale_pela_fazenda(engine_etl):
    """A29: a mudança de categoria vem com outro idCustomer, mas com a fazenda do cliente; de fazenda alheia, bloqueia."""
    credenciais.registrar(engine_etl, CLIENTE, "token-teste", "Cliente Teste")
    dados = payloads_metryx()
    mudanca = {"idCustomer": "id-trocado-pela-api", "idFarm": FAZENDA, "idRetiro": RETIRO, "retiroName": "Sede",
               "date": "2025-08-10", "uuidCategoryOrigin": CAT_VACA, "uuidCategoryDestiny": CAT_DESM, "amount": 2}
    dados["mudanca_categoria"] = [mudanca]
    adapter = AdapterMetryx(engine_etl, cliente(transporte_metryx(dados)))
    lote = adapter.normalizar(adapter.extrair(adapter.descobrir()[0]))
    assert [m.qtd for m in lote.mov_animal if m.tipo == "MUDANCA_CATEGORIA"] == [2]

    dados["mudanca_categoria"] = [{**mudanca, "idFarm": "fazenda-de-outro-cliente"}]
    adapter = AdapterMetryx(engine_etl, cliente(transporte_metryx(dados)))
    with pytest.raises(ErroSegurancaMetryx):
        adapter.extrair(adapter.descobrir()[0])


def test_venda_e_compra_sem_idfarm_vao_pela_fazenda_do_retiro():
    """A30: venda e compra vêm sem idFarm; a fazenda sai do retiro (por id), e não do nome."""
    dados = payloads_metryx()
    venda = dict(dados["venda"][0])
    del venda["idFarm"]
    compra = {**venda, "amount": 4, "weightTotal": 1800, "provider": "Vendedor", "totalFaturamento": 12000}
    dados["venda"], dados["compra"] = [venda], [compra]
    lote = normalizar(conteudo_bruto(dados))
    fazendas = {m.tipo: m.fazenda for m in lote.mov_animal if m.tipo in ("VENDA_EM_PE", "COMPRA")}
    assert fazendas == {"VENDA_EM_PE": f"{CLIENTE}|{FAZENDA}", "COMPRA": f"{CLIENTE}|{FAZENDA}"}
    assert "FARM_BY_NAME" not in {ocorrencia.codigo for ocorrencia in lote.ocorrencias}


def test_transferencia_antiga_sem_quantidade_fica_de_fora_com_aviso():
    """A31: as transferências antigas vêm sem amount (as novas vêm com ele, sem o id da fazenda de destino e sem o
    retiro de origem). A antiga não tem o que somar: um aviso só, nada na quarentena; a nova entra inteira."""
    dados = payloads_metryx()
    antiga = {"id": "t-antiga", "idCustomer": CLIENTE, "idFarmOrigin": FAZENDA, "farmNameDestiny": "Fazenda Metryx",
              "idRetiroDestiny": RETIRO, "retiroNameDestiny": "Sede", "date": "2023-07-03", "categoryId": CAT_VACA}
    nova = {**antiga, "id": "t-nova", "itemId": "17159", "date": "2025-09-01", "amount": 3}
    dados["transferencia"] = [antiga, nova]
    lote = normalizar(conteudo_bruto(dados))
    transferidos = sorted((m.tipo, m.qtd, m.retiro) for m in lote.mov_animal if m.tipo.startswith("TRANSF"))
    # sem o retiro de origem, dentro da mesma fazenda: as duas pontas sem retiro, para se anularem no estoque
    assert transferidos == [("TRANSF_ENTRADA", 3, None), ("TRANSF_SAIDA", 3, None)]
    assert [r for r in lote.rejeitadas if r.origem_linha.startswith("transferencia")] == []
    avisos = [o.mensagem for o in lote.ocorrencias if o.codigo == "TRANSFER_WITHOUT_AMOUNT"]
    assert avisos == ["1 transferência(s) sem quantidade na API do Metryx, de 2023-07-03 a 2023-07-03: ficaram de fora"]


def test_destino_da_transferencia_pelo_retiro():
    """A30 na transferência: sem o id da fazenda de destino, vale a fazenda do retiro de destino."""
    dados = payloads_metryx()
    transferencia = dict(dados["transferencia"][0])
    del transferencia["idFarmDestiny"]
    transferencia["idRetiroDestiny"] = RETIRO
    dados["transferencia"] = [transferencia]
    lote = normalizar(conteudo_bruto(dados))
    assert [m.fazenda for m in lote.mov_animal if m.tipo == "TRANSF_ENTRADA"] == [f"{CLIENTE}|{FAZENDA}"]


def test_mudanca_que_repete_o_desmame_fica_de_fora_e_retiro_legado_vai_pelo_nome():
    """A32: o endpoint de mudança de categoria repete cada desmame (mesma data, categorias, retiro e quantidade);
    a mudança de verdade entra, com o idRetiro legado trocado pelo uuid do retiro de mesmo nome."""
    dados = payloads_metryx()
    base = {"idCustomer": CLIENTE, "idFarm": FAZENDA, "retiroName": "Sede", "idRetiro": "620"}
    repetida = {**base, "date": "2025-07-20", "uuidCategoryOrigin": "ca000001", "uuidCategoryDestiny": CAT_DESM,
                "amount": 300}                                              # o desmame de 20/07 do payload
    de_verdade = {**base, "date": "2025-08-10", "uuidCategoryOrigin": CAT_VACA, "uuidCategoryDestiny": CAT_DESM,
                  "amount": 2}
    dados["mudanca_categoria"] = [repetida, de_verdade]
    lote = normalizar(conteudo_bruto(dados))
    mudancas = [(m.qtd, m.retiro) for m in lote.mov_animal if m.tipo == "MUDANCA_CATEGORIA"]
    assert mudancas == [(2, f"{CLIENTE}|{FAZENDA}|{RETIRO}")]
    assert [m.qtd for m in lote.mov_animal if m.tipo == "DESMAME"] == [300]
    codigos = {ocorrencia.codigo for ocorrencia in lote.ocorrencias}
    assert {"CATEGORY_CHANGE_IS_WEANING", "LEGACY_RETIRO_ID"} <= codigos


# --- área de pasto (utilizacao-pasto) ------------------------------------------------------------------------------

def test_area_do_mes_sai_das_pastagens_de_uso_pecuaria():
    """Fim de julho: p1 (600) e p2 (400) são pasto. Em agosto p2 virou agricultura (um período novo começa no dia em
    que o anterior acaba, sem contar duas vezes) e só p1 conta. A APP nunca entra; a pastagem de outra fazenda fica de
    fora com um aviso. Do primeiro período (jun) até o último mês do rebanho médio (ago, o do último balanço)."""
    pastos = [pastagem("p1", "Pecuária", 600, "2025-06-15", produtiva=500),
              pastagem("p2", "Pecuária", 400, "2025-06-15", fim="2025-08-01"),
              pastagem("p2", "Agricultura", 400, "2025-08-01"),
              pastagem("p3", "APP", 50, "2025-06-15"),
              pastagem("p9", "Pecuária", 999, "2025-06-15", fazenda="fazenda-de-outro-cliente")]
    lote = normalizar(conteudo_bruto(payloads_metryx(pasto=pastos)))
    areas = {linha.competencia: (linha.area_total_ha, linha.area_produtiva_ha) for linha in lote.area}
    assert areas == {date(2025, 6, 1): (1000, 900), date(2025, 7, 1): (1000, 900), date(2025, 8, 1): (600, 500)}
    assert {linha.fazenda for linha in lote.area} == {f"{CLIENTE}|{FAZENDA}"}
    assert "PASTURE_FARM_UNKNOWN" in {ocorrencia.codigo for ocorrencia in lote.ocorrencias}
    assert ("area", f"{CLIENTE}|{FAZENDA}") in {(p.entidade, p.fazenda) for p in lote.particoes}


def test_sem_rebanho_medio_nao_ha_area():
    lote = normalizar(conteudo_bruto(payloads_metryx(balanco=[])))
    assert lote.area == []


def test_dia_da_troca_de_periodo_conta_a_pastagem_uma_vez():
    antigo = PeriodoDePasto("p1", date(2025, 1, 1), date(2025, 7, 31), True, 100, 100)
    novo = PeriodoDePasto("p1", date(2025, 7, 31), None, True, 120, 110)
    assert area_no_dia([antigo, novo], date(2025, 7, 31)) == (120, 110)
    assert area_no_dia([antigo, novo], date(2025, 7, 30)) == (100, 100)
    assert area_no_dia([antigo, novo], date(2024, 12, 31)) == (0, 0)


def test_uso_pecuario_com_ou_sem_acento():
    assert eh_uso_pecuario("Pecuária") and eh_uso_pecuario("PECUARIA") and eh_uso_pecuario(" pecuária ")
    assert not eh_uso_pecuario("Agricultura") and not eh_uso_pecuario(None)


# --- baixas de consumo e doação (como o Consolidado Pecuário do Metryx) ------------------------------------------------

def test_consumo_e_doacao_seguem_o_metryx():
    """O Metryx põe em "Consumo e Doação" as causas "Consumo ..." e "Doação" (o BI só contava "Consumo Abate")."""
    base = payloads_metryx()["morte"][0]
    mortes = []
    for numero, causa in enumerate(("Consumo Abate", "Consumo Acidente", "Doação", "Fraqueza", "Ajuste de saldo")):
        mortes.append({**base, "date": f"2025-07-{numero + 10}", "cause": causa, "amount": 1})
    lote = normalizar(conteudo_bruto(payloads_metryx(morte=mortes)))
    tipos = {m.causa: m.tipo for m in lote.mov_animal if m.tipo in ("MORTE", "CONSUMO_DOACAO")}
    assert tipos == {"Consumo Abate": "CONSUMO_DOACAO", "Consumo Acidente": "CONSUMO_DOACAO",
                     "Doação": "CONSUMO_DOACAO", "Fraqueza": "MORTE", "Ajuste de saldo": "MORTE"}
