// O quadro de um recorte (GERAL, MACHO, FÊMEA, BEZERROS, JOVENS, ADULTOS) na lista que veio da API.
// A API sempre manda todos os recortes da página; sem o recorte, o quadro não aparece (em vez de quebrar a página).
export function doRecorte<T extends { recorte: string }>(quadros: T[], recorte: string): T | undefined {
  return quadros.find((quadro) => quadro.recorte === recorte);
}
