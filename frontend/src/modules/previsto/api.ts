import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { chamarApi } from "../../core/api/cliente";
import type { PrevistoRealizado } from "../../core/api/tipos";
import { parametrosDaConsulta, type Consulta } from "../../logic/filtro";

// GET /dashboards/previsto_realizado?fazendas=..&inicio=AAAA-MM&fim=AAAA-MM
export function usePrevistoRealizado(consulta: Consulta) {
  return useQuery({
    queryKey: ["previsto_realizado", consulta],
    queryFn: () => chamarApi<PrevistoRealizado>(`/dashboards/previsto_realizado?${parametrosDaConsulta(consulta)}`),
    placeholderData: keepPreviousData,
  });
}
