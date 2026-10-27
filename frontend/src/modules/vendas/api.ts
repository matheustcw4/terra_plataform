import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { chamarApi } from "../../core/api/cliente";
import type { Vendas } from "../../core/api/tipos";
import { parametrosDaConsulta, type Consulta } from "../../logic/filtro";

export type TipoDeVenda = "abate" | "em_pe";

// GET /dashboards/vendas?tipo=abate|em_pe&fazendas=..&inicio=AAAA-MM&fim=AAAA-MM
export function useVendas(consulta: Consulta, tipo: TipoDeVenda) {
  const parametros = parametrosDaConsulta(consulta);
  parametros.set("tipo", tipo);
  return useQuery({
    queryKey: ["vendas", tipo, consulta],
    queryFn: () => chamarApi<Vendas>(`/dashboards/vendas?${parametros}`),
    placeholderData: keepPreviousData,
  });
}
