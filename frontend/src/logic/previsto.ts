import { parametrosDaConsulta, type Consulta } from "./filtro";

// De qual orçamento vem o planejado do financeiro nas páginas Previsto × Realizado e Financeiro (pedido do usuário,
// 29/10/2026): o tipo ("previsao" ou "planejamento"). A versão do plano (`versao`) vale nas metas de todas as
// páginas e vai na consulta (filtro.ts). Os dois ficam na URL, como o filtro do MENU: vão junto no link e no PDF.
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

// A URL com o tipo trocado; a versão do plano continua (ela vale também nas metas das outras páginas).
export function urlComTipo(parametros: URLSearchParams, tipo: string): URLSearchParams {
  const nova = new URLSearchParams(parametros);
  nova.set("previsto", tipo);
  return nova;
}

// A URL com a versão trocada; vazio volta para a mais recente.
export function urlComVersao(parametros: URLSearchParams, versao: string): URLSearchParams {
  const nova = new URLSearchParams(parametros);
  if (versao) {
    nova.set("versao", versao);
  } else {
    nova.delete("versao");
  }
  return nova;
}
