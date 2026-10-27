import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { chamarApi } from "../../core/api/cliente";
import type {
  AlteracaoDeFuncao,
  AlteracaoDeUsuario,
  CategoriasDeOrigem,
  ContasDeOrigem,
  FazendaDoAcesso,
  Funcao,
  NovoUsuario,
  UsuarioDoAdmin,
} from "../../core/api/tipos";

function parametrosDaLista(soPendentes: boolean, busca: string): string {
  return new URLSearchParams({ so_pendentes: String(soPendentes), busca }).toString();
}

// GET /admin/categorias?so_pendentes=true&busca=..
export function useCategorias(soPendentes: boolean, busca: string) {
  return useQuery({
    queryKey: ["admin", "categorias", soPendentes, busca],
    queryFn: () => chamarApi<CategoriasDeOrigem>(`/admin/categorias?${parametrosDaLista(soPendentes, busca)}`),
    placeholderData: keepPreviousData,
  });
}

// GET /admin/contas?so_pendentes=true&busca=..
export function useContas(soPendentes: boolean, busca: string) {
  return useQuery({
    queryKey: ["admin", "contas", soPendentes, busca],
    queryFn: () => chamarApi<ContasDeOrigem>(`/admin/contas?${parametrosDaLista(soPendentes, busca)}`),
    placeholderData: keepPreviousData,
  });
}

// GET /admin/usuarios
export function useUsuarios() {
  return useQuery({ queryKey: ["admin", "usuarios"], queryFn: () => chamarApi<UsuarioDoAdmin[]>("/admin/usuarios") });
}

// GET /admin/usuarios/{id}/fazendas
export function useFazendasDoUsuario(usuarioId: string) {
  return useQuery({
    queryKey: ["admin", "acesso", usuarioId],
    queryFn: () => chamarApi<FazendaDoAcesso[]>(`/admin/usuarios/${usuarioId}/fazendas`),
  });
}

// Depois de qualquer mudança no admin, tudo o que veio da API pode ter mudado (estoque, DRE, escopo): relê tudo.
function useRelerTudo() {
  const cliente = useQueryClient();
  return () => cliente.invalidateQueries();
}

// PUT /admin/categorias/{id}; categoria vazia volta o de-para para pendente
export function useClassificarCategoria() {
  const relerTudo = useRelerTudo();
  return useMutation({
    mutationFn: (pedido: { id: string; categoria: number | null }) =>
      chamarApi<void>(`/admin/categorias/${pedido.id}`, {
        method: "PUT",
        body: JSON.stringify({ categoria_bi_id: pedido.categoria }),
      }),
    onSuccess: relerTudo,
  });
}

// PUT /admin/contas/{id}; centro vazio volta a conta para "A classificar"
export function useClassificarConta() {
  const relerTudo = useRelerTudo();
  return useMutation({
    mutationFn: (pedido: { id: string; centro: number | null }) =>
      chamarApi<void>(`/admin/contas/${pedido.id}`, {
        method: "PUT",
        body: JSON.stringify({ centro_custo_id: pedido.centro }),
      }),
    onSuccess: relerTudo,
  });
}

// POST /admin/usuarios
export function useCriarUsuario() {
  const relerTudo = useRelerTudo();
  return useMutation({
    mutationFn: (novo: NovoUsuario) =>
      chamarApi<UsuarioDoAdmin>("/admin/usuarios", { method: "POST", body: JSON.stringify(novo) }),
    onSuccess: relerTudo,
  });
}

// PATCH /admin/usuarios/{id} (só os campos enviados mudam)
export function useAlterarUsuario() {
  const relerTudo = useRelerTudo();
  return useMutation({
    mutationFn: (pedido: { id: string; alteracao: AlteracaoDeUsuario }) =>
      chamarApi<UsuarioDoAdmin>(`/admin/usuarios/${pedido.id}`, {
        method: "PATCH",
        body: JSON.stringify(pedido.alteracao),
      }),
    onSuccess: relerTudo,
  });
}

// PUT /admin/usuarios/{id}/fazendas: a lista completa de fazendas que o usuário passa a ver
export function useTrocarAcesso() {
  const relerTudo = useRelerTudo();
  return useMutation({
    mutationFn: (pedido: { id: string; fazendas: string[] }) =>
      chamarApi<FazendaDoAcesso[]>(`/admin/usuarios/${pedido.id}/fazendas`, {
        method: "PUT",
        body: JSON.stringify({ fazendas: pedido.fazendas }),
      }),
    onSuccess: relerTudo,
  });
}

// GET /admin/funcoes (ativas primeiro)
export function useFuncoes() {
  return useQuery({ queryKey: ["admin", "funcoes"], queryFn: () => chamarApi<Funcao[]>("/admin/funcoes") });
}

// POST /admin/funcoes
export function useCriarFuncao() {
  const relerTudo = useRelerTudo();
  return useMutation({
    mutationFn: (nome: string) =>
      chamarApi<Funcao>("/admin/funcoes", { method: "POST", body: JSON.stringify({ nome }) }),
    onSuccess: relerTudo,
  });
}

// PATCH /admin/funcoes/{id}: renomear ou ativar/desativar
export function useAlterarFuncao() {
  const relerTudo = useRelerTudo();
  return useMutation({
    mutationFn: (pedido: { id: number; alteracao: AlteracaoDeFuncao }) =>
      chamarApi<Funcao>(`/admin/funcoes/${pedido.id}`, { method: "PATCH", body: JSON.stringify(pedido.alteracao) }),
    onSuccess: relerTudo,
  });
}

// DELETE /admin/funcoes/{id} (a API recusa função que algum usuário tem)
export function useApagarFuncao() {
  const relerTudo = useRelerTudo();
  return useMutation({
    mutationFn: (id: number) => chamarApi<void>(`/admin/funcoes/${id}`, { method: "DELETE" }),
    onSuccess: relerTudo,
  });
}
