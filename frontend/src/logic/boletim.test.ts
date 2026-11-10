import { describe, expect, it } from "vitest";
import type { FazendaDoEscopo, LinhaDoPlacar, SecaoDeLotes } from "../core/api/tipos";
import type { Filtro } from "./filtro";
import {
  alturaDaColuna,
  ateAReferencia,
  ehParteDoDesembolso,
  grupoDaLetra,
  identificacaoDoBoletim,
  nomeDaClassificacao,
  cabecasOuTraco,
  celulaEmMilhoes,
  diferencaEmReais,
  emMilhoes,
  folhasDoBoletim,
  maiorValor,
  mesDoEixo,
  periodoDosDados,
  quantidadeDeMeses,
  reaisCurtos,
  rotuloDaPagina,
  temMovimento,
  variacaoComSinal,
  variacaoDaLinha,
} from "./boletim";

function secao(meses: { realizado: number | null; previsto: number }[]): SecaoDeLotes {
  return {
    tipo: "abate", titulo: "Vendas abate", lancamentos: [], resumo: [], leitura: [],
    meses: meses.map((mes, posicao) => ({
      mes: `2026-0${posicao + 1}-01`, realizado: mes.realizado, previsto: mes.previsto, realizado_acumulado: null,
      previsto_acumulado: 0, valor: null, valor_previsto: 0,
    })),
  };
}

function linhaDoLote(unidade: string, variacao: number | null, percentualDaVariacao: number | null): LinhaDoPlacar {
  return {
    grupo: "VENDAS", indicador: "x", unidade, meta_periodo: null,
    mes: { previsto: null, realizado: null, variacao: null, variacao_percentual: null, status: null },
    acumulado: { previsto: 1, realizado: 1, variacao, variacao_percentual: percentualDaVariacao, status: null },
  };
}

