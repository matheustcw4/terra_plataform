import { useQuery } from "@tanstack/react-query";
import { chamarApi } from "../../core/api/cliente";
import type { CargaDaIntegracao, IntegracaoPorApi } from "../../core/api/tipos";
import { algumaRodando } from "../../logic/integracoes";

// GET /admin/integracoes: as APIs que alimentam o painel (só o admin; para os outros, nem pergunta).
export function useIntegracoes(ehAdmin: boolean) {
  return useQuery({
    queryKey: ["integracoes"],
    queryFn: () => chamarApi<IntegracaoPorApi[]>("/admin/integracoes"),
    enabled: ehAdmin,
  });
}

// GET /admin/integracoes/{fonte}/cargas: as cargas mais recentes. Enquanto alguma roda, pergunta de novo a cada 5 s.
export function useCargasDaApi(fonte: string) {
  return useQuery({
    queryKey: ["integracoes", fonte, "cargas"],
    queryFn: () => chamarApi<CargaDaIntegracao[]>(`/admin/integracoes/${fonte}/cargas`),
    staleTime: 0,
    refetchInterval: (consulta) => {
      if (algumaRodando(consulta.state.data ?? [])) {
        return 5000;
      }
      return false;
    },
  });
}
