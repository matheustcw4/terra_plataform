"""Contrato canônico: o que todo adapter entrega ao motor.

Os adapters (planilha, Metryx) produzem exatamente estes modelos. Eles referenciam identidades EXTERNAS
(id do cliente/fazenda/categoria na fonte); o motor resolve tudo para ids internos pelos de-paras
(core.fonte_vinculo, dim.categoria_map, dim.plano_contas_map). Daqui para frente nada sabe a fonte.

Regras de conformação (docs/01 §3):
- só grandezas físicas e TOTAIS (cab, kg vivo total, kg carcaça total, R$ total, ha, datas);
- classificação (grupo, sexo, DCM/CCM…) vem das dimensões, nunca do texto da fonte;
- cada lote declara as PARTIÇÕES pelas quais é autoritativo (o que ele substitui ou mescla no banco).
"""

import hashlib
import json
from datetime import date
from decimal import Decimal
from typing import Annotated, Any, Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, model_validator

Fonte = Literal["planilha", "metryx"]
Cenario = Literal["realizado", "planejado"]
TipoMov = Literal[
    "COMPRA", "NASCIMENTO", "TRANSF_ENTRADA",
    "ABATE", "VENDA_EM_PE", "MORTE", "CONSUMO_DOACAO", "TRANSF_SAIDA",
    "DESMAME", "MUDANCA_CATEGORIA",
]
TIPOS_COM_DESTINO: frozenset[str] = frozenset({"DESMAME", "MUDANCA_CATEGORIA"})
# De qual orçamento vem o planejado do financeiro (a tela escolhe, pedido do usuário em 29/10/2026): a previsão
# financeira (o DRE previsto: o `previsao-financeiro` do Metryx, a aba de DRE planejado da planilha) ou o planejamento
# (o fluxo de caixa do plano do Metryx, por versão).
TipoOrcamento = Literal["previsao", "planejamento"]
Grupo = Literal["BEZERROS", "JOVENS", "ADULTOS"]
FonteMapaCategoria = Literal["planilha", "metryx_realizado", "metryx_plano"]
SistemaProdutivo = Literal["CRIA", "RECRIA E ENGORDA", "CICLO COMPLETO"]
Entidade = Literal["mov_animal", "inventario", "rebanho_medio", "area", "lancamento", "orcamento"]
Estrategia = Literal["substituir", "mesclar"]
Nivel = Literal["erro", "aviso", "info"]

NaoNegativo = Annotated[Decimal, Field(ge=0)]


class _Modelo(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)


# --- identidades (referências externas) ------------------------------------------------------------------------------

class RefCliente(_Modelo):
    id_externo: str            # planilha: código do cliente; Metryx: idCustomer
    nome: str
    codigo: int | None = None  # código do cliente na consultoria, quando a fonte conhece


class RefFazenda(_Modelo):
    id_externo: str            # planilha: 'codigo|FAZENDA'; Metryx: 'idCustomer|idFarm'
    cliente: str               # id_externo do cliente
    nome: str
    proprietario: str | None = None
    sistema_produtivo: SistemaProdutivo | None = None
    tipo_ano: Literal["CIVIL", "SAFRA"] | None = None


class RefRetiro(_Modelo):
    id_externo: str
    fazenda: str               # id_externo da fazenda
    nome: str


class ChaveCategoria(_Modelo):
    """Identidade de uma categoria na fonte. O escopo diz a quem pertence o de-para (fazenda ou cliente)."""

    fonte_mapa: FonteMapaCategoria
    escopo: Literal["cliente", "fazenda"]
    escopo_id: str             # id_externo do cliente ou da fazenda
    id_externo: str            # planilha: nome normalizado da categoria da fazenda; Metryx: id da categoria


class RefCategoria(_Modelo):
    chave: ChaveCategoria
    nome: str                  # texto original, para exibição
    categoria_bi: str | None = None  # nome da categoria BI (dim.categoria_bi), se a fonte informa/sugere
    confirmada: bool = False   # True = o de-para veio confirmado da fonte (ex.: CADASTROINICIAL da planilha)
    atributos: dict[str, Any] | None = None


