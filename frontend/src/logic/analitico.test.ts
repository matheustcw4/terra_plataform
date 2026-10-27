import { describe, expect, test } from "vitest";
import type { LinhaDoPlacar } from "../core/api/tipos";
import {
  blocosDoPlacar,
  colunasDoLote,
  dataCurta,
  paragrafosDaNota,
  rotuloDaMeta,
  rotuloDoPeriodo,
  valorComUnidade,
  variacaoComUnidade,
} from "./analitico";

const VAZIO = { previsto: null, realizado: null, variacao: null, variacao_percentual: null, status: null };

function linha(grupo: string, indicador: string): LinhaDoPlacar {
  return { grupo, indicador, unidade: "cab", mes: VAZIO, acumulado: VAZIO, meta_periodo: null };
}

describe("boletim analítico", () => {
  test("cada unidade com o seu formato", () => {
    expect(valorComUnidade(1234, "cab")).toBe("1.234");
    expect(valorComUnidade(1.684, "cab/ha")).toBe("1,68");
    expect(valorComUnidade(0.0234, "%")).toBe("2,34%");
    expect(valorComUnidade(339.87, "R$/@")).toBe("R$ 339,87");
    expect(valorComUnidade(252781.3, "R$")).toBe("R$ 252.781");
    expect(valorComUnidade(486.25, "kg")).toBe("486,3");
    expect(valorComUnidade(null, "cab")).toBe("—");
  });

  test("variação com sinal", () => {
    expect(variacaoComUnidade(12, "cab")).toBe("+12");
    expect(variacaoComUnidade(-0.005, "%")).toBe("−0,50%");
    expect(variacaoComUnidade(0, "cab")).toBe("0");
  });

  test("linhas do placar em blocos pelo grupo, na ordem da API", () => {
    const blocos = blocosDoPlacar([linha("REBANHO", "Rebanho médio"), linha("REBANHO", "Lotação"),
      linha("VENDAS ABATE", "Cabeças")]);
    expect(blocos.map((bloco) => [bloco.grupo, bloco.linhas.length])).toEqual([["REBANHO", 2], ["VENDAS ABATE", 1]]);
  });

  test("data curta", () => {
    expect(dataCurta("2026-09-23")).toBe("23/09/2026");
  });

  test("a meta é a da safra ou a do ano", () => {
    expect(rotuloDaMeta("safra")).toBe("Meta da safra");
    expect(rotuloDaMeta("civil")).toBe("Meta do ano");
    expect(rotuloDoPeriodo(2025, "safra")).toBe("Safra 25/26");
    expect(rotuloDoPeriodo(2026, "civil")).toBe("Ano civil 2026");
  });

  test("colunas da tabela de lotes pelo tipo", () => {
    expect(colunasDoLote("abate")).toMatchObject({ contraparte: "Cliente", carcaca: true, precos: true });
    expect(colunasDoLote("transf_saida")).toMatchObject({ contraparte: "Destino", precos: false });
    expect(colunasDoLote("nascimento")).toMatchObject({ contraparte: null, pesos: false });
  });

  test("a nota técnica em parágrafos, separados por linha em branco", () => {
    expect(paragrafosDaNota("  Primeiro parágrafo.\nmesma linha lógica\n\n\n  Segundo.  \n \n")).toEqual([
      "Primeiro parágrafo.\nmesma linha lógica",
      "Segundo.",
    ]);
    expect(paragrafosDaNota("   \n  ")).toEqual([]);
  });
});
