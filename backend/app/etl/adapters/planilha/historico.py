"""Carga única do histórico das planilhas a partir do snapshot do datalake do BI (decisão Q6, 14/10/2026).

Por quê: na virada de safra o consultor começa a planilha do zero, e a safra anterior só existe no datalake do BI
(`DATALAKE_PLAN`, tabelas `stg_*` gravadas pelo Pentaho). Esta carga a traz para o canônico com a MESMA identidade
do adapter de planilhas (fonte 'planilha', código do projeto + fazenda); daí em diante quem responde é o arquivo.

Fronteira, por fazenda e entidade: o histórico só entra ANTES do que os arquivos já carregados cobrem, pela mesma
regra do `desde` do adapter: min(início do PERÍODO do arquivo, mês mais antigo das linhas do arquivo). Fazenda sem
arquivo carregado recebe tudo até `ate` (aviso `HISTORY_WITHOUT_FILE`). Por isso esta carga roda DEPOIS da carga das
planilhas. A fronteira vai no bruto, então reprocessar dá o mesmo resultado.

Estoque: o snapshot só tem o saldo por categoria BI (aba fMovRebanho). O histórico usa categorias próprias
("BI:<categoria>", que nunca colidem com as categorias locais da planilha). No dia do saldo inicial do arquivo, cada
categoria do histórico recebe checkpoint 0: dali em diante vale o saldo da planilha, e a diferença aparece como ajuste
de inventário. Se o arquivo traz lançamentos anteriores ao próprio PERÍODO, o saldo do histórico não fecharia com eles
e fica de fora (só o checkpoint 0).

A montagem do lote (função pura) está em `historico_normalizar.py`.
"""

from datetime import date
from decimal import Decimal
from typing import Any

import psycopg
from psycopg.rows import dict_row
from sqlalchemy import Engine, text

from app.core.config import get_settings
from app.etl.adapters.base import Bruto, UnidadeOrigem, sha256_json
from app.etl.adapters.planilha.historico_normalizar import identidade, normalizar_historico
from app.etl.canonical import LoteCanonico

ATE_PADRAO = date(2026, 6, 1)       # último mês do histórico (Q6: "até 06/2026"); dali em diante, os arquivos
PREFIXO = "historico:"

# Chave de fazenda do BI (a mesma das tabelas stg_*): proprietário + fazenda, sem acento e sem espaço.
PROP_FAZ = """unaccent(replace(concat("proprietÁrio", fazenda), ' ', '')) AS prop_faz"""
COLUNAS_COMUNS = f'"DATA" AS data, qtd, categoria_bi, retiro, {PROP_FAZ}'
COLUNAS_COMPRA = f'{COLUNAS_COMUNS}, total_peso, "VALOR TOTAL" AS valor, origem AS contraparte, categ_fazenda'
COLUNAS_ABATE = f"{COLUNAS_COMUNS}, pesovivo_total, pesomorto_total, faturamento, cliente, era, categ_fazenda"
COLUNAS_EM_PE = f"{COLUNAS_COMUNS}, pesovivo_total, faturamento, cliente, documento, categ_fazenda"
COLUNAS_MORTE = f'{COLUNAS_COMUNS}, peso_total, causa, "LOCAL" AS local, safra, categ_fazenda'
COLUNAS_NASCIMENTO = f"{COLUNAS_COMUNS}, peso_nasc, safra, categ_fazenda"
COLUNAS_TRANSFERENCIA = f'{COLUNAS_COMUNS}, total_peso, "VALOR TOTAL" AS valor, categoria_fazenda AS categ_fazenda'
COLUNAS_REBANHO = f'grupo_categoria, qtd_cab, qtd_ua, "DATA" AS data, {PROP_FAZ}'
COLUNAS_AREA = f'"DATA" AS data, "Área_pasto" AS pasto, "Área_ilp" AS ilp, "Área_total" AS total, {PROP_FAZ}'
COLUNAS_DRE = (f'centro_de_custo, sub_centro, valor, "operaÇÃo" AS operacao, centro_de_custo_bi, sub_centro_bi, '
               f'data_pag, {PROP_FAZ}')

