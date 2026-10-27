import { describe, expect, test } from "vitest";
import type { FazendaDoEscopo } from "../core/api/tipos";
import {
  alternarItem,
  anosDisponiveis,
  fazendasDaOrigem,
  clientesDoEscopo,
  consultaDoFiltro,
  filtroDaUrl,
  filtroParaUrl,
  mesesDoPeriodo,
  nomeDaSelecao,
  parametrosDaConsulta,
  rotuloDoFiltro,
} from "./filtro";

const HOJE = "2026-10";

function fazenda(id: string, cliente: string, primeiroMes: string, ultimoMes: string,
  origem = "planilha"): FazendaDoEscopo {
  return {
    id,
    nome: `FAZENDA ${id}`,
    cliente,
    origem,
    sistema_produtivo: null,
    primeiro_mes: primeiroMes,
    ultimo_mes: ultimoMes,
    capacidades: { estoque: true, rebanho_medio: true, area: true, financeiro: true, planejado: true },
  };
}

const FAZENDAS = [
  fazenda("a1", "ANA SOUZA", "2024-06-01", "2026-03-01"),
  fazenda("a2", "ANA SOUZA", "2025-06-01", "2025-08-01"),
  fazenda("b1", "Cliente Metryx", "2025-01-01", "2026-09-01", "metryx"),
  fazenda("c1", "ANA SOUZA", "2025-01-01", "2026-09-01", "metryx"),     // o mesmo nome também no Metryx
];

describe("períodos", () => {
  test("safra vai de julho a junho e para no mês atual", () => {
    expect(mesesDoPeriodo("safra", 2025, HOJE)).toEqual([
      "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12",
      "2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06",
    ]);
    expect(mesesDoPeriodo("safra", 2026, HOJE)).toEqual(["2026-07", "2026-08", "2026-09", "2026-10"]);
    expect(mesesDoPeriodo("civil", 2026, HOJE)).toHaveLength(10);
  });

  test("safras com dado, da mais recente para a mais antiga", () => {
    expect(anosDisponiveis(FAZENDAS.slice(0, 2), "safra", HOJE)).toEqual([2026, 2025, 2024, 2023]);
    expect(anosDisponiveis(FAZENDAS.slice(0, 2), "civil", HOJE)).toEqual([2026, 2025, 2024]);
  });
});

