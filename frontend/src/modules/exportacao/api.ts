import { useQuery } from "@tanstack/react-query";
import { chamarApi } from "../../core/api/cliente";
import type { BoletimAnalitico } from "../../core/api/tipos";
import type { Visao } from "../../logic/filtro";

// GET /dashboards/analitico?fazendas=..&mes_referencia=AAAA-MM&visao=safra|civil: tudo o que as folhas do modo
// Analítico mostram, numa chamada só.
export function useBoletimAnalitico(fazendas: string[], mesReferencia: string, visao: Visao) {
  const parametros = new URLSearchParams({ mes_referencia: mesReferencia, visao });
  for (const fazenda of fazendas) {
    parametros.append("fazendas", fazenda);
  }
  return useQuery({
    queryKey: ["analitico", fazendas, mesReferencia, visao],
    queryFn: () => chamarApi<BoletimAnalitico>(`/dashboards/analitico?${parametros.toString()}`),
  });
}
