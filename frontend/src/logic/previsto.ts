import { parametrosDaConsulta, type Consulta } from "./filtro";

// De qual orçamento vem o planejado do financeiro nas páginas Previsto × Realizado e Financeiro (pedido do usuário,
// 29/10/2026): o tipo ("previsao" ou "planejamento"). As versões do plano de cada fazenda são do filtro (filtro.ts) e
// valem nas metas de todas as páginas. O tipo fica na URL, como o filtro do MENU: vai junto no link e no PDF.
// Vazio = a escolha padrão da API.
export type PedidoDoPrevisto = {
  previsto: string | null;
};

export function pedidoDaUrl(parametros: URLSearchParams): PedidoDoPrevisto {
  return { previsto: parametros.get("previsto") };
}

// A consulta da página com a escolha do orçamento.
export function parametrosComPrevisto(consulta: Consulta, pedido: PedidoDoPrevisto): URLSearchParams {
  const parametros = parametrosDaConsulta(consulta);
  if (pedido.previsto) {
    parametros.set("previsto", pedido.previsto);
  }
  return parametros;
}

// A URL com o tipo trocado; o resto do filtro continua.
export function urlComTipo(parametros: URLSearchParams, tipo: string): URLSearchParams {
  const nova = new URLSearchParams(parametros);
  nova.set("previsto", tipo);
  return nova;
}

