"""JSON da API Metryx -> LoteCanonico. Função pura (sem banco, sem rede): reprocessável a partir do bruto guardado.

Entrada (o que AdapterMetryx.extrair grava em raw.payload):
    {"idCustomer": "...",
     "endpoints": {"<nome>": "ok" | "proibido" | "ausente" | "erro"},
     "dados": {"<nome>": [<itens do DTO, campos como no OpenAPI>]}}

Regras (validadas contra o BI em 14/10/2026, docs/validacao/2026-10-14_cruzamento_bi.md):
- estoque: checkpoints no fim de cada mês com registro de balanço, pela regra do BI (saldo.py);
- `morte-pecuario` traz o idRetiro legado (inteiro): resolvido pelo nome do retiro dentro da fazenda;
- `weightTotal` da compra às vezes é total, às vezes por cabeça (doc 02 §5.1);
- baixa com causa de consumo ou doação ("Consumo Abate", "Consumo Acidente", "Doação") vira consumo/doação, como
  no Consolidado Pecuário do próprio Metryx (o BI só contava "Consumo Abate"); estorno (valor negativo) inverte a
  natureza;
- financeiro realizado = pago; fazenda = destino (D2), fazenda fiscal guardada;
- transferência: 1 registro vira 2 linhas (saída na origem, entrada no destino), só para fazendas deste cliente;
- payload real (15/10/2026): venda, compra e o destino da transferência vêm sem o id da fazenda, que sai do retiro
  (A30); as transferências antigas vêm sem quantidade e ficam de fora, com um aviso só (A31);
- área de pasto: `utilizacao-pasto`, as pastagens de uso Pecuária no fim de cada mês (pasto.py), do mês do primeiro
  período cadastrado até o último mês do rebanho médio; a UA ainda não vem da API (o `weight` do rebanho médio não
  entra);
- partições só dos endpoints que vieram ("ok"), com guarda de volume: resposta vazia/parcial não apaga dados.

Como ler: `normalizar()` chama uma etapa por endpoint; cada etapa é um método de `MontagemMetryx`.
"""

import unicodedata
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import ValidationError

from app.etl.adapters.metryx.categoria import sugerir_categoria_bi
from app.etl.adapters.metryx.pasto import PeriodoDePasto, area_no_dia, eh_uso_pecuario
from app.etl.adapters.metryx.saldo import RegistroBalanco, fim_do_mes, saldo_fim_de_mes
from app.etl.canonical import (
    AreaMensal,
    ChaveCategoria,
    ContaOrigem,
    Inventario,
    LancamentoFinanceiro,
    LinhaRejeitada,
    LoteCanonico,
    MovAnimal,
    Ocorrencia,
    Particao,
    RebanhoMedio,
    RefCategoria,
    RefCliente,
    RefFazenda,
    RefRetiro,
    proximo_mes,
)

GUARDA_VOLUME = 0.5
CARACTERES_INVISIVEIS = dict.fromkeys(map(ord, "​‌‍﻿"))   # aparecem nos nomes de centro de custo

# endpoint -> (entidade canônica, tipos de mov_animal pelos quais ele é autoritativo)
PARTICOES_DO_ENDPOINT: dict[str, tuple[str, tuple[str, ...] | None]] = {
    "venda": ("mov_animal", ("ABATE", "VENDA_EM_PE")),
    "compra": ("mov_animal", ("COMPRA",)),
    "nascimento": ("mov_animal", ("NASCIMENTO",)),
    "morte": ("mov_animal", ("MORTE", "CONSUMO_DOACAO")),
    "desmame": ("mov_animal", ("DESMAME",)),
    "mudanca_categoria": ("mov_animal", ("MUDANCA_CATEGORIA",)),
    "transferencia": ("mov_animal", ("TRANSF_ENTRADA", "TRANSF_SAIDA")),
    "balanco": ("inventario", None),
    "rebanho_medio": ("rebanho_medio", None),
    "lancamento": ("lancamento", None),
    "pasto": ("area", None),
}


def para_decimal(valor: Any) -> Decimal | None:
    if valor is None or valor == "":
        return None
    return Decimal(str(valor))


