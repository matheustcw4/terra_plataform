"""Layout das páginas do BI (PBIX no formato PBIR): cada visual com posição, tipo, título e campos, para as telas da
plataforma serem desenhadas a partir do BI.

    python -m validacao.layout_do_bi "C:/Users/.../CICLO COMPLETO - BOLETIM MENSAL (6).pbix" [saida.md]

Só lê o JSON de dentro do arquivo (Report/definition/pages/*): nada do PBIX é executado nem copiado. A posição de um
visual dentro de um grupo é relativa ao grupo; aqui ela sai somada (absoluta, em px da página de 1920×1080). Visual
oculto (ex.: os filtros sincronizados que o BI repete em todas as páginas) sai marcado.
"""

import json
import re
import sys
import zipfile
from pathlib import Path

SAIDA_PADRAO = Path(__file__).resolve().parents[2] / "docs" / "referencias" / "pbix_ciclo" / "layout_paginas.md"


def ler_paginas(pbix: Path) -> dict[str, dict]:
    """pasta da página -> {"pagina": page.json, "visuais": {nome: visual.json}} e a ordem das páginas."""
    paginas: dict[str, dict] = {}
    with zipfile.ZipFile(pbix) as arquivo:
        for nome in arquivo.namelist():
            partes = nome.split("/")
            if not nome.startswith("Report/definition/pages/") or len(partes) < 5:
                continue
            pasta = partes[3]
            conteudo = json.loads(arquivo.read(nome).decode("utf-8"))
            pagina = paginas.setdefault(pasta, {"pagina": {}, "visuais": {}})
            if partes[4] == "page.json":
                pagina["pagina"] = conteudo
            elif partes[-1] == "visual.json":
                pagina["visuais"][conteudo["name"]] = conteudo
        ordem = json.loads(arquivo.read("Report/definition/pages/pages.json").decode("utf-8"))["pageOrder"]
    return {pasta: paginas[pasta] for pasta in ordem if pasta in paginas}


def posicao_absoluta(visuais: dict, nome: str) -> tuple[float, float, bool]:
    """(x, y, oculto), somando a posição dos grupos-pai."""
    visual = visuais[nome]
    posicao = visual.get("position", {})
    x, y = posicao.get("x", 0), posicao.get("y", 0)
    oculto = visual.get("isHidden", False)
    pai = visual.get("parentGroupName")
    if pai in visuais:
        x_pai, y_pai, oculto_pai = posicao_absoluta(visuais, pai)
        x, y, oculto = x + x_pai, y + y_pai, oculto or oculto_pai
    return x, y, oculto


def descricao(visual: dict) -> str:
    """Título do visual, ou o texto da caixa, ou os campos, ou a imagem."""
    for item in visual.get("visualContainerObjects", {}).get("title", []):
        valor = item.get("properties", {}).get("text", {}).get("expr", {}).get("Literal", {}).get("Value")
        if valor:
            return valor.strip("'")
    textos = []
    for item in visual.get("objects", {}).get("general", []):
        for paragrafo in item.get("properties", {}).get("paragraphs", []):
            for trecho in paragrafo.get("textRuns", []):
                textos.append(trecho.get("value", ""))
    if textos:
        return " ".join(textos)
    campos = []
    for estado in visual.get("query", {}).get("queryState", {}).values():
        for projecao in estado.get("projections", []):
            campos.append(projecao.get("displayName") or projecao.get("queryRef", ""))
    if campos:
        return ", ".join(campos)
    imagem = re.search(r'"ItemName": "([^"]+)"', json.dumps(visual))
    return imagem.group(1) if imagem else ""


def linhas_da_pagina(visuais: dict) -> list[tuple]:
    linhas = []
    for nome, conteudo in visuais.items():
        visual = conteudo.get("visual")
        if visual is None:          # grupo: só serve para somar a posição dos filhos
            continue
        x, y, oculto = posicao_absoluta(visuais, nome)
        posicao = conteudo.get("position", {})
        linhas.append((round(y), round(x), round(posicao.get("width", 0)), round(posicao.get("height", 0)),
                       visual.get("visualType", ""), "sim" if oculto else "", descricao(visual).replace("|", "/")))
    return sorted(linhas)


def main() -> None:
    pbix = Path(sys.argv[1])
    saida = Path(sys.argv[2]) if len(sys.argv) > 2 else SAIDA_PADRAO
    texto = [f"# Layout das páginas do BI ({pbix.name})", "",
             "Gerado por `python -m validacao.layout_do_bi`. Posições em px de cada página (a maioria 1920×1080), "
             "absolutas. Formas e imagens sem texto ficam de fora.", ""]
    for pasta in ler_paginas(pbix).values():
        pagina = pasta["pagina"]
        texto += [f"## {pagina.get('displayName')} ({pagina.get('width')}×{pagina.get('height')})", "",
                  "| y | x | largura | altura | tipo | oculto | título / campos |", "|---|---|---|---|---|---|---|"]
        for y, x, largura, altura, tipo, oculto, rotulo in linhas_da_pagina(pasta["visuais"]):
            if tipo in ("shape", "image") and not rotulo.endswith((".png", ".svg")):
                continue
            texto.append(f"| {y} | {x} | {largura} | {altura} | {tipo} | {oculto} | {rotulo} |")
        texto.append("")
    saida.write_text("\n".join(texto), encoding="utf-8")
    print(f"layout gravado em {saida}")


if __name__ == "__main__":
    main()
