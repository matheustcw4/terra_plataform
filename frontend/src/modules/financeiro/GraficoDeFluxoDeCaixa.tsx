import { Bar, CartesianGrid, ComposedChart, LabelList, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis }
  from "recharts";
import type { MesDoFinanceiro } from "../../core/api/tipos";
import { dinheiro, rotuloDeColuna } from "../../logic/formatar";
import { mesCurto } from "../../logic/meses";
import { CAIXA_DO_MOUSE, COLUNA, EIXO, GRADE, LEGENDA } from "../../core/ui/estiloDosGraficos";

// "FLUXO DE CAIXA MENSAL" do BI: receitas e despesas do mês em colunas e o saldo em linha (o saldo soma também as
// outras receitas, como no BI; a API já manda pronto). Sem animação: o painel é para ler número.
export function GraficoDeFluxoDeCaixa({ serie }: { serie: MesDoFinanceiro[] }) {
  return (
    <section className="painel-grafico">
      <h2>FLUXO DE CAIXA MENSAL</h2>
      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={serie} margin={{ top: 24, right: 8, bottom: 0, left: 8 }}>
          <CartesianGrid {...GRADE} />
          <XAxis dataKey="mes" tickFormatter={mesCurto} {...EIXO} />
          <YAxis hide />
          <Tooltip {...CAIXA_DO_MOUSE} labelFormatter={(mes) => mesCurto(String(mes))} formatter={(valor) => dinheiro(Number(valor))} />
          <Legend {...LEGENDA} />
          <Bar {...COLUNA} dataKey="receitas" name="Receitas" fill="var(--cor-realizado)" isAnimationActive={false}>
            <LabelList dataKey="receitas" position="top" formatter={(valor) => rotuloDeColuna(Number(valor))}
              className="rotulo-de-coluna" />
          </Bar>
          <Bar {...COLUNA} dataKey="despesas" name="Despesas" fill="var(--cor-despesa)" isAnimationActive={false}>
            <LabelList dataKey="despesas" position="top" formatter={(valor) => rotuloDeColuna(Number(valor))}
              className="rotulo-de-coluna" />
          </Bar>
          <Line dataKey="saldo" name="Saldo" stroke="var(--cor-rebanho-final)" strokeWidth={2}
            isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </section>
  );
}
