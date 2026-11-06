import { describe, expect, test } from "vitest";
import { parametrosComPrevisto, pedidoDaUrl, urlComTipo, urlComVersao } from "./previsto";

const CONSULTA = { fazendas: ["f1"], inicio: "2025-07", fim: "2026-06", meses: [], versao: null };

describe("escolha do orçamento do planejado", () => {
  test("lê o tipo da URL; sem ele, a escolha padrão", () => {
    expect(pedidoDaUrl(new URLSearchParams("origem=metryx&previsto=planejamento&versao=v3"))).toEqual({
      previsto: "planejamento",
    });
    expect(pedidoDaUrl(new URLSearchParams("origem=metryx"))).toEqual({ previsto: null });
  });

  test("a consulta leva o tipo só quando há um; a versão vem da consulta", () => {
    expect(parametrosComPrevisto(CONSULTA, { previsto: null }).toString()).toBe(
      "inicio=2025-07&fim=2026-06&fazendas=f1",
    );
    expect(parametrosComPrevisto({ ...CONSULTA, versao: "v3" }, { previsto: "planejamento" }).toString()).toBe(
      "inicio=2025-07&fim=2026-06&fazendas=f1&versao=v3&previsto=planejamento",
    );
  });

  test("trocar o tipo mantém a versão e o filtro do MENU", () => {
    const url = new URLSearchParams("cliente=X&previsto=planejamento&versao=v3");
    expect(urlComTipo(url, "previsao").toString()).toBe("cliente=X&previsto=previsao&versao=v3");
  });

  test("versão vazia volta para a mais recente", () => {
    const url = new URLSearchParams("cliente=X&previsto=planejamento");
    expect(urlComVersao(url, "v1").toString()).toBe("cliente=X&previsto=planejamento&versao=v1");
    expect(urlComVersao(new URLSearchParams("previsto=planejamento&versao=v1"), "").toString()).toBe(
      "previsto=planejamento",
    );
  });
});
