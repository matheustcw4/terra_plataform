"""Construtores de lotes canônicos e um adapter em memória para testar o motor sem fonte real."""

from datetime import date, time
from decimal import Decimal

from app.etl.adapters.base import Bruto, UnidadeOrigem, sha256_json
from app.etl.canonical import (
    ChaveCategoria,
    Inventario,
    LoteCanonico,
    MovAnimal,
    Particao,
    RefCategoria,
    RefCliente,
    RefFazenda,
)


class AdapterMemoria:
    """Adapter de teste: cada unidade é um LoteCanonico serializado em JSON (o motor guarda o bruto e reprocessa)."""

    def __init__(self, fonte: str, lotes: dict[str, LoteCanonico], falhar_extracao: set[str] = frozenset(),
                 bruto_nao_json: set[str] = frozenset()):
        self.fonte = fonte
        self.lotes = lotes
        self.falhar_extracao = falhar_extracao
        self.bruto_nao_json = bruto_nao_json

    def descobrir(self):
        return [UnidadeOrigem(chave=k, descricao=k) for k in self.lotes]

    def extrair(self, unidade: UnidadeOrigem) -> Bruto:
        if unidade.chave in self.falhar_extracao:
            raise OSError(f"não consegui ler {unidade.chave}")
        conteudo = self.lotes[unidade.chave].model_dump(mode="json")
        sha = sha256_json(conteudo)
        if unidade.chave in self.bruto_nao_json:          # extrai, mas o raw.payload (JSONB) não aceita
            conteudo = {**conteudo, "hora": time(8, 30)}
        return Bruto(unidade, "json", conteudo, sha, len(str(conteudo)), {"endpoint": "teste"})

    def normalizar(self, bruto: Bruto) -> LoteCanonico:
        return LoteCanonico.model_validate(bruto.conteudo)


def cat(nome: str, fazenda: str = "85|BELA VISTA", fonte_mapa: str = "planilha", escopo: str = "fazenda",
        escopo_id: str | None = None) -> ChaveCategoria:
    return ChaveCategoria(fonte_mapa=fonte_mapa, escopo=escopo, escopo_id=escopo_id or fazenda, id_externo=nome)


def lote_base(fonte: str = "planilha", *, cliente: str = "85", fazenda: str = "85|BELA VISTA",
              nome_fazenda: str = "BELA VISTA", categorias: dict[str, str | None] | None = None,
              confirmadas: bool = True, fonte_mapa: str = "planilha", escopo: str = "fazenda") -> LoteCanonico:
    """Lote com 1 cliente, 1 fazenda e o de-para de categorias {nome na fonte: categoria BI}."""
    if categorias is None:
        categorias = {"BEZERRO MAMANDO": "BEZERRO", "DESMAMA MACHO": "MACHOS 8-12"}
    escopo_id = fazenda if escopo == "fazenda" else cliente
    return LoteCanonico(
        fonte=fonte,
        clientes=[RefCliente(id_externo=cliente, nome=f"CLIENTE {cliente}",
                             codigo=int(cliente) if cliente.isdigit() else None)],
        fazendas=[RefFazenda(id_externo=fazenda, cliente=cliente, nome=nome_fazenda, proprietario="FULANO",
                             sistema_produtivo="CICLO COMPLETO", tipo_ano="SAFRA")],
        categorias=[RefCategoria(chave=cat(n, fazenda, fonte_mapa, escopo, escopo_id), nome=n, categoria_bi=bi,
                                 confirmada=confirmadas) for n, bi in categorias.items()],
    )


def mov(tipo: str, data_: date, categoria: ChaveCategoria, qtd: int | str, n: int, fazenda: str = "85|BELA VISTA",
        destino: ChaveCategoria | None = None, **kw) -> MovAnimal:
    return MovAnimal(fazenda=fazenda, cenario="realizado", tipo=tipo, data=data_, categoria=categoria,
                     categoria_destino=destino, qtd=Decimal(str(qtd)), origem_linha=f"teste!{n}", **kw)


def checkpoint(data_: date, categoria: ChaveCategoria, qtd: int, n: int, fazenda: str = "85|BELA VISTA") -> Inventario:
    return Inventario(fazenda=fazenda, categoria=categoria, data=data_, qtd=Decimal(qtd), origem_linha=f"saldo!{n}")


def particoes_pecuario(fazenda: str = "85|BELA VISTA", estrategia_inventario: str = "mesclar") -> list[Particao]:
    return [
        Particao(entidade="mov_animal", fazenda=fazenda, cenario="realizado", estrategia="substituir"),
        Particao(entidade="inventario", fazenda=fazenda, cenario="realizado", estrategia=estrategia_inventario),
    ]


def exemplo_doc01(fonte: str = "planilha", com_checkpoint_julho: bool = False, **kw) -> LoteCanonico:
    """docs/01 §5.1: BEZERRO com 1.000 em 30/06; em julho +120 nascimentos, −5 mortes, −300 desmame.

    Planilha: saldo final 815, ajuste 0. Metryx (checkpoint de 812 em 31/07): saldo final 812, ajuste −3.
    """
    lote = lote_base(fonte, **kw)
    bez, desm = (c.chave for c in lote.categorias)
    fazenda = lote.fazendas[0].id_externo
    lote.inventario = [checkpoint(date(2025, 6, 30), bez, 1000, 1, fazenda),
                       checkpoint(date(2025, 6, 30), desm, 0, 2, fazenda)]
    if com_checkpoint_julho:
        lote.inventario += [checkpoint(date(2025, 7, 31), bez, 812, 3, fazenda),
                            checkpoint(date(2025, 7, 31), desm, 300, 4, fazenda)]
    lote.mov_animal = [
        mov("NASCIMENTO", date(2025, 7, 10), bez, 120, 1, fazenda),
        mov("MORTE", date(2025, 7, 12), bez, 5, 2, fazenda),
        mov("DESMAME", date(2025, 7, 20), bez, 300, 3, fazenda, destino=desm, peso_vivo_total_kg=Decimal(60000)),
    ]
    lote.particoes = particoes_pecuario(fazenda)
    return lote
