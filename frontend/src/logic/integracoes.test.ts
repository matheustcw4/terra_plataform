import { describe, expect, test } from "vitest";
import type { CargaDaIntegracao, UnidadeDaCarga } from "../core/api/tipos";
import {
  algumaRodando,
  classeDaCarga,
  duracaoDaCarga,
  origemDoPedido,
  resumoDosClientes,
  rotuloDaCarga,
  textoSemAvisos,
} from "./integracoes";

function carga(campos: Partial<CargaDaIntegracao>): CargaDaIntegracao {
  return {
    id: "c1",
    status: "concluido",
    iniciado_em: "2026-11-10T15:20:00-04:00",
    finalizado_em: "2026-11-10T15:22:05-04:00",
    pedida_por: null,
    unidades: [],
    avisos: [],
    ...campos,
  };
}

function unidade(status: UnidadeDaCarga["status"]): UnidadeDaCarga {
  return { nome: "Cliente", status, erro: null, avisos: 0 };
}

describe("cargas das integrações", () => {
  test("o selo e o rótulo de cada situação", () => {
    expect([rotuloDaCarga("concluido_com_avisos"), classeDaCarga("concluido_com_avisos")]).toEqual(
      ["Concluída, com avisos", "selo selo-aviso"]);
    expect(classeDaCarga("erro")).toBe("selo selo-erro");
    expect(classeDaCarga("processando")).toBe("selo selo-andamento");
  });

  test("a duração em segundos ou minutos; sem fim, um traço", () => {
    expect(duracaoDaCarga(carga({}))).toBe("2 min 05 s");
    expect(duracaoDaCarga(carga({ finalizado_em: "2026-11-10T15:20:45-04:00" }))).toBe("45 s");
    expect(duracaoDaCarga(carga({ status: "processando", finalizado_em: null }))).toBe("—");
  });

  test("quem pediu: o admin ou a agenda", () => {
    expect(origemDoPedido(carga({}))).toBe("pela agenda");
    expect(origemDoPedido(carga({ pedida_por: "Ana" }))).toBe("pedida por Ana");
  });

  test("o resumo dos clientes conta cada resultado", () => {
    const unidades = [unidade("carregada"), unidade("carregada_com_avisos"), unidade("inalterada"), unidade("erro")];
    expect(resumoDosClientes(unidades)).toBe("4 clientes: 2 carregados · 1 sem mudança · 1 com erro");
    expect(resumoDosClientes([unidade("ignorada")])).toBe("1 cliente: 1 não entrou");
    expect(resumoDosClientes([])).toBe("nenhum cliente");
  });

  test("sem avisos: rodando, limpa ou com os avisos trocados pela carga seguinte", () => {
    expect(textoSemAvisos(carga({ status: "processando" }))).toContain("ainda está rodando");
    expect(textoSemAvisos(carga({}))).toBe("Nenhum erro ou aviso nesta carga.");
    expect(textoSemAvisos(carga({ status: "concluido_com_avisos" }))).toContain("já saíram");
  });

  test("acompanha enquanto alguma carga roda", () => {
    expect(algumaRodando([carga({}), carga({ status: "processando" })])).toBe(true);
    expect(algumaRodando([carga({ status: "erro" })])).toBe(false);
  });
});
