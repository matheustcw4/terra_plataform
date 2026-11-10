import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { chamarApi } from "../../core/api/cliente";
import type { EscolhaDaVersao } from "../../core/api/tipos";
import { parametrosDaConsulta, type Consulta } from "../../logic/filtro";

// GET /dashboards/versoes_do_plano?fazendas=..&inicio=AAAA-MM&fim=AAAA-MM[&versao=..]: no MENU, as versões do plano
// de cada fazenda do filtro que tem mais de uma no período (das metas e do orçamento do planejamento).
export function useVersoesDoPlano(consulta: Consulta) {
  return useQuery({
    queryKey: ["versoes_do_plano", consulta],
    queryFn: () => chamarApi<EscolhaDaVersao>(`/dashboards/versoes_do_plano?${parametrosDaConsulta(consulta)}`),
    placeholderData: keepPreviousData,
  });
}