class RefVersaoPlano(_Modelo):
    cliente: str
    codigo: str
    nome: str | None = None
    oficial: bool = False
    ordem: int | None = None      # maior = mais recente (a escolha padrão de versão nas telas)


class ContaOrigem(_Modelo):
    """Conta (centro/subcentro) na nomenclatura da fonte; o motor resolve para o plano de contas canônico."""

    centro: str
    subcentro: str | None = None


# --- linhas de fato ---------------------------------------------------------------------------------------------------

class _Linha(_Modelo):
    origem_linha: str          # rastreabilidade: 'aba!linha' (planilha) ou 'hash#n' (Metryx)
    extra: dict[str, Any] | None = None


class MovAnimal(_Linha):
    fazenda: str
    retiro: str | None = None
    cenario: Cenario
    versao_plano: str | None = None
    tipo: TipoMov
    data: date
    categoria: ChaveCategoria
    categoria_destino: ChaveCategoria | None = None
    qtd: NaoNegativo
    peso_vivo_total_kg: NaoNegativo | None = None
    peso_carcaca_total_kg: NaoNegativo | None = None
    valor_total: NaoNegativo | None = None
    contraparte: str | None = None
    documento: str | None = None
    causa: str | None = None
    local: str | None = None
    era: str | None = None
    safra: str | None = None

    @model_validator(mode="after")
    def _coerencia(self) -> "MovAnimal":
        if (self.cenario == "planejado") != (self.versao_plano is not None):
            raise ValueError("versao_plano é obrigatória no planejado e proibida no realizado")
        if (self.tipo in TIPOS_COM_DESTINO) != (self.categoria_destino is not None):
            raise ValueError("categoria_destino é obrigatória em DESMAME/MUDANCA_CATEGORIA e proibida nos demais")
        return self


class Inventario(_Linha):
    """Checkpoint de estoque: saldo da categoria ao FIM do dia `data`."""

    fazenda: str
    retiro: str | None = None
    categoria: ChaveCategoria
    data: date
    qtd: NaoNegativo


class _Mensal(_Linha):
    fazenda: str
    cenario: Cenario
    versao_plano: str | None = None
    competencia: date

    @model_validator(mode="after")
    def _mensal(self):
        if self.competencia.day != 1:
            raise ValueError("competencia deve ser o 1º dia do mês")
        if (self.cenario == "planejado") != (self.versao_plano is not None):
            raise ValueError("versao_plano é obrigatória no planejado e proibida no realizado")
        return self


class RebanhoMedio(_Mensal):
    """Grão mínimo comum: grupo × mês. Quem só tem categoria informa a categoria (o grupo vem da dimensão)."""

    grupo: Grupo | None = None
    categoria: ChaveCategoria | None = None
    qtd_cab: NaoNegativo
    peso_vivo_total_kg: NaoNegativo | None = None
    qtd_ua_informada: NaoNegativo | None = None

    @model_validator(mode="after")
    def _grao(self) -> "RebanhoMedio":
        if (self.grupo is None) == (self.categoria is None):
            raise ValueError("informe grupo OU categoria")
        return self


class AreaMensal(_Mensal):
    area_pasto_ha: NaoNegativo | None = None
    area_ilp_ha: NaoNegativo | None = None
    area_total_ha: NaoNegativo | None = None
    area_produtiva_ha: NaoNegativo | None = None


class LancamentoFinanceiro(_Linha):
    fazenda: str
    fazenda_fiscal: str | None = None
    conta: ContaOrigem
    natureza: Literal["C", "D"]
    valor: NaoNegativo
    data_pagamento: date
    data_vencimento: date | None = None
    descricao: str | None = None
    contraparte: str | None = None
    documento: str | None = None


