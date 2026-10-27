import { describe, expect, test } from "vitest";
import type { IndicadoresDoLote } from "../../core/api/tipos";
import { indicadoresDoTipo, type TipoDeLote } from "./indicadores";

// Abate da fazenda sintética do backend (tests/test_api.py), recorte GERAL do realizado.
const ABATE: IndicadoresDoLote = {
  cabecas: 30,
  valor: 154200,
  kg_vivo: 14000,
  arrobas: 490,
  preco_arroba: 314.6938775,
  preco_kg: 11.0142857,
  peso_medio_kg: 466.6666667,
  rendimento_carcaca: 0.525,
};

function mostrados(tipo: TipoDeLote, indicadores: IndicadoresDoLote): Record<string, string> {
  const resultado: Record<string, string> = {};
  for (const indicador of indicadoresDoTipo(tipo)) {
    resultado[indicador.titulo] = indicador.mostrar(indicadores);
  }
  return resultado;
}

describe("linhas dos quadros de lote (as mesmas do BI)", () => {
  test("abate: rendimento de carcaça", () => {
    expect(mostrados("abate", ABATE)).toEqual({
      "Cabeças Vendidas": "30",
      "Peso Médio": "466,7 kg",
      "Rendimento de Carcaça": "52,5%",
      "Valor da @": "R$ 314,69",
    });
  });

  test("em pé: preço do kg no lugar do rendimento; sem venda, média vira traço", () => {
    const semVenda = { ...ABATE, cabecas: 0, valor: 0, kg_vivo: 0, arrobas: 0, preco_arroba: null, preco_kg: null,
      peso_medio_kg: null, rendimento_carcaca: null };
    expect(mostrados("em_pe", semVenda)).toEqual({
      "Cabeças Vendidas": "0",
      "Peso Médio": "—",
      "Preço do KG": "—",
      "Valor da @": "—",
    });
  });

  test("compra: cabeças compradas, peso médio e preço do kg", () => {
    const compra = { ...ABATE, cabecas: 70, valor: 192000, kg_vivo: 18000, preco_kg: 10.6667, peso_medio_kg: 257.14 };
    expect(mostrados("compra", compra)).toEqual({
      "Cabeças Compradas": "70",
      "Peso Médio": "257,1 kg",
      "Preço do KG": "R$ 10,67",
    });
  });

  test("transferência: quantidade, peso médio e valor da @", () => {
    const entrada = { ...ABATE, cabecas: 30, valor: 60000, kg_vivo: 6000, arrobas: 200, preco_arroba: 300,
      peso_medio_kg: 200 };
    expect(mostrados("transferencia", entrada)).toEqual({
      Quantidade: "30",
      "Peso Médio": "200,0 kg",
      "Valor da @": "R$ 300,00",
    });
  });
});
