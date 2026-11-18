import type { FazendaDoEscopo } from "../core/api/tipos";

// Os filtros do financeiro além do status (pedido do usuário, 18/11/2026): o tipo de atividade, a classificação e a
// conta bancária, de seleção múltipla (vazio = tudo). As opções são as que as fazendas do filtro têm, pelas
// capacidades que a API manda: a tela não sabe de fonte nenhuma. A conta bancária só existe no realizado; o planejado
// fica inteiro quando ela é escolhida (decisão do usuário).

export type Opcao = { valor: string; rotulo: string };

// As opções que alguma das fazendas tem, na ordem geral que a API manda (`opcoes_do_financeiro` do escopo: os tipos
// na ordem da dimensão e as classificações na ordem do DRE). Uma opção fora da ordem geral entra no fim.
export function opcoesNaOrdem(ordem: string[], listas: string[][]): string[] {
  const presentes = new Set(listas.flat());
  const opcoes = ordem.filter((opcao) => presentes.has(opcao));
  for (const opcao of presentes) {
    if (!opcoes.includes(opcao)) {
      opcoes.push(opcao);
    }
  }
  return opcoes;
}

export function tiposDasFazendas(fazendas: FazendaDoEscopo[], ordem: string[]): Opcao[] {
  const tipos = opcoesNaOrdem(ordem, fazendas.map((fazenda) => fazenda.capacidades.tipos_de_atividade));
  return tipos.map((tipo) => ({ valor: tipo, rotulo: tipo }));
}

export function classificacoesDasFazendas(fazendas: FazendaDoEscopo[], ordem: string[]): Opcao[] {
  const classificacoes = opcoesNaOrdem(ordem, fazendas.map((fazenda) => fazenda.capacidades.classificacoes));
  return classificacoes.map((classificacao) => ({ valor: classificacao, rotulo: classificacao }));
}

// As contas bancárias das fazendas, uma vez cada (a conta é do cliente: duas fazendas podem usar a mesma), pelo nome.
export function contasDasFazendas(fazendas: FazendaDoEscopo[]): Opcao[] {
  const porId = new Map<string, string>();
  for (const fazenda of fazendas) {
    for (const conta of fazenda.capacidades.contas_bancarias) {
      porId.set(conta.id, conta.nome);
    }
  }
  const contas: Opcao[] = [];
  for (const [id, nome] of porId) {
    contas.push({ valor: id, rotulo: nome });
  }
  contas.sort((uma, outra) => uma.rotulo.localeCompare(outra.rotulo, "pt-BR"));
  return contas;
}

// O que o campo mostra fechado: o rótulo de "todos", até dois nomes ou a quantidade.
export function resumoDaEscolha(marcados: string[], opcoes: Opcao[], rotuloDeTodos: string): string {
  if (marcados.length === 0) {
    return rotuloDeTodos;
  }
  if (marcados.length > 2) {
    return `${marcados.length} marcados`;
  }
  const nomes: string[] = [];
  for (const valor of marcados) {
    const opcao = opcoes.find((uma) => uma.valor === valor);
    nomes.push(opcao?.rotulo ?? valor);
  }
  return nomes.join(", ");
}

// O filtro só aparece quando há o que escolher; uma escolha que veio pelo link continua desfazível.
export function mostrarOFiltro(opcoes: Opcao[], marcados: string[]): boolean {
  return opcoes.length > 1 || marcados.length > 0;
}
