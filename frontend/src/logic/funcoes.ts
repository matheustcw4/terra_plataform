import type { Funcao } from "../core/api/tipos";

// As funções que o cadastro de usuário oferece: as ativas, em ordem de nome. A função atual de um usuário entra mesmo
// inativa, para a lista não mostrar uma função diferente da que ele tem.
export function opcoesDeFuncao(funcoes: Funcao[], atual: number | null = null): Funcao[] {
  const opcoes = funcoes.filter((funcao) => funcao.ativo || funcao.id === atual);
  return [...opcoes].sort((uma, outra) => uma.nome.localeCompare(outra.nome, "pt-BR"));
}
