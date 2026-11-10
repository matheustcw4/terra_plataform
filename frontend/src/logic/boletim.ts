import type {
  BoletimAnalitico,
  FazendaDoEscopo,
  LinhaDoPlacar,
  QuadroDoLote,
  SecaoDeLotes,
  SecaoDeVendas,
} from "../core/api/tipos";
import { mesPorExtenso, nomesDaCapa, periodoDaCapa } from "./exportacao";
import { nomeDaSelecao, rotuloDaOrigem, type Filtro } from "./filtro";
import { numero } from "./formatar";
import { mesCurto } from "./meses";

// O boletim de resultados (o "Exportar PDF" no Boletim Resumido), no desenho do gerador oficial da Terra
// (gerar_boletim.py): capa, Resumo, Financeiro, Rebanho e Comercialização, em folhas de paisagem. A API manda os
// números e as frases prontos; aqui só se decide o que aparece e como cada número se escreve.

export const SITE_DA_TERRA = "terradesenvolvimento.com.br";
export const LEMA_DA_TERRA = "Razão para produzir, emoção para transformar.";
export const SERVICOS_DA_TERRA = ["Diagnósticos", "Controle de dados", "Planejamento", "Recuperação gerencial",
  "Resultados financeiros", "Treinamentos"];

// As folhas que a pessoa pode marcar no Boletim Resumido, na ordem do arquivo.
export type ChaveDaFolha = "resumo" | "financeiro" | "rebanho" | "comercializacao";
export const TITULO_DA_FOLHA: Record<ChaveDaFolha, string> = {
  resumo: "Resumo · Previsto × Realizado",
  financeiro: "Financeiro",
  rebanho: "Rebanho",
  comercializacao: "Comercialização",
};
const ORDEM_DAS_FOLHAS: ChaveDaFolha[] = ["resumo", "financeiro", "rebanho", "comercializacao"];

export type FolhaNumerada = { chave: ChaveDaFolha; numero: number };

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

// "jan/26" -> "jan": o eixo dos gráficos pequenos só mostra o mês.
export function mesDoEixo(data: string): string {
  return mesCurto(data).slice(0, 3);
}

// "2026-09-01" -> "Set/26": o mês no título das tabelas.
export function mesComAno(data: string): string {
  return comMaiuscula(mesCurto(data));
}

// "jan/26" -> "Jan": o cabeçalho das tabelas de meses.
export function mesDaTabela(data: string): string {
  return comMaiuscula(mesDoEixo(data));
}

// "R$ 6,46 mi", "−R$ 6,46 mi", "R$ 819,4 mil", "R$ 450": o número grande dos cartões.
export function reaisCurtos(valor: number | null): string {
  if (valor === null) {
    return "—";
  }
  return `${sinalDe(valor)}R$ ${semMoeda(Math.abs(valor))}`;
}

// "1,59 mi", "540,7 mil", "450": o valor compacto sem o "R$" (os grupos de desembolso, a diferença do resultado).
export function semMoeda(valor: number): string {
  if (valor >= 1_000_000) {
    return `${numero(valor / 1_000_000, 2)} mi`;
  }
  if (valor >= 1_000) {
    return `${numero(valor / 1_000, 1)} mil`;
  }
  return numero(valor);
}

function sinalDe(valor: number): string {
  if (valor < 0) {
    return "−";
  }
  return "";
}

// "+1,59 mi" e "−540,7 mil": a diferença do resultado na tabela (no resultado, o % não diz nada).
export function diferencaCompacta(valor: number): string {
  if (valor >= 0) {
    return `+${semMoeda(valor)}`;
  }
  return `−${semMoeda(-valor)}`;
}

// "R$ 1,59 mi melhor" ou "R$ 540,7 mil abaixo": a linha do resultado na lateral do resumo.
export function diferencaDoResultado(valor: number): string {
  if (valor >= 0) {
    return `${reaisCurtos(valor)} melhor`;
  }
  return `${reaisCurtos(-valor)} abaixo`;
}

// A escala dos valores de um gráfico em reais, pelo maior deles: milhões, milhares ou reais.
export type UnidadeDosValores = { divisor: number; rotulo: string; casas: number };

export function unidadeDosValores(series: (number | null)[][]): UnidadeDosValores {
  const maior = maiorValor(series.map((serie) => serie.map(absolutoOuNulo)));
  if (maior >= 1_000_000) {
    return { divisor: 1_000_000, rotulo: "R$ mi", casas: 1 };
  }
  if (maior >= 1_000) {
    return { divisor: 1_000, rotulo: "R$ mil", casas: 1 };
  }
  return { divisor: 1, rotulo: "R$", casas: 0 };
}

