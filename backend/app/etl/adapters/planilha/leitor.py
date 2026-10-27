"""Leitura do .xlsm (calamine, só valores em cache; nunca executa macro nem grava no arquivo).

Produz um dict JSON-ável com tudo o que o normalizador precisa — é o "bruto" guardado em raw.payload, o que permite
reprocessar sem reabrir o arquivo. Posições fixas só onde o template é posicional (fUnidade linha 2,
CADASTROINICIAL); nas abas de lançamento, sempre pelo nome do cabeçalho com apelidos.
"""

import io
import math
from datetime import date, datetime, time, timedelta
from typing import Any

from python_calamine import CalamineWorkbook

from app.etl.adapters.planilha.template import ABAS_LANCAMENTO, Aba, norm

# apelidos esperados no template (CATEG_FAZENDA x CATEGORIA_FAZENDA) não geram aviso; estes mudam o significado
APELIDOS_COM_AVISO = {"ILP", "SILAGEM"}
CAMPOS_DA_UNIDADE = ("projeto", "proprietario", "fazenda", "codigo", "sistema", "retiro", "ano")   # fUnidade A2:G2


def ler_planilha(dados: bytes) -> dict[str, Any]:
    planilha = CalamineWorkbook.from_filelike(io.BytesIO(dados))
    nomes = {norm(nome): nome for nome in planilha.sheet_names}        # nome normalizado -> nome real da aba
    avisos: list[dict] = []
    return {
        "unidade": ler_unidade(aba_inteira(planilha, nomes, "fUnidade")),
        "cadastro": ler_cadastro(aba_inteira(planilha, nomes, "CADASTROINICIAL")),
        "plano": ler_plano_de_contas(aba_inteira(planilha, nomes, "BASEPLANODECONTAS"),
                                     aba_inteira(planilha, nomes, "ConsultaPlanoContas")),
        "abas": ler_abas_de_lancamento(planilha, nomes, avisos),
        "avisos_leitura": avisos,
        "abas_do_arquivo": list(planilha.sheet_names),
    }


# --- células -------------------------------------------------------------------------------------------------------

def valor_da_celula(valor: Any) -> Any:
    """Célula -> valor JSON-ável (o bruto vai para raw.payload como JSONB)."""
    if valor is None or isinstance(valor, bool | int):
        return valor
    if isinstance(valor, float):
        return valor if math.isfinite(valor) else None
    if isinstance(valor, datetime):
        if valor.time() == datetime.min.time():
            return valor.date().isoformat()
        return valor.isoformat()
    if isinstance(valor, date | time):              # célula formatada como hora vem como datetime.time
        return valor.isoformat()
    if isinstance(valor, timedelta):                # duração ([h]:mm)
        return valor.total_seconds()
    texto = str(valor).strip()                      # str e qualquer outro tipo do calamine (ex.: erro de fórmula)
    return texto or None


def celula(linhas: list[list], linha: int, coluna: int) -> Any:
    """Linha/coluna contadas a partir de 1, como no Excel. Fora da área preenchida -> None."""
    try:
        return valor_da_celula(linhas[linha - 1][coluna - 1])
    except IndexError:
        return None


def coluna(linha: list, indice: int) -> Any:
    """Valor da coluna `indice` (a partir de 0) de uma linha que pode ser mais curta."""
    if indice < len(linha):
        return valor_da_celula(linha[indice])
    return None


def aba_inteira(planilha: CalamineWorkbook, nomes: dict[str, str], nome: str) -> list[list]:
    """Todas as linhas da aba, a partir de A1 (as posições fixas do template dependem disso). Sem a aba -> []."""
    if norm(nome) not in nomes:
        return []
    return planilha.get_sheet_by_name(nomes[norm(nome)]).to_python(skip_empty_area=False)


# --- abas posicionais ----------------------------------------------------------------------------------------------

def ler_unidade(linhas: list[list]) -> dict[str, Any]:
    unidade = {}
    for numero_coluna, campo in enumerate(CAMPOS_DA_UNIDADE, start=1):
        unidade[campo] = celula(linhas, 2, numero_coluna)
    return unidade


def ler_cadastro(linhas: list[list]) -> dict[str, Any]:
    """CADASTROINICIAL: PERÍODO escolhido (B8), datas de cada período (O9:T22) e categorias (A11:B74 + saldo em F)."""
    periodos = {}
    for numero_coluna in range(15, 21):            # O..T: rótulo (linha 9), 1º mês (10), mês anterior (22)
        rotulo = celula(linhas, 9, numero_coluna)
        if rotulo:
            periodos[str(rotulo)] = {"inicio": celula(linhas, 10, numero_coluna),
                                     "anterior": celula(linhas, 22, numero_coluna)}
    categorias = []
    for numero_linha in range(11, 75):
        nome_local = celula(linhas, numero_linha, 1)
        if nome_local is None:
            continue
        categorias.append({"linha": numero_linha, "categoria": str(nome_local),
                           "categoria_bi": celula(linhas, numero_linha, 2), "saldo": celula(linhas, numero_linha, 6)})
    return {"periodo": celula(linhas, 8, 2), "periodos": periodos, "categorias": categorias}


