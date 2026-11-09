import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { chamarApi } from "../../core/api/cliente";
import type { Importacao } from "../../core/api/tipos";
import { algumaEmAndamento } from "../../logic/importacao";

const CHAVE = ["importacoes"];

// GET /importacoes: as mais recentes que o usuário vê. Enquanto alguma espera o worker, pergunta de novo a cada 5 s.
export function useImportacoes() {
  return useQuery({
    queryKey: CHAVE,
    queryFn: () => chamarApi<Importacao[]>("/importacoes"),
    staleTime: 0,
    refetchInterval: (consulta) => {
      if (algumaEmAndamento(consulta.state.data ?? [])) {
        return 5000;
      }
      return false;
    },
  });
}

// POST /importacoes (multipart, um arquivo por pedido): a planilha vai para a fila do worker.
export function useEnviarPlanilha() {
  const cliente = useQueryClient();
  return useMutation({
    mutationFn: (arquivo: File) => {
      const corpo = new FormData();
      corpo.append("arquivo", arquivo, arquivo.name);
      return chamarApi<Importacao>("/importacoes", { method: "POST", body: corpo });
    },
    onSuccess: () => cliente.invalidateQueries({ queryKey: CHAVE }),
  });
}
