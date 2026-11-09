"""Importação de planilhas pela tela: a API guarda o arquivo na fila e o worker carrega pelo motor de sempre,
conferindo o acesso de quem enviou (o admin pode tudo, inclusive cadastrar fazenda nova; o técnico, só as fazendas
dele). Postgres real: a API conecta como app_user (RLS) e o worker como app_etl; o Redis é trocado por um contador.
"""

import pytest
from fastapi.testclient import TestClient
from kombu.exceptions import OperationalError
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.etl.importacao import JA_CARREGADA
from app.services import importacoes
from app.tasks.cargas import importacoes_na_fila
from app.tasks.trava import trava_das_cargas
from tests.conftest import como_usuario
from tests.sinteticos import gerar_planilha
from tests.test_api import entrar, usuario_com_senha

ARQUIVO = "RELATÓRIO - 85 - TESTE.xlsx"
OUTRA = "RELATÓRIO - 86 - OUTRA.xlsx"


class FilaDeTeste:
    """No lugar do Redis: conta quantas vezes a API avisou o worker."""

    def __init__(self):
        self.avisos = 0

    def avisar(self) -> None:
        self.avisos += 1


@pytest.fixture
def fila(monkeypatch) -> FilaDeTeste:
    fila_de_teste = FilaDeTeste()
    monkeypatch.setattr(importacoes, "enviar_para_a_fila", fila_de_teste.avisar)
    return fila_de_teste


@pytest.fixture
def admin(api: TestClient, engine_super) -> dict:
    usuario_com_senha(engine_super, "admin@terra.test", admin=True)
    return entrar(api, "admin@terra.test")


def planilha(pasta, nome: str = ARQUIVO, codigo: int = 85, fazenda: str = "TESTE", saldo_bezerro: int = 1000) -> bytes:
    subpasta = pasta / f"{codigo}-{saldo_bezerro}"
    subpasta.mkdir(exist_ok=True)
    return gerar_planilha(subpasta, nome, codigo=codigo, fazenda=fazenda, saldo_bezerro=saldo_bezerro).read_bytes()


def enviar(api: TestClient, cabecalho: dict, nome: str, dados: bytes):
    return api.post("/api/v1/importacoes", headers=cabecalho, files={"arquivo": (nome, dados, "application/zip")})


def importadas(api: TestClient, cabecalho: dict) -> list[dict]:
    resposta = api.get("/api/v1/importacoes", headers=cabecalho)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def fazenda_do_codigo(engine_super, codigo: int):
    with engine_super.connect() as c:
        return c.scalar(text("SELECT entidade_id FROM core.fonte_vinculo WHERE entidade = 'fazenda' "
                             "AND id_externo LIKE :codigo"), {"codigo": f"{codigo}|%"})


def bezerros_no_saldo_inicial(engine_super, fazenda_id) -> int:
    with engine_super.connect() as c:
        return c.scalar(text("SELECT sum(qtd) FROM fato.inventario WHERE fazenda_id = :f"), {"f": fazenda_id})


def test_admin_importa_fazenda_nova_e_o_worker_carrega(api, admin, fila, engine_etl, engine_super, tmp_path):
    resposta = enviar(api, admin, ARQUIVO, planilha(tmp_path))
    assert resposta.status_code == 202, resposta.text
    recebida = resposta.json()
    assert (recebida["status"], recebida["minha"], recebida["enviado_por"]) == ("na_fila", True, "admin@terra.test")
    assert fila.avisos == 1

    resultado = importacoes_na_fila(engine_etl)
    assert resultado["status"] == "concluido"
    assert sum(resultado["importacoes"].values()) == 1

    [importada] = importadas(api, admin)
    assert importada["status"] in ("carregada", "carregada_com_avisos")
    assert importada["fazendas"] == ["TESTE"]
    assert importada["finalizado_em"] is not None
    with engine_super.connect() as c:
        guardado = c.execute(text("SELECT conteudo, job_id FROM ingest.importacao")).one()
        quem_pediu = c.scalar(text("SELECT u.email FROM ingest.job j JOIN core.usuario u ON u.id = j.usuario_id "
                                   "WHERE j.id = :j"), {"j": guardado.job_id})
        unidade = c.execute(text("SELECT chave, metadados FROM ingest.unidade_origem")).one()
    assert guardado.conteudo is None                        # o arquivo sai depois de carregado
    assert quem_pediu == "admin@terra.test"
    assert unidade.chave == ARQUIVO                         # a mesma unidade que a pasta usaria
    assert unidade.metadados["importacao_id"] == recebida["id"]


