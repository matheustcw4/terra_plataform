import type { FazendaDoEscopo } from "../core/api/tipos";
import {
  fazendasDaOrigem,
  fazendasDoCliente,
  nomeDaSelecao,
  nomesDasFazendas,
  rotuloDoAno,
  type Filtro,
} from "./filtro";
import { mesCurto } from "./meses";

// O que a capa do PDF mostra (a capa do boletim de resultados, nos três modos) e o nome do arquivo. A cidade é
// digitada na hora da exportação e não é gravada em lugar nenhum.

const MESES_POR_EXTENSO = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro",
  "outubro", "novembro", "dezembro"];

// "2026-10" -> "outubro de 2026"
export function mesPorExtenso(mes: string): string {
  const numero = Number(mes.slice(5, 7));
  return `${MESES_POR_EXTENSO[numero - 1]} de ${mes.slice(0, 4)}`;
}

// Na visão safra, "SAFRA" e "24/25"; na civil, "ANO" e "2025".
export function periodoDaCapa(filtro: Filtro): { titulo: string; valor: string } {
  if (filtro.visao === "civil") {
    return { titulo: "ANO", valor: String(filtro.ano) };
  }
  return { titulo: "SAFRA", valor: `${String(filtro.ano).slice(2)}/${String(filtro.ano + 1).slice(2)}` };
}

// As fazendas marcadas; com "GRUPO" (todas as do cliente), os nomes de todas. Sempre separados por " | ".
export function nomesDaCapa(filtro: Filtro, fazendas: FazendaDoEscopo[]): string {
  const doCliente = fazendasDoCliente(fazendasDaOrigem(fazendas, filtro.origem), filtro.cliente);
  if (filtro.fazendas.length > 0) {
    return nomesDasFazendas(filtro.fazendas, doCliente).join(" | ");
  }
  return doCliente.map((fazenda) => fazenda.nome).join(" | ");
}

// As páginas marcadas, na ordem do boletim (a mesma das abas), com a capa primeiro.
export function paginasNaOrdem(marcadas: string[], ordem: string[]): string[] {
  return ordem.filter((pagina) => marcadas.includes(pagina));
}

// "Boletim - GRUPO - Safra 25-26.pdf"
export function nomeDoArquivo(filtro: Filtro, fazendas: FazendaDoEscopo[]): string {
  const periodo = rotuloDoAno(filtro.ano, filtro.visao).replace("/", "-");
  const selecao = semCaracterProibido(nomeDaSelecao(filtro, fazendas));
  return `Boletim - ${selecao} - ${periodo}.pdf`;
}

// "Boletim resumido - GRUPO - set-26.pdf": nos modos Boletim Resumido e Personalizado o que importa é o mês de referência.
export function nomeDoArquivoDoMes(tipo: string, filtro: Filtro, fazendas: FazendaDoEscopo[], mes: string): string {
  const selecao = semCaracterProibido(nomeDaSelecao(filtro, fazendas));
  return `${tipo} - ${selecao} - ${mesCurto(mes).replace("/", "-")}.pdf`;
}

// O Windows não aceita \ / : * ? " < > | no nome do arquivo.
function semCaracterProibido(nome: string): string {
  return nome.replace(/[\\/:*?"<>|]/g, "-");
}
