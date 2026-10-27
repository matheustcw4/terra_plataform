// O estilo comum dos gráficos (o mesmo do AgTechLab, nas cores da Terra): eixo discreto, grade tracejada só na
// horizontal, caixa do mouse com borda fina e colunas com o canto de cima arredondado. O número escrito junto da
// coluna usa a cor do texto (classe .rotulo-de-coluna), nunca a da série.

export const EIXO = {
  tick: { fontSize: 11, fill: "var(--cor-texto-terciario)" },
  tickLine: false,
  axisLine: { stroke: "var(--cor-borda)" },
} as const;

export const GRADE = { vertical: false, stroke: "var(--cor-borda)", strokeDasharray: "3 3" } as const;

export const CAIXA_DO_MOUSE = {
  contentStyle: { fontSize: 12, borderRadius: 6, border: "1px solid var(--cor-borda)", boxShadow: "var(--sombra)" },
  cursor: { fill: "var(--cor-superficie-2)" },
} as const;

export const LEGENDA = { wrapperStyle: { fontSize: 12, paddingTop: 4 }, iconType: "circle", iconSize: 8 } as const;

// colunas em pé: canto de cima arredondado; largura máxima para a série curta não virar um bloco
export const COLUNA = { radius: [4, 4, 0, 0] as [number, number, number, number], maxBarSize: 44 };

// barras deitadas: o canto arredondado fica na ponta, do lado do número
export const BARRA_DEITADA = { radius: [0, 4, 4, 0] as [number, number, number, number], maxBarSize: 22 };

// o nome da categoria no eixo das barras deitadas é para ler, então usa a cor do texto e um corpo maior
export const EIXO_DE_NOMES = {
  tick: { fontSize: 12, fill: "var(--cor-texto-apagado)" },
  tickLine: false,
  axisLine: false,
} as const;
