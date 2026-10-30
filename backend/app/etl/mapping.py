"""Resolução de identidades externas -> ids internos (de-paras). Nada é casado por nome cru.

- cliente/fazenda/retiro: core.fonte_vinculo (fonte, entidade, id_externo). Desconhecido -> criado e vinculado
  (a fazenda nova recebe esta fonte como ativa em todos os domínios; o admin ajusta clientes híbridos depois).
- categoria: dim.categoria_map. De-para confirmado pela fonte (planilha) grava a categoria BI; sugestão (Metryx) só
  preenche categoria_bi_sugerida_id — nunca sobrescreve uma confirmação.
- conta: dim.plano_contas_map; sem de-para, tenta o nome canônico do plano de contas e grava o de-para achado.
"""

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.etl.canonical import (
    ChaveCategoria,
    ContaOrigem,
    Fonte,
    LoteCanonico,
    Ocorrencia,
    RefCategoria,
)
from app.etl.quality import Cod
from app.models.core import Cliente, Fazenda, FazendaFonte, FonteVinculo, Retiro
from app.models.dim import CategoriaBi, CategoriaMap, VersaoPlano

DOMINIOS = (
    "pecuario_realizado", "pecuario_planejado", "rebanho_medio_realizado", "rebanho_medio_planejado",
    "area_realizado", "area_planejado", "financeiro_realizado", "financeiro_planejado",
)
GRUPO_DO_DOMINIO = {"mov_animal": "pecuario", "inventario": "pecuario", "rebanho_medio": "rebanho_medio",
                    "area": "area", "lancamento": "financeiro", "orcamento": "financeiro"}


def dominio(entidade: str, cenario: str) -> str:
    """Domínio de uma entidade num cenário (ex.: mov_animal + realizado -> pecuario_realizado)."""
    return f"{GRUPO_DO_DOMINIO[entidade]}_{cenario}"


@dataclass
class Resolvido:
    clientes: dict[str, UUID] = field(default_factory=dict)
    fazendas: dict[str, UUID] = field(default_factory=dict)
    cliente_da_fazenda: dict[str, UUID] = field(default_factory=dict)   # fazenda (externo) -> cliente_id
    retiros: dict[str, UUID] = field(default_factory=dict)
    categorias: dict[ChaveCategoria, UUID] = field(default_factory=dict)
    versoes: dict[tuple[UUID, str], UUID] = field(default_factory=dict)   # (cliente_id, codigo) -> id
    contas: dict[ContaOrigem, UUID] = field(default_factory=dict)   # conta -> dim.plano_contas_map.id
    fonte_ativa: dict[tuple[UUID, str], str] = field(default_factory=dict)  # (fazenda_id, dominio) -> fonte
    ocorrencias: list[Ocorrencia] = field(default_factory=list)


def resolver(s: Session, lote: LoteCanonico) -> Resolvido:
    """Troca cada identidade externa do lote pelo id interno, criando o que ainda não existe."""
    resolvido = Resolvido()
    fonte = lote.fonte
    _clientes(s, fonte, lote, resolvido)
    _fazendas(s, fonte, lote, resolvido)
    _retiros(s, fonte, lote, resolvido)
    _versoes(s, fonte, lote, resolvido)
    _categorias(s, lote, resolvido)
    _contas(s, fonte, lote, resolvido)
    _fontes_ativas(s, resolvido)
    return resolvido


# --- vínculos (identidade externa -> id interno) --------------------------------------------------------------------

def _vinculo(s: Session, fonte: str, entidade: str, id_externo: str) -> UUID | None:
    return s.scalar(select(FonteVinculo.entidade_id).where(
        FonteVinculo.fonte == fonte, FonteVinculo.entidade == entidade, FonteVinculo.id_externo == id_externo))


def _vincular(s: Session, fonte: str, entidade: str, id_externo: str, entidade_id: UUID, nome: str | None) -> None:
    s.execute(pg_insert(FonteVinculo)
              .values(fonte=fonte, entidade=entidade, id_externo=id_externo, entidade_id=entidade_id,
                      nome_externo=nome)
              .on_conflict_do_nothing(constraint="uq_fonte_vinculo"))


