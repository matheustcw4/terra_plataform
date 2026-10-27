import type { FazendaDoEscopo } from "../core/api/tipos";
import { mesAtual, mesCurto, mesDaData, somarMeses } from "./meses";

// O filtro do MENU, como no BI: origem (temporário), cliente, fazendas (seleção múltipla; nenhuma = todas, o "GRUPO"),
// forma de visualização (safra ou civil), a safra ou o ano, e os meses (seleção múltipla, como o filtro de mês do BI;
// nenhum = todos). Fica na URL (dá para mandar o link) e o navegador lembra o último usado.
export type Visao = "safra" | "civil";

// TEMPORÁRIO (pedido do usuário, 15/10/2026): escolher de onde vêm os dados enquanto o mesmo cliente nas duas fontes
// não tem de-para (Q9). Só escolhe quais clientes e fazendas aparecem; nenhum número muda por causa dela.
export type Origem = "planilha" | "metryx";

export const ORIGENS: { valor: Origem; rotulo: string }[] = [
  { valor: "planilha", rotulo: "Integração Planilhas" },
  { valor: "metryx", rotulo: "Metryx" },
];

export type Filtro = {
  origem: Origem;
  cliente: string; // proprietário (planilha) ou customer (Metryx)
  fazendas: string[]; // ids das fazendas marcadas, na ordem do cliente; vazio = todas as do cliente ("GRUPO")
  visao: Visao;
  ano: number; // safra: o ano em que ela começa (Safra 25/26 = 2025); civil: o próprio ano
  meses: string[]; // "AAAA-MM", em ordem; vazio = todos os meses do período
};

// O que as páginas mandam para a API. Com meses salteados, a API soma só os marcados e o estoque final é o do último.
export type Consulta = {
  fazendas: string[];
  inicio: string; // "AAAA-MM"
  fim: string; // "AAAA-MM"
  meses: string[]; // os meses marcados; vazio = todos de inicio a fim
};

// Fazenda sem origem conhecida aparece nas duas.
export function fazendasDaOrigem(fazendas: FazendaDoEscopo[], origem: Origem): FazendaDoEscopo[] {
  return fazendas.filter((fazenda) => fazenda.origem === origem || fazenda.origem === null);
}

// A API manda as fazendas ordenadas por cliente; aqui só tiro os nomes repetidos.
export function clientesDoEscopo(fazendas: FazendaDoEscopo[]): string[] {
  const clientes: string[] = [];
  for (const fazenda of fazendas) {
    if (!clientes.includes(fazenda.cliente)) {
      clientes.push(fazenda.cliente);
    }
  }
  return clientes;
}

export function fazendasDoCliente(fazendas: FazendaDoEscopo[], cliente: string): FazendaDoEscopo[] {
  return fazendas.filter((fazenda) => fazenda.cliente === cliente);
}

// A safra vai de julho a junho: jan/2026 é da Safra 25/26.
export function anoDoMes(mes: string, visao: Visao): number {
  const ano = Number(mes.slice(0, 4));
  const numero = Number(mes.slice(5, 7));
  if (visao === "safra" && numero < 7) {
    return ano - 1;
  }
  return ano;
}

export function rotuloDoAno(ano: number, visao: Visao): string {
  if (visao === "civil") {
    return String(ano);
  }
  return `Safra ${String(ano).slice(2)}/${String(ano + 1).slice(2)}`;
}

export function rotuloDaOrigem(origem: Origem): string {
  return origem === "metryx" ? "Metryx" : "Integração Planilhas";
}

// Meses da safra (jul→jun) ou do ano (jan→dez), só até o mês atual: como o calendário do BI, que termina hoje.
export function mesesDoPeriodo(visao: Visao, ano: number, hoje: string = mesAtual()): string[] {
  const primeiro = visao === "safra" ? `${ano}-07` : `${ano}-01`;
  const meses: string[] = [];
  for (let posicao = 0; posicao < 12; posicao++) {
    const mes = somarMeses(primeiro, posicao);
    if (mes > hoje) {
      break;
    }
    meses.push(mes);
  }
  return meses;
}

// Safras (ou anos) que têm dado: do primeiro mês com dado das fazendas até hoje, a mais recente primeiro.
export function anosDisponiveis(fazendas: FazendaDoEscopo[], visao: Visao, hoje: string = mesAtual()): number[] {
  const primeiroMes = primeiroMesComDado(fazendas) ?? hoje;
  const anos: number[] = [];
  for (let ano = anoDoMes(hoje, visao); ano >= anoDoMes(primeiroMes, visao); ano--) {
    anos.push(ano);
  }
  return anos;
}

