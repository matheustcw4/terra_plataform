// Meses como texto "AAAA-MM": o mesmo formato do <input type="month"> e dos filtros da API.
// Não uso Date de propósito: "2025-07-01" vira 30/06 às 21h no fuso de Brasília e o mês sai errado.

const NOMES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

export function ehMes(texto: string): boolean {
  return /^\d{4}-(0[1-9]|1[0-2])$/.test(texto);
}

// somarMeses("2025-11", 3) -> "2026-02"; aceita número negativo.
export function somarMeses(mes: string, quantos: number): string {
  const ano = Number(mes.slice(0, 4));
  const numero = Number(mes.slice(5, 7));
  const totalDeMeses = ano * 12 + (numero - 1) + quantos;
  const novoAno = Math.floor(totalDeMeses / 12);
  const novoMes = (totalDeMeses % 12) + 1;
  return `${novoAno}-${String(novoMes).padStart(2, "0")}`;
}

// A API manda datas "AAAA-MM-DD" (1º dia do mês); o filtro usa só "AAAA-MM".
export function mesDaData(data: string): string {
  return data.slice(0, 7);
}

// "2025-07-01" ou "2025-07" -> "jul/25"
export function mesCurto(data: string): string {
  const ano = data.slice(2, 4);
  const numero = Number(data.slice(5, 7));
  return `${NOMES[numero - 1]}/${ano}`;
}

export function mesAtual(): string {
  const hoje = new Date();
  return `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, "0")}`;
}
