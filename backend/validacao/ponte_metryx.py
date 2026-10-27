"""Ponte de validação Metryx: monta, a partir das `stg_*` do datalake atual, o MESMO JSON que a API devolveria e usa o
normalizador de produção (app/etl/adapters/metryx/normalizar.py). Assim o cruzamento com o BI testa o adapter real.

As stg_* são os DTOs da API com os nomes em minúsculas; os nomes voltam ao formato do OpenAPI. O que a stg perdeu é
reconstruído como o Pentaho/BI faz, e fica marcado:
- vendas/compras sem idFarm (a API tem): casadas pelo nome da fazenda via stg_farm;
- financeiro sem idFarmFiscal (a API tem): casado pelo nome da fazenda fiscal;
- transferências e retiros: o Pentaho não extrai -> status "ausente" (nenhuma partição desses endpoints).
"""

import json
from collections import defaultdict

from app.core.config import RAIZ_REPO
from app.etl.adapters.base import Bruto, UnidadeOrigem, sha256_json
from app.etl.adapters.metryx.normalizar import normalizar
from app.etl.canonical import LoteCanonico
from validacao.datalake import consultar, jsonavel

BANCO = "METRYX"

# endpoint -> (tabela stg, DTO do OpenAPI)
STG = {
    "fazenda": ("stg_farm", "ApiMetryxFazendasDTO"),
    "categoria": ("stg_category", "ApiMetryxLiCategoriesDTO"),
    "balanco": ("stg_balanco_pecuario", "ApiMetryxLiBalanceDTO"),
    "venda": ("stg_vendas", "ApiMetryxLiSaleDTO"),
    "compra": ("stg_compras", "ApiMetryxLiBuyDTO"),
    "nascimento": ("stg_nascimentos", "ApiMetryxLiBirthDTO"),
    "morte": ("stg_mortes", "ApiMetryxDeathsDTO"),
    "desmame": ("stg_desmames", "ApiMetryxDesmamesPecuariosDTO"),
    "mudanca_categoria": ("stg_mudanca_categoria", "ApiMetryxLiCategoryChangeDTO"),
    "rebanho_medio": ("stg_rebanho_medio", "ApiMetryxLiAvgRebanhoDTO"),
    "lancamento": ("stg_dre", "ApiMetryxLancamentoFinanceiroDTO"),
}


def _campos_openapi() -> dict[str, dict[str, str]]:
    api = json.loads((RAIZ_REPO / "docs/referencias/metryx_openapi.json").read_text(encoding="utf-8-sig"))
    schemas = api["components"]["schemas"]
    return {dto: {p.lower(): p for p in schemas[dto]["properties"]} for _, dto in STG.values()}


class PonteMetryx:
    fonte = "metryx"

    def __init__(self, clientes: list[str] | None = None):
        campos = _campos_openapi()
        self._por_cliente: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
        for nome, (tabela, dto) in STG.items():
            mapa = campos[dto]
            colunas = "*" if tabela != "stg_customers" else "idcustomer, customer, idfarm, farmname"
            # ORDER BY ctid: ordem gravada pelo Pentaho = ordem do JSON da API (decide empates como o BI)
            for linha in consultar(BANCO, f'SELECT {colunas} FROM "DATABASE".{tabela} ORDER BY ctid'):
                item = {mapa.get(k, k): jsonavel(v) for k, v in linha.items()}
                self._por_cliente[linha["idcustomer"]][nome].append(item)
        for dados in self._por_cliente.values():   # reconstrói os ids que a stg perdeu (a API tem)
            por_nome = {f["farmName"]: f["idFarm"] for f in dados["fazenda"]}
            for nome in ("venda", "compra"):
                for item in dados[nome]:
                    item.setdefault("idFarm", por_nome.get(item.get("farmName")))
            for item in dados["lancamento"]:
                item.setdefault("idFarmFiscal", por_nome.get(item.get("farmFiscal")))
        self.clientes = clientes or sorted(c for c, d in self._por_cliente.items() if d["fazenda"])

    def descobrir(self) -> list[UnidadeOrigem]:
        return [UnidadeOrigem(chave=f"stg:{c}", descricao=f"Metryx (stg) cliente {c}") for c in self.clientes]

    def extrair(self, unidade: UnidadeOrigem) -> Bruto:
        cid = unidade.chave.split(":", 1)[1]
        dados = self._por_cliente[cid]
        status = {nome: "ok" for nome in STG} | {"retiro": "ausente", "transferencia": "ausente"}
        conteudo = {"idCustomer": cid, "endpoints": status, "dados": {nome: dados.get(nome, []) for nome in STG}}
        return Bruto(unidade, "json", conteudo, sha256_json(conteudo), len(str(conteudo)), {"endpoint": "stg_*"})

    def normalizar(self, bruto: Bruto) -> LoteCanonico:
        return normalizar(bruto.conteudo)