describe("boletim de resultados", () => {
  it("escreve o período e conta os meses, inclusive na virada do ano", () => {
    expect(periodoDosDados("2026-01-01", "2026-10-01")).toBe("Jan/26 a Out/26");
    expect(quantidadeDeMeses("2026-01-01", "2026-10-01")).toBe(10);
    expect(quantidadeDeMeses("2025-07-01", "2026-06-01")).toBe(12);
    expect(mesDoEixo("2026-03-01")).toBe("mar");
  });

  it("escreve reais curtos, com sinal e na escala certa", () => {
    expect(reaisCurtos(-6_462_495)).toBe("−R$ 6,46 mi");
    expect(reaisCurtos(540_700)).toBe("R$ 540,7 mil");
    expect(reaisCurtos(450)).toBe("R$ 450");
    expect(reaisCurtos(null)).toBe("—");
    expect(diferencaEmReais(1_591_183)).toBe("+R$ 1,59 mi");
    expect(diferencaEmReais(-540_692)).toBe("−R$ 540,7 mil");
  });

  it("escreve milhões nas colunas e nas tabelas, sem o zero", () => {
    expect(emMilhoes(1_095_599)).toBe("1,1");
    expect(emMilhoes(492_335)).toBe("0,49");
    expect(emMilhoes(0)).toBe("");
    expect(celulaEmMilhoes(0)).toBe("—");
    expect(celulaEmMilhoes(2_462_403)).toBe("2,5");
    expect(cabecasOuTraco(1723)).toBe("1.723");
    expect(cabecasOuTraco(0)).toBe("—");
  });

  it("escreve a variação com sinal", () => {
    expect(variacaoComSinal(0.072)).toBe("+7,2%");
    expect(variacaoComSinal(-0.038)).toBe("−3,8%");
    expect(variacaoComSinal(0)).toBe("0,0%");
    expect(variacaoComSinal(null)).toBe("—");
  });

  it("escreve a variação de cada indicador do lote na unidade que se lê melhor", () => {
    expect(variacaoDaLinha(linhaDoLote("cab", -68, -0.038))).toBe("−68 cab");
    expect(variacaoDaLinha(linhaDoLote("kg", -18.83, -0.033))).toBe("−18,8 kg");
    expect(variacaoDaLinha(linhaDoLote("%", 0.0262, 0.047))).toBe("+2,6 p.p.");
    expect(variacaoDaLinha(linhaDoLote("R$/@", 14.3, 0.0419))).toBe("+4,2%");
    expect(variacaoDaLinha(linhaDoLote("R$", 199_275, 0.0155))).toBe("+R$ 199,3 mil");
    expect(variacaoDaLinha(linhaDoLote("cab", null, null))).toBe("—");
  });

  it("vê movimento no realizado ou na meta", () => {
    expect(temMovimento(secao([{ realizado: 0, previsto: 0 }, { realizado: null, previsto: 0 }]))).toBe(false);
    expect(temMovimento(secao([{ realizado: 0, previsto: 0 }, { realizado: null, previsto: 12 }]))).toBe(true);
    expect(temMovimento(secao([{ realizado: 5, previsto: 0 }]))).toBe(true);
  });

  it("numera as folhas e põe dois blocos de comercialização por folha", () => {
    const todas = ["resumo", "financeiro", "rebanho", "comercializacao"];
    expect(folhasDoBoletim(todas, ["abate", "compras"])).toEqual([
      { chave: "resumo", numero: 1, blocos: [] },
      { chave: "financeiro", numero: 2, blocos: [] },
      { chave: "rebanho", numero: 3, blocos: [] },
      { chave: "comercializacao", numero: 4, blocos: ["abate", "compras"] },
    ]);
    expect(folhasDoBoletim(["comercializacao", "resumo"], ["abate", "em_pe", "compras"])).toEqual([
      { chave: "resumo", numero: 1, blocos: [] },
      { chave: "comercializacao", numero: 2, blocos: ["abate", "em_pe"] },
      { chave: "comercializacao", numero: 3, blocos: ["compras"] },
    ]);
    expect(folhasDoBoletim(["comercializacao"], [])).toEqual([{ chave: "comercializacao", numero: 1, blocos: [] }]);
    expect(rotuloDaPagina(2, 4)).toBe("Página 02/04");
  });

  it("identifica a fazenda (ou o grupo), o período e a cidade", () => {
    const fazendas: FazendaDoEscopo[] = [
      { id: "c1", nome: "FAZENDA CMI", cliente: "RENE", origem: "planilha", sistema_produtivo: null,
        primeiro_mes: "2025-01-01", ultimo_mes: "2026-10-01",
        capacidades: { estoque: true, rebanho_medio: true, area: true, financeiro: true, planejado: true } },
      { id: "c2", nome: "FAZENDA PALMARES", cliente: "RENE", origem: "planilha", sistema_produtivo: null,
        primeiro_mes: "2025-01-01", ultimo_mes: "2026-10-01",
        capacidades: { estoque: true, rebanho_medio: true, area: true, financeiro: true, planejado: true } },
    ];
    const filtro: Filtro = { origem: "planilha", cliente: "RENE", fazendas: ["c1"], visao: "civil", ano: 2026,
      meses: [] };
    const datas = { inicio_do_periodo: "2026-01-01", mes_referencia: "2026-10-01",
      plano: { versoes: [], versao: null, em_uso: [] } };
    const uma = identificacaoDoBoletim(filtro, fazendas, datas, " Cuiabá ", "2026-11");
    expect(uma).toMatchObject({ titulo: "FAZENDA CMI", variasFazendas: false, periodo: "Jan/26 a Out/26", meses: 10,
      rotuloDoPeriodo: "ANO 2026", sistema: "Integração Planilhas", planejamento: "Sem planejamento",
      localEData: "Cuiabá, novembro de 2026" });
    const grupo = identificacaoDoBoletim({ ...filtro, fazendas: [] }, fazendas, datas, "", "2026-11");
    expect(grupo).toMatchObject({ titulo: "GRUPO", fazendas: "FAZENDA CMI | FAZENDA PALMARES", variasFazendas: true,
      localEData: "Novembro de 2026" });
  });

  it("escreve as classificações do caixa e acha os grupos pela letra", () => {
    expect(nomeDaClassificacao("A - RECEITAS")).toBe("Receitas");
    expect(nomeDaClassificacao("F - OUTROS DÉBITOS")).toBe("Outros débitos");
    expect(nomeDaClassificacao("A CLASSIFICAR")).toBe("A classificar");
    expect(ehParteDoDesembolso("C - INVESTIMENTOS")).toBe(true);
    expect(ehParteDoDesembolso("B - DESEMBOLSO")).toBe(false);
    const grupos = [{ classificacao: "A - RECEITAS" }, { classificacao: "A CLASSIFICAR" }, { classificacao: "B - X" }];
    expect(grupoDaLetra(grupos, "B")).toEqual({ classificacao: "B - X" });
    expect(grupoDaLetra(grupos, "A")).toEqual({ classificacao: "A - RECEITAS" });
    expect(grupoDaLetra(grupos, "Z")).toBeNull();
    const meses = [{ mes: "2026-09-01" }, { mes: "2026-10-01" }, { mes: "2026-11-01" }];
    expect(ateAReferencia(meses, "2026-10-01")).toEqual([{ mes: "2026-09-01" }, { mes: "2026-10-01" }]);
  });

  it("dá a altura das colunas pela maior de todas as séries", () => {
    expect(maiorValor([[1, null, 4], [3, 2]])).toBe(4);
    expect(alturaDaColuna(2, 4)).toBe(50);
    expect(alturaDaColuna(null, 4)).toBe(0);
    expect(alturaDaColuna(3, 0)).toBe(0);
  });
});
