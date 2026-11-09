import type { Importacao, SituacaoDaImportacao } from "../core/api/tipos";

// O mesmo padrão de nome que a API confere (backend: REGEX_ARQUIVO em planilha/template.py): o código e a fazenda do
// nome conferem o fUnidade, e o nome é a chave do arquivo na plataforma. Conferir aqui só poupa o envio de um arquivo
// que a API recusaria; quem decide é ela.
const PADRAO_DO_NOME = /^RELAT[ÓO]RIOS?\s*[-_]\s*(\d+)\s*[-_]\s*(.+?)\s*\.xls[xm]$/iu;
export const TAMANHO_MAXIMO = 50 * 1024 * 1024;
export const PADRAO_EXPLICADO = "RELATÓRIO - código do projeto - fazenda.xlsm";

// Por que o arquivo nem vai para a API (ou null, quando pode ir).
export function motivoDaRecusa(nome: string, tamanho: number): string | null {
  if (!PADRAO_DO_NOME.test(nome.normalize("NFC").trim())) {
    return `o nome tem de seguir o padrão ${PADRAO_EXPLICADO}`;
  }
  if (tamanho === 0) {
    return "o arquivo está vazio";
  }
  if (tamanho > TAMANHO_MAXIMO) {
    return "o arquivo passa de 50 MB";
  }
  return null;
}

const ROTULOS: Record<SituacaoDaImportacao, string> = {
  na_fila: "Na fila",
  processando: "Carregando",
  carregada: "Carregada",
  carregada_com_avisos: "Carregada, com avisos",
  inalterada: "Sem mudança",
  ignorada: "Não entrou",
  erro: "Não carregou",
};

export function rotuloDaSituacao(situacao: SituacaoDaImportacao): string {
  return ROTULOS[situacao];
}

// A classe do selo: verde quando entrou, laranja quando é para conferir, vermelho quando não entrou.
export function classeDaSituacao(situacao: SituacaoDaImportacao): string {
  if (situacao === "carregada" || situacao === "inalterada") {
    return "selo selo-ok";
  }
  if (situacao === "carregada_com_avisos" || situacao === "ignorada") {
    return "selo selo-aviso";
  }
  if (situacao === "erro") {
    return "selo selo-erro";
  }
  return "selo selo-andamento";
}

export function estaEmAndamento(importacao: Importacao): boolean {
  return importacao.status === "na_fila" || importacao.status === "processando";
}

// Enquanto alguma espera o worker, a tela pergunta de novo a cada poucos segundos.
export function algumaEmAndamento(lista: Importacao[]): boolean {
  return lista.some(estaEmAndamento);
}

// Alguma que estava na fila (ou carregando) na leitura anterior terminou nesta? Então os números mudaram.
export function terminouAlguma(antes: Importacao[], agora: Importacao[]): boolean {
  const emAndamentoAntes = new Set(antes.filter(estaEmAndamento).map((importacao) => importacao.id));
  return agora.some((importacao) => emAndamentoAntes.has(importacao.id) && !estaEmAndamento(importacao));
}

// "2 avisos · 5 linhas fora dos números" (o detalhe fica na página Pendências); vazio quando não há nada a conferir.
export function resumoDaCarga(importacao: Importacao): string {
  const partes: string[] = [];
  if (importacao.avisos > 0) {
    partes.push(importacao.avisos === 1 ? "1 aviso" : `${importacao.avisos} avisos`);
  }
  if (importacao.quarentena > 0) {
    const linhas = importacao.quarentena === 1 ? "1 linha" : `${importacao.quarentena} linhas`;
    partes.push(`${linhas} fora dos números`);
  }
  return partes.join(" · ");
}

export function tamanhoLegivel(bytes: number): string {
  if (bytes >= 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} MB`;
  }
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}
