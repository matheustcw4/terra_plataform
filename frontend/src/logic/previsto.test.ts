import { describe, expect, test } from "vitest";
import { parametrosComPrevisto, pedidoDaUrl, urlComTipo, urlComVersao } from "./previsto";

const CONSULTA = { fazendas: ["f1"], inicio: "2025-07", fim: "2026-06", meses: [] };

describe("escolha do orçamento do planejado", () => {
  test("lê o tipo e a versão da URL; sem eles, a escolha padrão", () => {
    expect(pedidoDaUrl(new URLSearchParams("origem=metryx&previsto=planejamento&versao=v3"))).toEqual({
      previsto: "planejamento",
      versao: "v3",
    });
    expect(pedidoDaUrl(new URLSearchParams("origem=metryx"))).toEqual({ previsto: null, versao: null });
  });

  test("a consulta leva a escolha só quando há uma", () => {
    expect(parametrosComPrevisto(CONSULTA, { previsto: null, versao: null }).toString()).toBe(
      "inicio=2025-07&fim=2026-06&fazendas=f1",
    );
    expect(parametrosComPrevisto(CONSULTA, { previsto: "planejamento", versao: "v3" }).toString()).toBe(
      "inicio=2025-07&fim=2026-06&fazendas=f1&previsto=planejamento&versao=v3",
    );
  });

  test("trocar o tipo tira a versão e mantém o filtro do MENU", () => {
    const url = new URLSearchParams("cliente=X&previsto=planejamento&versao=v3");
    expect(urlComTipo(url, "previsao").toString()).toBe("cliente=X&previsto=previsao");
  });

  test("versão vazia volta para a mais recente", () => {
    const url = new URLSearchParams("cliente=X&previsto=planejamento");
    expect(urlComVersao(url, "v1").toString()).toBe("cliente=X&previsto=planejamento&versao=v1");
    expect(urlComVersao(new URLSearchParams("previsto=planejamento&versao=v1"), "").toString()).toBe(
      "previsto=planejamento",
    );
  });
});
