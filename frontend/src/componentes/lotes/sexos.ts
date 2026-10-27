import femea from "../../assets/bi/femea.png";
import macho from "../../assets/bi/macho.png";
import soma from "../../assets/bi/soma.png";
import type { QuadroDoLote } from "../../core/api/tipos";

// Os três quadros das páginas de lote, na ordem do BI (da esquerda para a direita).
export const SEXOS = [
  { recorte: "FÊMEA", titulo: "FÊMEA", icone: femea },
  { recorte: "MACHO", titulo: "MACHO", icone: macho },
  { recorte: "GERAL", titulo: "GERAL", icone: soma },
];

// A API sempre manda os três recortes; se um faltar, o quadro mostra zero em vez de quebrar a página.
export function quadroDo(quadros: QuadroDoLote[], recorte: string): QuadroDoLote {
  const encontrado = quadros.find((quadro) => quadro.recorte === recorte);
  if (encontrado !== undefined) {
    return encontrado;
  }
  const vazio = { cabecas: 0, valor: 0, kg_vivo: 0, arrobas: 0, preco_arroba: null, preco_kg: null,
    peso_medio_kg: null, rendimento_carcaca: null };
  return { recorte, realizado: vazio, planejado: vazio };
}