# nome no bruto -> consulta (as tabelas ficam no schema "DATABASE" do datalake)
CONSULTAS = {
    "unidades": f'SELECT projeto, "CÓDIGO PROJETO" AS codigo, "SISTEMA PRODUTIVO" AS sistema, ano, fazenda, '
                f'"proprietÁrio" AS proprietario, filename, {PROP_FAZ} FROM "DATABASE".stg_unidades '
                f'WHERE projeto IS NOT NULL',
    "movgado": f'SELECT "operaÇÃo" AS operacao, "DATA" AS data, qtd, categoria_bi, retiro, {PROP_FAZ} '
               f'FROM "DATABASE".stg_fmovgado',
    "rebanho": f'SELECT {COLUNAS_REBANHO} FROM "DATABASE".stg_frebanhomedio',
    "area": f'SELECT {COLUNAS_AREA} FROM "DATABASE".stg_area',
    "dre": f'SELECT {COLUNAS_DRE} FROM "DATABASE".stg_fdre',
    "meta_rebanho": f'SELECT {COLUNAS_REBANHO} FROM "DATABASE".stg_fmetasrebanhomedio',
    "meta_area": f'SELECT {COLUNAS_AREA} FROM "DATABASE".stg_fmetasarea',
    "meta_dre": f'SELECT {COLUNAS_DRE} FROM "DATABASE".stg_fmetasdre',
    "compras": f'SELECT {COLUNAS_COMPRA} FROM "DATABASE".stg_fcompras',
    "meta_compras": f'SELECT {COLUNAS_COMPRA} FROM "DATABASE".stg_fmetascompras',
    "abate": f'SELECT {COLUNAS_ABATE} FROM "DATABASE".stg_fvendaabate',
    "meta_abate": f'SELECT {COLUNAS_ABATE} FROM "DATABASE".stg_fmetasabates',
    "empe": f'SELECT {COLUNAS_EM_PE} FROM "DATABASE".stg_fvendaempe',
    "meta_empe": f'SELECT {COLUNAS_EM_PE} FROM "DATABASE".stg_fmetasempe',
    "mortes": f'SELECT {COLUNAS_MORTE} FROM "DATABASE".stg_fmortes',
    "meta_mortes": f'SELECT {COLUNAS_MORTE} FROM "DATABASE".stg_fmetasmorte',
    "nascimentos": f'SELECT {COLUNAS_NASCIMENTO} FROM "DATABASE".stg_fnascimento',
    "meta_nascimentos": f'SELECT {COLUNAS_NASCIMENTO} FROM "DATABASE".stg_fmetasnascimento',
    "transf_entrada": f'SELECT {COLUNAS_TRANSFERENCIA} FROM "DATABASE".stg_ftransfentrada',
    "meta_transf_entrada": f'SELECT {COLUNAS_TRANSFERENCIA} FROM "DATABASE".stg_fmetastransfentrada',
    "transf_saida": f'SELECT {COLUNAS_TRANSFERENCIA} FROM "DATABASE".stg_ftransfsaida',
    "meta_transf_saida": f'SELECT {COLUNAS_TRANSFERENCIA} FROM "DATABASE".stg_fmetatransfsaida',
}

# Até onde os arquivos já carregados cobrem a fazenda (unidade com mtime = arquivo; o histórico não tem mtime).
FRONTEIRA = """
WITH faz AS (SELECT entidade_id AS id FROM core.fonte_vinculo
             WHERE fonte = 'planilha' AND entidade = 'fazenda' AND id_externo = :f),
     arq AS (SELECT v.id FROM ingest.versao_origem v JOIN ingest.unidade_origem u ON u.id = v.unidade_id
             WHERE u.fonte = 'planilha' AND u.metadados ? 'mtime')
SELECT
  (SELECT min(data) + 1 FROM fato.inventario
    WHERE fazenda_id IN (SELECT id FROM faz) AND origem_ref IN (SELECT id FROM arq)) AS inicio_arquivo,
  (SELECT min(competencia) FROM fato.mov_animal WHERE cenario = 'realizado'
     AND fazenda_id IN (SELECT id FROM faz) AND origem_ref IN (SELECT id FROM arq)) AS mov_realizado,
  (SELECT min(competencia) FROM fato.mov_animal WHERE cenario = 'planejado'
     AND fazenda_id IN (SELECT id FROM faz) AND origem_ref IN (SELECT id FROM arq)) AS mov_planejado,
  (SELECT min(competencia) FROM fato.lancamento_financeiro
    WHERE fazenda_id IN (SELECT id FROM faz) AND origem_ref IN (SELECT id FROM arq)) AS lancamento,
  (SELECT min(competencia) FROM fato.orcamento_financeiro
    WHERE fazenda_id IN (SELECT id FROM faz) AND origem_ref IN (SELECT id FROM arq)) AS orcamento,
  (SELECT min(competencia) FROM fato.rebanho_medio_mensal WHERE cenario = 'realizado'
     AND fazenda_id IN (SELECT id FROM faz) AND origem_ref IN (SELECT id FROM arq)) AS rebanho_realizado,
  (SELECT min(competencia) FROM fato.rebanho_medio_mensal WHERE cenario = 'planejado'
     AND fazenda_id IN (SELECT id FROM faz) AND origem_ref IN (SELECT id FROM arq)) AS rebanho_planejado,
  (SELECT min(competencia) FROM fato.area_mensal WHERE cenario = 'realizado'
     AND fazenda_id IN (SELECT id FROM faz) AND origem_ref IN (SELECT id FROM arq)) AS area_realizado,
  (SELECT min(competencia) FROM fato.area_mensal WHERE cenario = 'planejado'
     AND fazenda_id IN (SELECT id FROM faz) AND origem_ref IN (SELECT id FROM arq)) AS area_planejado
"""