def ler_plano_de_contas(base: list[list], consulta: list[list]) -> dict[str, Any]:
    """BASEPLANODECONTAS: tradução de centros (A -> B) e subcentros (D -> E ou F).
    ConsultaPlanoContas: natureza C/D e flags de cada conta (coluna B)."""
    centros, subcentros = {}, {}
    for linha in base[1:]:
        centro_local, centro_traduzido = coluna(linha, 0), coluna(linha, 1)
        subcentro_local = coluna(linha, 3)
        subcentro_infra, subcentro_demais = coluna(linha, 4), coluna(linha, 5)
        if centro_local and centro_traduzido:
            centros[str(centro_local)] = str(centro_traduzido)
        if subcentro_local and (subcentro_infra or subcentro_demais):
            # E quando o centro é "Investimentos em infraestrutura"; F nos demais
            subcentros[str(subcentro_local)] = [subcentro_infra, subcentro_demais]
    contas = {}
    for linha in consulta:
        nome, natureza = coluna(linha, 1), coluna(linha, 5)
        if nome and natureza in ("C", "D"):
            contas[str(nome)] = {"natureza": natureza, "desembolso": valor_da_celula(linha[2]),
                                 "custeio": valor_da_celula(linha[3]), "tipo_custeio": valor_da_celula(linha[4])}
    return {"centros": centros, "subcentros": subcentros, "contas": contas}


# --- abas de lançamento (pelo nome do cabeçalho) -------------------------------------------------------------------

def ler_abas_de_lancamento(planilha: CalamineWorkbook, nomes: dict[str, str], avisos: list[dict]) -> dict[str, list]:
    abas = {}
    for aba in ABAS_LANCAMENTO.values():
        nome_real = nome_real_da_aba(aba, nomes)
        if nome_real is None:
            avisos.append({"codigo": "SHEET_MISSING", "aba": aba.nome})
            continue
        abas[aba.nome] = ler_aba_de_lancamento(planilha, aba, nome_real, avisos)
    return abas


def nome_real_da_aba(aba: Aba, nomes: dict[str, str]) -> str | None:
    """A aba pelo nome oficial ou por um dos apelidos usados em versões antigas do template."""
    for candidato in (aba.nome, *aba.apelidos_aba):
        if norm(candidato) in nomes:
            return nomes[norm(candidato)]
    return None


def ler_aba_de_lancamento(planilha: CalamineWorkbook, aba: Aba, nome_real: str, avisos: list[dict]) -> list[dict]:
    linhas = planilha.get_sheet_by_name(nome_real).to_python(skip_empty_area=False)
    if not linhas:
        return []
    colunas = posicao_das_colunas(aba, linhas[0], avisos)
    colunas_digitadas = [campo for campo in colunas if campo not in aba.cache]   # as de fórmula não contam
    registros = []
    for numero_linha, linha in enumerate(linhas[1:], start=2):
        registro = {}
        for campo, indice in colunas.items():
            registro[campo] = coluna(linha, indice)
        # linha sem nada digitado (só fórmulas do modelo) fica de fora
        if any(registro.get(campo) not in (None, "") for campo in colunas_digitadas):
            registro["_linha"] = numero_linha
            registros.append(registro)
    return registros


def posicao_das_colunas(aba: Aba, cabecalho: list, avisos: list[dict]) -> dict[str, int]:
    """Campo -> índice da coluna, pelo nome do cabeçalho (ou apelido). Avisa campos ausentes e apelidos que mudam o
    significado."""
    nomes_no_cabecalho = [norm(nome) for nome in cabecalho]
    colunas: dict[str, int] = {}
    for campo in aba.campos:
        for nome in (campo, *aba.apelidos_coluna.get(campo, ())):
            if nome not in nomes_no_cabecalho:
                continue
            colunas[campo] = nomes_no_cabecalho.index(nome)
            if nome in APELIDOS_COM_AVISO:
                avisos.append({"codigo": "HEADER_ALIAS", "aba": aba.nome, "campo": campo, "cabecalho": nome})
            break
    faltando = [campo for campo in aba.campos if campo not in colunas]
    if faltando:
        avisos.append({"codigo": "HEADER_MISSING", "aba": aba.nome, "campos": faltando})
    return colunas
