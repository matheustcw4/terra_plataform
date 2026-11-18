import { describe, expect, test } from "vitest";
import type { FazendaDoEscopo } from "../core/api/tipos";
import {
  classificacoesDasFazendas,
  contasDasFazendas,
  mostrarOFiltro,
  opcoesNaOrdem,
  resumoDaEscolha,
  tiposDasFazendas,
} from "./filtrosDoFinanceiro";

function fazenda(id: string, tipos: string[], classificacoes: string[],
  contas: { id: string; nome: string }[]): FazendaDoEscopo {
  return {
    id, nome: id, cliente: "MAISTER", origem: "metryx", sistema_produtivo: null, primeiro_mes: "2025-01-01",
    ultimo_mes: "2025-10-01",
    capacidades: { estoque: true, rebanho_medio: true, area: false, financeiro: true, planejado: true,
      situacoes: ["pago"], tipos_de_atividade: tipos, classificacoes, contas_bancarias: contas },
  };
}

// a ordem geral do escopo (`opcoes_do_financeiro`)
const TIPOS = ["Pecuária", "Agricultura", "Silvicultura", "A classificar", "Sem atividade"];
const CLASSIFICACOES = ["Receitas operacionais", "Investimento em fazenda", "Custeio", "Outros débitos"];

const AGUA_BOA = fazenda("f1", ["Pecuária", "Agricultura", "Sem atividade"], ["Custeio", "Outros débitos"],
  [{ id: "c2", nome: "Itaú - SP" }]);
const IPANEMA = fazenda("f2", ["Pecuária", "A classificar"], ["Receitas operacionais", "Custeio"],
  [{ id: "c1", nome: "Banco do Brasil" }, { id: "c2", nome: "Itaú - SP" }]);

describe("filtros do financeiro", () => {
  test("as opções das fazendas, sem repetir e na ordem geral da API", () => {
    expect(opcoesNaOrdem(["a", "b", "c", "d"], [["c", "a"], ["a"], ["x"]])).toEqual(["a", "c", "x"]);
    expect(tiposDasFazendas([AGUA_BOA, IPANEMA], TIPOS).map((opcao) => opcao.valor))
      .toEqual(["Pecuária", "Agricultura", "A classificar", "Sem atividade"]);
    expect(classificacoesDasFazendas([AGUA_BOA, IPANEMA], CLASSIFICACOES).map((opcao) => opcao.valor))
      .toEqual(["Receitas operacionais", "Custeio", "Outros débitos"]);
    expect(classificacoesDasFazendas([AGUA_BOA], CLASSIFICACOES).map((opcao) => opcao.valor))
      .toEqual(["Custeio", "Outros débitos"]);
  });

  test("a conta bancária é do cliente: aparece uma vez, pelo nome", () => {
    expect(contasDasFazendas([AGUA_BOA, IPANEMA])).toEqual([{ valor: "c1", rotulo: "Banco do Brasil" },
      { valor: "c2", rotulo: "Itaú - SP" }]);
  });

  test("o resumo do campo fechado", () => {
    const contas = contasDasFazendas([IPANEMA]);
    expect(resumoDaEscolha([], contas, "Todas")).toBe("Todas");
    expect(resumoDaEscolha(["c2"], contas, "Todas")).toBe("Itaú - SP");
    expect(resumoDaEscolha(["c1", "c2"], contas, "Todas")).toBe("Banco do Brasil, Itaú - SP");
    expect(resumoDaEscolha(["a", "b", "c"], [], "Todos")).toBe("3 marcados");
  });

  test("só aparece com o que escolher, ou com uma escolha a desfazer", () => {
    const planilha = tiposDasFazendas([fazenda("p1", ["Sem atividade"], ["Custeio"], [])], TIPOS);
    expect(mostrarOFiltro(planilha, [])).toBe(false);
    expect(mostrarOFiltro(planilha, ["Pecuária"])).toBe(true);
    expect(mostrarOFiltro(tiposDasFazendas([AGUA_BOA], TIPOS), [])).toBe(true);
  });
});
