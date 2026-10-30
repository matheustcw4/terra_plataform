import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { chamarApi } from "../../core/api/cliente";
import type { Financeiro } from "../../core/api/tipos";
import type { Consulta } from "../../logic/filtro";
import { parametrosComPrevisto, type PedidoDoPrevisto } from "../../logic/previsto";

// GET /dashboards/financeiro?fazendas=..&inicio=AAAA-MM&fim=AAAA-MM[&previsto=..&versao=..]
export function useFinanceiro(consulta: Consulta, pedido: PedidoDoPrevisto) {
  return useQuery({
    queryKey: ["financeiro", consulta, pedido],
    queryFn: () => chamarApi<Financeiro>(`/dashboards/financeiro?${parametrosComPrevisto(consulta, pedido)}`),
    placeholderData: keepPreviousData,
  });
}