def test_tecnico_importa_so_as_fazendas_dele(api, admin, fila, engine_etl, engine_super, tmp_path):
    enviar(api, admin, ARQUIVO, planilha(tmp_path))
    importacoes_na_fila(engine_etl)
    fazenda = fazenda_do_codigo(engine_super, 85)
    usuario_com_senha(engine_super, "tecnico@terra.test", fazendas=[fazenda])
    usuario_com_senha(engine_super, "outro@terra.test")
    tecnico, outro = entrar(api, "tecnico@terra.test"), entrar(api, "outro@terra.test")

    enviar(api, tecnico, ARQUIVO, planilha(tmp_path, saldo_bezerro=1200))
    importacoes_na_fila(engine_etl)
    assert importadas(api, tecnico)[0]["status"] in ("carregada", "carregada_com_avisos")
    com_o_tecnico = bezerros_no_saldo_inicial(engine_super, fazenda)

    enviar(api, outro, ARQUIVO, planilha(tmp_path, saldo_bezerro=1500))
    importacoes_na_fila(engine_etl)
    [recusada] = importadas(api, outro)
    assert recusada["status"] == "erro"
    assert "não tem acesso à fazenda 'TESTE'" in recusada["mensagem"]
    assert recusada["fazendas"] == []
    assert bezerros_no_saldo_inicial(engine_super, fazenda) == com_o_tecnico     # nada mudou
    with engine_super.connect() as c:
        codigos = set(c.scalars(text("SELECT codigo FROM ingest.ocorrencia")))
    assert "PERMISSION_DENIED" in codigos


def test_fazenda_nova_so_o_admin_cadastra(api, fila, engine_etl, engine_super, tmp_path):
    usuario_com_senha(engine_super, "tecnico@terra.test")
    tecnico = entrar(api, "tecnico@terra.test")
    enviar(api, tecnico, ARQUIVO, planilha(tmp_path))
    importacoes_na_fila(engine_etl)
    [recusada] = importadas(api, tecnico)
    assert recusada["status"] == "erro"
    assert "ainda não está na plataforma" in recusada["mensagem"]
    with engine_super.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM core.fazenda")) == 0


def test_o_mesmo_arquivo_de_novo_sai_inalterado(api, admin, fila, engine_etl, tmp_path):
    dados = planilha(tmp_path)
    enviar(api, admin, ARQUIVO, dados)
    importacoes_na_fila(engine_etl)
    enviar(api, admin, ARQUIVO, dados)
    assert importacoes_na_fila(engine_etl)["importacoes"] == {"inalterada": 1}
    segunda = importadas(api, admin)[0]
    assert (segunda["status"], segunda["mensagem"], segunda["fazendas"]) == ("inalterada", JA_CARREGADA, ["TESTE"])


def test_o_que_nao_e_planilha_e_recusado_na_hora(api, admin, fila, engine_super, tmp_path):
    nome_errado = enviar(api, admin, "minha planilha.xlsm", planilha(tmp_path))
    assert nome_errado.status_code == 422
    assert "RELATÓRIO - código do projeto - fazenda" in nome_errado.json()["detail"]
    nao_e_excel = enviar(api, admin, ARQUIVO, b"isto nao e um arquivo do excel")
    assert nao_e_excel.status_code == 422
    assert "não é uma planilha do Excel" in nao_e_excel.json()["detail"]
    vazio = enviar(api, admin, ARQUIVO, b"")
    assert vazio.status_code == 422
    assert fila.avisos == 0
    with engine_super.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM ingest.importacao")) == 0


