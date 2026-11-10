import type { BoletimAnalitico, FazendaDoEscopo, LinhaDoPlacar, SecaoDeLotes } from "../core/api/tipos";
import { mesPorExtenso, nomesDaCapa, periodoDaCapa } from "./exportacao";
import { nomeDaSelecao, rotuloDaOrigem, type Filtro } from "./filtro";
import { numero } from "./formatar";
import { mesCurto } from "./meses";

// O boletim de resultados (o "Exportar PDF" no modo Analítico), no desenho da apresentação da Terra: capa, Resumo,
// Financeiro, Rebanho e Comercialização, em folhas de paisagem. A API manda os números e as frases prontos; aqui só se
// decide o que aparece, em que folha, e como cada número se escreve.

export const SITE_DA_TERRA = "terradesenvolvimento.com.br";
export const LEMA_DA_TERRA = "Razão para produzir, emoção para transformar.";
export const SERVICOS_DA_TERRA = ["Diagnósticos", "Controle de dados", "Planejamento", "Recuperação gerencial",
  "Resultados financeiros", "Treinamentos"];

// As folhas que a pessoa pode marcar no modo Analítico, na ordem do arquivo.
export type ChaveDaFolha = "resumo" | "financeiro" | "rebanho" | "comercializacao";
export const TITULO_DA_FOLHA: Record<ChaveDaFolha, string> = {
  resumo: "Resumo · Previsto × Realizado",
  financeiro: "Financeiro",
  rebanho: "Rebanho",
  comercializacao: "Comercialização",
};
const ORDEM_DAS_FOLHAS: ChaveDaFolha[] = ["resumo", "financeiro", "rebanho", "comercializacao"];

// Os blocos da Comercialização (dois por folha); o que não teve lote nem meta no período não ganha bloco.
export type BlocoDeComercializacao = "abate" | "em_pe" | "compras";
const BLOCOS_DE_COMERCIALIZACAO: BlocoDeComercializacao[] = ["abate", "em_pe", "compras"];
const BLOCOS_POR_FOLHA = 2;

export type FolhaNumerada = { chave: ChaveDaFolha; numero: number; blocos: BlocoDeComercializacao[] };

// O que a capa e o topo de todas as folhas repetem: quem, de quando a quando e de onde vêm os números.
export type Identificacao = {
  titulo: string; // "FAZENDA CMI", ou "GRUPO" com várias fazendas
  fazendas: string; // todos os nomes, separados por " | "
  variasFazendas: boolean;
  cliente: string;
  periodo: string; // "Jan/26 a Out/26": do começo do período ao mês de referência
  meses: number;
  rotuloDoPeriodo: string; // "ANO 2026" ou "SAFRA 25/26"
  sistema: string; // "Integração Planilhas" ou "Metryx"
  planejamento: string; // a versão do planejamento das metas
  localEData: string; // "Cuiabá, novembro de 2026" (a cidade é digitada na exportação)
};

type DatasDoBoletim = Pick<BoletimAnalitico, "inicio_do_periodo" | "mes_referencia" | "plano">;

export function identificacaoDoBoletim(filtro: Filtro, fazendas: FazendaDoEscopo[], boletim: DatasDoBoletim,
  cidade: string, hoje: string): Identificacao {
  const nomes = nomesDaCapa(filtro, fazendas);
  const variasFazendas = nomes.includes(" | ");
  let titulo = nomes;
  if (variasFazendas) {
    titulo = nomeDaSelecao(filtro, fazendas);
  }
  const periodoDoFiltro = periodoDaCapa(filtro);
  let planejamento = boletim.plano.em_uso.join("; ");
  if (planejamento === "") {
    planejamento = "Sem planejamento";
  }
  return {
    titulo, fazendas: nomes, variasFazendas, cliente: filtro.cliente,
    periodo: periodoDosDados(boletim.inicio_do_periodo, boletim.mes_referencia),
    meses: quantidadeDeMeses(boletim.inicio_do_periodo, boletim.mes_referencia),
    rotuloDoPeriodo: `${periodoDoFiltro.titulo} ${periodoDoFiltro.valor}`, sistema: rotuloDaOrigem(filtro.origem),
    planejamento, localEData: localEDataDoBoletim(cidade, hoje),
  };
}

// "Cuiabá, novembro de 2026"; sem cidade, "Novembro de 2026".
export function localEDataDoBoletim(cidade: string, hoje: string): string {
  const data = mesPorExtenso(hoje);
  if (cidade.trim() === "") {
    return comMaiuscula(data);
  }
  return `${cidade.trim()}, ${data}`;
}

// "2026-01-01", "2026-10-01" -> "Jan/26 a Out/26"
export function periodoDosDados(inicio: string, fim: string): string {
  return `${comMaiuscula(mesCurto(inicio))} a ${comMaiuscula(mesCurto(fim))}`;
}