def _clientes(s: Session, fonte: Fonte, lote: LoteCanonico, resolvido: Resolvido) -> None:
    for cliente in lote.clientes:
        cliente_id = _vinculo(s, fonte, "cliente", cliente.id_externo)
        if cliente_id is None and cliente.codigo is not None:      # mesmo código de projeto vindo de outra fonte
            cliente_id = s.scalar(select(Cliente.id).where(Cliente.codigo == cliente.codigo))
        if cliente_id is None:
            cliente_id = s.scalar(pg_insert(Cliente).values(nome=cliente.nome, codigo=cliente.codigo)
                                  .returning(Cliente.id))
        _vincular(s, fonte, "cliente", cliente.id_externo, cliente_id, cliente.nome)
        resolvido.clientes[cliente.id_externo] = cliente_id


def _fazendas(s: Session, fonte: Fonte, lote: LoteCanonico, resolvido: Resolvido) -> None:
    for fazenda in lote.fazendas:
        cliente_id = resolvido.clientes[fazenda.cliente]
        atributos = {"nome": fazenda.nome, "proprietario": fazenda.proprietario,
                     "sistema_produtivo": fazenda.sistema_produtivo, "tipo_ano": fazenda.tipo_ano}
        fazenda_id = _vinculo(s, fonte, "fazenda", fazenda.id_externo)
        if fazenda_id is None:
            fazenda_id = _criar_fazenda(s, fonte, fazenda.id_externo, cliente_id, atributos)
            resolvido.ocorrencias.append(Ocorrencia(
                nivel="info", codigo=Cod.FARM_CREATED, fazenda=fazenda.id_externo,
                mensagem=f"fazenda '{fazenda.nome}' cadastrada a partir da fonte {fonte}"))
        else:
            _atualizar_atributos(s, fonte, fazenda_id, atributos)
        resolvido.fazendas[fazenda.id_externo] = fazenda_id
        resolvido.cliente_da_fazenda[fazenda.id_externo] = cliente_id


def _criar_fazenda(s: Session, fonte: Fonte, id_externo: str, cliente_id: UUID, atributos: dict) -> UUID:
    """Fazenda nova: esta fonte fica ativa em todos os domínios (o admin ajusta clientes híbridos depois)."""
    fazenda_id = s.scalar(pg_insert(Fazenda).values(cliente_id=cliente_id, **atributos).returning(Fazenda.id))
    _vincular(s, fonte, "fazenda", id_externo, fazenda_id, atributos["nome"])
    linhas = []
    for dominio_da_fazenda in DOMINIOS:
        linhas.append({"fazenda_id": fazenda_id, "dominio": dominio_da_fazenda, "fonte": fonte})
    s.execute(pg_insert(FazendaFonte).values(linhas).on_conflict_do_nothing())
    return fazenda_id


def _atualizar_atributos(s: Session, fonte: Fonte, fazenda_id: UUID, atributos: dict) -> None:
    """Nome, proprietário etc. seguem a fonte ativa do pecuário realizado (evita duas fontes brigando pelo nome)."""
    ativa = s.scalar(select(FazendaFonte.fonte).where(FazendaFonte.fazenda_id == fazenda_id,
                                                      FazendaFonte.dominio == "pecuario_realizado"))
    if ativa != fonte:
        return
    preenchidos = {campo: valor for campo, valor in atributos.items() if valor is not None}
    s.execute(Fazenda.__table__.update().where(Fazenda.id == fazenda_id)
              .values(**preenchidos, atualizado_em=text("now()")))


def _retiros(s: Session, fonte: Fonte, lote: LoteCanonico, resolvido: Resolvido) -> None:
    for retiro in lote.retiros:
        retiro_id = _vinculo(s, fonte, "retiro", retiro.id_externo)
        if retiro_id is None:
            retiro_id = s.scalar(pg_insert(Retiro).values(fazenda_id=resolvido.fazendas[retiro.fazenda],
                                                          nome=retiro.nome).returning(Retiro.id))
            _vincular(s, fonte, "retiro", retiro.id_externo, retiro_id, retiro.nome)
        resolvido.retiros[retiro.id_externo] = retiro_id


