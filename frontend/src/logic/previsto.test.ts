import { describe, expect, test } from "vitest";
import { parametrosComPrevisto, pedidoDaUrl, urlComTipo } from "./previsto";

const CONSULTA = { fazendas: ["f1"], inicio: "2025-07", fim: "2026-06", meses: [], situacoes: [], versoes: [],
  semPlano: [] };

describe("escolha do orçamento do planejado", () => {
  test("lê o tipo da URL; sem ele, a escolha padrão", () => {
    expect(pedidoDaUrl(new URLSearchParams("origem=metryx&previsto=planejamento&versao=v3"))).toEqual({
      previsto: "planejamento",
    });
    expect(pedidoDaUrl(new URLSearchParams("origem=metryx"))).toEqual({ previsto: null });
  });

  test("a consulta leva o tipo só quando há um; as versões e o status vêm da consulta", () => {
    expect(parametrosComPrevisto(CONSULTA, { previsto: null }).toString()).toBe(
      "inicio=2025-07&fim=2026-06&fazendas=f1",
    );
    const escolhas = { ...CONSULTA, situacoes: ["em_aberto" as const], versoes: ["v3", "v7"] };
    expect(parametrosComPrevisto(escolhas, { previsto: "planejamento" }).toString()).toBe(
      "inicio=2025-07&fim=2026-06&fazendas=f1&situacao=em_aberto&versao=v3&versao=v7&previsto=planejamento",
    );
  });

  test("trocar o tipo mantém o filtro do MENU (com as versões)", () => {
    const url = new URLSearchParams("cliente=X&previsto=planejamento&versao=v3");
    expect(urlComTipo(url, "previsao").toString()).toBe("cliente=X&previsto=previsao&versao=v3");
  });

});
