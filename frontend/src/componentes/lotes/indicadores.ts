import type { IndicadoresDoLote } from "../../core/api/tipos";
import { dinheiro, numero, percentual } from "../../logic/formatar";

// Venda para abate, venda em pé, compra ou transferência: os lotes de gado das páginas Venda Abate, Venda em Pé,
// Compras e Transferências.
export type TipoDeLote = "abate" | "em_pe" | "compra" | "transferencia";

// Uma linha dos quadros Fêmea / Macho / Geral: o nome (como no BI) e como mostrar o valor que veio pronto da API.
export type Indicador = {
  titulo: string;
  mostrar: (indicadores: IndicadoresDoLote) => string;
};

const CABECAS_VENDIDAS: Indicador = {
  titulo: "Cabeças Vendidas",
  mostrar: (indicadores) => numero(indicadores.cabecas),
};
const CABECAS_COMPRADAS: Indicador = {
  titulo: "Cabeças Compradas",
  mostrar: (indicadores) => numero(indicadores.cabecas),
};
const QUANTIDADE: Indicador = {
  titulo: "Quantidade",
  mostrar: (indicadores) => numero(indicadores.cabecas),
};
const PESO_MEDIO: Indicador = {
  titulo: "Peso Médio",
  mostrar: (indicadores) => comUnidade(numero(indicadores.peso_medio_kg, 1), "kg"),
};
const RENDIMENTO: Indicador = {
  titulo: "Rendimento de Carcaça",
  mostrar: (indicadores) => percentual(indicadores.rendimento_carcaca),
};
const PRECO_DO_KG: Indicador = {
  titulo: "Preço do KG",
  mostrar: (indicadores) => dinheiro(indicadores.preco_kg, 2),
};
const VALOR_DA_ARROBA: Indicador = {
  titulo: "Valor da @",
  mostrar: (indicadores) => dinheiro(indicadores.preco_arroba, 2),
};

// As linhas dos quadros das páginas do BI: Venda Abate, Venda em Pé, Compras e Transferências.
export function indicadoresDoTipo(tipo: TipoDeLote): Indicador[] {
  if (tipo === "abate") {
    return [CABECAS_VENDIDAS, PESO_MEDIO, RENDIMENTO, VALOR_DA_ARROBA];
  }
  if (tipo === "em_pe") {
    return [CABECAS_VENDIDAS, PESO_MEDIO, PRECO_DO_KG, VALOR_DA_ARROBA];
  }
  if (tipo === "compra") {
    return [CABECAS_COMPRADAS, PESO_MEDIO, PRECO_DO_KG];
  }
  return [QUANTIDADE, PESO_MEDIO, VALOR_DA_ARROBA];
}

// "466,7 kg"; sem valor, só o traço.
function comUnidade(valor: string, unidade: string): string {
  if (valor === "—") {
    return valor;
  }
  return `${valor} ${unidade}`;
}
