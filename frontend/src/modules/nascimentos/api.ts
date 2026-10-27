import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { chamarApi } from "../../core/api/cliente";
import type { Nascimentos } from "../../core/api/tipos";
import { parametrosDaConsulta, type Consulta } from "../../logic/filtro";

// GET /dashboards/nascimentos?fazendas=..&inicio=AAAA-MM&fim=AAAA-MM
export function useNascimentos(consulta: Consulta) {
  return useQuery({
    queryKey: ["nascimentos", consulta],
    queryFn: () => chamarApi<Nascimentos>(`/dashboards/nascimentos?${parametrosDaConsulta(consulta)}`),
    placeholderData: keepPreviousData,
  });
}
