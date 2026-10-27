import { Bar, CartesianGrid, ComposedChart, LabelList, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis }
  from "recharts";
import type { MesDoLote } from "../../core/api/tipos";
import { rotuloDeColuna } from "../../logic/formatar";
import { mesCurto } from "../../logic/meses";
import { CAIXA_DO_MOUSE, COLUNA, EIXO, GRADE, LEGENDA } from "../../core/ui/estiloDosGraficos";

type Props = {
  titulo: string;
  serie: MesDoLote[];
  realizado: "cabecas" | "valor"; // campo da série que vira a coluna do realizado
  planejado: "cabecas_planejadas" | "valor_planejado";
  linha?: { campo: "cabecas_acumuladas" | "preco_arroba"; nome: string }; // no eixo da direita
  formatar: (valor: number) => string; // valor exato, na caixa que aparece ao passar o mouse
};

// Os gráficos "RELAÇÃO MENSAL" das páginas de venda e de compra do BI: realizado (azul) × planejado (cinza) por mês,
// com o número em cima das colunas e, quando há, uma linha (cabeças acumuladas ou preço da @). Sem animação: o painel
// é para ler número, e a animação não roda em aba em segundo plano nem na impressão.
export function GraficoMensalDoLote({ titulo, serie, realizado, planejado, linha, formatar }: Props) {
  return (
    <section className="painel-grafico">
      <h2>{titulo}</h2>
      <ResponsiveContainer width="100%" height={320}>
        <ComposedChart data={serie} margin={{ top: 24, right: 8, bottom: 0, left: 8 }}>
          <CartesianGrid {...GRADE} />
          <XAxis dataKey="mes" tickFormatter={mesCurto} {...EIXO} />
          <YAxis yAxisId="mes" hide />
          {linha && <YAxis yAxisId="linha" orientation="right" hide />}
          <Tooltip {...CAIXA_DO_MOUSE} labelFormatter={(mes) => mesCurto(String(mes))} formatter={(valor) => formatar(Number(valor))} />
          <Legend {...LEGENDA} />
          <Bar {...COLUNA} yAxisId="mes" dataKey={realizado} name="Realizado" fill="var(--cor-realizado)" isAnimationActive={false}>
            <LabelList dataKey={realizado} position="top" formatter={(valor) => rotuloDeColuna(Number(valor))}
              className="rotulo-de-coluna" />
          </Bar>
          <Bar {...COLUNA} yAxisId="mes" dataKey={planejado} name="Planejado" fill="var(--cor-planejado)"
            isAnimationActive={false}>
            <LabelList dataKey={planejado} position="top" formatter={(valor) => rotuloDeColuna(Number(valor))}
              className="rotulo-de-coluna" />
          </Bar>
          {linha && (
            <Line yAxisId="linha" dataKey={linha.campo} name={linha.nome} stroke="var(--cor-acumulado)"
              strokeWidth={2} connectNulls isAnimationActive={false} />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </section>
  );
}
