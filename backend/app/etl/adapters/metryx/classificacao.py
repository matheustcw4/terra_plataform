"""Os campos dos filtros do financeiro no payload do Metryx (pedido do usuário, 18/11/2026).

- atividade: o realizado e a previsão financeira trazem a atividade (`activity`: "Pecuária Campo"…), e o plano, o tipo
  (`typeActivity`: "Pecuária"). Os dois vão como vêm; o de-para `dim.atividade_map` dá o tipo do filtro;
- classificação: o plano (`previsao-fluxo-caixa-planejamento`) e a previsão (`previsao-financeiro`) trazem a
  classificação analítica (Custeio, Investimento em fazenda…) e a marca de desembolso. O lançamento não traz; no
  Metryx a classificação é do centro de custo (nos três clientes da API, cada centro tem uma só, 18/11/2026), e o
  lançamento recebe a do seu centro no plano e na previsão do mesmo cliente. O lançamento só traz o nome do centro, por
  isso o casamento é pelo nome dentro do cliente. Centro com mais de uma: vale a mais frequente. Centro que não aparece
  no plano nem na previsão fica sem: vale a classificação da conta;
- conta bancária: só o lançamento traz (`idBankAccount`, `banckAccount`, com o erro de grafia da API).
"""

import unicodedata
from collections import Counter
from typing import Any

from app.etl.adapters.metryx.conversao import limpar_nome
from app.etl.canonical import ClassificacaoOrigem, ContaBancariaOrigem

TEXTOS_VERDADEIROS = ("true", "sim", "s", "1")
TEXTOS_FALSOS = ("false", "nao", "não", "n", "0")


def atividade_do_item(item: dict, campo: str) -> str | None:
    atividade = limpar_nome(item.get(campo))
    if not atividade:
        return None
    return atividade


def marca_de_desembolso(valor: Any) -> bool | None:
    """Booleano no plano e texto na previsão ("true"/"false"), como o OpenAPI descreve."""
    if isinstance(valor, bool):
        return valor
    texto = str(valor or "").strip().casefold()
    if texto in TEXTOS_VERDADEIROS:
        return True
    if texto in TEXTOS_FALSOS:
        return False
    return None


def classificacao_do_item(item: dict) -> ClassificacaoOrigem | None:
    nome = limpar_nome(item.get("classificationAnalyticDescription"))
    if not nome:
        return None
    desembolso = marca_de_desembolso(item.get("classificationAnalyticDisbursement"))
    return ClassificacaoOrigem(nome=nome, desembolso=desembolso)


def conta_bancaria_do_item(item: dict) -> ContaBancariaOrigem | None:
    id_externo = limpar_nome(str(item.get("idBankAccount") or ""))
    if not id_externo:
        return None
    nome = limpar_nome(item.get("banckAccount")) or id_externo
    return ContaBancariaOrigem(id_externo=id_externo, nome=nome)


def chave_do_centro(nome: Any) -> str:
    """O nome do centro sem acento, sem diferença de maiúsculas e com os espaços colapsados."""
    sem_acento = unicodedata.normalize("NFKD", limpar_nome(nome))
    letras = "".join(letra for letra in sem_acento if not unicodedata.combining(letra))
    return " ".join(letras.casefold().split())


class ClassificacaoPorCentro:
    """A classificação de cada centro de custo do cliente, tirada do plano e da previsão do mesmo payload."""

    def __init__(self, dados: dict[str, list[dict]]):
        self.contagem: dict[str, Counter] = {}
        self.do_nome: dict[str, ClassificacaoOrigem] = {}
        for item in dados.get("fluxo_caixa_plano", []):
            self.contar(item.get("costCenterName"), classificacao_do_item(item))
        for item in dados.get("previsao_financeiro", []):
            self.contar(item.get("costCenter"), classificacao_do_item(item))

    def contar(self, centro: Any, classificacao: ClassificacaoOrigem | None) -> None:
        chave = chave_do_centro(centro)
        if not chave or classificacao is None:
            return
        self.contagem.setdefault(chave, Counter())[classificacao.nome] += 1
        if self.do_nome.get(classificacao.nome) is None or self.do_nome[classificacao.nome].desembolso is None:
            self.do_nome[classificacao.nome] = classificacao

    def do_centro(self, centro: Any) -> ClassificacaoOrigem | None:
        contagem = self.contagem.get(chave_do_centro(centro))
        if not contagem:
            return None
        nome, _ = contagem.most_common(1)[0]
        return self.do_nome[nome]

    def centros_com_mais_de_uma(self) -> list[str]:
        centros = []
        for chave, contagem in self.contagem.items():
            if len(contagem) > 1:
                centros.append(chave)
        return sorted(centros)
