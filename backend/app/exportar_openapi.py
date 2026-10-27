"""Grava o contrato da API (OpenAPI) num arquivo; o front gera os tipos TypeScript a partir dele.

    python -m app.exportar_openapi ../frontend/src/core/api/openapi.json
    (depois, em frontend/: npm run tipos)

Rodar de novo sempre que um schema ou rota mudar, para o front não usar um formato velho.
"""

import json
import sys

from app.main import app


def main() -> None:
    caminho = sys.argv[1]
    with open(caminho, "w", encoding="utf-8", newline="\n") as arquivo:
        json.dump(app.openapi(), arquivo, ensure_ascii=False, indent=2)
        arquivo.write("\n")
    print(f"OpenAPI gravado em {caminho}")


if __name__ == "__main__":
    main()
