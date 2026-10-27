import { expect, test } from "vitest";
import { alternarItem } from "./listas";

test("abrir e fechar um item, sem mexer nos outros", () => {
  expect(alternarItem([], "A - RECEITAS")).toEqual(["A - RECEITAS"]);
  expect(alternarItem(["A - RECEITAS", "D - CUSTEIO"], "A - RECEITAS")).toEqual(["D - CUSTEIO"]);
});
