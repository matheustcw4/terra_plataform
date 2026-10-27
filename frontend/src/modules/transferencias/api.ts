import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { chamarApi } from "../../core/api/cliente";
import type { Transferencias } from "../../core/api/tipos";
import { parametrosDaConsulta, type Consulta } from "../../logic/filtro";

// GET /dashboards/transferencias?fazendas=..&inicio=AAAA-MM&fim=AAAA-MM
export function useTransferencias(consulta: Consulta) {
  return useQuery({
    queryKey: ["transferencias", consulta],
    queryFn: () => chamarApi<Transferencias>(`/dashboards/transferencias?${parametrosDaConsulta(consulta)}`),
    placeholderData: keepPreviousData,
  });
}
