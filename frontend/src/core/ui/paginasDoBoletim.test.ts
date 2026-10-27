import { describe, expect, test } from "vitest";
import { gruposDoBoletim, PAGINAS_DO_BOLETIM, paginaDoCaminho } from "./paginasDoBoletim";

function caminhos(ehAdmin: boolean, titulo: string): string[] {
  const grupo = gruposDoBoletim(ehAdmin).find((candidato) => candidato.titulo === titulo);
  return (grupo?.itens ?? []).map((item) => item.caminho);
}

describe("gruposDoBoletim", () => {
  test("o boletim tem as páginas do PDF, na ordem do BI; pendências ficam à parte", () => {
    const boletim = caminhos(false, "Boletim");
    expect(boletim[0]).toBe("/previsto_realizado");
    expect(boletim).toContain("/transferencias");
    expect(boletim).not.toContain("/pendencias");
    expect(caminhos(false, "Qualidade")).toEqual(["/pendencias"]);
  });

  test("só o admin vê a administração; todos veem o MENU", () => {
    expect(caminhos(false, "Geral")).toEqual(["/menu"]);
    expect(caminhos(true, "Geral")).toEqual(["/menu", "/admin"]);
  });
});

describe("paginaDoCaminho", () => {
  test("acha a página pelo caminho exato ou por um caminho de dentro dela", () => {
    expect(paginaDoCaminho("/vendas/abate", PAGINAS_DO_BOLETIM)?.rotulo).toBe("Venda Abate");
    expect(paginaDoCaminho("/mortes/qualquer", PAGINAS_DO_BOLETIM)?.rotulo).toBe("Mortes");
  });

  test("não confunde um caminho que só começa igual", () => {
    expect(paginaDoCaminho("/comprasx", PAGINAS_DO_BOLETIM)).toBeNull();
    expect(paginaDoCaminho("/menu", PAGINAS_DO_BOLETIM)).toBeNull();
  });
});
