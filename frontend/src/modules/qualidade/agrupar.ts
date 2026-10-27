import type { Pendencia } from "../../core/api/tipos";

export type FiltroDePendencia = "todas" | "nao_entrou" | "confira" | "equipe";

export const FILTROS_DE_PENDENCIA: { valor: FiltroDePendencia; rotulo: string }[] = [
  { valor: "todas", rotulo: "Todas" },
  { valor: "nao_entrou", rotulo: "Não entraram" },
  { valor: "confira", rotulo: "Para conferir" },
  { valor: "equipe", rotulo: "Com a equipe Terra" },
];

export function filtrarPendencias(itens: Pendencia[], filtro: FiltroDePendencia): Pendencia[] {
  if (filtro === "equipe") {
    return itens.filter((item) => item.quem_corrige === "equipe");
  }
  if (filtro === "todas") {
    return itens;
  }
  return itens.filter((item) => item.situacao === filtro);
}

// Um grupo por arquivo (ou fonte) de cada fazenda: é o que a pessoa abre para corrigir.
export type GrupoDePendencias = {
  chave: string;
  fazenda: string;
  origem: string;
  salvoEm: string | null;
  itens: Pendencia[];
};

// A API já manda a lista ordenada por fazenda e arquivo; aqui só junto os vizinhos do mesmo arquivo.
export function agruparPorOrigem(itens: Pendencia[]): GrupoDePendencias[] {
  const grupos: GrupoDePendencias[] = [];
  for (const item of itens) {
    const chave = `${item.fazenda_id}|${item.origem}`;
    const ultimo = grupos[grupos.length - 1];
    if (ultimo !== undefined && ultimo.chave === chave) {
      ultimo.itens.push(item);
    } else {
      grupos.push({ chave, fazenda: item.fazenda, origem: item.origem, salvoEm: item.salvo_em, itens: [item] });
    }
  }
  return grupos;
}