def para_json(valor: Any) -> Any:
    """Linhas do datalake -> valores que cabem em JSON (Decimal vira número, data vira texto ISO)."""
    if isinstance(valor, dict):
        return {chave: para_json(item) for chave, item in valor.items()}
    if isinstance(valor, list | tuple):
        return [para_json(item) for item in valor]
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, date):
        return valor.isoformat()
    return valor


def ler_datalake(conninfo: str) -> dict[str, dict[str, list[dict]]]:
    """PROP_FAZ -> {consulta: linhas}. Conexão somente leitura; nunca toca em tabelas de token."""
    por_fazenda: dict[str, dict[str, list[dict]]] = {}
    with psycopg.connect(conninfo, options="-c default_transaction_read_only=on", row_factory=dict_row) as conexao:
        for nome, sql in CONSULTAS.items():
            for linha in conexao.execute(sql):
                tabelas_da_fazenda = por_fazenda.setdefault(linha["prop_faz"], {})
                tabelas_da_fazenda.setdefault(nome, []).append(linha)
    return por_fazenda


def tem_algum_fato(tabelas: dict[str, list[dict]]) -> bool:
    """Há fazenda só com cadastro (stg_unidades) e nenhum dado: essa não vira unidade."""
    return any(linhas for nome, linhas in tabelas.items() if nome != "unidades")


class AdapterHistoricoPlanilha:
    """Uma unidade por PROP_FAZ do snapshot. Roda depois da carga das planilhas (ver a fronteira no docstring)."""

    fonte = "planilha"

    def __init__(self, engine: Engine, *, ate: date = ATE_PADRAO, prop_faz: list[str] | None = None,
                 linhas: dict[str, dict[str, list[dict]]] | None = None, conninfo: str | None = None):
        if ate.day != 1:
            raise ValueError("ate é o 1º dia do último mês do histórico")
        self.engine = engine
        self.ate = ate
        self.prop_faz = prop_faz
        self._linhas = linhas            # nos testes, as linhas vêm prontas; em produção, do datalake
        self._conninfo = conninfo

    def _dados(self) -> dict[str, dict[str, list[dict]]]:
        if self._linhas is None:
            conninfo = self._conninfo or get_settings().datalake_plan_url
            if not conninfo:
                raise ValueError("defina DATALAKE_PLAN_URL no .env (datalake do BI de planilhas, só leitura)")
            self._linhas = ler_datalake(conninfo)
        return self._linhas

    def descobrir(self) -> list[UnidadeOrigem]:
        dados = self._dados()
        if self.prop_faz:
            chaves = self.prop_faz
        else:
            chaves = sorted(chave for chave, tabelas in dados.items() if chave and tem_algum_fato(tabelas))
        unidades = []
        for prop_faz in chaves:
            # carga_unica: o snapshot não é relido, então corrigir a planilha antiga não muda nada; a aba Pendências
            # (app.pendencias_de_carga) deixa essas unidades de fora
            unidades.append(UnidadeOrigem(chave=f"{PREFIXO}{prop_faz}",
                                          descricao=f"Histórico da planilha (snapshot do BI) {prop_faz}",
                                          metadados={"prop_faz": prop_faz, "ate": self.ate.isoformat(),
                                                     "carga_unica": True}))
        return unidades

    def extrair(self, unidade: UnidadeOrigem) -> Bruto:
        prop_faz = unidade.chave.removeprefix(PREFIXO)
        tabelas = self._dados().get(prop_faz, {})
        cadastro = (tabelas.get("unidades") or [None])[0]
        _, fazenda = identidade(cadastro)
        with self.engine.connect() as conexao:
            fronteira = dict(conexao.execute(text(FRONTEIRA), {"f": fazenda}).mappings().one())
        conteudo = para_json({"prop_faz": prop_faz, "ate": self.ate.isoformat(), "fronteira": fronteira, **tabelas})
        return Bruto(unidade, "json", conteudo, sha256_json(conteudo), len(str(conteudo)),
                     {"endpoint": "stg_*", "prop_faz": prop_faz})

    def normalizar(self, bruto: Bruto) -> LoteCanonico:
        return normalizar_historico(bruto.conteudo)
