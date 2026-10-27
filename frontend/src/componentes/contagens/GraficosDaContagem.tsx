import { Bar, CartesianGrid, ComposedChart, LabelList, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis }
  from "recharts";
import type { MesDaContagem } from "../../core/api/tipos";
import { numero, rotuloDeColuna } from "../../logic/formatar";
import { mesCurto } from "../../logic/meses";
import { CAIXA_DO_MOUSE, COLUNA, EIXO, GRADE, LEGENDA } from "../../core/ui/estiloDosGraficos";

type MensalProps = {
  titulo: string;
  serie: MesDaContagem[];
  comAcumulado?: boolean; // a linha do realizado acumulado, no eixo da direita (o gráfico mensal de mortes do BI)
};

// "REALIZADO X PLANEJADO - MENSAL" das páginas Nascimentos e Mortes: cabeças do mês, realizado (azul) × planejado
// (cinza), com o número em cima das colunas. Sem animação: o painel é para ler número, e a animação não roda em aba
// em segundo plano nem na impressão.
export function GraficoMensalDaContagem({ titulo, serie, comAcumulado = false }: MensalProps) {
  return (
    <section className="painel-grafico">
      <h2>{titulo}</h2>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={serie} margin={{ top: 24, right: 8, bottom: 0, left: 8 }}>
          <CartesianGrid {...GRADE} />
          <XAxis dataKey="mes" tickFormatter={mesCurto} {...EIXO} />
          <YAxis yAxisId="mes" hide />
          {comAcumulado && <YAxis yAxisId="acumulado" orientation="right" hide />}
          <Tooltip {...CAIXA_DO_MOUSE} labelFormatter={(mes) => mesCurto(String(mes))} formatter={(valor) => numero(Number(valor))} />
          <Legend {...LEGENDA} />
          <Bar {...COLUNA} yAxisId="mes" dataKey="realizado" name="Realizado" fill="var(--cor-realizado)"
            isAnimationActive={false}>
            <LabelList dataKey="realizado" position="top" formatter={(valor) => rotuloDeColuna(Number(valor))}
              className="rotulo-de-coluna" />
          </Bar>
          <Bar {...COLUNA} yAxisId="mes" dataKey="planejado" name="Planejado" fill="var(--cor-planejado)"
            isAnimationActive={false}>
            <LabelList dataKey="planejado" position="top" formatter={(valor) => rotuloDeColuna(Number(valor))}
              className="rotulo-de-coluna" />
          </Bar>
          {comAcumulado && (
            <Line yAxisId="acumulado" dataKey="realizado_acumulado" name="Acumulado" stroke="var(--cor-acumulado)"
              strokeWidth={2} isAnimationActive={false} />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </section>
  );
}

type AcumuladoProps = {
  titulo: string;
  serie: MesDaContagem[];
  forma: "colunas" | "linhas"; // nascimentos: linhas; mortes: colunas (como no BI)
};

// "REALIZADO X PLANEJADO - ACUMULADO": o realizado e o planejado somados do início do período até cada mês.
export function GraficoAcumuladoDaContagem({ titulo, serie, forma }: AcumuladoProps) {
  return (
    <section className="painel-grafico">
      <h2>{titulo}</h2>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={serie} margin={{ top: 24, right: 24, bottom: 0, left: 24 }}>
          <CartesianGrid {...GRADE} />
          <XAxis dataKey="mes" tickFormatter={mesCurto} {...EIXO} />
          <YAxis hide />
          <Tooltip {...CAIXA_DO_MOUSE} labelFormatter={(mes) => mesCurto(String(mes))} formatter={(valor) => numero(Number(valor))} />
          <Legend {...LEGENDA} />
          {forma === "colunas" && (
            <>
              <Bar {...COLUNA} dataKey="realizado_acumulado" name="Realizado" fill="var(--cor-realizado)"
                isAnimationActive={false}>
                <LabelList dataKey="realizado_acumulado" position="top"
                  formatter={(valor) => rotuloDeColuna(Number(valor))} className="rotulo-de-coluna" />
              </Bar>
              <Bar {...COLUNA} dataKey="planejado_acumulado" name="Planejado" fill="var(--cor-planejado)"
                isAnimationActive={false}>
                <LabelList dataKey="planejado_acumulado" position="top"
                  formatter={(valor) => rotuloDeColuna(Number(valor))} className="rotulo-de-coluna" />
              </Bar>
            </>
          )}
          {forma === "linhas" && (
            <>
              <Line dataKey="realizado_acumulado" name="Realizado" stroke="var(--cor-realizado)" strokeWidth={3}
                isAnimationActive={false}>
                <LabelList dataKey="realizado_acumulado" position="top"
                  formatter={(valor) => rotuloDeColuna(Number(valor))} className="rotulo-de-coluna" />
              </Line>
              <Line dataKey="planejado_acumulado" name="Planejado" stroke="var(--cor-planejado)" strokeWidth={3}
                isAnimationActive={false}>
                <LabelList dataKey="planejado_acumulado" position="bottom"
                  formatter={(valor) => rotuloDeColuna(Number(valor))} className="rotulo-de-coluna" />
              </Line>
            </>
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </section>
  );
}
