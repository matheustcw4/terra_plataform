import { describe, expect, test } from "vitest";
import type { Importacao } from "../core/api/tipos";
import {
  algumaEmAndamento,
  classeDaSituacao,
  motivoDaRecusa,
  resumoDaCarga,
  rotuloDaSituacao,
  tamanhoLegivel,
  terminouAlguma,
} from "./importacao";

function importacao(id: string, status: Importacao["status"], avisos = 0, quarentena = 0): Importacao {
  return {
    id,
    arquivo: "RELATÓRIO - 85 - TESTE.xlsm",
    tamanho_bytes: 1000,
    enviado_por: "Fulano",
    enviado_em: "2026-11-09T10:00:00Z",
    minha: true,
    status,
    mensagem: null,
    avisos,
    quarentena,
    fazendas: [],
    iniciado_em: null,
    finalizado_em: null,
  };
}

describe("o arquivo antes de enviar", () => {
  test("o nome segue o padrão das planilhas, com ou sem acento, .xlsm ou .xlsx", () => {
    expect(motivoDaRecusa("RELATÓRIO - 85 - TESTE.xlsm", 10)).toBeNull();
    expect(motivoDaRecusa("Relatorio_94_MATER (1).xlsx", 10)).toBeNull();
    expect(motivoDaRecusa("RELATÓRIO - 85 - TESTE.xlsm".normalize("NFD"), 10)).toBeNull();   // nome vindo do Mac
    expect(motivoDaRecusa("planilha da fazenda.xlsm", 10)).toContain("RELATÓRIO - código do projeto - fazenda");
    expect(motivoDaRecusa("RELATÓRIO - 85 - TESTE.pdf", 10)).not.toBeNull();
  });

  test("vazio ou grande demais nem vai para a API", () => {
    expect(motivoDaRecusa("RELATÓRIO - 85 - TESTE.xlsm", 0)).toBe("o arquivo está vazio");
    expect(motivoDaRecusa("RELATÓRIO - 85 - TESTE.xlsm", 51 * 1024 * 1024)).toBe("o arquivo passa de 50 MB");
  });

  test("tamanho legível", () => {
    expect(tamanhoLegivel(9686938)).toBe("9,2 MB");
    expect(tamanhoLegivel(300)).toBe("1 KB");
    expect(tamanhoLegivel(85 * 1024)).toBe("85 KB");
  });
});

describe("a lista de importações", () => {
  test("situação e cor do selo", () => {
    expect(rotuloDaSituacao("carregada_com_avisos")).toBe("Carregada, com avisos");
    expect(classeDaSituacao("carregada")).toBe("selo selo-ok");
    expect(classeDaSituacao("ignorada")).toBe("selo selo-aviso");
    expect(classeDaSituacao("erro")).toBe("selo selo-erro");
    expect(classeDaSituacao("na_fila")).toBe("selo selo-andamento");
  });

  test("acompanha enquanto alguma espera o worker e percebe quando ela termina", () => {
    const antes = [importacao("a", "processando"), importacao("b", "carregada")];
    expect(algumaEmAndamento(antes)).toBe(true);
    expect(terminouAlguma(antes, [importacao("a", "processando"), importacao("b", "carregada")])).toBe(false);
    const depois = [importacao("a", "erro"), importacao("b", "carregada")];
    expect(terminouAlguma(antes, depois)).toBe(true);
    expect(algumaEmAndamento(depois)).toBe(false);
    expect(terminouAlguma([], [importacao("c", "carregada")])).toBe(false);   // a primeira leitura não conta
  });

  test("o resumo do que é para conferir", () => {
    expect(resumoDaCarga(importacao("a", "carregada"))).toBe("");
    expect(resumoDaCarga(importacao("a", "carregada_com_avisos", 1))).toBe("1 aviso");
    expect(resumoDaCarga(importacao("a", "carregada_com_avisos", 3, 2))).toBe("3 avisos · 2 linhas fora dos números");
  });
});
