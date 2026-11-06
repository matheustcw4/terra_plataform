import { useQuery } from "@tanstack/react-query";
import { chamarApi } from "../../core/api/cliente";
import type { BoletimAnalitico } from "../../core/api/tipos";
import type { Visao } from "../../logic/filtro";

// GET /dashboards/analitico?fazendas=..&mes_referencia=AAAA-MM&visao=safra|civil[&versao=..]: tudo o que as folhas
// do modo Analítico mostram, numa chamada só; as metas na versão do planejamento escolhida nas páginas.
export function useBoletimAnalitico(fazendas: string[], mesReferencia: string, visao: Visao, versao: string | null) {
  const parametros = new URLSearchParams({ mes_referencia: mesReferencia, visao });
  for (const fazenda of fazendas) {
    parametros.append("fazendas", fazenda);
  }
  if (versao) {
    parametros.set("versao", versao);
  }
  return useQuery({
    queryKey: ["analitico", fazendas, mesReferencia, visao, versao],
    queryFn: () => chamarApi<BoletimAnalitico>(`/dashboards/analitico?${parametros.toString()}`),
  });
}
