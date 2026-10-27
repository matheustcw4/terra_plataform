import { expect, test } from "vitest";
import type { Pendencia } from "../../core/api/tipos";
import { agruparPorOrigem, filtrarPendencias } from "./agrupar";

function pendencia(origem: string, situacao: string, quemCorrige: string, local: string): Pendencia {
  return {
    fazenda_id: "f1", fazenda: "TESTE", situacao, codigo: "X", problema: "", detalhe: "", como_corrigir: "",
    quem_corrige: quemCorrige, origem, local, valores: [], salvo_em: null, carregado_em: null,
  };
}

const ITENS = [
  pendencia("RELATÓRIO A.xlsm", "nao_entrou", "origem", "aba fVendaemPe, linha 3"),
  pendencia("RELATÓRIO A.xlsm", "confira", "equipe", "—"),
  pendencia("RELATÓRIO B.xlsm", "confira", "origem", "aba fAbate, linha 9"),
];

test("um grupo por arquivo, na ordem que a API mandou", () => {
  const grupos = agruparPorOrigem(ITENS);
  expect(grupos.map((grupo) => [grupo.origem, grupo.itens.length])).toEqual([
    ["RELATÓRIO A.xlsm", 2],
    ["RELATÓRIO B.xlsm", 1],
  ]);
});

test("filtros: não entraram, para conferir e com a equipe", () => {
  expect(filtrarPendencias(ITENS, "todas")).toHaveLength(3);
  expect(filtrarPendencias(ITENS, "nao_entrou").map((item) => item.local)).toEqual(["aba fVendaemPe, linha 3"]);
  expect(filtrarPendencias(ITENS, "confira")).toHaveLength(2);
  expect(filtrarPendencias(ITENS, "equipe").map((item) => item.origem)).toEqual(["RELATÓRIO A.xlsm"]);
});
