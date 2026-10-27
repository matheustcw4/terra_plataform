import { Bar, BarChart, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { numero } from "../../logic/formatar";
import { BARRA_DEITADA, CAIXA_DO_MOUSE, EIXO_DE_NOMES } from "./estiloDosGraficos";

export type Barra = { rotulo: string; valor: number };

type Props = {
  titulo: string;
  barras: Barra[]; // já na ordem de mostrar (a API manda da maior para a menor)
  semDados: string; // o que dizer quando não há barra
  formatar?: (valor: number) => string; // o número na ponta da barra e na caixa do mouse (padrão: cabeças)
};

const ALTURA_DA_BARRA = 30;

// Barras deitadas com o número na ponta, como "Causa Morte" do BI. A altura cresce com o número de barras para cada
// rótulo caber na sua linha. Sem animação: o painel é para ler número.
export function GraficoDeBarras({ titulo, barras, semDados, formatar = numero }: Props) {
  if (barras.length === 0) {
    return (
      <section className="painel-grafico">
        <h2>{titulo}</h2>
        <p className="explicacao">{semDados}</p>
      </section>
    );
  }
  const altura = barras.length * ALTURA_DA_BARRA + 40;
  return (
    <section className="painel-grafico">
      <h2>{titulo}</h2>
      <ResponsiveContainer width="100%" height={altura}>
        <BarChart data={barras} layout="vertical" margin={{ top: 8, right: 48, bottom: 8, left: 8 }}>
          <XAxis type="number" hide />
          <YAxis type="category" dataKey="rotulo" width={170} interval={0} {...EIXO_DE_NOMES} />
          <Tooltip {...CAIXA_DO_MOUSE} formatter={(valor) => formatar(Number(valor))} />
          <Bar {...BARRA_DEITADA} dataKey="valor" name={titulo} fill="var(--cor-realizado)" isAnimationActive={false}>
            <LabelList dataKey="valor" position="right" formatter={(valor) => formatar(Number(valor))}
              className="rotulo-de-coluna" />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}
