// Números no padrão brasileiro (1.234,5). O front só formata: os valores já chegam calculados da API.

export function numero(valor: number | null, casas = 0): string {
  if (valor === null) {
    return "—";
  }
  return valor.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });
}

// Variação com sinal: "+105", "−12", "0".
export function comSinal(valor: number): string {
  if (valor > 0) {
    return `+${numero(valor)}`;
  }
  if (valor < 0) {
    return `−${numero(-valor)}`;
  }
  return "0";
}

// "R$ 154.200" nos totais, "R$ 314,69" nos preços.
export function dinheiro(valor: number | null, casas = 0): string {
  if (valor === null) {
    return "—";
  }
  return `R$ ${numero(valor, casas)}`;
}

// A API manda fração (0,525); a tela mostra "52,5%".
export function percentual(valor: number | null, casas = 1): string {
  if (valor === null) {
    return "—";
  }
  return `${numero(valor * 100, casas)}%`;
}

// Eixo de gráfico: "3,2 mi", "154,2 mil", "450" (o valor exato aparece ao passar o mouse).
// Recebe só o valor: o Recharts chama o formatador do eixo com (valor, posição), e um segundo parâmetro opcional
// (como as casas de `numero`) receberia a posição.
export function compacto(valor: number): string {
  return valor.toLocaleString("pt-BR", { notation: "compact", maximumFractionDigits: 1 });
}

// Rótulo de barra em reais: "R$ 1,1 mi", "R$ 50 mil" (o valor exato aparece ao passar o mouse).
export function dinheiroCompacto(valor: number): string {
  return `R$ ${compacto(valor)}`;
}

// Momento vindo da API (com fuso) -> "15/10/2026 10:33", no fuso do navegador.
export function dataEHora(momento: string | null): string {
  if (momento === null) {
    return "—";
  }
  return new Date(momento).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

// Rótulo em cima da coluna do gráfico: compacto, e nada quando a coluna é zero (o BI também não escreve).
export function rotuloDeColuna(valor: number): string {
  if (valor === 0) {
    return "";
  }
  return compacto(valor);
}
