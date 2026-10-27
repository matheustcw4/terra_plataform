import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import { numero } from "../../logic/formatar";
import { CAIXA_DO_MOUSE, COLUNA, EIXO, GRADE } from "./estiloDosGraficos";

export type Coluna = { rotulo: string; valor: number };

type Props = {
  titulo: string;
  colunas: Coluna[];
  altura?: number;
};

// Gráfico de colunas com o número em cima de cada uma, como "ESTOQUE FINAL MENSAL" e "ESTOQUE POR CATEGORIA" do BI
// (eixo de valores escondido: o rótulo já diz o número). Sem animação: o painel é para ler número, e a animação não
// roda em aba em segundo plano nem na impressão.
export function GraficoDeColunas({ titulo, colunas, altura = 300 }: Props) {
  return (
    <section className="painel-grafico">
      <h2>{titulo}</h2>
      <ResponsiveContainer width="100%" height={altura}>
        <BarChart data={colunas} margin={{ top: 24, right: 8, bottom: 0, left: 8 }}>
          <CartesianGrid {...GRADE} />
          <XAxis dataKey="rotulo" {...EIXO} interval={0} tick={{ fontSize: 12 }} />
          <Tooltip {...CAIXA_DO_MOUSE} formatter={(valor) => numero(Number(valor))} />
          <Bar {...COLUNA} dataKey="valor" name={titulo} fill="var(--cor-realizado)" isAnimationActive={false}>
            <LabelList dataKey="valor" position="top" formatter={(valor) => rotuloInteiro(Number(valor))}
              className="rotulo-de-coluna" />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}

// O número inteiro em cima da coluna (o estoque cabe), e nada quando a coluna é zero.
function rotuloInteiro(valor: number): string {
  if (valor === 0) {
    return "";
  }
  return numero(valor);
}
