import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { chamarApi } from "../../core/api/cliente";
import type { Pendencias } from "../../core/api/tipos";
import type { Consulta } from "../../logic/filtro";

// GET /qualidade/pendencias?fazendas=..&fazendas=..  (sem período: data errada é um dos problemas)
export function usePendencias(consulta: Consulta) {
  const parametros = new URLSearchParams();
  for (const fazenda of consulta.fazendas) {
    parametros.append("fazendas", fazenda);
  }
  return useQuery({
    queryKey: ["pendencias", consulta.fazendas],
    queryFn: () => chamarApi<Pendencias>(`/qualidade/pendencias?${parametros}`),
    placeholderData: keepPreviousData,
  });
}
