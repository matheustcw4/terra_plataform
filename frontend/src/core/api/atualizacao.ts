import { useMutation, useQuery } from "@tanstack/react-query";
import { intervaloDeAcompanhamento } from "../../logic/atualizacao";
import { chamarApi } from "./cliente";
import type { PedidoDeAtualizacao, SituacaoDaAtualizacao } from "./tipos";

// GET /admin/atualizacao (só admin): a trava das cargas e a carga mais recente. Enquanto espera o worker, pergunta de
// novo a cada poucos segundos.
export function useSituacaoDaAtualizacao(pedidaEm: string | null) {
  return useQuery({
    queryKey: ["admin", "atualizacao"],
    queryFn: () => chamarApi<SituacaoDaAtualizacao>("/admin/atualizacao"),
    staleTime: 30 * 1000,
    refetchInterval: (consulta) => intervaloDeAcompanhamento(consulta.state.data, pedidaEm),
  });
}

// POST /admin/atualizacao: põe a carga na fila do worker (409 se já tem carga rodando, 503 se a fila não responde).
export function usePedirAtualizacao() {
  return useMutation({
    mutationFn: () => chamarApi<PedidoDeAtualizacao>("/admin/atualizacao", { method: "POST" }),
  });
}