function comMaiuscula(texto: string): string {
  return `${texto.charAt(0).toUpperCase()}${texto.slice(1)}`;
}

// Os meses do começo do período ao mês de referência, contando os dois: jan a out = 10.
export function quantidadeDeMeses(inicio: string, fim: string): number {
  const meses = (Number(fim.slice(0, 4)) - Number(inicio.slice(0, 4))) * 12;
  return meses + Number(fim.slice(5, 7)) - Number(inicio.slice(5, 7)) + 1;
}

// "jan/26" -> "jan": o eixo dos gráficos do boletim só mostra o mês (o ano está no topo da folha).
export function mesDoEixo(data: string): string {
  return mesCurto(data).slice(0, 3);
}

// "R$ 6,46 mi", "−R$ 6,46 mi", "R$ 819,4 mil", "R$ 450": o número grande dos cartões.
export function reaisCurtos(valor: number | null): string {
  if (valor === null) {
    return "—";
  }
  let sinal = "";
  if (valor < 0) {
    sinal = "−";
  }
  const absoluto = Math.abs(valor);
  if (absoluto >= 1_000_000) {
    return `${sinal}R$ ${numero(absoluto / 1_000_000, 2)} mi`;
  }
  if (absoluto >= 1_000) {
    return `${sinal}R$ ${numero(absoluto / 1_000, 1)} mil`;
  }
  return `${sinal}R$ ${numero(absoluto)}`;
}

// "+R$ 1,59 mi" e "−R$ 540,7 mil": a diferença do resultado (no resultado, o % não diz nada).
export function diferencaEmReais(valor: number): string {
  if (valor > 0) {
    return `+${reaisCurtos(valor)}`;
  }
  return reaisCurtos(valor);
}

// O rótulo das colunas em milhões de reais: "1,1"; zero não se escreve.
export function emMilhoes(valor: number | null): string {
  if (valor === null || valor === 0) {
    return "";
  }
  if (Math.abs(valor) < 1_000_000) {
    return numero(valor / 1_000_000, 2);
  }
  return numero(valor / 1_000_000, 1);
}

// A célula das tabelas em milhões: "2,5", "0,96"; zero ou vazio, o traço.
export function celulaEmMilhoes(valor: number | null): string {
  if (valor === null || valor === 0) {
    return "—";
  }
  return emMilhoes(valor);
}

// "+7,2%", "−3,8%", "0,0%"; sem previsto, o traço.
export function variacaoComSinal(fracao: number | null): string {
  if (fracao === null) {
    return "—";
  }
  const texto = numero(Math.abs(fracao) * 100, 1);
  if (fracao > 0) {
    return `+${texto}%`;
  }
  if (fracao < 0) {
    return `−${texto}%`;
  }
  return `${texto}%`;
}

// A variação de um indicador do lote, do jeito que se lê melhor: cabeças e kg em unidades ("−68 cab"), rendimento em
// pontos percentuais ("+2,6 p.p."), preços em % ("+4,2%") e totais em reais ("+R$ 199,3 mil").
export function variacaoDaLinha(linha: LinhaDoPlacar): string {
  const acumulado = linha.acumulado;
  if (linha.unidade === "R$") {
    if (acumulado.variacao === null) {
      return "—";
    }
    return diferencaEmReais(acumulado.variacao);
  }
  if (linha.unidade.startsWith("R$")) {
    return variacaoComSinal(acumulado.variacao_percentual);
  }
  if (linha.unidade === "%") {
    return pontosPercentuais(acumulado.variacao);
  }
  if (acumulado.variacao === null) {
    return "—";
  }
  return `${comSinalDeVariacao(acumulado.variacao, numero(Math.abs(acumulado.variacao), casasDaUnidade(linha.unidade)))} ${linha.unidade}`;
}

function pontosPercentuais(fracao: number | null): string {
  if (fracao === null) {
    return "—";
  }
  return `${comSinalDeVariacao(fracao, numero(Math.abs(fracao) * 100, 1))} p.p.`;
}

function comSinalDeVariacao(valor: number, texto: string): string {
  if (valor > 0) {
    return `+${texto}`;
  }
  if (valor < 0) {
    return `−${texto}`;
  }
  return texto;
}

function casasDaUnidade(unidade: string): number {
  if (unidade === "cab") {
    return 0;
  }
  return 1;
}

// Cabeças nas células: "1.723"; zero ou vazio, o traço.
export function cabecasOuTraco(valor: number | null): string {
  if (valor === null || valor === 0) {
    return "—";
  }
  return numero(valor);
}

