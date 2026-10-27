import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { chamarApi } from "../../core/api/cliente";
import type { Compras } from "../../core/api/tipos";
import { parametrosDaConsulta, type Consulta } from "../../logic/filtro";

// GET /dashboards/compras?fazendas=..&inicio=AAAA-MM&fim=AAAA-MM
export function useCompras(consulta: Consulta) {
  return useQuery({
    queryKey: ["compras", consulta],
    queryFn: () => chamarApi<Compras>(`/dashboards/compras?${parametrosDaConsulta(consulta)}`),
    placeholderData: keepPreviousData,
  });
}
