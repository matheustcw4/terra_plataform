import { describe, expect, test } from "vitest";
import { assuntoTemConteudo, paginar, recortar, TODAS_AS_PARTES } from "./personalizado";

describe("boletim personalizado", () => {
  test("o assunto entra só com alguma parte que ele tem", () => {
    expect(assuntoTemConteudo("estoque", TODAS_AS_PARTES)).toBe(true);
    expect(assuntoTemConteudo("estoque", ["graficos"])).toBe(false); // o estoque não tem gráfico
    expect(assuntoTemConteudo("lotacao", ["graficos"])).toBe(true);
    expect(assuntoTemConteudo("caixa", ["notas"])).toBe(false); // nota sozinha não faz bloco
    expect(assuntoTemConteudo("desconhecido", TODAS_AS_PARTES)).toBe(false);
  });

  const MEDIDAS = { alturaUtil: 1500, entreBlocos: 30, entrePecas: 20, tituloRepetido: 50 };

  test("blocos pequenos dividem a folha", () => {
    expect(paginar([[100, 300], [100, 400], [100, 300]], MEDIDAS)).toEqual([
      [{ bloco: 0, de: 0, ate: 2 }, { bloco: 1, de: 0, ate: 2 }, { bloco: 2, de: 0, ate: 2 }],
    ]);
  });

  test("o bloco que não cabe continua na folha seguinte, entre dois quadros", () => {
    // bloco 0 ocupa 700; o bloco 1 começa (100 + 400) e o terceiro quadro dele (500) passa para a próxima folha
    expect(paginar([[100, 600], [100, 400, 500]], MEDIDAS)).toEqual([
      [{ bloco: 0, de: 0, ate: 2 }, { bloco: 1, de: 0, ate: 2 }],
      [{ bloco: 1, de: 2, ate: 3 }],
    ]);
  });

  test("o título não fica sozinho no fim da folha", () => {
    expect(paginar([[100, 1200], [100, 400]], MEDIDAS)).toEqual([
      [{ bloco: 0, de: 0, ate: 2 }],
      [{ bloco: 1, de: 0, ate: 2 }],
    ]);
  });

  test("quadro maior que a folha vai sozinho", () => {
    expect(paginar([[100, 2000], [100, 300]], MEDIDAS)).toEqual([
      [{ bloco: 0, de: 0, ate: 2 }],
      [{ bloco: 1, de: 0, ate: 2 }],
    ]);
    expect(paginar([], MEDIDAS)).toEqual([]);
  });

  test("recorta as peças do trecho", () => {
    expect(recortar(["a", "b", "c"], [1, 3])).toEqual(["b", "c"]);
    expect(recortar(["a", "b"], undefined)).toEqual(["a", "b"]);
  });
});
