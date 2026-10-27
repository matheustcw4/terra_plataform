"""Allow-list dos endpoints Metryx que o adapter pode chamar (somente GET).

`POST /api-metryx/control-birth` ESCREVE no Metryx e nunca entra aqui. O cliente HTTP recusa qualquer caminho fora
desta lista. A API não aceita parâmetros: cada chamada devolve o histórico completo do cliente dono do token.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Endpoint:
    nome: str
    caminho: str
    obrigatorio: bool = False   # sem ele o lote não faz sentido (falha => unidade em erro, nada muda)
    # A29 (API real, 15/10/2026): o endpoint devolve outro idCustomer nos itens do próprio cliente; o item vale se a
    # fazenda dele for do cliente (conferida pelo endpoint `fazenda`). Nos outros, idCustomer diferente bloqueia.
    confere_pela_fazenda: bool = False


ENDPOINTS: dict[str, Endpoint] = {e.nome: e for e in (
    Endpoint("fazenda", "/api-metryx/fazenda", obrigatorio=True),
    Endpoint("categoria", "/api-metryx/categoria", obrigatorio=True),
    Endpoint("retiro", "/api-metryx/retiro"),
    Endpoint("balanco", "/api-metryx/balanco-pecuario"),
    Endpoint("nascimento", "/api-metryx/nascimento-pecuario"),
    Endpoint("morte", "/api-metryx/morte-pecuario"),
    Endpoint("desmame", "/api-metryx/desmames-pecuario"),
    Endpoint("mudanca_categoria", "/api-metryx/mudanca-categoria-pecuario", confere_pela_fazenda=True),
    Endpoint("transferencia", "/api-metryx/transferencia-animal-pecuario"),
    Endpoint("venda", "/api-metryx/venda-pecuario"),
    Endpoint("compra", "/api-metryx/compra-pecuario"),
    Endpoint("rebanho_medio", "/api-metryx/rebanho-medio-pecuario"),
    Endpoint("lancamento", "/api-metryx/lancamento-financeiro"),
    # vai para o bruto, mas o normalizador ainda não usa: o estoque segue o balanço (regra do BI); serve para conferir
    # o saldo de implantação contra o DMG do Metryx (relatório de validação §17). O nome do caminho é assim na API.
    Endpoint("saldo_inicial", "/api-metryx/saldo-inical-pecuario"),
    # área de pasto (lotação); o token precisa da permissão UTILIZACAO_PASTO: sem ela (403), a área fica como estava
    Endpoint("pasto", "/api-metryx/utilizacao-pasto"),
    # TODO: previsao-financeiro e os *-mensal-planejamento (planejado)
)}

CAMINHOS_PERMITIDOS: frozenset[str] = frozenset(e.caminho for e in ENDPOINTS.values())
CAMINHOS_PROIBIDOS: frozenset[str] = frozenset({"/api-metryx/control-birth"})
assert not CAMINHOS_PERMITIDOS & CAMINHOS_PROIBIDOS