def test_arquivo_corrompido_volta_com_o_motivo_em_portugues(api, admin, fila, engine_etl):
    corrompido = b"PK\x03\x04" + b"\x00" * 64                  # parece zip, mas não abre
    assert enviar(api, admin, ARQUIVO, corrompido).status_code == 202
    assert importacoes_na_fila(engine_etl)["importacoes"] == {"erro": 1}
    [importada] = importadas(api, admin)
    assert importada["mensagem"].startswith("o arquivo não abre como planilha do Excel")


def test_cada_um_ve_as_suas_e_as_das_fazendas_que_acompanha(api, admin, fila, engine_etl, engine_super, engine_api,
                                                             tmp_path):
    enviar(api, admin, ARQUIVO, planilha(tmp_path))
    enviar(api, admin, OUTRA, planilha(tmp_path, OUTRA, codigo=86, fazenda="OUTRA"))
    assert sum(importacoes_na_fila(engine_etl)["importacoes"].values()) == 2
    teste, outra = fazenda_do_codigo(engine_super, 85), fazenda_do_codigo(engine_super, 86)
    usuario_com_senha(engine_super, "a@terra.test", fazendas=[teste])
    sem_fazenda_id = usuario_com_senha(engine_super, "c@terra.test")
    da_teste, sem_fazenda = entrar(api, "a@terra.test"), entrar(api, "c@terra.test")
    enviar(api, sem_fazenda, OUTRA, planilha(tmp_path, OUTRA, codigo=86, fazenda="OUTRA", saldo_bezerro=7))
    importacoes_na_fila(engine_etl)

    assert len(importadas(api, admin)) == 3                                     # o admin vê todas
    vistas = importadas(api, da_teste)                                          # a da fazenda dele, enviada pelo admin
    assert [(item["arquivo"], item["minha"], item["fazendas"]) for item in vistas] == [(ARQUIVO, False, ["TESTE"])]
    [propria] = importadas(api, sem_fazenda)                                    # só a que ele mesmo enviou
    assert (propria["minha"], propria["status"]) == (True, "erro")

    with como_usuario(engine_api, sem_fazenda_id) as s:                         # gravar só em nome próprio, na fila
        alteradas = s.execute(text("UPDATE ingest.importacao SET status = 'carregada'")).rowcount
        assert alteradas == 0
    with pytest.raises(ProgrammingError), como_usuario(engine_api, sem_fazenda_id) as s:
        s.execute(text("INSERT INTO ingest.importacao (usuario_id, enviado_por, arquivo, sha256, tamanho_bytes, "
                       "conteudo) VALUES (:u, 'x', 'x', 'x', 1, 'x')"), {"u": outra})


def test_sem_redis_a_importacao_fica_guardada_para_a_agenda(api, admin, monkeypatch, engine_etl, tmp_path):
    def fila_fora():
        raise OperationalError("Redis fora do ar")

    monkeypatch.setattr(importacoes, "enviar_para_a_fila", fila_fora)
    resposta = enviar(api, admin, ARQUIVO, planilha(tmp_path))
    assert resposta.status_code == 202
    assert resposta.json()["status"] == "na_fila"
    assert sum(importacoes_na_fila(engine_etl)["importacoes"].values()) == 1


def test_com_outra_carga_rodando_a_importacao_espera(api, admin, fila, engine_etl, tmp_path):
    enviar(api, admin, ARQUIVO, planilha(tmp_path))
    with trava_das_cargas(engine_etl, esperar=False):
        assert importacoes_na_fila(engine_etl) == {"status": "ocupada"}
    assert importadas(api, admin)[0]["status"] == "na_fila"


def test_carga_interrompida_no_meio_vira_erro(api, admin, fila, engine_etl, engine_super, tmp_path):
    enviar(api, admin, ARQUIVO, planilha(tmp_path))
    with engine_super.begin() as c:                  # um worker que caiu depois de pegar o arquivo
        c.execute(text("UPDATE ingest.importacao SET status = 'processando'"))
    assert importacoes_na_fila(engine_etl)["importacoes"] == {}
    [interrompida] = importadas(api, admin)
    assert interrompida["status"] == "erro"
    assert "envie o arquivo de novo" in interrompida["mensagem"]
