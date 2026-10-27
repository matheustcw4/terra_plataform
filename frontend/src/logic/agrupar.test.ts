import { expect, test } from "vitest";
import { agruparPor, contemTexto, marcarVarios } from "./agrupar";

test("agrupa pela chave, na ordem em que cada chave aparece", () => {
  const fazendas = [
    { nome: "ÁGUA BOA", cliente: "MAISTER" },
    { nome: "ITAÚBA", cliente: "PEDRO" },
    { nome: "IPANEMA", cliente: "MAISTER" },
  ];
  const grupos = agruparPor(fazendas, (fazenda) => fazenda.cliente);
  expect(grupos.map((grupo) => [grupo.chave, grupo.itens.map((fazenda) => fazenda.nome)])).toEqual([
    ["MAISTER", ["ÁGUA BOA", "IPANEMA"]],
    ["PEDRO", ["ITAÚBA"]],
  ]);
});

test("marca e desmarca vários de uma vez, sem repetir", () => {
  expect(marcarVarios(["a"], ["a", "b"], true)).toEqual(["a", "b"]);
  expect(marcarVarios(["a", "b", "c"], ["a", "c"], false)).toEqual(["b"]);
});

test("busca sem acento e sem diferenciar maiúsculas", () => {
  expect(contemTexto("ÁGUA BOA", "agua")).toBe(true);
  expect(contemTexto("Itaúba", " ITAUBA ")).toBe(true);
  expect(contemTexto("Ipanema", "boa")).toBe(false);
});
