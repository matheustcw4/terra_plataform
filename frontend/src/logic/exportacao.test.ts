import { describe, expect, test } from "vitest";
import type { FazendaDoEscopo } from "../core/api/tipos";
import type { Filtro } from "./filtro";
import {
  localEData,
  mesPorExtenso,
  nomeDoArquivo,
  nomeDoArquivoDoMes,
  nomesDaCapa,
  paginasNaOrdem,
  periodoDaCapa,
  tamanhoDoLocal,
  tamanhoDosNomes,
} from "./exportacao";

function fazenda(id: string, nome: string, cliente: string, origem = "metryx"): FazendaDoEscopo {
  return {
    id,
    nome,
    cliente,
    origem,
    sistema_produtivo: null,
    primeiro_mes: "2025-01-01",
    ultimo_mes: "2026-09-01",
    capacidades: { estoque: true, rebanho_medio: true, area: true, financeiro: true, planejado: true },
  };
}

const FAZENDAS = [
  fazenda("s1", "Serra Dourada", "MARIA"),
  fazenda("s2", "Santa Fé", "MARIA"),
  fazenda("p1", "SERRA DOURADA", "MARIA", "planilha"),        // o mesmo cliente na outra origem não entra
  fazenda("o1", "Outra", "JOÃO"),
];

const GRUPO: Filtro = { origem: "metryx", cliente: "MARIA", fazendas: [], visao: "safra", ano: 2024, meses: [] };

describe("capa do PDF", () => {
  test("safra 24/25 ou ano 2025", () => {
    expect(periodoDaCapa(GRUPO)).toEqual({ titulo: "SAFRA", valor: "24/25" });
    expect(periodoDaCapa({ ...GRUPO, visao: "civil", ano: 2025 })).toEqual({ titulo: "ANO", valor: "2025" });
  });

  test("as fazendas marcadas, ou todas as do cliente, separadas por ' | '", () => {
    expect(nomesDaCapa(GRUPO, FAZENDAS)).toBe("Serra Dourada | Santa Fé");
    expect(nomesDaCapa({ ...GRUPO, fazendas: ["s2"] }, FAZENDAS)).toBe("Santa Fé");
    expect(nomesDaCapa({ ...GRUPO, fazendas: ["s1", "s2"] }, FAZENDAS)).toBe("Serra Dourada | Santa Fé");
  });

  test("a data é o mês de hoje por extenso; a cidade é livre", () => {
    expect(mesPorExtenso("2026-10")).toBe("outubro de 2026");
    expect(mesPorExtenso("2027-03")).toBe("março de 2027");
    expect(localEData("Cuiabá", "2026-10")).toBe("Cuiabá, outubro de 2026.");
    expect(localEData("  ", "2026-10")).toBe("Outubro de 2026.");
  });

  test("texto comprido usa letra menor", () => {
    expect(tamanhoDosNomes("GRUPO")).toBe(64);
    expect(tamanhoDosNomes("Serra Dourada | Santa Fé | Boa Vista | Três Irmãos")).toBe(46);
    expect(tamanhoDosNomes("x".repeat(300))).toBe(20);
    expect(tamanhoDoLocal("Cuiabá, outubro de 2026.")).toBe(27);
    expect(tamanhoDoLocal("Campo Novo do Parecis, outubro de 2026.")).toBe(19);
  });
});

describe("exportação", () => {
  test("as páginas marcadas saem na ordem do boletim", () => {
    const ordem = ["capa", "/financeiro", "/rebanho/movimentacao", "/compras"];
    expect(paginasNaOrdem(["/compras", "capa", "/financeiro"], ordem)).toEqual(["capa", "/financeiro", "/compras"]);
  });

  test("nome do arquivo sem caractere proibido", () => {
    expect(nomeDoArquivo(GRUPO, FAZENDAS)).toBe("Boletim - GRUPO - Safra 24-25.pdf");
    const comBarra = [fazenda("b1", "FAZ. A/B", "MARIA")];
    expect(nomeDoArquivo({ ...GRUPO, fazendas: ["b1"], visao: "civil", ano: 2025 }, comBarra))
      .toBe("Boletim - FAZ. A-B - 2025.pdf");
  });

  test("nome do arquivo analítico leva o mês de referência", () => {
    expect(nomeDoArquivoDoMes("Boletim analítico", GRUPO, FAZENDAS, "2026-09"))
      .toBe("Boletim analítico - GRUPO - set-26.pdf");
  });
});