// Ao escolher um cliente: todas as fazendas dele, por safra, na safra do último mês com dado, todos os meses.
export function filtroDoCliente(fazendas: FazendaDoEscopo[], origem: Origem, cliente: string,
  hoje: string = mesAtual()): Filtro {
  const doCliente = fazendasDoCliente(fazendasDaOrigem(fazendas, origem), cliente);
  const ultimo = ultimoMesComDado(doCliente) ?? hoje;
  return { origem, cliente, fazendas: [], visao: "safra", ano: anoDoMes(ultimo, "safra"), meses: [] };
}

// Seleção múltipla do MENU (meses e fazendas): os marcados que existem entre as opções, na ordem delas e sem repetir.
// Vazio quer dizer "todos"; por isso marcar todos é o mesmo que vazio.
export function itensEscolhidos(marcados: string[], opcoes: string[]): string[] {
  const escolhidos = opcoes.filter((opcao) => marcados.includes(opcao));
  if (escolhidos.length === opcoes.length) {
    return [];
  }
  return escolhidos;
}

// Marca ou desmarca um item. Com "todos", marcar um item deixa só ele; desmarcar o último volta a "todos".
export function alternarItem(marcados: string[], item: string, opcoes: string[]): string[] {
  let novos = [...marcados, item];
  if (marcados.includes(item)) {
    novos = marcados.filter((outro) => outro !== item);
  }
  return itensEscolhidos(novos, opcoes);
}

export function mesesEscolhidos(marcados: string[], doPeriodo: string[]): string[] {
  return itensEscolhidos(marcados, doPeriodo);
}

export function fazendasEscolhidas(marcadas: string[], doCliente: FazendaDoEscopo[]): string[] {
  return itensEscolhidos(marcadas, doCliente.map((fazenda) => fazenda.id));
}

// Ao escolher uma origem: o primeiro cliente dela. Origem sem nenhuma fazenda visível: null.
export function filtroDaOrigem(fazendas: FazendaDoEscopo[], origem: Origem, hoje: string = mesAtual()): Filtro | null {
  const primeiro = clientesDoEscopo(fazendasDaOrigem(fazendas, origem))[0];
  if (primeiro === undefined) {
    return null;
  }
  return filtroDoCliente(fazendas, origem, primeiro, hoje);
}

// Lê o filtro da URL. O que não servir para este usuário (origem ou cliente que ele não vê, fazenda de outro cliente,
// ano sem dado, mês fora do período) volta ao padrão. Sem fazenda visível: null. Fazenda e mês podem se repetir.
export function filtroDaUrl(parametros: URLSearchParams, fazendas: FazendaDoEscopo[],
  hoje: string = mesAtual()): Filtro | null {
  const origem = origemDaUrl(parametros, fazendas);
  if (origem === null) {
    return null;
  }
  const daOrigem = fazendasDaOrigem(fazendas, origem);
  const clienteDaUrl = parametros.get("cliente") ?? "";
  if (!clientesDoEscopo(daOrigem).includes(clienteDaUrl)) {
    return filtroDaOrigem(fazendas, origem, hoje);
  }
  const doCliente = fazendasDoCliente(daOrigem, clienteDaUrl);
  const marcadas = fazendasEscolhidas(parametros.getAll("fazenda"), doCliente);
  const visao: Visao = parametros.get("visao") === "civil" ? "civil" : "safra";
  const anoDaUrl = Number(parametros.get("ano"));
  const anoPadrao = anoDoMes(ultimoMesComDado(doCliente) ?? hoje, visao);
  const ano = anosDisponiveis(doCliente, visao, hoje).includes(anoDaUrl) ? anoDaUrl : anoPadrao;
  const meses = mesesEscolhidos(parametros.getAll("mes"), mesesDoPeriodo(visao, ano, hoje));
  return { origem, cliente: clienteDaUrl, fazendas: marcadas, visao, ano, meses };
}

// A origem da URL, se o usuário tiver fazenda nela; senão a primeira origem que tiver.
function origemDaUrl(parametros: URLSearchParams, fazendas: FazendaDoEscopo[]): Origem | null {
  const comFazenda = ORIGENS.filter((opcao) => fazendasDaOrigem(fazendas, opcao.valor).length > 0);
  const daUrl = comFazenda.find((opcao) => opcao.valor === parametros.get("origem"));
  return (daUrl ?? comFazenda[0])?.valor ?? null;
}

