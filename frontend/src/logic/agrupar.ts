// Agrupamentos e buscas das listas de admin (fazendas por cliente, centros de custo por classificação).

export type Grupo<T> = { chave: string; itens: T[] };

// Junta os itens com a mesma chave, na ordem em que a chave aparece pela primeira vez (a API já manda ordenado).
export function agruparPor<T>(itens: T[], chaveDe: (item: T) => string): Grupo<T>[] {
  const grupos: Grupo<T>[] = [];
  const porChave = new Map<string, Grupo<T>>();
  for (const item of itens) {
    const chave = chaveDe(item);
    let grupo = porChave.get(chave);
    if (grupo === undefined) {
      grupo = { chave, itens: [] };
      porChave.set(chave, grupo);
      grupos.push(grupo);
    }
    grupo.itens.push(item);
  }
  return grupos;
}

// Marca ou desmarca vários ids de uma vez (ex.: todas as fazendas de um cliente), sem repetir nenhum.
export function marcarVarios(marcados: string[], ids: string[], marcar: boolean): string[] {
  if (marcar) {
    return [...new Set([...marcados, ...ids])];
  }
  return marcados.filter((id) => !ids.includes(id));
}

// "Água Boa" acha "agua"; a busca ignora acento e maiúsculas.
export function contemTexto(texto: string, busca: string): boolean {
  return semAcento(texto).includes(semAcento(busca.trim()));
}

function semAcento(texto: string): string {
  return texto.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
}
