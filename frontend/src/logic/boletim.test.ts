import { describe, expect, it } from "vitest";
import type { FazendaDoEscopo, QuadroDoLote, SecaoDeLotes } from "../core/api/tipos";
import type { Filtro } from "./filtro";
import {
  alturaDaColuna,
  ateAReferencia,
  cabeONumeroDoPlanejado,
  nomeLegivel,
  cabecasOuTraco,
  diferencaCompacta,
  diferencaDoResultado,
  ehParteDoDesembolso,
  folhasDoBoletim,
  grupoDaLetra,
  identificacaoDoBoletim,
  maiorValor,
  mesComAno,
  mesDaTabela,
  mesDoEixo,
  naUnidade,
  nomeDaClassificacao,
  percentualDaMeta,
  periodoDosDados,
  quantidadeDeMeses,
  reaisCurtos,
  rotuloDaPagina,
  semMoeda,
  temMovimento,
  unidadeDosValores,
  variacaoComSinal,
  vendeuOsDoisSexos,
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

function indicadores(cabecas: number) {
  return { cabecas, valor: 0, kg_vivo: 0, arrobas: 0, preco_arroba: null, preco_kg: null, peso_medio_kg: null,
    rendimento_carcaca: null };
}

function quadro(recorte: string, realizado: number, planejado: number): QuadroDoLote {
  return { recorte, realizado: indicadores(realizado), planejado: indicadores(planejado) };
}

describe("boletim de resultados", () => {
  it("escreve o período e conta os meses, inclusive na virada do ano", () => {
    expect(periodoDosDados("2026-01-01", "2026-10-01")).toBe("Jan/26 a Out/26");
    expect(quantidadeDeMeses("2026-01-01", "2026-10-01")).toBe(10);
    expect(quantidadeDeMeses("2025-07-01", "2026-06-01")).toBe(12);
    expect(mesDoEixo("2026-03-01")).toBe("mar");
    expect(mesDaTabela("2026-03-01")).toBe("Mar");
    expect(mesComAno("2026-09-01")).toBe("Set/26");
  });

  it("escreve reais curtos, a diferença do resultado e o valor sem moeda", () => {
    expect(reaisCurtos(-6_462_495)).toBe("−R$ 6,46 mi");
    expect(reaisCurtos(540_700)).toBe("R$ 540,7 mil");
    expect(reaisCurtos(450)).toBe("R$ 450");
    expect(reaisCurtos(null)).toBe("—");
    expect(semMoeda(936_255)).toBe("936,3 mil");
    expect(diferencaCompacta(1_591_183)).toBe("+1,59 mi");
    expect(diferencaCompacta(-540_692)).toBe("−540,7 mil");
    expect(diferencaDoResultado(1_591_183)).toBe("R$ 1,59 mi melhor");
    expect(diferencaDoResultado(-540_692)).toBe("R$ 540,7 mil abaixo");
  });

  it("escolhe a unidade do gráfico pelo maior valor", () => {
    const milhoes = unidadeDosValores([[1_095_599, null], [4_437_109]]);
    expect(milhoes).toEqual({ divisor: 1_000_000, rotulo: "R$ mi", casas: 1 });
    expect(naUnidade(1_095_599, milhoes)).toBe("1,1");
    expect(unidadeDosValores([[874_500]]).rotulo).toBe("R$ mil");
    expect(unidadeDosValores([[0, null]]).rotulo).toBe("R$");
    expect(naUnidade(null, milhoes)).toBe("—");
  });

  it("escreve a variação, o % da meta e as cabeças", () => {
    expect(variacaoComSinal(0.072)).toBe("+7,2%");
    expect(variacaoComSinal(-0.038)).toBe("−3,8%");
    expect(variacaoComSinal(0)).toBe("0,0%");
    expect(variacaoComSinal(null)).toBe("—");
    expect(percentualDaMeta(0.962)).toBe("96,2%");
    expect(percentualDaMeta(null)).toBe("—");
    expect(cabecasOuTraco(1723)).toBe("1.723");
    expect(cabecasOuTraco(0)).toBe("—");
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

  it("deixa legível o nome em maiúsculas e tira o número do planejado quando não cabe", () => {
    expect(nomeLegivel("TRISTEZA PARASITÁRIA")).toBe("Tristeza parasitária");
    expect(nomeLegivel("MACHOS 8-12")).toBe("Machos 8-12");
    expect(nomeLegivel("Rebanho Investimento")).toBe("Rebanho Investimento");
    expect(cabeONumeroDoPlanejado(3)).toBe(true);
    expect(cabeONumeroDoPlanejado(10)).toBe(false);
  });

  it("vê movimento no realizado ou na meta", () => {
    expect(temMovimento(secao([{ realizado: 0, previsto: 0 }, { realizado: null, previsto: 0 }]))).toBe(false);
    expect(temMovimento(secao([{ realizado: 0, previsto: 0 }, { realizado: null, previsto: 12 }]))).toBe(true);
    expect(temMovimento(secao([{ realizado: 5, previsto: 0 }]))).toBe(true);
  });

  it("separa por sexo só quando os dois sexos venderam ou tinham meta", () => {
    const soMachos = [quadro("GERAL", 1723, 1791), quadro("MACHO", 1723, 1791), quadro("FÊMEA", 0, 0)];
    expect(vendeuOsDoisSexos(soMachos)).toBe(false);
    const osDois = [quadro("GERAL", 30, 30), quadro("MACHO", 20, 25), quadro("FÊMEA", 10, 5)];
    expect(vendeuOsDoisSexos(osDois)).toBe(true);
    const femeaSoNoPlano = [quadro("GERAL", 20, 25), quadro("MACHO", 20, 20), quadro("FÊMEA", 0, 5)];
    expect(vendeuOsDoisSexos(femeaSoNoPlano)).toBe(true);
  });

  it("numera as folhas marcadas, na ordem do boletim", () => {
    expect(folhasDoBoletim(["comercializacao", "resumo", "capa"])).toEqual([
      { chave: "resumo", numero: 1 },
      { chave: "comercializacao", numero: 2 },
    ]);
    expect(folhasDoBoletim(["resumo", "financeiro", "rebanho", "comercializacao"]).length).toBe(4);
    expect(rotuloDaPagina(2, 4)).toBe("Página 02/04");
  });

  it("identifica a fazenda (ou o grupo), o período e a cidade", () => {
    const fazendas: FazendaDoEscopo[] = [
      { id: "c1", nome: "FAZENDA CMI", cliente: "RENE", origem: "planilha", sistema_produtivo: null,
        primeiro_mes: "2025-01-01", ultimo_mes: "2026-10-01",
        capacidades: { estoque: true, rebanho_medio: true, area: true, financeiro: true, planejado: true,
        situacoes: ["pago"] } },
      { id: "c2", nome: "FAZENDA PALMARES", cliente: "RENE", origem: "planilha", sistema_produtivo: null,
        primeiro_mes: "2025-01-01", ultimo_mes: "2026-10-01",
        capacidades: { estoque: true, rebanho_medio: true, area: true, financeiro: true, planejado: true,
        situacoes: ["pago"] } },
    ];
    const filtro: Filtro = { origem: "planilha", cliente: "RENE", fazendas: ["c1"], visao: "civil", ano: 2026,
      meses: [], situacoes: [], versoes: [], semPlano: [] };
    const datas = { inicio_do_periodo: "2026-01-01", mes_referencia: "2026-10-01",
      plano: { fazendas: [], em_uso: [] } };
    const uma = identificacaoDoBoletim(filtro, fazendas, datas, " Cuiabá ", "2026-11");
    expect(uma).toMatchObject({ titulo: "FAZENDA CMI", variasFazendas: false, periodo: "Jan/26 a Out/26", meses: 10,
      rotuloDoPeriodo: "ANO 2026", sistema: "Integração Planilhas", planejamento: "Sem planejamento",
      localEData: "Cuiabá, novembro de 2026" });
    const grupo = identificacaoDoBoletim({ ...filtro, fazendas: [] }, fazendas, datas, "", "2026-11");
    expect(grupo).toMatchObject({ titulo: "GRUPO", fazendas: "FAZENDA CMI | FAZENDA PALMARES", variasFazendas: true,
      localEData: "Novembro de 2026" });
  });

  it("dá a altura das colunas em px, como o gerador", () => {
    expect(maiorValor([[1, null, 4], [3, 2]])).toBe(4);
    expect(alturaDaColuna(2, 4, 182)).toBe(91);
    expect(alturaDaColuna(0.001, 4, 182)).toBe(2);       // a pequena ainda aparece
    expect(alturaDaColuna(null, 4, 182)).toBe(1);
    expect(alturaDaColuna(0, 4, 182)).toBe(1);
  });
});