def _versoes(s: Session, fonte: Fonte, lote: LoteCanonico, resolvido: Resolvido) -> None:
    for versao in lote.versoes:
        cliente_id = resolvido.clientes[versao.cliente]
        comando = pg_insert(VersaoPlano).values(cliente_id=cliente_id, fonte=fonte, codigo=versao.codigo,
                                                nome=versao.nome, oficial=versao.oficial, ordem=versao.ordem)
        atualizar = {"nome": comando.excluded.nome, "ordem": comando.excluded.ordem}
        versao_id = s.scalar(comando.on_conflict_do_update(constraint="uq_versao_plano", set_=atualizar)
                             .returning(VersaoPlano.id))
        resolvido.versoes[(cliente_id, versao.codigo)] = versao_id


def _fontes_ativas(s: Session, resolvido: Resolvido) -> None:
    """Qual fonte alimenta cada domínio de cada fazenda do lote (core.fazenda_fonte)."""
    if not resolvido.fazendas:
        return
    consulta = select(FazendaFonte.fazenda_id, FazendaFonte.dominio, FazendaFonte.fonte).where(
        FazendaFonte.fazenda_id.in_(list(resolvido.fazendas.values())))
    for fazenda_id, dominio_da_fazenda, fonte in s.execute(consulta):
        resolvido.fonte_ativa[(fazenda_id, dominio_da_fazenda)] = fonte


# --- categorias ----------------------------------------------------------------------------------------------------

def _categorias(s: Session, lote: LoteCanonico, resolvido: Resolvido) -> None:
    """Grava/atualiza o de-para de cada categoria do lote."""
    categoria_bi_por_nome = {}
    for categoria_id, nome in s.execute(select(CategoriaBi.id, CategoriaBi.nome)):
        categoria_bi_por_nome[nome] = categoria_id
    declaradas = {categoria.chave: categoria for categoria in lote.categorias}
    _declarar_categorias_usadas(lote, declaradas, resolvido)
    for chave, categoria in declaradas.items():
        categoria_bi_id = None
        if categoria.categoria_bi is not None:
            categoria_bi_id = categoria_bi_por_nome.get(categoria.categoria_bi.strip().upper())
            if categoria_bi_id is None:
                resolvido.ocorrencias.append(Ocorrencia(
                    nivel="aviso", codigo=Cod.CATEGORY_BI_UNKNOWN,
                    mensagem=f"categoria BI '{categoria.categoria_bi}' não existe",
                    contexto={"categoria_origem": categoria.nome}))
        resolvido.categorias[chave] = _gravar_de_para_categoria(s, resolvido, categoria, categoria_bi_id)


def _declarar_categorias_usadas(lote: LoteCanonico, declaradas: dict, resolvido: Resolvido) -> None:
    """Categoria usada numa linha mas não declarada no lote entra assim mesmo (pendente), com aviso."""
    usadas: set[ChaveCategoria] = set()
    for linha in [*lote.mov_animal, *lote.inventario, *lote.rebanho_medio]:
        if getattr(linha, "categoria", None) is not None:              # o rebanho médio pode vir por grupo
            usadas.add(linha.categoria)
        if getattr(linha, "categoria_destino", None) is not None:      # só desmame e mudança têm destino
            usadas.add(linha.categoria_destino)
    for chave in usadas - declaradas.keys():
        declaradas[chave] = RefCategoria(chave=chave, nome=chave.id_externo)
        resolvido.ocorrencias.append(Ocorrencia(
            nivel="aviso", codigo=Cod.CATEGORY_UNDECLARED,
            mensagem=f"categoria '{chave.id_externo}' usada sem declaração no lote",
            contexto={"fonte_mapa": chave.fonte_mapa}))