describe("filtro do menu", () => {
  test("cliente é o proprietário (ou o customer), um de cada, só da origem escolhida", () => {
    expect(clientesDoEscopo(fazendasDaOrigem(FAZENDAS, "planilha"))).toEqual(["ANA SOUZA"]);
    expect(clientesDoEscopo(fazendasDaOrigem(FAZENDAS, "metryx"))).toEqual(["Cliente Metryx", "ANA SOUZA"]);
  });

  test("o mesmo nome nas duas origens não mistura as fazendas", () => {
    const url = new URLSearchParams("origem=metryx&cliente=ANA SOUZA&visao=safra&ano=2025");
    const filtro = filtroDaUrl(url, FAZENDAS, HOJE);
    if (filtro === null) {
      throw new Error("filtro vazio");
    }
    expect(consultaDoFiltro(filtro, FAZENDAS, HOJE).fazendas).toEqual(["c1"]);
  });

  test("sem nada na URL: primeiro cliente, todas as fazendas (GRUPO), safra do último dado, todos os meses", () => {
    const filtro = filtroDaUrl(new URLSearchParams(), FAZENDAS, HOJE);
    expect(filtro).toEqual({ origem: "planilha", cliente: "ANA SOUZA", fazendas: [], visao: "safra", ano: 2025,
      meses: [] });
    if (filtro === null) {
      throw new Error("filtro vazio");
    }
    expect(nomeDaSelecao(filtro, FAZENDAS)).toBe("GRUPO");
    expect(rotuloDoFiltro(filtro)).toBe("Safra 25/26 · todos os meses");
    expect(consultaDoFiltro(filtro, FAZENDAS, HOJE)).toEqual({
      fazendas: ["a1", "a2"],
      inicio: "2025-07",
      fim: "2026-06",
      meses: [],
    });
  });

  test("uma fazenda e um mês", () => {
    const url = new URLSearchParams("cliente=ANA SOUZA&fazenda=a2&visao=civil&ano=2025&mes=2025-08");
    const filtro = filtroDaUrl(url, FAZENDAS, HOJE);
    expect(filtro).toEqual({ origem: "planilha", cliente: "ANA SOUZA", fazendas: ["a2"], visao: "civil", ano: 2025,
      meses: ["2025-08"] });
    if (filtro === null) {
      throw new Error("filtro vazio");
    }
    expect(nomeDaSelecao(filtro, FAZENDAS)).toBe("FAZENDA a2");
    expect(rotuloDoFiltro(filtro)).toBe("2025 · ago/25");
    expect(consultaDoFiltro(filtro, FAZENDAS, HOJE)).toEqual({ fazendas: ["a2"], inicio: "2025-08", fim: "2025-08",
      meses: ["2025-08"] });
  });

  test("fazenda de outro cliente, ano sem dado e mês fora do período voltam ao padrão", () => {
    const url = new URLSearchParams("cliente=ANA SOUZA&fazenda=b1&visao=safra&ano=1999&mes=2030-01");
    expect(filtroDaUrl(url, FAZENDAS, HOJE)).toEqual({
      origem: "planilha",
      cliente: "ANA SOUZA",
      fazendas: [],
      visao: "safra",
      ano: 2025,
      meses: [],
    });
  });

  test("cliente que o usuário não vê cai no primeiro; sem fazenda nenhuma, não há filtro", () => {
    expect(filtroDaUrl(new URLSearchParams("cliente=OUTRO"), FAZENDAS, HOJE)?.cliente).toBe("ANA SOUZA");
    expect(filtroDaUrl(new URLSearchParams(), [], HOJE)).toBeNull();
  });

  test("ida e volta pela URL não muda o filtro", () => {
    const filtro = { origem: "planilha" as const, cliente: "ANA SOUZA", fazendas: ["a2"], visao: "safra" as const,
      ano: 2025, meses: ["2025-07", "2025-09"] };
    expect(filtroDaUrl(filtroParaUrl(filtro), FAZENDAS, HOJE)).toEqual(filtro);
  });
});

describe("meses de seleção múltipla, como no BI", () => {
  const SAFRA = mesesDoPeriodo("safra", 2025, HOJE);

  test("meses salteados: a API recebe o primeiro, o último e os marcados", () => {
    const url = new URLSearchParams("cliente=ANA SOUZA&visao=safra&ano=2025&mes=2025-09&mes=2025-07&mes=2025-09");
    const filtro = filtroDaUrl(url, FAZENDAS, HOJE);
    if (filtro === null) {
      throw new Error("filtro vazio");
    }
    expect(filtro.meses).toEqual(["2025-07", "2025-09"]);       // em ordem e sem repetir
    expect(rotuloDoFiltro(filtro)).toBe("Safra 25/26 · jul/25, set/25");
    const consulta = consultaDoFiltro(filtro, FAZENDAS, HOJE);
    expect(consulta).toEqual({ fazendas: ["a1", "a2"], inicio: "2025-07", fim: "2025-09",
      meses: ["2025-07", "2025-09"] });
    expect(parametrosDaConsulta(consulta).getAll("meses")).toEqual(["2025-07", "2025-09"]);
  });

  test("mês fora do período sai; marcar todos é o mesmo que Todos", () => {
    const fora = new URLSearchParams("cliente=ANA SOUZA&visao=safra&ano=2025&mes=2024-12&mes=2025-08");
    expect(filtroDaUrl(fora, FAZENDAS, HOJE)?.meses).toEqual(["2025-08"]);
    const todos = new URLSearchParams(`cliente=ANA SOUZA&visao=safra&ano=2025&${SAFRA.map((mes) => `mes=${mes}`).join("&")}`);
    expect(filtroDaUrl(todos, FAZENDAS, HOJE)?.meses).toEqual([]);
  });

  test("marcar e desmarcar no MENU", () => {
    expect(alternarItem([], "2025-08", SAFRA)).toEqual(["2025-08"]);                 // de Todos para um mês
    expect(alternarItem(["2025-08"], "2025-07", SAFRA)).toEqual(["2025-07", "2025-08"]);
    expect(alternarItem(["2025-07", "2025-08"], "2025-07", SAFRA)).toEqual(["2025-08"]);
    expect(alternarItem(["2025-08"], "2025-08", SAFRA)).toEqual([]);                 // desmarcar o último: Todos
  });

  test("mais de três meses aparecem pela quantidade", () => {
    const filtro = { origem: "planilha" as const, cliente: "ANA SOUZA", fazendas: [], visao: "safra" as const,
      ano: 2025, meses: SAFRA.slice(0, 4) };
    expect(rotuloDoFiltro(filtro)).toBe("Safra 25/26 · 4 meses");
  });
});

