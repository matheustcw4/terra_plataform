import { describe, expect, test } from "vitest";
import type { Funcao } from "../core/api/tipos";
import { opcoesDeFuncao } from "./funcoes";

const FUNCOES: Funcao[] = [
  { id: 1, nome: "Técnico", ativo: true, usuarios: 2 },
  { id: 2, nome: "Gerente", ativo: false, usuarios: 1 },
  { id: 3, nome: "Consultor", ativo: true, usuarios: 0 },
];

describe("opções de função no cadastro de usuário", () => {
  test("só as ativas, em ordem de nome", () => {
    expect(opcoesDeFuncao(FUNCOES).map((funcao) => funcao.nome)).toEqual(["Consultor", "Técnico"]);
  });

  test("a função atual do usuário entra mesmo inativa", () => {
    expect(opcoesDeFuncao(FUNCOES, 2).map((funcao) => funcao.nome)).toEqual(["Consultor", "Gerente", "Técnico"]);
  });
});
