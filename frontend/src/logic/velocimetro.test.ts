import { expect, test } from "vitest";
import { caminhoDoArco, fracaoDaEscala, pontoDoArco } from "./velocimetro";

const CENTRO = { x: 100, y: 100 };

test("fração da escala: limitada a 1, zero sem valor e cheia quando não há meta", () => {
  expect(fracaoDaEscala(30, 120)).toBe(0.25);
  expect(fracaoDaEscala(200, 120)).toBe(1);
  expect(fracaoDaEscala(null, 120)).toBe(0);
  expect(fracaoDaEscala(-5, 120)).toBe(0);
  expect(fracaoDaEscala(30, null)).toBe(1);
});

test("pontas e topo do arco", () => {
  const esquerda = pontoDoArco(0, CENTRO, 80);
  const topo = pontoDoArco(0.5, CENTRO, 80);
  const direita = pontoDoArco(1, CENTRO, 80);
  expect([esquerda.x, Math.round(esquerda.y)]).toEqual([20, 100]);
  expect([Math.round(topo.x), Math.round(topo.y)]).toEqual([100, 20]);
  expect([direita.x, Math.round(direita.y)]).toEqual([180, 100]);
});

test("caminho SVG do arco até a metade", () => {
  expect(caminhoDoArco(0.5, CENTRO, 80)).toBe("M 20.00 100.00 A 80 80 0 0 1 100.00 20.00");
});
