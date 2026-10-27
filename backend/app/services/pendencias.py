"""Pendências de lançamento: o que a última carga de cada arquivo deixou fora dos números ou marcou para conferir.

A lista vem da função app.pendencias_de_carga (migração 0013), que já aplica a visibilidade do usuário. Aqui cada código
de ocorrência vira um texto para o usuário (o problema, como corrigir e quem corrige) e a linha de origem vira um
endereço que ele acha na planilha ("aba fVendaemPe, linha 18").
"""

import re
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.api import Pendencia, Pendencias, ResumoDePendencias


@dataclass(frozen=True)
class Explicacao:
    problema: str
    como_corrigir: str
    quem_corrige: str = "origem"      # origem: na planilha (ou no sistema de origem); equipe: equipe Terra


CATALOGO = {
    # não entrou nos números (quarentena)
    "REQUIRED_MISSING": Explicacao("Data ou quantidade faltando ou ilegível",
                                   "Preencha a data (dd/mm/aaaa) e a quantidade da linha."),
    "DATE_OUT_OF_RANGE": Explicacao("Data fora do esperado",
                                    "Confira o ano: a data está antes de 2000 ou, no realizado, mais de um mês "
                                    "no futuro."),
    "VALUE_OUT_OF_RANGE": Explicacao("Valor absurdo", "O valor passa de R$ 1 bilhão: confira vírgulas e zeros."),
    "NEGATIVE_VALUE": Explicacao("Valor negativo", "Quantidade, peso e valor não podem ser negativos."),
    "NATURE_UNKNOWN": Explicacao("Conta marcada como VERIFICAR",
                                 "Escolha a conta certa no plano de contas: com VERIFICAR a linha não soma "
                                 "(nem no BI)."),
    "INVALID_ROW": Explicacao("Linha que não dá para ler", "Confira os campos da linha."),
    "NEGATIVE_STOCK": Explicacao("Saldo inicial negativo", "Corrija o saldo inicial no CADASTROINICIAL."),
    "FARM_UNRESOLVED": Explicacao("Fazenda não identificada",
                                  "A linha aponta para uma fazenda que a plataforma não conhece.", "equipe"),
    # entrou, mas confira
    "OUTLIER": Explicacao("Valor fora do padrão",
                          "Confira peso, valor e quantidade: o número parece digitado errado."),
    "VALUE_MISSING": Explicacao("Venda ou compra sem valor", "Preencha o valor total ou o valor por cabeça."),
    "TOTAL_INCONSISTENT": Explicacao("Total não bate com o valor por cabeça",
                                     "Confira a coluna de total e a de valor (ou peso) por cabeça: uma delas está "
                                     "errada. O painel usa o total."),
    "SALE_WITHOUT_CLIENT": Explicacao("Venda sem cliente", "Preencha o CLIENTE da venda."),
    "CATEGORY_NOT_IN_CADASTRO": Explicacao("Categoria fora do cadastro inicial",
                                           "Inclua a categoria no CADASTROINICIAL ou corrija o nome na linha."),
    "SHEET_MISSING": Explicacao("Aba não encontrada",
                                "A planilha não tem esta aba do modelo: se foi apagada ou renomeada, restaure-a."),
    "HEADER_MISSING": Explicacao("Coluna não encontrada",
                                 "Confira o cabeçalho da aba: a coluna sumiu ou mudou de nome."),
    "HEADER_ALIAS": Explicacao("Coluna com outro nome",
                               "A coluna foi lida pelo nome alternativo; vale padronizar o cabeçalho."),
    "CATEGORY_UNMAPPED": Explicacao("Categoria sem categoria BI",
                                    "A equipe Terra precisa mapear a categoria; até lá ela fica fora do estoque.",
                                    "equipe"),
    "ACCOUNT_UNCLASSIFIED": Explicacao("Conta \"A classificar\"",
                                       "A equipe Terra precisa classificar a conta no plano unificado.", "equipe"),
}
SEM_EXPLICACAO = Explicacao("Aviso da carga", "Leia o detalhe; se não souber corrigir, fale com a equipe Terra.",
                            "equipe")
