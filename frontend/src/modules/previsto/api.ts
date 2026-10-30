import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { chamarApi } from "../../core/api/cliente";
import type { PrevistoRealizado } from "../../core/api/tipos";
import type { Consulta } from "../../logic/filtro";
import { parametrosComPrevisto, type PedidoDoPrevisto } from "../../logic/previsto";

// GET /dashboards/previsto_realizado?fazendas=..&inicio=AAAA-MM&fim=AAAA-MM[&previsto=..&versao=..]
export function usePrevistoRealizado(consulta: Consulta, pedido: PedidoDoPrevisto) {
  return useQuery({
    queryKey: ["previsto_realizado", consulta, pedido],
    queryFn: () =>
      chamarApi<PrevistoRealizado>(`/dashboards/previsto_realizado?${parametrosComPrevisto(consulta, pedido)}`),
    placeholderData: keepPreviousData,
  });
}
