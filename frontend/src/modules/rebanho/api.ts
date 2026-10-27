import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { chamarApi } from "../../core/api/cliente";
import type { Movimentacao } from "../../core/api/tipos";
import { parametrosDaConsulta, type Consulta } from "../../logic/filtro";

// GET /dashboards/movimentacao?fazendas=..&fazendas=..&inicio=AAAA-MM&fim=AAAA-MM
export function useMovimentacao(consulta: Consulta) {
  return useQuery({
    queryKey: ["movimentacao", consulta],
    queryFn: () => chamarApi<Movimentacao>(`/dashboards/movimentacao?${parametrosDaConsulta(consulta)}`),
    // Ao trocar o filtro, a página anterior continua na tela (esmaecida) até a nova chegar.
    placeholderData: keepPreviousData,
  });
}
