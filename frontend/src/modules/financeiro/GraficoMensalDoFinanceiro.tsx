import { Bar, BarChart, CartesianGrid, LabelList, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { MesDoFinanceiro } from "../../core/api/tipos";
import { rotuloDeColuna } from "../../logic/formatar";
import { mesCurto } from "../../logic/meses";
import { CAIXA_DO_MOUSE, COLUNA, EIXO, GRADE, LEGENDA } from "../../core/ui/estiloDosGraficos";

type CampoDoMes =
  | "receitas"
  | "receitas_planejadas"
  | "desembolso"
  | "desembolso_planejado"
  | "desembolso_por_cabeca"
  | "desembolso_por_cabeca_planejado";

type Props = {
  titulo: string;
  serie: MesDoFinanceiro[];
  realizado: CampoDoMes; // a coluna azul
  planejado: CampoDoMes; // a coluna cinza
  formatar: (valor: number) => string; // valor exato, na caixa que aparece ao passar o mouse
};

// Os gráficos "REALIZADO X PLANEJADO" da página Financeiro do BI (receitas, desembolso e desembolso por cabeça):
// realizado × planejado por mês. O número fica só em cima do realizado: na coluna estreita da página, 24 rótulos se
// sobrepõem (o planejado aparece ao passar o mouse). Sem animação: o painel é para ler número.
export function GraficoMensalDoFinanceiro({ titulo, serie, realizado, planejado, formatar }: Props) {
  return (
    <section className="painel-grafico">
      <h2>{titulo}</h2>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={serie} margin={{ top: 24, right: 8, bottom: 0, left: 8 }}>
          <CartesianGrid {...GRADE} />
          <XAxis dataKey="mes" tickFormatter={mesCurto} {...EIXO} />
          <YAxis hide />
          <Tooltip {...CAIXA_DO_MOUSE} labelFormatter={(mes) => mesCurto(String(mes))} formatter={(valor) => formatar(Number(valor))} />
          <Legend {...LEGENDA} />
          <Bar {...COLUNA} dataKey={realizado} name="Realizado" fill="var(--cor-realizado)" isAnimationActive={false}>
            <LabelList dataKey={realizado} position="top" formatter={(valor) => rotuloDeColuna(Number(valor))}
              className="rotulo-de-coluna" />
          </Bar>
          <Bar {...COLUNA} dataKey={planejado} name="Planejado" fill="var(--cor-planejado)" isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}