class OrcamentoFinanceiro(_Linha):
    fazenda: str
    versao_plano: str
    tipo: TipoOrcamento = "previsao"
    conta: ContaOrigem
    natureza: Literal["C", "D"]
    competencia: date
    valor: NaoNegativo

    @model_validator(mode="after")
    def _mensal(self) -> "OrcamentoFinanceiro":
        if self.competencia.day != 1:
            raise ValueError("competencia deve ser o 1º dia do mês")
        return self


# --- partições, ocorrências e o lote ----------------------------------------------------------------------------

CENARIO_FIXO: dict[str, str] = {"inventario": "realizado", "lancamento": "realizado", "orcamento": "planejado"}
# entidade -> os tipos pelos quais uma partição dela pode se limitar
TIPOS_DA_ENTIDADE: dict[str, set[str]] = {"mov_animal": set(get_args(TipoMov)),
                                          "orcamento": set(get_args(TipoOrcamento))}
# data que posiciona a linha no tempo (recorte `desde`/`ate` da partição)
CAMPO_DATA: dict[str, str] = {"mov_animal": "data", "inventario": "data", "rebanho_medio": "competencia",
                              "area": "competencia", "lancamento": "data_pagamento", "orcamento": "competencia"}


def proximo_mes(d: date) -> date:
    return date(d.year + d.month // 12, d.month % 12 + 1, 1)


class Particao(_Modelo):
    """Recorte do banco pelo qual o lote é autoritativo.

    substituir: apaga o que a fonte tinha nesse recorte e grava as linhas do lote (lançamentos; snapshots completos).
    mesclar:    upsert pela chave natural, sem apagar o que não veio (mensais da planilha: trocar o PERÍODO não apaga
                o histórico; checkpoints de estoque de períodos anteriores).
    desde:      limita o `substituir` às linhas a partir deste mês; o que é anterior fica. A planilha da safra nova
                começa vazia, então o arquivo só responde pelo período dele (e pelo que ainda traz de antes).
    ate:        limita o `substituir` às linhas até este mês (inclusive); o que é posterior fica. Usado pela carga do
                histórico, que só responde pelo que vem antes do que o arquivo atual cobre.
    """

    entidade: Entidade
    fazenda: str
    cenario: Cenario
    estrategia: Estrategia
    tipos: tuple[TipoMov | TipoOrcamento, ...] | None = None    # mov_animal e orçamento; None = todos os tipos
    versao_plano: str | None = None               # None = todas as versões desta fonte
    # Guarda de volume (snapshots completos, ex.: Metryx): se o lote trouxer menos que esta fração do que já existe no
    # recorte, a partição é RETIDA (nada é apagado) e vira aviso. Protege contra resposta vazia/parcial da fonte.
    guarda_volume: float | None = None
    desde: date | None = None                     # só 'substituir'; 1º dia do mês
    ate: date | None = None                       # só 'substituir'; 1º dia do mês (inclusive)

    @model_validator(mode="after")
    def _coerencia(self) -> "Particao":
        fixo = CENARIO_FIXO.get(self.entidade)
        if fixo and self.cenario != fixo:
            raise ValueError(f"{self.entidade} só existe no cenário {fixo}")
        if self.tipos is not None and not set(self.tipos) <= TIPOS_DA_ENTIDADE.get(self.entidade, set()):
            raise ValueError(f"tipos {self.tipos} não se aplicam a {self.entidade}")
        if self.versao_plano is not None and self.cenario != "planejado":
            raise ValueError("versao_plano só se aplica ao planejado")
        if self.estrategia == "mesclar" and self.entidade not in ("inventario", "rebanho_medio", "area"):
            raise ValueError(f"{self.entidade} não tem chave natural: use 'substituir'")
        if self.guarda_volume is not None and (self.estrategia != "substituir" or not 0 < self.guarda_volume <= 1):
            raise ValueError("guarda_volume é uma fração (0, 1] e só vale para 'substituir'")
        for nome, d in (("desde", self.desde), ("ate", self.ate)):
            if d is not None and (self.estrategia != "substituir" or d.day != 1):
                raise ValueError(f"{nome} é o 1º dia de um mês e só vale para 'substituir'")
        if self.desde and self.ate and self.desde > self.ate:
            raise ValueError("desde depois de ate")
        return self

    def cobre(self, entidade: str, linha: BaseModel) -> bool:
        if entidade != self.entidade or linha.fazenda != self.fazenda:
            return False
        if getattr(linha, "cenario", CENARIO_FIXO.get(entidade)) != self.cenario:
            return False
        if self.tipos is not None and linha.tipo not in self.tipos:
            return False
        if self.desde is not None and getattr(linha, CAMPO_DATA[entidade]) < self.desde:
            return False
        if self.ate is not None and getattr(linha, CAMPO_DATA[entidade]) >= proximo_mes(self.ate):
            return False
        return self.versao_plano is None or getattr(linha, "versao_plano", None) == self.versao_plano


class Ocorrencia(_Modelo):
    nivel: Nivel
    codigo: str
    mensagem: str
    entidade: str | None = None
    origem_linha: str | None = None
    fazenda: str | None = None          # id_externo
    contexto: dict[str, Any] | None = None


class LinhaRejeitada(_Modelo):
    """Linha que o adapter não conseguiu converter (vai para a quarentena; o resto do lote carrega)."""

    entidade: str
    origem_linha: str | None
    codigo: str
    motivo: str
    dados: dict[str, Any]
    fazenda: str | None = None


# nome da entidade -> atributo do lote
ATRIBUTO_ENTIDADE: dict[str, str] = {
    "mov_animal": "mov_animal",
    "inventario": "inventario",
    "rebanho_medio": "rebanho_medio",
    "area": "area",
    "lancamento": "lancamentos",
    "orcamento": "orcamentos",
}


class LoteCanonico(BaseModel):
    """Tudo o que uma unidade de origem (um arquivo, um payload) produziu, já no formato canônico."""

    model_config = ConfigDict(extra="forbid")

    fonte: Fonte
    clientes: list[RefCliente] = Field(default_factory=list)
    fazendas: list[RefFazenda] = Field(default_factory=list)
    retiros: list[RefRetiro] = Field(default_factory=list)
    categorias: list[RefCategoria] = Field(default_factory=list)
    versoes: list[RefVersaoPlano] = Field(default_factory=list)

    mov_animal: list[MovAnimal] = Field(default_factory=list)
    inventario: list[Inventario] = Field(default_factory=list)
    rebanho_medio: list[RebanhoMedio] = Field(default_factory=list)
    area: list[AreaMensal] = Field(default_factory=list)
    lancamentos: list[LancamentoFinanceiro] = Field(default_factory=list)
    orcamentos: list[OrcamentoFinanceiro] = Field(default_factory=list)

    particoes: list[Particao] = Field(default_factory=list)
    ocorrencias: list[Ocorrencia] = Field(default_factory=list)
    rejeitadas: list[LinhaRejeitada] = Field(default_factory=list)

    def linhas(self, entidade: str) -> list[Any]:
        return getattr(self, ATRIBUTO_ENTIDADE[entidade])

    def impressao_dados(self) -> str:
        """sha256 só dos dados (sem ocorrências nem cadastro): dois arquivos com o mesmo conteúdo dão o mesmo valor."""
        dados = self.model_dump(mode="json", include=set(ATRIBUTO_ENTIDADE.values()))
        return hashlib.sha256(json.dumps(dados, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    def linhas_dados(self) -> int:
        return sum(len(self.linhas(e)) for e in ATRIBUTO_ENTIDADE)

    def validar_contrato(self) -> list[str]:
        """Erros de contrato (bug do adapter, não do dado): o lote inteiro é recusado se houver algum.

        1. todo cliente, fazenda, retiro e versão citado foi declarado;
        2. as partições são de fazendas declaradas e não se repetem;
        3. cada linha é coberta por exatamente uma partição (senão seria apagada sem ser regravada, ou gravada duas
           vezes) e só cita o que foi declarado;
        4. a chave natural das entidades com 'mesclar' não se repete (o adapter agrega antes).
        """
        erros: list[str] = []
        self._conferir_cadastro(erros)
        self._conferir_particoes(erros)
        self._conferir_linhas(erros)
        self._conferir_chave_natural(erros)
        return erros

    def _conferir_cadastro(self, erros: list[str]) -> None:
        clientes = {cliente.id_externo for cliente in self.clientes}
        fazendas = {fazenda.id_externo for fazenda in self.fazendas}
        for fazenda in self.fazendas:
            if fazenda.cliente not in clientes:
                erros.append(f"fazenda {fazenda.id_externo}: cliente {fazenda.cliente} não declarado")
        for retiro in self.retiros:
            if retiro.fazenda not in fazendas:
                erros.append(f"retiro {retiro.id_externo}: fazenda {retiro.fazenda} não declarada")
        for versao in self.versoes:
            if versao.cliente not in clientes:
                erros.append(f"versão {versao.codigo}: cliente {versao.cliente} não declarado")

    def _conferir_particoes(self, erros: list[str]) -> None:
        fazendas = {fazenda.id_externo for fazenda in self.fazendas}
        vistas: set[tuple] = set()
        for particao in self.particoes:
            if particao.fazenda not in fazendas:
                erros.append(f"partição {particao.entidade}: fazenda {particao.fazenda} não declarada")
            chave = (particao.entidade, particao.fazenda, particao.cenario, particao.tipos, particao.versao_plano)
            if chave in vistas:
                erros.append(f"partição duplicada: {chave}")
            vistas.add(chave)

    def _conferir_linhas(self, erros: list[str]) -> None:
        for entidade in ATRIBUTO_ENTIDADE:
            for linha in self.linhas(entidade):
                erros.extend(self._erros_da_linha(entidade, linha))
            if len(erros) > 50:
                erros.append("… (truncado)")
                return

    def _erros_da_linha(self, entidade: str, linha: Any) -> list[str]:
        erros = []
        onde = f"{entidade} {linha.origem_linha}"
        cobertura = sum(1 for particao in self.particoes if particao.cobre(entidade, linha))
        if cobertura != 1:
            erros.append(f"{onde}: coberta por {cobertura} partições (esperado 1)")
        if linha.fazenda not in {fazenda.id_externo for fazenda in self.fazendas}:
            erros.append(f"{onde}: fazenda {linha.fazenda} não declarada")
        retiro = getattr(linha, "retiro", None)               # nem toda entidade tem retiro/versão
        if retiro is not None and retiro not in {r.id_externo for r in self.retiros}:
            erros.append(f"{onde}: retiro {retiro} não declarado")
        versao = getattr(linha, "versao_plano", None)
        if versao is not None and (self._cliente_da_fazenda(linha.fazenda), versao) not in self._versoes():
            erros.append(f"{onde}: versão {versao} não declarada")
        return erros

    def _cliente_da_fazenda(self, fazenda_id: str) -> str | None:
        for fazenda in self.fazendas:
            if fazenda.id_externo == fazenda_id:
                return fazenda.cliente
        return None

    def _versoes(self) -> set[tuple[str, str]]:
        return {(versao.cliente, versao.codigo) for versao in self.versoes}

    def _conferir_chave_natural(self, erros: list[str]) -> None:
        for entidade, campos in CHAVE_NATURAL_CANONICA.items():
            contagem: dict[tuple, int] = {}
            for linha in self.linhas(entidade):
                chave = tuple(getattr(linha, campo, None) for campo in campos)
                contagem[chave] = contagem.get(chave, 0) + 1
            repetidas = [chave for chave, vezes in contagem.items() if vezes > 1]
            for chave in repetidas[:10]:
                erros.append(f"{entidade}: chave natural repetida {chave}")


CHAVE_NATURAL_CANONICA: dict[str, tuple[str, ...]] = {
    "inventario": ("fazenda", "retiro", "categoria", "data"),
    "rebanho_medio": ("fazenda", "cenario", "versao_plano", "competencia", "grupo", "categoria"),
    "area": ("fazenda", "cenario", "versao_plano", "competencia"),
}