describe("fazendas de seleção múltipla", () => {
  const VARIAS = [
    fazenda("v1", "JOSÉ", "2024-01-01", "2026-09-01"),
    fazenda("v2", "JOSÉ", "2024-01-01", "2026-09-01"),
    fazenda("v3", "JOSÉ", "2024-01-01", "2026-09-01"),
    fazenda("v4", "JOSÉ", "2024-01-01", "2026-09-01"),
    fazenda("v5", "JOSÉ", "2024-01-01", "2026-09-01"),
  ];

  function filtroDe(consulta: string) {
    const filtro = filtroDaUrl(new URLSearchParams(`cliente=JOSÉ&visao=safra&ano=2025&${consulta}`), VARIAS, HOJE);
    if (filtro === null) {
      throw new Error("filtro vazio");
    }
    return filtro;
  }

  test("as marcadas vão para a API, na ordem do cliente e sem repetir", () => {
    const filtro = filtroDe("fazenda=v3&fazenda=v1&fazenda=v3");
    expect(filtro.fazendas).toEqual(["v1", "v3"]);
    expect(consultaDoFiltro(filtro, VARIAS, HOJE).fazendas).toEqual(["v1", "v3"]);
    expect(filtroParaUrl(filtro).getAll("fazenda")).toEqual(["v1", "v3"]);
  });

  test("marcar todas é o mesmo que GRUPO; fazenda de outro cliente sai", () => {
    expect(filtroDe("fazenda=v1&fazenda=v2&fazenda=v3&fazenda=v4&fazenda=v5").fazendas).toEqual([]);
    expect(filtroDe("fazenda=v2&fazenda=a1").fazendas).toEqual(["v2"]);
  });

  test("o topo mostra os nomes separados por ' | ' e, com mais de 3, a quantidade", () => {
    expect(nomeDaSelecao(filtroDe(""), VARIAS)).toBe("GRUPO");
    expect(nomeDaSelecao(filtroDe("fazenda=v1&fazenda=v2"), VARIAS)).toBe("FAZENDA v1 | FAZENDA v2");
    expect(nomeDaSelecao(filtroDe("fazenda=v1&fazenda=v2&fazenda=v3&fazenda=v4"), VARIAS)).toBe("4 fazendas");
  });

  test("marcar e desmarcar fazendas segue a mesma regra dos meses", () => {
    const ids = VARIAS.map((item) => item.id);
    expect(alternarItem([], "v2", ids)).toEqual(["v2"]);
    expect(alternarItem(["v2", "v3", "v4", "v5"], "v1", ids)).toEqual([]);         // marcou a última: GRUPO
  });
});
