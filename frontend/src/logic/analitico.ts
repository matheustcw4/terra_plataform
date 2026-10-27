import type { FazendaDoEscopo, LinhaDoPlacar } from "../core/api/tipos";
import { consultaDoFiltro, rotuloDoAno, type Filtro, type Visao } from "./filtro";
import { dinheiro, numero, percentual } from "./formatar";
import { mesPorExtenso, nomesDaCapa } from "./exportacao";

// O boletim analítico (o "Exportar PDF" no modo Analítico). A API manda os números e as frases prontos; aqui só se
// formata o que vai em cada célula.

// O que todas as folhas A4 (as do analítico, do personalizado e as da nota técnica) repetem no cabeçalho.
export type Cabecalho = {
  fazendas: string; // a fazenda ou as fazendas do grupo
  mesDeReferencia: string; // "setembro de 2026"
  periodo: string; // "Safra 26/27"
  rotuloDaMeta: string; // "Meta da safra" ou "Meta do ano"
};

export function cabecalhoDoBoletim(filtro: Filtro, fazendas: FazendaDoEscopo[]): Cabecalho {
  return {
    fazendas: nomesDaCapa(filtro, fazendas),
    mesDeReferencia: rotuloDoMesDeReferencia(mesDeReferencia(filtro, fazendas)),
    periodo: rotuloDoPeriodo(filtro.ano, filtro.visao),
    rotuloDaMeta: rotuloDaMeta(filtro.visao),
  };
}

// A nota técnica digitada na exportação, em parágrafos: a linha em branco separa os parágrafos; a quebra simples
// continua dentro do parágrafo (a folha mostra com white-space: pre-line).
export function paragrafosDaNota(texto: string): string[] {
  const paragrafos = [];
  for (const trecho of texto.split(/\n\s*\n/)) {
    const limpo = trecho.trim();
    if (limpo !== "") {
      paragrafos.push(limpo);
    }
  }
  return paragrafos;
}

// O mês de referência do boletim analítico: o último mês do filtro do MENU ("AAAA-MM").
export function mesDeReferencia(filtro: Filtro, fazendas: FazendaDoEscopo[]): string {
  return consultaDoFiltro(filtro, fazendas).fim;
}

// "2026-09" -> "setembro de 2026"
export function rotuloDoMesDeReferencia(mes: string): string {
  return mesPorExtenso(mes);
}

// O período no cabeçalho das folhas: "Safra 25/26" ou "Ano civil 2026" (só "2026" ficaria solto).
export function rotuloDoPeriodo(ano: number, visao: Visao): string {
  if (visao === "civil") {
    return `Ano civil ${ano}`;
  }
  return rotuloDoAno(ano, visao);
}

// A meta é a do período inteiro do filtro: a safra (jul a jun) ou o ano civil.
export function rotuloDaMeta(visao: Visao): string {
  if (visao === "civil") {
    return "Meta do ano";
  }
  return "Meta da safra";
}

// O valor na unidade do indicador: cabeças sem casas, lotação e @ com duas, preços em reais, % com duas.
export function valorComUnidade(valor: number | null | undefined, unidade: string): string {
  if (valor === null || valor === undefined) {
    return "—";
  }
  if (unidade === "%") {
    return percentual(valor, 2);
  }
  if (unidade === "R$") {
    return dinheiro(valor);
  }
  if (unidade.startsWith("R$")) {
    return dinheiro(valor, 2);
  }
  if (unidade === "cab") {
    return numero(valor);
  }
  if (unidade === "kg") {
    return numero(valor, 1);
  }
  return numero(valor, 2);
}

// A diferença (realizado − previsto) na unidade do indicador, com sinal: "+12", "−0,50%".
export function variacaoComUnidade(valor: number | null | undefined, unidade: string): string {
  if (valor === null || valor === undefined) {
    return "—";
  }
  const texto = valorComUnidade(Math.abs(valor), unidade);
  if (valor > 0) {
    return `+${texto}`;
  }
  if (valor < 0) {
    return `−${texto}`;
  }
  return texto;
}

// As linhas do placar em blocos pelo grupo (REBANHO, VENDAS ABATE...), na ordem em que a API mandou.
export function blocosDoPlacar(linhas: LinhaDoPlacar[]): { grupo: string; linhas: LinhaDoPlacar[] }[] {
  const blocos: { grupo: string; linhas: LinhaDoPlacar[] }[] = [];
  for (const linha of linhas) {
    const ultimo = blocos[blocos.length - 1];
    if (ultimo !== undefined && ultimo.grupo === linha.grupo) {
      ultimo.linhas.push(linha);
    } else {
      blocos.push({ grupo: linha.grupo, linhas: [linha] });
    }
  }
  return blocos;
}

// "2026-09-23" -> "23/09/2026"
export function dataCurta(data: string): string {
  return `${data.slice(8, 10)}/${data.slice(5, 7)}/${data.slice(0, 4)}`;
}

// As colunas da tabela de lotes do mês, pelo tipo do lote: quem é a outra parte, se tem peso, carcaça e preços.
export type ColunasDoLote = {
  contraparte: string | null; // o título da coluna; nascimento não tem outra parte
  pesos: boolean; // kg vivo e @
  carcaca: boolean; // kg de carcaça e rendimento (só abate)
  precos: boolean; // R$/@, R$/cab, R$/kg e R$ total
  semLancamento: string;
};

const COLUNAS_DA_COMPRA: ColunasDoLote = {
  contraparte: "Fornecedor", pesos: true, carcaca: false, precos: true, semLancamento: "Nenhuma compra no mês.",
};

const COLUNAS_DO_LOTE: Record<string, ColunasDoLote> = {
  abate: {
    contraparte: "Cliente", pesos: true, carcaca: true, precos: true,
    semLancamento: "Nenhuma venda deste tipo no mês.",
  },
  em_pe: {
    contraparte: "Cliente", pesos: true, carcaca: false, precos: true,
    semLancamento: "Nenhuma venda deste tipo no mês.",
  },
  compra: COLUNAS_DA_COMPRA,
  transf_entrada: {
    contraparte: "Origem", pesos: true, carcaca: false, precos: false, semLancamento: "Nenhuma entrada no mês.",
  },
  transf_saida: {
    contraparte: "Destino", pesos: true, carcaca: false, precos: false, semLancamento: "Nenhuma saída no mês.",
  },
  nascimento: {
    contraparte: null, pesos: false, carcaca: false, precos: false, semLancamento: "Nenhum nascimento no mês.",
  },
};

export function colunasDoLote(tipo: string): ColunasDoLote {
  return COLUNAS_DO_LOTE[tipo] ?? COLUNAS_DA_COMPRA;
}