def para_data(valor: Any) -> date | None:
    """Datas do Metryx: 'AAAA-MM-DD' (às vezes com hora depois) ou 'DD/MM/AAAA'; nos mensais, 'M-AAAA' / 'MM/AA'."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, date):
        return valor
    texto = str(valor).strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto[:10], formato).date()
        except ValueError:
            continue
    return _mes_e_ano(texto)


def _mes_e_ano(texto: str) -> date | None:
    for separador in ("-", "/"):
        partes = texto.split(separador)
        if len(partes) != 2 or not all(parte.isdigit() for parte in partes):
            continue
        mes, ano = int(partes[0]), int(partes[1])
        if ano < 100:
            ano += 2000
        if 1 <= mes <= 12:
            return date(ano, mes, 1)
    return None


def peso_total_compra(peso: Any, qtd: Any) -> tuple[Decimal | None, str | None]:
    """`weightTotal` da compra: total se der 100–900 kg/cab; senão, se 20–900, é por cabeça; senão, sem peso.
    Devolve (peso total, problema)."""
    peso_informado, cabecas = para_decimal(peso), para_decimal(qtd)
    if peso_informado is None or not cabecas:
        return None, None
    if 100 <= peso_informado / cabecas <= 900:
        return peso_informado, None
    if 20 <= peso_informado <= 900:
        return peso_informado * cabecas, None
    return None, f"weightTotal={peso_informado} para {cabecas} cab: nem total nem por cabeça plausível"


def chave_do_evento(item: dict, campo_origem: str, campo_destino: str) -> tuple:
    """O mesmo evento em dois endpoints (desmame e mudança de categoria): data, categorias, retiro e quantidade."""
    return (str(item.get("date"))[:10], item.get(campo_origem), item.get(campo_destino), item.get("retiroName"),
            para_decimal(item.get("amount")))


def sem_vazios(campos: dict[str, Any]) -> dict[str, Any]:
    return {nome: valor for nome, valor in campos.items() if valor is not None}


def eh_consumo_ou_doacao(causa: Any) -> bool:
    """O Consolidado Pecuário do Metryx põe em "Consumo e Doação" as baixas de causa "Consumo ..." (U6, mai/2026:
    "Consumo Abate" e "Consumo Acidente") e as de doação. A regra segue o Metryx, não o BI (que só contava "Consumo
    Abate"): o número tem de bater com o Metryx (pedido do usuário, 20/10/2026)."""
    texto = unicodedata.normalize("NFKD", str(causa or "")).encode("ascii", "ignore").decode().upper().strip()
    return texto.startswith("CONSUMO") or texto.startswith("DOACAO")


def limpar_nome(texto: Any) -> str:
    return (texto or "").translate(CARACTERES_INVISIVEIS).strip()


# --- montagem do lote ----------------------------------------------------------------------------------------------

def normalizar(conteudo: dict[str, Any]) -> LoteCanonico:
    metryx = MontagemMetryx(conteudo)
    metryx.identidades()
    metryx.retiros_do_cadastro()
    metryx.categorias()
    metryx.saldos_do_balanco()
    metryx.vendas()
    metryx.compras()
    metryx.nascimentos()
    metryx.mortes()
    metryx.desmames()
    metryx.mudancas_de_categoria()
    metryx.transferencias()
    metryx.rebanho_medio()
    metryx.areas()
    metryx.lancamentos()
    metryx.particoes()
    return metryx.lote


class MontagemMetryx:
    def __init__(self, conteudo: dict[str, Any]):
        self.cliente: str = conteudo["idCustomer"]
        self.status: dict[str, str] = conteudo.get("endpoints", {})
        self.dados: dict[str, list[dict]] = conteudo.get("dados", {})
        self.lote = LoteCanonico(fonte="metryx")
        self.fazenda_por_id: dict[str, str] = {}        # idFarm -> id externo da fazenda
        self.fazenda_por_nome: dict[str, str] = {}      # farmName -> id externo da fazenda
        self.fazenda_do_retiro: dict[str, str] = {}     # idRetiro uuid -> idFarm
        self.retiros: dict[str, RefRetiro] = {}
        self.categorias_da_api: dict[str, dict] = {}    # idCategory -> categoria
        self.uuid_do_retiro: dict[tuple[str, str], str] = {}     # (idFarm, retiroName) -> idRetiro uuid

    # -- apoio --

    def aviso(self, codigo: str, mensagem: str, contexto: dict | None = None) -> None:
        self.lote.ocorrencias.append(Ocorrencia(nivel="aviso", codigo=codigo, mensagem=mensagem,
                                                contexto=contexto or None))

    def rejeitar(self, entidade: str, item: dict, ref: str, codigo: str, motivo: str,
                 fazenda: str | None = None) -> None:
        self.lote.rejeitadas.append(LinhaRejeitada(entidade=entidade, origem_linha=ref, codigo=codigo, motivo=motivo,
                                                   dados=item, fazenda=fazenda))

    def fazenda_pelo_id(self, item: dict, campo_id: str = "idFarm", campo_retiro: str = "idRetiro") -> str | None:
        """Fazenda do item pelo id dela; sem ele, pela fazenda do retiro (venda, compra e o destino da transferência
        vêm sem o id da fazenda na API real: A30)."""
        if item.get(campo_id) in self.fazenda_por_id:
            return self.fazenda_por_id[item[campo_id]]
        id_da_fazenda = self.fazenda_do_retiro.get(item.get(campo_retiro))
        return self.fazenda_por_id.get(id_da_fazenda)

    def fazenda_de(self, item: dict, campo_id: str = "idFarm", campo_nome: str = "farmName") -> str | None:
        """Fazenda do item pelo id (ou pelo retiro); pelo nome só como último recurso, com aviso."""
        fazenda = self.fazenda_pelo_id(item, campo_id)
        if fazenda is not None:
            return fazenda
        if item.get(campo_nome) in self.fazenda_por_nome:
            self.aviso("FARM_BY_NAME", f"fazenda resolvida pelo nome '{item.get(campo_nome)}'")
            return self.fazenda_por_nome[item[campo_nome]]
        return None

    def retiro(self, fazenda: str, id_retiro: Any, nome: Any) -> str | None:
        if id_retiro in (None, ""):
            return None
        chave = f"{fazenda}|{id_retiro}"
        if chave not in self.retiros:
            self.retiros[chave] = RefRetiro(id_externo=chave, fazenda=fazenda, nome=str(nome or id_retiro))
        return chave

    def categoria(self, id_categoria: Any) -> ChaveCategoria:
        return ChaveCategoria(fonte_mapa="metryx_realizado", escopo="cliente", escopo_id=self.cliente,
                              id_externo=str(id_categoria))

    def lancar(self, ref: str, item: dict, fazenda: str | None, tipo: str, categoria: Any, qtd: Any,
               campos: dict[str, Any], id_retiro: Any = None, nome_retiro: Any = None,
               campo_data: str = "date") -> None:
        """Um lançamento de animais. Sem fazenda deste cliente, sem data, quantidade ou categoria -> quarentena."""
        data = para_data(item.get(campo_data))
        if fazenda is None:
            self.rejeitar("mov_animal", item, ref, "FARM_UNRESOLVED", "fazenda fora deste cliente Metryx")
            return
        if data is None or para_decimal(qtd) is None or categoria in (None, ""):
            self.rejeitar("mov_animal", item, ref, "REQUIRED_MISSING", "sem data, quantidade ou categoria", fazenda)
            return
        if id_retiro is None:
            id_retiro = item.get("idRetiro")
        if nome_retiro is None:
            nome_retiro = item.get("retiroName")
        retiro = self.retiro(fazenda, id_retiro, nome_retiro)
        try:
            mov = MovAnimal(fazenda=fazenda, retiro=retiro, cenario="realizado", tipo=tipo, data=data,
                            categoria=self.categoria(categoria), qtd=para_decimal(qtd), origem_linha=ref,
                            **sem_vazios(campos))
        except ValidationError as exc:
            self.rejeitar("mov_animal", item, ref, "INVALID_ROW", str(exc.errors()[0]["msg"]), fazenda)
            return
        self.lote.mov_animal.append(mov)

    # -- cadastro --

    def identidades(self) -> None:
        fazendas = self.dados.get("fazenda", [])
        nome_cliente = self.cliente
        for fazenda in fazendas:
            if fazenda.get("customer"):
                nome_cliente = fazenda["customer"]
                break
        self.lote.clientes = [RefCliente(id_externo=self.cliente, nome=nome_cliente)]
        for fazenda in fazendas:
            if not fazenda.get("idFarm"):
                continue
            id_externo = f"{self.cliente}|{fazenda['idFarm']}"
            self.fazenda_por_id[fazenda["idFarm"]] = id_externo
            self.fazenda_por_nome[fazenda.get("farmName")] = id_externo
            # o "cliente" que o usuário escolhe no menu: na planilha é o PROPRIETÁRIO; no Metryx, o customer
            self.lote.fazendas.append(RefFazenda(id_externo=id_externo, cliente=self.cliente,
                                                 nome=fazenda.get("farmName") or fazenda["idFarm"],
                                                 proprietario=nome_cliente))

    def retiros_do_cadastro(self) -> None:
        """Guarda a fazenda de cada retiro (A30) e o uuid de cada retiro pelo nome (para as mortes, que trazem o id
        legado) e cadastra os retiros."""
        for endpoint in ("retiro", "balanco", "nascimento", "desmame"):
            for item in self.dados.get(endpoint, []):
                if not item.get("idRetiro") or not item.get("idFarm"):
                    continue
                self.fazenda_do_retiro[item["idRetiro"]] = item["idFarm"]
                if item.get("retiroName"):
                    self.uuid_do_retiro[(item["idFarm"], item["retiroName"])] = item["idRetiro"]
        for item in self.dados.get("retiro", []):
            fazenda = self.fazenda_de(item)
            if fazenda:
                self.retiro(fazenda, item.get("idRetiro"), item.get("retiroName"))

    def categorias(self) -> None:
        """Categorias do cliente com a sugestão de categoria BI (o consultor confirma — D6)."""
        for item in self.dados.get("categoria", []):
            if item.get("idCategory"):
                self.categorias_da_api[item["idCategory"]] = item
        for item in self.categorias_da_api.values():
            sugestao = sugerir_categoria_bi(item.get("categoryGroup"), item.get("ageCategory"), item.get("gender"))
            atributos = {campo: item.get(campo) for campo in ("categoryGroup", "ageCategory", "gender")}
            self.lote.categorias.append(RefCategoria(chave=self.categoria(item["idCategory"]),
                                                     nome=item.get("category") or item["idCategory"],
                                                     categoria_bi=sugestao, atributos=atributos))

    # -- estoque --

    def saldos_do_balanco(self) -> None:
        """Checkpoints de estoque no fim de cada mês, pela regra do BI (saldo.py)."""
        registros = []
        for ordem, item in enumerate(self.dados.get("balanco", [])):
            fazenda = self.fazenda_de(item)
            data = para_data(item.get("date"))
            qtd = para_decimal(item.get("amount"))
            if fazenda is None or data is None or qtd is None:
                continue
            categoria = self.categorias_da_api.get(item.get("uuidCategory"))
            registros.append(RegistroBalanco(
                fazenda=fazenda, retiro=self.retiro(fazenda, item.get("idRetiro"), item.get("retiroName")),
                categoria=item.get("uuidCategory"), owner=item.get("owner"), data=data, quantidade=qtd,
                grupo=categoria.get("categoryGroup") if categoria else None, ano_safra=item.get("anoSafra"),
                nascimento=item.get("birth"), safra=item.get("harvest"), ordem=ordem))
        for (fazenda, retiro, categoria), por_mes in saldo_fim_de_mes(registros).items():
            for fim, qtd in por_mes.items():
                self._checkpoint(fazenda, retiro, categoria, fim, qtd)

    def _checkpoint(self, fazenda: str, retiro: str | None, categoria: str, fim: date, qtd: Decimal) -> None:
        ref = f"balanco:{categoria}:{retiro}:{fim}"
        if qtd < 0:
            dados = {"fazenda": fazenda, "retiro": retiro, "categoria": categoria, "data": fim.isoformat(),
                     "qtd": str(qtd)}
            self.rejeitar("inventario", dados, ref, "NEGATIVE_STOCK", f"saldo negativo ({qtd}) no balanço", fazenda)
            return
        self.lote.inventario.append(Inventario(fazenda=fazenda, retiro=retiro, categoria=self.categoria(categoria),
                                               data=fim, qtd=qtd, origem_linha=ref))

    # -- fluxos --

    def vendas(self) -> None:
        """Abate quando a venda tem arroba morta; senão, venda em pé."""
        for numero, item in enumerate(self.dados.get("venda", [])):
            abate = item.get("deadArrobaAvg") is not None
            qtd = para_decimal(item.get("amount"))
            peso_vivo = para_decimal(item.get("weightTotal"))
            peso_carcaca = None
            if abate and item.get("deadWeightAvg") and qtd:
                peso_carcaca = para_decimal(item["deadWeightAvg"]) * qtd
            veio_por_cabeca = peso_vivo is not None and qtd and peso_vivo / qtd < 20
            if veio_por_cabeca and item.get("liveWeightAVG"):
                peso_vivo = para_decimal(item["liveWeightAVG"]) * qtd
            campos = {"peso_vivo_total_kg": peso_vivo, "peso_carcaca_total_kg": peso_carcaca,
                      "valor_total": para_decimal(item.get("totalFaturamento")), "contraparte": item.get("client"),
                      "extra": {campo: item.get(campo)
                                for campo in ("valueArroba", "additions", "discounts", "owner", "tipo")}}
            self.lancar(f"venda:{numero}", item, self.fazenda_de(item), "ABATE" if abate else "VENDA_EM_PE",
                        item.get("categoryId"), qtd, campos)

    def compras(self) -> None:
        for numero, item in enumerate(self.dados.get("compra", [])):
            peso, problema = peso_total_compra(item.get("weightTotal"), item.get("amount"))
            if problema:
                self.aviso("WEIGHT_AMBIGUOUS", problema, {"origem": f"compra:{numero}"})
            campos = {"peso_vivo_total_kg": peso, "valor_total": para_decimal(item.get("totalFaturamento")),
                      "contraparte": item.get("provider"),
                      "extra": {"weightTotal": item.get("weightTotal"), "owner": item.get("owner")}}
            self.lancar(f"compra:{numero}", item, self.fazenda_de(item), "COMPRA", item.get("categoryId"),
                        item.get("amount"), campos)

    def nascimentos(self) -> None:
        for numero, item in enumerate(self.dados.get("nascimento", [])):
            self.lancar(f"nascimento:{numero}", item, self.fazenda_de(item), "NASCIMENTO", item.get("idCategory"),
                        item.get("amount"), {"safra": item.get("harvest")})

    def id_do_retiro_atual(self, item: dict) -> tuple[Any, bool]:
        """(id do retiro, se veio legado). Morte e mudança de categoria trazem o idRetiro legado (inteiro): troca pelo
        uuid do retiro de mesmo nome na fazenda; sem a troca, o movimento cairia num retiro sem balanço, que o estoque
        nunca corrige."""
        id_retiro = item.get("idRetiro")
        uuid = self.uuid_do_retiro.get((item.get("idFarm"), item.get("retiroName")))
        if uuid and uuid != id_retiro:
            return uuid, True
        return id_retiro, False

    def mortes(self) -> None:
        legados = 0
        for numero, item in enumerate(self.dados.get("morte", [])):
            id_retiro, legado = self.id_do_retiro_atual(item)
            if legado:
                legados += 1
            tipo = "MORTE"
            if eh_consumo_ou_doacao(item.get("cause")):
                tipo = "CONSUMO_DOACAO"
            campos = {"peso_vivo_total_kg": para_decimal(item.get("totalWeight")) or None,
                      "causa": item.get("cause"), "local": item.get("locale"), "safra": item.get("harvest"),
                      "extra": {"notes": item.get("notes"), "idRetiro_original": item.get("idRetiro")}}
            self.lancar(f"morte:{numero}", item, self.fazenda_de(item), tipo, item.get("categoryId"),
                        item.get("amount"), campos, id_retiro=id_retiro)
        if legados:
            self.aviso("LEGACY_RETIRO_ID", f"{legados} morte(s) com idRetiro legado; retiro resolvido pelo nome na "
                       "fazenda")

    def desmames(self) -> None:
        for numero, item in enumerate(self.dados.get("desmame", [])):
            qtd = para_decimal(item.get("amount"))
            peso_por_cabeca = para_decimal(item.get("weight"))
            destino = self.categoria(item["newCategoryId"]) if item.get("newCategoryId") else None
            peso_total = peso_por_cabeca * qtd if peso_por_cabeca and qtd else None
            self.lancar(f"desmame:{numero}", item, self.fazenda_de(item), "DESMAME", item.get("oldCategoryId"), qtd,
                        {"categoria_destino": destino, "peso_vivo_total_kg": peso_total})

    def mudancas_de_categoria(self) -> None:
        """A32 (API real, 15/10/2026): o endpoint repete cada desmame como mudança de categoria (mesma data, categorias,
        retiro e quantidade). A repetição fica de fora, porque o desmame já entrou pelo endpoint dele; sem isso, o mês
        mostraria o desmame em dobro e um ajuste para compensar."""
        desmames = Counter()
        for item in self.dados.get("desmame", []):
            desmames[chave_do_evento(item, "oldCategoryId", "newCategoryId")] += 1
        repetidas = 0
        legados = 0
        for numero, item in enumerate(self.dados.get("mudanca_categoria", [])):
            chave = chave_do_evento(item, "uuidCategoryOrigin", "uuidCategoryDestiny")
            if desmames[chave] > 0:
                desmames[chave] -= 1
                repetidas += 1
                continue
            id_retiro, legado = self.id_do_retiro_atual(item)
            if legado:
                legados += 1
            destino = None
            if item.get("uuidCategoryDestiny"):
                destino = self.categoria(item["uuidCategoryDestiny"])
            self.lancar(f"mudanca:{numero}", item, self.fazenda_de(item), "MUDANCA_CATEGORIA",
                        item.get("uuidCategoryOrigin"), item.get("amount"), {"categoria_destino": destino},
                        id_retiro=id_retiro)
        if repetidas:
            self.aviso("CATEGORY_CHANGE_IS_WEANING",
                       f"{repetidas} mudança(s) de categoria repetiam um desmame e ficaram de fora (o desmame já "
                       "entrou pelo endpoint dele)")
        if legados:
            self.aviso("LEGACY_RETIRO_ID", f"{legados} mudança(s) de categoria com idRetiro legado; retiro resolvido "
                       "pelo nome na fazenda")

    def transferencias(self) -> None:
        """Um registro vira saída na fazenda de origem e entrada na de destino (só fazendas deste cliente, pelo id ou
        pelo retiro; nunca pelo nome, que pode ser de uma fazenda de outro cliente)."""
        datas_sem_quantidade = []
        for numero, item in enumerate(self.dados.get("transferencia", [])):
            if item.get("amount") is None:
                datas_sem_quantidade.append(str(item.get("date"))[:10])
            else:
                self._lancar_transferencia(numero, item)
        if datas_sem_quantidade:
            self._avisar_transferencias_sem_quantidade(datas_sem_quantidade)

    def _lancar_transferencia(self, numero: int, item: dict) -> None:
        """Sem o retiro de origem (a API real não o manda), a saída cairia numa série sem retiro, que nenhum balanço
        corrige, e o estoque da fazenda desceria para sempre. Dentro da mesma fazenda, as duas pontas ficam sem retiro
        e se anulam (o balanço de cada retiro mostra a troca); entre fazendas, a saída fica de fora e o balanço da
        origem mostra a baixa como ajuste."""
        peso, _ = peso_total_compra(item.get("weightTotal"), item.get("amount"))
        origem = self.fazenda_pelo_id(item, "idFarmOrigin", "idRetiroOrigin")
        destino = self.fazenda_pelo_id(item, "idFarmDestiny", "idRetiroDestiny")
        retiro_de_destino = item.get("idRetiroDestiny")
        if not item.get("idRetiroOrigin"):
            if origem == destino:
                retiro_de_destino = None
            else:
                origem = None
        if origem:
            campos = self._campos_transferencia(item, peso, contraparte=item.get("farmNameDestiny"))
            self.lancar(f"transferencia:{numero}:saida", item, origem, "TRANSF_SAIDA", item.get("categoryId"),
                        item.get("amount"), campos, id_retiro=item.get("idRetiroOrigin"),
                        nome_retiro=item.get("retiroNameOrigin"))
        if destino:
            campos = self._campos_transferencia(item, peso, contraparte=item.get("farmNameOrigin"))
            self.lancar(f"transferencia:{numero}:entrada", item, destino, "TRANSF_ENTRADA",
                        item.get("categoryId"), item.get("amount"), campos, id_retiro=retiro_de_destino,
                        nome_retiro=item.get("retiroNameDestiny"))
        if not origem and not destino:
            self.rejeitar("mov_animal", item, f"transferencia:{numero}", "FARM_UNRESOLVED",
                          "origem e destino fora deste cliente")

    def _avisar_transferencias_sem_quantidade(self, datas: list[str]) -> None:
        """A31: a API real devolve as transferências antigas sem `amount` (as novas vêm com ele). Sem quantidade não há
        o que somar, e o defeito é do endpoint, não da linha: o consultor não tem o que corrigir no Metryx, então vai um
        aviso só, e não uma linha por transferência na quarentena. No total da fazenda nada muda (a transferência é
        entre retiros); no estoque por retiro, a diferença aparece como ajuste."""
        self.aviso("TRANSFER_WITHOUT_AMOUNT",
                   f"{len(datas)} transferência(s) sem quantidade na API do Metryx, de {min(datas)} a {max(datas)}: "
                   "ficaram de fora")

    @staticmethod
    def _campos_transferencia(item: dict, peso: Decimal | None, contraparte: Any) -> dict[str, Any]:
        return {"contraparte": contraparte, "peso_vivo_total_kg": peso,
                "valor_total": para_decimal(item.get("totalFaturamento")),
                "extra": {"id": item.get("id"), "itemId": item.get("itemId")}}

    # -- rebanho médio --

    def rebanho_medio(self) -> None:
        """Soma das linhas da mesma categoria no mês (entre retiros e owners)."""
        somas: dict[tuple, Decimal] = {}                  # (fazenda, mês, categoria) -> cabeças
        for numero, item in enumerate(self.dados.get("rebanho_medio", [])):
            fazenda = self.fazenda_de(item)
            mes = para_data(item.get("month"))
            qtd = para_decimal(item.get("amount"))
            if fazenda is None or mes is None or qtd is None:
                continue
            if qtd < 0:
                self.rejeitar("rebanho_medio", item, f"rebanho:{numero}", "NEGATIVE_VALUE", "rebanho médio negativo",
                              fazenda)
                continue
            chave = (fazenda, mes.replace(day=1), item.get("idCategory"))
            somas[chave] = somas.get(chave, Decimal(0)) + qtd
        # TODO (doc 02 §5.2): `weight` é médio ou total? Até validar com payload real, o peso não entra (UA estimada).
        for (fazenda, mes, categoria), qtd in somas.items():
            self.lote.rebanho_medio.append(RebanhoMedio(fazenda=fazenda, cenario="realizado", competencia=mes,
                                                        categoria=self.categoria(categoria), qtd_cab=qtd,
                                                        origem_linha=f"rebanho:{categoria}:{mes}"))

    # -- área de pasto --

    def areas(self) -> None:
        """Uma linha por fazenda e mês, do mês do primeiro período de pasto até o último mês do rebanho médio: antes do
        cadastro das pastagens no Metryx não há área (a lotação fica sem número), e sem rebanho não há lotação."""
        ultimo_mes_do_rebanho: dict[str, date] = {}
        for linha in self.lote.rebanho_medio:
            if linha.competencia > ultimo_mes_do_rebanho.get(linha.fazenda, date.min):
                ultimo_mes_do_rebanho[linha.fazenda] = linha.competencia
        for fazenda, periodos in self.periodos_de_pasto().items():
            ultimo_mes = ultimo_mes_do_rebanho.get(fazenda)
            if ultimo_mes is None:
                continue
            mes = min(periodo.inicio for periodo in periodos).replace(day=1)
            while mes <= ultimo_mes:
                total, produtiva = area_no_dia(periodos, fim_do_mes(mes))
                self.lote.area.append(AreaMensal(fazenda=fazenda, cenario="realizado", competencia=mes,
                                                 area_pasto_ha=total, area_total_ha=total,
                                                 area_produtiva_ha=produtiva, origem_linha=f"pasto:{mes:%Y-%m}"))
                mes = proximo_mes(mes)

    def periodos_de_pasto(self) -> dict[str, list[PeriodoDePasto]]:
        """Os períodos de uso das pastagens, por fazenda. Pastagem de fazenda que não é do cliente fica de fora."""
        por_fazenda: dict[str, list[PeriodoDePasto]] = {}
        fora_do_cliente = 0
        for numero, item in enumerate(self.dados.get("pasto", [])):
            fazenda = self.fazenda_pelo_id(item, "fazendaId", "retiroId")
            if fazenda is None:
                fora_do_cliente += 1
                continue
            periodo = self.periodo_de_pasto(numero, item, fazenda)
            if periodo is not None:
                por_fazenda.setdefault(fazenda, []).append(periodo)
        if fora_do_cliente:
            self.aviso("PASTURE_FARM_UNKNOWN", f"{fora_do_cliente} período(s) de pasto de fazenda fora do cadastro "
                                               "do cliente ficaram de fora da área")
        return por_fazenda

    def periodo_de_pasto(self, numero: int, item: dict, fazenda: str) -> PeriodoDePasto | None:
        inicio = para_data(item.get("dataInicio"))
        total = para_decimal(item.get("areaTotal")) or Decimal(0)
        produtiva = para_decimal(item.get("areaProdutiva")) or Decimal(0)
        if inicio is None:
            self.rejeitar("area", item, f"pasto:{numero}", "MISSING_DATE", "período de pasto sem data de início",
                          fazenda)
            return None
        if total < 0 or produtiva < 0:
            self.rejeitar("area", item, f"pasto:{numero}", "NEGATIVE_VALUE", "área negativa", fazenda)
            return None
        return PeriodoDePasto(pastagem=str(item.get("id")), inicio=inicio, fim=para_data(item.get("dataFim")),
                              pecuario=eh_uso_pecuario(item.get("utilizacaoArea")), area_total=total,
                              area_produtiva=produtiva)

    # -- financeiro realizado --

    def lancamentos(self) -> None:
        """Só o que foi pago é realizado; a fazenda é a de destino (D2), e a fiscal fica guardada."""
        for numero, item in enumerate(self.dados.get("lancamento", [])):
            ref = f"lancamento:{item.get('idFinancialEntrie')}:{item.get('idPayment')}:{item.get('parcel')}:{numero}"
            pago = para_data(item.get("datePayment"))
            vencimento = para_data(item.get("dueDate"))
            if pago is None:
                continue                                  # não pago: não é realizado
            destino = self.fazenda_de(item, "idfarmDestination", "farmDestination")
            fiscal = self.fazenda_de(item, "idFarmFiscal", "farmFiscal")
            fazenda = destino or fiscal                   # TODO(D2): fazenda destino e data de pagamento
            valor = para_decimal(item.get("amountPaid"))
            if fazenda is None or valor is None or not item.get("type"):
                self.rejeitar("lancamento", item, ref, "REQUIRED_MISSING", "sem fazenda, valor pago ou tipo")
                continue
            natureza = "C" if str(item["type"]).startswith("Cr") else "D"
            if valor < 0:                                 # estorno: valor negativo vira a natureza oposta
                natureza = "D" if natureza == "C" else "C"
                valor = -valor
            conta = ContaOrigem(centro=limpar_nome(item.get("costCenter")) or "(vazio)",
                                subcentro=limpar_nome(item.get("subCenter")) or None)
            extra = {campo: item.get(campo)
                     for campo in ("idFinancialEntrie", "idPayment", "parcel", "status", "classe", "activity")}
            self.lote.lancamentos.append(LancamentoFinanceiro(
                fazenda=fazenda, fazenda_fiscal=fiscal, conta=conta, natureza=natureza, valor=valor,
                data_pagamento=pago, data_vencimento=vencimento, descricao=item.get("description"),
                contraparte=item.get("clientProvider"), documento=item.get("documents"), origem_linha=ref,
                extra=extra))

    # -- partições --

    def particoes(self) -> None:
        """Só os endpoints que vieram nesta carga são autoritativos; os outros ficam como estavam no banco."""
        self.lote.retiros = list(self.retiros.values())
        vieram = {nome for nome, situacao in self.status.items() if situacao == "ok"}
        for fazenda in self.lote.fazendas:
            for nome in sorted(vieram & PARTICOES_DO_ENDPOINT.keys()):
                entidade, tipos = PARTICOES_DO_ENDPOINT[nome]
                self.lote.particoes.append(Particao(entidade=entidade, fazenda=fazenda.id_externo, cenario="realizado",
                                                    estrategia="substituir", tipos=tipos, guarda_volume=GUARDA_VOLUME))
        ausentes = sorted(PARTICOES_DO_ENDPOINT.keys() - vieram)
        if ausentes:
            situacao = {nome: self.status.get(nome, "ausente") for nome in ausentes}
            self.aviso("ENDPOINT_NOT_LOADED",
                       f"endpoints sem dados nesta carga (mantidos como estavam): {', '.join(ausentes)}",
                       {"status": situacao})
