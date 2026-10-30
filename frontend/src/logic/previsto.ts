import { parametrosDaConsulta, type Consulta } from "./filtro";

// De qual orçamento vem o planejado do financeiro nas páginas Previsto × Realizado e Financeiro (pedido do usuário,
// 29/10/2026): o tipo ("previsao" ou "planejamento") e a versão do plano. Fica na URL, como o filtro do MENU: vale
// nas duas páginas, vai junto no link e no PDF. Vazio = a escolha padrão da API.
export type PedidoDoPrevisto = {
  previsto: string | null;
  versao: string | null; // id da versão; vazio = a mais recente de cada fazenda e safra
};

export function pedidoDaUrl(parametros: URLSearchParams): PedidoDoPrevisto {
  return { previsto: parametros.get("previsto"), versao: parametros.get("versao") };
}

// A consulta da página com a escolha do orçamento.
export function parametrosComPrevisto(consulta: Consulta, pedido: PedidoDoPrevisto): URLSearchParams {
  const parametros = parametrosDaConsulta(consulta);
  if (pedido.previsto) {
    parametros.set("previsto", pedido.previsto);
  }
  if (pedido.versao) {
    parametros.set("versao", pedido.versao);
  }
  return parametros;
}

// A URL com o tipo trocado: a versão é de um tipo só, então sai junto.
export function urlComTipo(parametros: URLSearchParams, tipo: string): URLSearchParams {
  const nova = new URLSearchParams(parametros);
  nova.set("previsto", tipo);
  nova.delete("versao");
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