// "A - RECEITAS" -> "Receitas"; "F - OUTROS DÉBITOS" -> "Outros débitos"; "A CLASSIFICAR" fica "A classificar".
export function nomeDaClassificacao(classificacao: string): string {
  const semLetra = classificacao.replace(/^[A-Z] - /, "");
  return comMaiuscula(semLetra.toLocaleLowerCase("pt-BR"));
}

// Investimentos e custeio são as partes do desembolso: na tabela, entram recuados embaixo dele.
export function ehParteDoDesembolso(classificacao: string): boolean {
  return classificacao.startsWith("C - ") || classificacao.startsWith("D - ");
}

// O grupo do Previsto × Realizado pela letra da classificação ("A" = receitas, "B" = desembolso).
export function grupoDaLetra<Grupo extends { classificacao: string }>(grupos: Grupo[], letra: string): Grupo | null {
  return grupos.find((grupo) => grupo.classificacao.startsWith(`${letra} - `)) ?? null;
}

// Os meses do começo do período ao mês de referência (os gráficos do boletim não mostram o que ainda não aconteceu).
export function ateAReferencia<Mes extends { mes: string }>(meses: Mes[], referencia: string): Mes[] {
  return meses.filter((mes) => mes.mes <= referencia);
}

// A linha do placar de um indicador ("Desembolso por cabeça", "Cabeças"...).
export function linhaDoIndicador(linhas: LinhaDoPlacar[], indicador: string): LinhaDoPlacar | null {
  return linhas.find((linha) => linha.indicador === indicador) ?? null;
}

// A seção teve algum lote no período ou alguma meta? Sem nenhum dos dois, ela vai para "Sem movimento no período".
export function temMovimento(secao: SecaoDeLotes): boolean {
  for (const mes of secao.meses) {
    if ((mes.realizado ?? 0) !== 0 || mes.previsto !== 0) {
      return true;
    }
  }
  return false;
}

export function secaoDoBloco(boletim: BoletimAnalitico, bloco: BlocoDeComercializacao): SecaoDeLotes {
  if (bloco === "compras") {
    return boletim.compras;
  }
  const venda = boletim.vendas.find((secao) => secao.tipo === bloco);
  if (venda === undefined) {
    throw new Error(`o boletim veio sem a seção de vendas "${bloco}"`);
  }
  return venda;
}

export function blocosComMovimento(boletim: BoletimAnalitico): BlocoDeComercializacao[] {
  return BLOCOS_DE_COMERCIALIZACAO.filter((bloco) => temMovimento(secaoDoBloco(boletim, bloco)));
}

// As folhas marcadas, na ordem do arquivo e numeradas; a Comercialização ganha uma folha a cada dois blocos (sem
// bloco nenhum, uma folha que diz que não houve venda nem compra).
export function folhasDoBoletim(marcadas: string[], blocos: BlocoDeComercializacao[]): FolhaNumerada[] {
  const folhas: FolhaNumerada[] = [];
  for (const chave of ORDEM_DAS_FOLHAS) {
    if (!marcadas.includes(chave)) {
      continue;
    }
    if (chave !== "comercializacao") {
      folhas.push({ chave, numero: folhas.length + 1, blocos: [] });
      continue;
    }
    for (const grupo of emGrupos(blocos, BLOCOS_POR_FOLHA)) {
      folhas.push({ chave, numero: folhas.length + 1, blocos: grupo });
    }
  }
  return folhas;
}

// [a, b, c] em grupos de 2 -> [[a, b], [c]]; lista vazia -> [[]] (a folha sai mesmo assim).
function emGrupos<Item>(itens: Item[], tamanho: number): Item[][] {
  if (itens.length === 0) {
    return [[]];
  }
  const grupos: Item[][] = [];
  for (let inicio = 0; inicio < itens.length; inicio += tamanho) {
    grupos.push(itens.slice(inicio, inicio + tamanho));
  }
  return grupos;
}

// "01", "02"...: o número no selo marrom e na contagem "Página 02/04".
export function doisDigitos(valor: number): string {
  return String(valor).padStart(2, "0");
}

export function rotuloDaPagina(numeroDaFolha: number, total: number): string {
  return `Página ${doisDigitos(numeroDaFolha)}/${doisDigitos(total)}`;
}

// A altura de cada coluna, em % da maior; com tudo zero, nenhuma coluna aparece.
export function alturaDaColuna(valor: number | null, maior: number): number {
  if (valor === null || valor <= 0 || maior <= 0) {
    return 0;
  }
  return (valor / maior) * 100;
}

// O maior valor de várias séries (a escala comum das colunas de um gráfico).
export function maiorValor(series: (number | null)[][]): number {
  let maior = 0;
  for (const serie of series) {
    for (const valor of serie) {
      if (valor !== null && valor > maior) {
        maior = valor;
      }
    }
  }
  return maior;
}
