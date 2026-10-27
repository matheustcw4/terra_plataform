import { describe, expect, test } from "vitest";
import type { SituacaoDaAtualizacao } from "../core/api/tipos";
import {
  ACOMPANHAR_A_CADA_MS,
  dicaDaAtualizacao,
  estadoDaAtualizacao,
  intervaloDeAcompanhamento,
  precisaAcompanhar,
} from "./atualizacao";

const PEDIDA_EM = "2026-10-16T10:00:00-04:00";

function situacao(agora: string, rodando: boolean, iniciadoEm: string | null): SituacaoDaAtualizacao {
  let ultima = null;
  if (iniciadoEm !== null) {
    ultima = { fonte: "planilha", status: "concluido", iniciado_em: iniciadoEm, finalizado_em: iniciadoEm };
  }
  return { rodando, agora, ultima };
}

describe("estado do Atualizar agora", () => {
  test("sem pedido: parado, a não ser que uma carga da agenda esteja rodando", () => {
    expect(estadoDaAtualizacao(situacao(PEDIDA_EM, false, "2026-10-16T08:00:00-04:00"), null)).toBe("parado");
    expect(estadoDaAtualizacao(situacao(PEDIDA_EM, true, null), null)).toBe("rodando");
  });

  test("pedida: na fila até o worker começar, rodando, e concluída quando a carga nova termina", () => {
    const antiga = "2026-10-16T08:00:00-04:00";
    expect(estadoDaAtualizacao(situacao("2026-10-16T10:00:05-04:00", false, antiga), PEDIDA_EM)).toBe("na_fila");
    expect(estadoDaAtualizacao(situacao("2026-10-16T10:00:10-04:00", true, antiga), PEDIDA_EM)).toBe("rodando");
    const nova = "2026-10-16T10:00:08-04:00";
    expect(estadoDaAtualizacao(situacao("2026-10-16T10:01:00-04:00", false, nova), PEDIDA_EM)).toBe("concluida");
  });

  test("o mesmo instante em fusos diferentes conta como depois do pedido", () => {
    const mesmoInstante = "2026-10-16T14:00:00+00:00";
    expect(estadoDaAtualizacao(situacao("2026-10-16T10:00:30-04:00", false, mesmoInstante), PEDIDA_EM))
      .toBe("concluida");
  });

  test("mais de 2 minutos sem começar: o worker não respondeu", () => {
    expect(estadoDaAtualizacao(situacao("2026-10-16T10:02:01-04:00", false, null), PEDIDA_EM)).toBe("sem_resposta");
    expect(estadoDaAtualizacao(situacao("2026-10-16T10:01:59-04:00", false, null), PEDIDA_EM)).toBe("na_fila");
  });

  test("só acompanha enquanto espera o worker", () => {
    expect(precisaAcompanhar("na_fila")).toBe(true);
    expect(precisaAcompanhar("rodando")).toBe(true);
    expect(precisaAcompanhar("parado")).toBe(false);
    expect(precisaAcompanhar("sem_resposta")).toBe(false);
    const naFila = situacao("2026-10-16T10:00:05-04:00", false, null);
    expect(intervaloDeAcompanhamento(naFila, PEDIDA_EM)).toBe(ACOMPANHAR_A_CADA_MS);
    expect(intervaloDeAcompanhamento(naFila, null)).toBe(false);
    expect(intervaloDeAcompanhamento(undefined, PEDIDA_EM)).toBe(false);
  });

  test("a dica diz a última carga quando está parado", () => {
    expect(dicaDaAtualizacao("parado", situacao(PEDIDA_EM, false, null))).toBe("Atualizar os dados agora");
    expect(dicaDaAtualizacao("parado", situacao(PEDIDA_EM, false, PEDIDA_EM))).toMatch(/^Atualizar os dados agora \(última carga: /);
    expect(dicaDaAtualizacao("sem_resposta", undefined)).toMatch(/worker/);
  });
});