export function filtroParaUrl(filtro: Filtro): URLSearchParams {
  const parametros = new URLSearchParams({
    origem: filtro.origem,
    cliente: filtro.cliente,
    visao: filtro.visao,
    ano: String(filtro.ano),
  });
  for (const fazenda of filtro.fazendas) {
    parametros.append("fazenda", fazenda);
  }
  for (const mes of filtro.meses) {
    parametros.append("mes", mes);
  }
  return parametros;
}

// Fazendas e meses que o filtro escolhe, no formato da API.
export function consultaDoFiltro(filtro: Filtro, fazendas: FazendaDoEscopo[], hoje: string = mesAtual()): Consulta {
  const doCliente = fazendasDoCliente(fazendasDaOrigem(fazendas, filtro.origem), filtro.cliente);
  let ids = doCliente.map((fazenda) => fazenda.id);
  if (filtro.fazendas.length > 0) {
    ids = filtro.fazendas;
  }
  const primeiroDoPeriodo = filtro.visao === "safra" ? `${filtro.ano}-07` : `${filtro.ano}-01`;
  let meses = filtro.meses;
  if (meses.length === 0) {
    meses = mesesDoPeriodo(filtro.visao, filtro.ano, hoje);
  }
  return {
    fazendas: ids,
    inicio: meses[0] ?? primeiroDoPeriodo,
    fim: meses[meses.length - 1] ?? primeiroDoPeriodo,
    meses: filtro.meses,
  };
}

// ?fazendas=..&fazendas=..&inicio=AAAA-MM&fim=AAAA-MM[&meses=AAAA-MM..]
export function parametrosDaConsulta(consulta: Consulta): URLSearchParams {
  const parametros = new URLSearchParams({ inicio: consulta.inicio, fim: consulta.fim });
  for (const fazenda of consulta.fazendas) {
    parametros.append("fazendas", fazenda);
  }
  for (const mes of consulta.meses) {
    parametros.append("meses", mes);
  }
  return parametros;
}

// O nome no topo das páginas, como o "Selected Farm" do BI: "GRUPO" (todas as do cliente), as fazendas marcadas
// separadas por " | " ou, com mais de 3, a quantidade (o topo tem pouco espaço; a capa mostra todos os nomes).
export function nomeDaSelecao(filtro: Filtro, fazendas: FazendaDoEscopo[]): string {
  if (filtro.fazendas.length === 0) {
    return "GRUPO";
  }
  if (filtro.fazendas.length > 3) {
    return `${filtro.fazendas.length} fazendas`;
  }
  return nomesDasFazendas(filtro.fazendas, fazendas).join(" | ");
}

// Os nomes das fazendas, na ordem dos ids.
export function nomesDasFazendas(ids: string[], fazendas: FazendaDoEscopo[]): string[] {
  const nomes: string[] = [];
  for (const id of ids) {
    const fazenda = fazendas.find((candidata) => candidata.id === id);
    if (fazenda !== undefined) {
      nomes.push(fazenda.nome);
    }
  }
  return nomes;
}

// "Safra 25/26 · todos os meses", "2025 · ago/25" ou "Safra 25/26 · jul/25, set/25"
export function rotuloDoFiltro(filtro: Filtro): string {
  return `${rotuloDoAno(filtro.ano, filtro.visao)} · ${rotuloDosMeses(filtro.meses)}`;
}

// Até 3 meses, os nomes; mais que isso, a quantidade (o topo das páginas tem pouco espaço).
export function rotuloDosMeses(meses: string[]): string {
  if (meses.length === 0) {
    return "todos os meses";
  }
  if (meses.length <= 3) {
    return meses.map(mesCurto).join(", ");
  }
  return `${meses.length} meses`;
}

function primeiroMesComDado(fazendas: FazendaDoEscopo[]): string | null {
  let primeiro: string | null = null;
  for (const fazenda of fazendas) {
    if (fazenda.primeiro_mes !== null && (primeiro === null || mesDaData(fazenda.primeiro_mes) < primeiro)) {
      primeiro = mesDaData(fazenda.primeiro_mes);
    }
  }
  return primeiro;
}

function ultimoMesComDado(fazendas: FazendaDoEscopo[]): string | null {
  let ultimo: string | null = null;
  for (const fazenda of fazendas) {
    if (fazenda.ultimo_mes !== null && (ultimo === null || mesDaData(fazenda.ultimo_mes) > ultimo)) {
      ultimo = mesDaData(fazenda.ultimo_mes);
    }
  }
  return ultimo;
}
