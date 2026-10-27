// Abre ou fecha um item numa lista de abertos (ex.: as classificações abertas da matriz do Previsto × Realizado).
export function alternarItem<Item extends string>(abertos: Item[], item: Item): Item[] {
  if (abertos.includes(item)) {
    return abertos.filter((aberto) => aberto !== item);
  }
  return [...abertos, item];
}
