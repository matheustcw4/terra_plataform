import { Bar, CartesianGrid, ComposedChart, LabelList, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis }
  from "recharts";
import type { MesDoFinanceiro } from "../../core/api/tipos";
import { dinheiro, rotuloDeColuna } from "../../logic/formatar";
import { mesCurto } from "../../logic/meses";
import {
  CAIXA_DO_MOUSE,
  COLUNA,
  EIXO,
  GRADE,
  LEGENDA,
  MARGEM_PARA_ROTULO_EM_PE,
  ROTULO,
  ROTULO_EM_PE,
} from "../../core/ui/estiloDosGraficos";

// O saldo negativo leva o número embaixo do ponto: a escala desce um pouco além dele para o número não cair em cima
// do nome do mês.
function folgaEmbaixo(menor: number): number {
  if (menor >= 0) {
    return 0;
  }
  return menor * 1.35;
}

// "FLUXO DE CAIXA MENSAL" do BI: receitas e despesas do mês em colunas e o saldo em linha (o saldo soma também as
// outras receitas, como no BI; a API já manda pronto). O número das colunas vai em pé (deitados, os das duas colunas
// do mês se encostam) e o do saldo embaixo do ponto, longe deles. Sem animação: o painel é para ler número.
export function GraficoDeFluxoDeCaixa({ serie }: { serie: MesDoFinanceiro[] }) {
  return (
    <section className="painel-grafico">
      <h2>FLUXO DE CAIXA MENSAL</h2>
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={serie} margin={{ top: MARGEM_PARA_ROTULO_EM_PE, right: 8, bottom: 0, left: 8 }}>
          <CartesianGrid {...GRADE} />
          <XAxis dataKey="mes" tickFormatter={mesCurto} {...EIXO} />
          <YAxis hide domain={[folgaEmbaixo, "auto"]} />
          <Tooltip {...CAIXA_DO_MOUSE} labelFormatter={(mes) => mesCurto(String(mes))} formatter={(valor) => dinheiro(Number(valor))} />
          <Legend {...LEGENDA} />
          <Bar {...COLUNA} dataKey="receitas" name="Receitas" fill="var(--cor-realizado)" isAnimationActive={false}>
            <LabelList dataKey="receitas" position="top" formatter={(valor) => rotuloDeColuna(Number(valor))}
              {...ROTULO_EM_PE} />
          </Bar>
          <Bar {...COLUNA} dataKey="despesas" name="Despesas" fill="var(--cor-despesa)" isAnimationActive={false}>
            <LabelList dataKey="despesas" position="top" formatter={(valor) => rotuloDeColuna(Number(valor))}
              {...ROTULO_EM_PE} />
          </Bar>
          <Line dataKey="saldo" name="Saldo" stroke="var(--cor-rebanho-final)" strokeWidth={2}
            isAnimationActive={false}>
            <LabelList dataKey="saldo" position="bottom" formatter={(valor) => rotuloDeColuna(Number(valor))}
              {...ROTULO} />
          </Line>
        </ComposedChart>
      </ResponsiveContainer>
    </section>
  );
}
