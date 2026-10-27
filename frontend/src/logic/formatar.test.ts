import { expect, test } from "vitest";
import { comSinal, compacto, dinheiro, dinheiroCompacto, numero, percentual, rotuloDeColuna } from "./formatar";

test("números no padrão brasileiro e traço quando não há valor", () => {
  expect(numero(1605)).toBe("1.605");
  expect(numero(1.55, 2)).toBe("1,55");
  expect(numero(null)).toBe("—");
  expect(comSinal(105)).toBe("+105");
  expect(comSinal(-1200)).toBe("−1.200");
  expect(comSinal(0)).toBe("0");
});

test("dinheiro e percentual", () => {
  expect(dinheiro(154200)).toBe("R$ 154.200");
  expect(dinheiro(314.6938, 2)).toBe("R$ 314,69");
  expect(dinheiro(null)).toBe("—");
  expect(percentual(0.525)).toBe("52,5%");
  expect(percentual(null)).toBe("—");
});

test("eixo de gráfico em formato compacto", () => {
  // o Intl separa o número da escala com espaço inseparável
  expect(compacto(3200000)).toBe("3,2 mi");
  expect(compacto(154200)).toBe("154,2 mil");
  expect(compacto(450)).toBe("450");
});

test("rótulo de coluna some quando o valor é zero", () => {
  expect(rotuloDeColuna(0)).toBe("");
  expect(rotuloDeColuna(450)).toBe("450");
});

test("dinheiro compacto nos rótulos de barra", () => {
  // o Intl separa número e sufixo com espaço não separável (U+00A0)
  expect(dinheiroCompacto(1061895)).toBe("R$ 1,1 mi");
  expect(dinheiroCompacto(50000)).toBe("R$ 50 mil");
});
