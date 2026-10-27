// Geometria do velocímetro (o "gauge" do BI): um meio círculo de 180°, da esquerda (zero) à direita (fim da escala).
// Só desenho: os valores (realizado, meta, fim da escala) chegam prontos da API.

export type Ponto = { x: number; y: number };

// Onde o valor cai na escala, de 0 a 1. Sem fim de escala (sem meta), um valor positivo enche o arco.
export function fracaoDaEscala(valor: number | null, maximo: number | null): number {
  if (valor === null || valor <= 0) {
    return 0;
  }
  if (maximo === null || maximo <= 0) {
    return 1;
  }
  return Math.min(valor / maximo, 1);
}

// O ponto do arco na fração dada: 0 = ponta esquerda, 1 = ponta direita (o SVG tem o y para baixo).
export function pontoDoArco(fracao: number, centro: Ponto, raio: number): Ponto {
  const angulo = Math.PI * (1 - fracao);
  return { x: centro.x + raio * Math.cos(angulo), y: centro.y - raio * Math.sin(angulo) };
}

// O caminho SVG do arco da ponta esquerda até a fração (nunca passa de meia volta, então o arco é sempre o menor).
export function caminhoDoArco(fracao: number, centro: Ponto, raio: number): string {
  const inicio = pontoDoArco(0, centro, raio);
  const fim = pontoDoArco(fracao, centro, raio);
  return `M ${coordenadas(inicio)} A ${raio} ${raio} 0 0 1 ${coordenadas(fim)}`;
}

// "x y" com duas casas: o seno de 180° não dá zero exato em ponto flutuante (sairia 99.99999999999999).
function coordenadas(ponto: Ponto): string {
  return `${ponto.x.toFixed(2)} ${ponto.y.toFixed(2)}`;
}