function absolutoOuNulo(valor: number | null): number | null {
  if (valor === null) {
    return null;
  }
  return Math.abs(valor);
}

export function naUnidade(valor: number | null, unidade: UnidadeDosValores): string {
  if (valor === null) {
    return "—";
  }
  return numero(valor / unidade.divisor, unidade.casas);
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

// "96,2%": quanto da meta o realizado atingiu; sem meta, o traço.
export function percentualDaMeta(fracao: number | null): string {
  if (fracao === null) {
    return "—";
  }
  return `${numero(fracao * 100, 1)}%`;
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

// "TRISTEZA PARASITÁRIA" -> "Tristeza parasitária": a fonte manda categorias e causas em maiúsculas, que não cabem nas
// colunas estreitas do boletim; o nome que já vem em letra normal fica como está.
export function nomeLegivel(nome: string): string {
  if (nome !== nome.toLocaleUpperCase("pt-BR")) {
    return nome;
  }
  return comMaiuscula(nome.toLocaleLowerCase("pt-BR"));
}

// Com mais de 6 meses, os números do realizado e do planejado se encostam em cima das colunas: o planejado fica sem
// número (a cor da coluna e a tabela embaixo já dizem quanto era).
export function cabeONumeroDoPlanejado(quantidadeDeMesesNoGrafico: number): boolean {
  return quantidadeDeMesesNoGrafico <= 6;
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

// A seção teve algum lote no período ou alguma meta? Sem nenhum dos dois, ela vira um quadro "sem movimento".
export function temMovimento(secao: SecaoDeLotes): boolean {
  for (const mes of secao.meses) {
    if ((mes.realizado ?? 0) !== 0 || mes.previsto !== 0) {
      return true;
    }
  }
  return false;
}

export function secaoDeVenda(boletim: BoletimAnalitico, tipo: "abate" | "em_pe"): SecaoDeVendas {
  const venda = boletim.vendas.find((secao) => secao.tipo === tipo);
  if (venda === undefined) {
    throw new Error(`o boletim veio sem a seção de vendas "${tipo}"`);
  }
  return venda;
}

// O quadro de um sexo (GERAL, MACHO, FÊMEA) da venda.
export function quadroDoSexo(quadros: QuadroDoLote[], recorte: string): QuadroDoLote | null {
  return quadros.find((quadro) => quadro.recorte === recorte) ?? null;
}

// Venda dos dois sexos (cabeças realizadas ou planejadas em fêmea e em macho): a tabela mostra Fêmea / Macho / Geral;
// com um sexo só, Realizado × Planejado × Variação.
export function vendeuOsDoisSexos(quadros: QuadroDoLote[]): boolean {
  return teveCabecas(quadroDoSexo(quadros, "FÊMEA")) && teveCabecas(quadroDoSexo(quadros, "MACHO"));
}

function teveCabecas(quadro: QuadroDoLote | null): boolean {
  if (quadro === null) {
    return false;
  }
  return quadro.realizado.cabecas + quadro.planejado.cabecas > 0;
}

// As folhas marcadas, na ordem do arquivo e numeradas.
export function folhasDoBoletim(marcadas: string[]): FolhaNumerada[] {
  const folhas: FolhaNumerada[] = [];
  for (const chave of ORDEM_DAS_FOLHAS) {
    if (marcadas.includes(chave)) {
      folhas.push({ chave, numero: folhas.length + 1 });
    }
  }
  return folhas;
}

// "01", "02"...: o número no selo marrom e na contagem "Página 02/04".
export function doisDigitos(valor: number): string {
  return String(valor).padStart(2, "0");
}

export function rotuloDaPagina(numeroDaFolha: number, total: number): string {
  return `Página ${doisDigitos(numeroDaFolha)}/${doisDigitos(total)}`;
}

// A altura de cada coluna em px, pela maior do gráfico (como o gerador: a coluna vazia fica com 1 px, a pequena com 2).
export function alturaDaColuna(valor: number | null, maior: number, areaUtil: number): number {
  if (valor === null || valor === 0 || maior <= 0) {
    return 1;
  }
  return Math.max(2, Math.round((Math.abs(valor) / maior) * areaUtil));
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