ORDEM_DA_SITUACAO = {"nao_entrou": 0, "confira": 1}
LINHA_DA_ABA = re.compile(r"^(?P<aba>[^!]+)!(?P<linha>\d+)$")           # fVendaemPe!18
CELULA_DA_ABA = re.compile(r"^(?P<aba>[^!]+)!(?P<celula>[A-Z]+\d+)$")    # CADASTROINICIAL!F13
MAXIMO_DE_VALORES = 8


def pendencias(s: Session, fazendas: list[UUID]) -> Pendencias:
    linhas = s.execute(text("SELECT * FROM app.pendencias_de_carga(CAST(:fazendas AS uuid[]))"),
                       {"fazendas": [str(fazenda) for fazenda in fazendas]}).mappings().all()
    itens = []
    for linha in linhas:
        itens.append(pendencia(linha))
    itens.sort(key=ordem)
    resumo = ResumoDePendencias(
        nao_entrou=sum(1 for item in itens if item.situacao == "nao_entrou"),
        confira=sum(1 for item in itens if item.situacao == "confira"),
        para_a_equipe=sum(1 for item in itens if item.quem_corrige == "equipe"))
    return Pendencias(resumo=resumo, itens=itens)


def pendencia(linha) -> Pendencia:
    explicacao = CATALOGO.get(linha["codigo"], SEM_EXPLICACAO)
    return Pendencia(fazenda_id=linha["fazenda_id"], fazenda=linha["fazenda"], situacao=linha["situacao"],
                     codigo=linha["codigo"], problema=explicacao.problema, detalhe=linha["detalhe"],
                     como_corrigir=explicacao.como_corrigir, quem_corrige=explicacao.quem_corrige,
                     origem=linha["origem"], local=local(linha["origem_linha"], linha["eh_arquivo"]),
                     valores=valores(linha["dados"]), salvo_em=linha["salvo_em"],
                     carregado_em=linha["carregado_em"])


def local(origem_linha: str | None, eh_arquivo: bool) -> str | None:
    """Endereço na planilha. Fora de arquivo (histórico do BI, API) a referência não é uma aba: fica como está."""
    if origem_linha is None or not eh_arquivo:
        return origem_linha
    linha = LINHA_DA_ABA.match(origem_linha)
    if linha:
        return f"aba {linha['aba']}, linha {linha['linha']}"
    celula = CELULA_DA_ABA.match(origem_linha)
    if celula:
        return f"aba {celula['aba']}, célula {celula['celula']}"
    return origem_linha


def valores(dados: dict | None) -> list[str]:
    """O que está escrito na linha, para a pessoa achá-la: só campos simples e preenchidos."""
    if not dados:
        return []
    resultado = []
    for campo, valor in dados.items():
        if campo.startswith("_") or valor is None or isinstance(valor, dict | list):
            continue
        resultado.append(f"{campo}: {texto_do_valor(valor)}")
    return resultado[:MAXIMO_DE_VALORES]


def texto_do_valor(valor) -> str:
    # 18.893999999999995 (resíduo de fórmula do Excel) vira 18.894
    if isinstance(valor, float):
        return f"{valor:.4f}".rstrip("0").rstrip(".")
    return str(valor)


def ordem(item: Pendencia) -> tuple:
    """Por fazenda e arquivo; dentro dele, o que não entrou primeiro e as linhas na ordem da planilha."""
    numero_da_linha = 0
    aba = item.local or ""
    if item.local:
        encontrado = re.search(r"linha (\d+)$", item.local)
        if encontrado:
            numero_da_linha = int(encontrado.group(1))
            aba = item.local[:encontrado.start()]
    return (item.fazenda, item.origem, ORDEM_DA_SITUACAO.get(item.situacao, 9), aba, numero_da_linha)
