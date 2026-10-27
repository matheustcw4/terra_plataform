import type { GrupoDoMenu } from "./Casca";
import type { ParteDoAssunto } from "../../logic/personalizado";

// As páginas do boletim, na ordem do menu (a mesma ordem do BI). `noPdf`: aparece no seletor do "Exportar PDF"
// (Pendências é para corrigir lançamentos, não faz parte do boletim). `icone`: nome em core/ui/Icone.
export type PaginaDoBoletim = { caminho: string; rotulo: string; icone: string; noPdf: boolean };

export const PAGINAS_DO_BOLETIM: PaginaDoBoletim[] = [
  { caminho: "/previsto_realizado", rotulo: "Previsto × Realizado", icone: "alvo", noPdf: true },
  { caminho: "/financeiro", rotulo: "Financeiro", icone: "moeda", noPdf: true },
  { caminho: "/rebanho/movimentacao", rotulo: "Movimentação", icone: "fluxo", noPdf: true },
  { caminho: "/vendas/abate", rotulo: "Venda Abate", icone: "etiqueta", noPdf: true },
  { caminho: "/vendas/em_pe", rotulo: "Venda em Pé", icone: "caminhao", noPdf: true },
  { caminho: "/compras", rotulo: "Compras", icone: "carrinho", noPdf: true },
  { caminho: "/nascimentos", rotulo: "Nascimentos", icone: "broto", noPdf: true },
  { caminho: "/mortes", rotulo: "Mortes", icone: "cruz", noPdf: true },
  { caminho: "/transferencias", rotulo: "Transferências", icone: "setas", noPdf: true },
  { caminho: "/pendencias", rotulo: "Pendências", icone: "alerta", noPdf: false },
];

// A página dona do caminho, numa lista de itens de menu (o título, o ícone do cabeçalho e as migalhas saem daqui).
export function paginaDoCaminho<Pagina extends { caminho: string }>(caminho: string, paginas: Pagina[]): Pagina | null {
  return paginas.find((pagina) => caminho === pagina.caminho || caminho.startsWith(`${pagina.caminho}/`)) ?? null;
}

// O menu lateral do boletim: as páginas, a de pendências à parte e, no fim, o MENU (filtros) e a administração (só
// para o admin; a API também recusa as rotas /admin para os outros).
export function gruposDoBoletim(ehAdmin: boolean): GrupoDoMenu[] {
  const geral = [{ caminho: "/menu", rotulo: "Filtros (MENU)", icone: "filtro" }];
  if (ehAdmin) {
    geral.push({ caminho: "/admin", rotulo: "Administração", icone: "ajustes" });
  }
  return [
    { titulo: "Boletim", itens: PAGINAS_DO_BOLETIM.filter((pagina) => pagina.noPdf) },
    { titulo: "Qualidade", itens: PAGINAS_DO_BOLETIM.filter((pagina) => !pagina.noPdf) },
    { titulo: "Geral", itens: geral },
  ];
}

// A capa entra no PDF como uma página a mais, antes das outras.
export const CAPA = "capa";

// O que o seletor do PDF oferece, na ordem em que as páginas saem no arquivo.
export const ORDEM_DO_PDF: string[] = [
  CAPA,
  ...PAGINAS_DO_BOLETIM.filter((pagina) => pagina.noPdf).map((pagina) => pagina.caminho),
];

export function rotuloDaPaginaDoPdf(chave: string): string {
  if (chave === CAPA) {
    return "Capa";
  }
  return PAGINAS_DO_BOLETIM.find((pagina) => pagina.caminho === chave)?.rotulo ?? chave;
}

// Os modos do "Exportar PDF": o padrão (as páginas do painel, como estão na tela), o analítico (folhas A4 com o mês de
// referência, o acumulado e a meta, explicados em frases) e o personalizado (os assuntos do analítico e mais
// nascimentos, compras e transferências, com a pessoa escolhendo o que mostrar em cada um).
export type ModoDoPdf = "padrao" | "analitico" | "personalizado";

// As folhas do modo Analítico, na ordem em que saem no arquivo (a capa é a mesma do modo padrão).
export const FOLHAS_ANALITICAS: { chave: string; rotulo: string }[] = [
  { chave: CAPA, rotulo: "Capa" },
  { chave: "estoque", rotulo: "Movimentação do estoque" },
  { chave: "lotacao", rotulo: "Lotação" },
  { chave: "placar_zootecnico", rotulo: "Placar zootécnico" },
  { chave: "vendas_abate", rotulo: "Vendas abate" },
  { chave: "vendas_em_pe", rotulo: "Vendas em pé" },
  { chave: "mortes", rotulo: "Mortes" },
  { chave: "placar_financeiro", rotulo: "Placar financeiro" },
  { chave: "caixa", rotulo: "Caixa (previsto × realizado)" },
];

export const ORDEM_ANALITICA: string[] = FOLHAS_ANALITICAS.map((folha) => folha.chave);

// Os assuntos do modo Personalizado, na ordem do boletim.
export const ASSUNTOS_PERSONALIZADOS: { chave: string; rotulo: string }[] = [
  { chave: CAPA, rotulo: "Capa" },
  { chave: "estoque", rotulo: "Movimentação do estoque" },
  { chave: "lotacao", rotulo: "Lotação" },
  { chave: "placar_zootecnico", rotulo: "Placar zootécnico" },
  { chave: "nascimentos", rotulo: "Nascimentos" },
  { chave: "compras", rotulo: "Compras" },
  { chave: "vendas_abate", rotulo: "Vendas abate" },
  { chave: "vendas_em_pe", rotulo: "Vendas em pé" },
  { chave: "transferencias", rotulo: "Transferências" },
  { chave: "mortes", rotulo: "Mortes" },
  { chave: "placar_financeiro", rotulo: "Financeiro" },
  { chave: "caixa", rotulo: "Fluxo de caixa" },
];

export const ORDEM_PERSONALIZADA: string[] = ASSUNTOS_PERSONALIZADOS.map((assunto) => assunto.chave);

export function ordemDoModo(modo: ModoDoPdf): string[] {
  if (modo === "analitico") {
    return ORDEM_ANALITICA;
  }
  if (modo === "personalizado") {
    return ORDEM_PERSONALIZADA;
  }
  return ORDEM_DO_PDF;
}

export function rotuloDaFolha(modo: ModoDoPdf, chave: string): string {
  if (modo === "analitico") {
    return FOLHAS_ANALITICAS.find((folha) => folha.chave === chave)?.rotulo ?? chave;
  }
  if (modo === "personalizado") {
    return ASSUNTOS_PERSONALIZADOS.find((assunto) => assunto.chave === chave)?.rotulo ?? chave;
  }
  return rotuloDaPaginaDoPdf(chave);
}

// O que a página de exportação recebe na navegação (location.state): nada disso vai para a URL nem é gravado.
export type PedidoDePdf = {
  modo: ModoDoPdf;
  paginas: string[]; // chaves da ordem do modo (ordemDoModo), já na ordem
  partes: ParteDoAssunto[]; // só no personalizado: o que mostrar em cada assunto
  cidade: string;
  notaInicial: string; // a nota técnica do começo do PDF (vazia = sem nota)
  notaFinal: string; // a nota técnica do fim do PDF
  voltar: string; // a página de onde a pessoa pediu o PDF
};
