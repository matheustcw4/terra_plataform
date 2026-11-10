import { describe, expect, test } from "vitest";
import type { VersoesDaFazenda } from "../core/api/tipos";
import {
  comMaisRecente,
  comVersaoAlternada,
  jeitoDaEscolha,
  maisRecenteEmTodas,
  resumoDasVersoes,
  semPlanejamento,
} from "./versaoDoPlano";

const ADMINISTRATIVO: VersoesDaFazenda = { fazenda_id: "f1", fazenda: "ADMINISTRATIVO", escolhidas: [], sem_plano: false,
  versoes: [{ id: "a3", rotulo: "Versao p/ financiament" }, { id: "a2", rotulo: "07.07.25_Ramon e Fuvio" }] };
const BONITO: VersoesDaFazenda = { fazenda_id: "f2", fazenda: "U6 BONITO", escolhidas: ["b1"], sem_plano: false,
  versoes: [{ id: "b2", rotulo: "26/27 - Bonito (erro)" }, { id: "b1", rotulo: "26/27 - Bonito" }] };

describe("versão do plano de cada fazenda, de seleção múltipla", () => {
  test("marcar duas versões da mesma fazenda guarda as duas (elas somam); desmarcar a última volta à mais recente", () => {
    const vazia = { versoes: ["b1"], semPlano: [] };
    const uma = comVersaoAlternada(vazia, ADMINISTRATIVO, "a2");
    expect(uma).toEqual({ versoes: ["b1", "a2"], semPlano: [] });
    const duas = comVersaoAlternada(uma, { ...ADMINISTRATIVO, escolhidas: ["a2"] }, "a3");
    expect(duas).toEqual({ versoes: ["b1", "a2", "a3"], semPlano: [] });
    expect(comVersaoAlternada(uma, { ...ADMINISTRATIVO, escolhidas: ["a2"] }, "a2")).toEqual(vazia);
  });

  test("nenhum planejamento tira as marcadas da fazenda; marcar uma versão desfaz o nenhum", () => {
    const nenhum = semPlanejamento({ versoes: ["b1", "a2"], semPlano: [] }, ADMINISTRATIVO);
    expect(nenhum).toEqual({ versoes: ["b1"], semPlano: ["f1"] });
    expect(comVersaoAlternada(nenhum, { ...ADMINISTRATIVO, sem_plano: true }, "a3"))
      .toEqual({ versoes: ["b1", "a3"], semPlano: [] });
    expect(comMaisRecente(nenhum, ADMINISTRATIVO)).toEqual({ versoes: ["b1"], semPlano: [] });
  });

  test("todas de volta para a mais recente, sem perder a escolha de fazenda fora da janela", () => {
    expect(maisRecenteEmTodas({ versoes: ["b1", "a2", "x9"], semPlano: ["f1", "f7"] }, [ADMINISTRATIVO, BONITO]))
      .toEqual({ versoes: ["x9"], semPlano: ["f7"] });
  });

  test("o jeito da escolha e o texto do botão", () => {
    expect(jeitoDaEscolha(ADMINISTRATIVO)).toBe("mais_recente");
    expect(jeitoDaEscolha(BONITO)).toBe("marcadas");
    expect(jeitoDaEscolha({ ...ADMINISTRATIVO, sem_plano: true })).toBe("nenhum");
    expect(resumoDasVersoes([ADMINISTRATIVO])).toBe("Mais recente");
    expect(resumoDasVersoes([ADMINISTRATIVO, { ...BONITO, escolhidas: [] }])).toBe("Mais recente em todas as fazendas");
    expect(resumoDasVersoes([ADMINISTRATIVO, BONITO])).toBe("1 fazenda com escolha própria");
    expect(resumoDasVersoes([{ ...ADMINISTRATIVO, sem_plano: true }, BONITO])).toBe("2 fazendas com escolha própria");
  });
});
