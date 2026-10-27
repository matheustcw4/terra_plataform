import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { chamarApi } from "../../core/api/cliente";
import type { Mortes } from "../../core/api/tipos";
import { parametrosDaConsulta, type Consulta } from "../../logic/filtro";

// GET /dashboards/mortes?fazendas=..&inicio=AAAA-MM&fim=AAAA-MM
export function useMortes(consulta: Consulta) {
  return useQuery({
    queryKey: ["mortes", consulta],
    queryFn: () => chamarApi<Mortes>(`/dashboards/mortes?${parametrosDaConsulta(consulta)}`),
    placeholderData: keepPreviousData,
  });
}
