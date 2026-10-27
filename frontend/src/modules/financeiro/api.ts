import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { chamarApi } from "../../core/api/cliente";
import type { Financeiro } from "../../core/api/tipos";
import { parametrosDaConsulta, type Consulta } from "../../logic/filtro";

// GET /dashboards/financeiro?fazendas=..&inicio=AAAA-MM&fim=AAAA-MM
export function useFinanceiro(consulta: Consulta) {
  return useQuery({
    queryKey: ["financeiro", consulta],
    queryFn: () => chamarApi<Financeiro>(`/dashboards/financeiro?${parametrosDaConsulta(consulta)}`),
    placeholderData: keepPreviousData,
  });
}