def _gravar_de_para_categoria(s: Session, resolvido: Resolvido, categoria: RefCategoria,
                              categoria_bi_id: int | None) -> UUID:
    """Confirmada (planilha: o CADASTROINICIAL é a confirmação) grava a categoria BI; sugestão (Metryx) só preenche a
    sugerida e nunca sobrescreve o que o consultor confirmou.

    A planilha só confirma quando traz a categoria BI: a categoria em branco no cadastro fica pendente e não apaga o
    que o admin classificou na plataforma (senão a próxima carga desfaria a classificação). Uma categoria preenchida
    na planilha vale mais que a do admin: o consultor corrigiu a origem."""
    chave = categoria.chave
    cliente_id, fazenda_id = _escopo(resolvido, chave)
    confirma = categoria.confirmada and categoria_bi_id is not None
    if confirma:
        confirmada_id, sugerida_id, confirmado_em = categoria_bi_id, None, text("now()")
    else:
        confirmada_id, sugerida_id, confirmado_em = None, categoria_bi_id, None
    comando = pg_insert(CategoriaMap).values(
        fonte=chave.fonte_mapa, cliente_id=cliente_id, fazenda_id=fazenda_id, categoria_origem=chave.id_externo,
        nome_origem=categoria.nome, atributos=categoria.atributos, categoria_bi_id=confirmada_id,
        categoria_bi_sugerida_id=sugerida_id, confirmado_em=confirmado_em)
    atualizar = {"nome_origem": comando.excluded.nome_origem,
                 "atributos": text("coalesce(excluded.atributos, dim.categoria_map.atributos)"),
                 "atualizado_em": text("now()")}
    if confirma:
        atualizar["categoria_bi_id"] = comando.excluded.categoria_bi_id
        atualizar["confirmado_em"] = text("now()")
        atualizar["confirmado_por"] = None                     # quem confirmou foi a planilha, não um usuário
    else:
        atualizar["categoria_bi_sugerida_id"] = comando.excluded.categoria_bi_sugerida_id
    return s.scalar(comando.on_conflict_do_update(constraint="uq_categoria_map", set_=atualizar)
                    .returning(CategoriaMap.__table__.c.id))


def _escopo(resolvido: Resolvido, chave: ChaveCategoria) -> tuple[UUID | None, UUID | None]:
    """(cliente_id, fazenda_id) do de-para: a planilha mapeia por fazenda; o Metryx, por cliente."""
    if chave.escopo == "fazenda":
        return None, resolvido.fazendas[chave.escopo_id]
    return resolvido.clientes[chave.escopo_id], None


# --- contas --------------------------------------------------------------------------------------------------------

CONTA_EXISTENTE = """
    SELECT id FROM dim.plano_contas_map
    WHERE fonte = :f AND centro_origem = coalesce(app.normalizar(:c), '(VAZIO)')
      AND subcentro_origem IN (coalesce(app.normalizar(:sc), ''), '')
    ORDER BY subcentro_origem DESC LIMIT 1
"""
# Conta nova: procura o centro/subcentro de mesmo nome no plano de contas unificado; sem correspondência, a linha nasce
# pendente (centro_custo_id NULL = "A classificar").
CONTA_NOVA = """
    INSERT INTO dim.plano_contas_map (fonte, centro_origem, subcentro_origem, centro_custo_id,
                                      subcentro_id, nome_centro_origem, nome_subcentro_origem)
    SELECT :f, coalesce(app.normalizar(:c), '(VAZIO)'), coalesce(app.normalizar(:sc), ''), c.id,
           sc.id, :c, :sc
    FROM (SELECT 1) AS um
    LEFT JOIN dim.centro_custo c ON c.nome_normalizado = app.normalizar(:c)
    LEFT JOIN dim.subcentro sc
           ON sc.centro_custo_id = c.id AND sc.nome_normalizado = app.normalizar(:sc)
    ON CONFLICT ON CONSTRAINT uq_plano_contas_map DO UPDATE SET atualizado_em = now()
    RETURNING id
"""


def _contas(s: Session, fonte: Fonte, lote: LoteCanonico, resolvido: Resolvido) -> None:
    """Conta da fonte -> linha de dim.plano_contas_map (sempre). O lançamento carrega mesmo com a conta "A classificar":
    o total bate com a fonte e a pendência fica visível no DRE até o admin classificar (decisão Q1)."""
    contas = {linha.conta for linha in [*lote.lancamentos, *lote.orcamentos]}
    for conta in contas:
        parametros = {"f": fonte, "c": conta.centro, "sc": conta.subcentro}
        conta_map_id = s.scalar(text(CONTA_EXISTENTE), parametros)
        if conta_map_id is None:
            conta_map_id = s.scalar(text(CONTA_NOVA), parametros)
        resolvido.contas[conta] = conta_map_id
