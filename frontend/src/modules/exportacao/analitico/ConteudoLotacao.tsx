import { Bar, CartesianGrid, ComposedChart, Legend, Line, XAxis, YAxis } from "recharts";
import type { SecaoLotacao } from "../../../core/api/tipos";
import { COLUNA, EIXO, GRADE, LEGENDA } from "../../../core/ui/estiloDosGraficos";
import { numero, percentual } from "../../../logic/formatar";
import { mesCurto } from "../../../logic/meses";
import { mostra, type ParteDoAssunto, recortar } from "../../../logic/personalizado";
import { CartaoAnalitico } from "./CartaoAnalitico";
import { QuadroAnalitico } from "./FolhaAnalitica";

const LARGURA_DO_GRAFICO = 1100; // a largura útil do quadro na folha A4

type Props = { secao: SecaoLotacao; partes: ParteDoAssunto[]; faixa?: [number, number] };

// Lotação: o rebanho no começo, no fim e na média do período, a lotação média, máxima e mínima, e o mês a mês
// (rebanho médio, UA, área, lotação realizada × prevista). Cada quadro é uma peça; `faixa` escolhe as peças.
export function ConteudoLotacao({ secao, partes, faixa }: Props) {
  const pecas = [];
  if (mostra(partes, "resumo")) {
    pecas.push(<CartoesDaLotacao key="cartoes" secao={secao} />);
    pecas.push(<AcompanhamentoMensal key="mensal" secao={secao} />);
  }
  if (mostra(partes, "graficos")) {
    pecas.push(<GraficoDaLotacao key="grafico" secao={secao} />);
  }
  return <>{recortar(pecas, faixa)}</>;
}

function CartoesDaLotacao({ secao }: { secao: SecaoLotacao }) {
  return (
    <div className="cartoes-analiticos quatro-colunas">
      <CartaoAnalitico rotulo="Rebanho inicial" valor={numero(secao.estoque_inicial)} unidade="cabeças" />
      <CartaoAnalitico rotulo="Variação" valor={percentual(secao.variacao_do_rebanho ?? null)}
        unidade="no período" />
      <CartaoAnalitico rotulo="Rebanho final" valor={numero(secao.estoque_final)} unidade="cabeças" />
      <CartaoAnalitico rotulo="Rebanho médio" valor={numero(secao.rebanho_medio_cab ?? null)} unidade="cabeças" />
      <CartaoAnalitico rotulo="Lotação média" valor={numero(secao.lotacao_cab_ha ?? null, 2)} unidade="cab/ha"
        forte />
      <CartaoAnalitico rotulo="Lotação prevista" valor={numero(secao.lotacao_cab_ha_prevista ?? null, 2)}
        unidade="cab/ha" />
      <CartaoAnalitico rotulo="Lotação máxima" valor={numero(secao.lotacao_maxima ?? null, 2)} unidade="cab/ha" />
      <CartaoAnalitico rotulo="Lotação mínima" valor={numero(secao.lotacao_minima ?? null, 2)} unidade="cab/ha" />
    </div>
  );
}

function AcompanhamentoMensal({ secao }: { secao: SecaoLotacao }) {
  return (
    <QuadroAnalitico titulo="Acompanhamento mensal">
      <table className="tabela-analitica tabela-lotacao">
        <thead>
          <tr>
            <th scope="col">Mês</th>
            <th scope="col">Rebanho médio (cab)</th>
            <th scope="col">UA</th>
            <th scope="col">Área (ha)</th>
            <th scope="col" className="inicio-do-bloco">Lotação cab/ha</th>
            <th scope="col">Lotação UA/ha</th>
            <th scope="col">Prevista cab/ha</th>
          </tr>
        </thead>
        <tbody>
          {secao.meses.map((mes) => (
            <tr key={mes.mes}>
              <th scope="row">{mesCurto(mes.mes)}</th>
              <td>{numero(mes.rebanho_medio_cab ?? null)}</td>
              <td>{numero(mes.rebanho_medio_ua ?? null)}</td>
              <td>{numero(mes.area_ha ?? null, 1)}</td>
              <td className="inicio-do-bloco destaque">{numero(mes.lotacao_cab_ha ?? null, 2)}</td>
              <td>{numero(mes.lotacao_ua_ha ?? null, 2)}</td>
              <td className="apagado">{numero(mes.lotacao_cab_ha_prevista ?? null, 2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </QuadroAnalitico>
  );
}

function GraficoDaLotacao({ secao }: { secao: SecaoLotacao }) {
  return (
    <QuadroAnalitico titulo="Rebanho médio e lotação mês a mês">
      <ComposedChart width={LARGURA_DO_GRAFICO} height={280} data={secao.meses}
        margin={{ top: 16, right: 24, bottom: 0, left: 8 }}>
        <CartesianGrid {...GRADE} />
        <XAxis dataKey="mes" tickFormatter={mesCurto} {...EIXO} />
        <YAxis yAxisId="rebanho" {...EIXO} tickFormatter={(valor) => numero(Number(valor))} />
        <YAxis yAxisId="lotacao" orientation="right" {...EIXO}
          tickFormatter={(valor) => numero(Number(valor), 1)} />
        <Legend {...LEGENDA} />
        <Bar {...COLUNA} yAxisId="rebanho" dataKey="rebanho_medio_cab" name="Rebanho médio (cab)"
          fill="var(--cor-azul-claro)" isAnimationActive={false} />
        <Line yAxisId="lotacao" dataKey="lotacao_cab_ha" name="Lotação realizada (cab/ha)"
          stroke="var(--cor-realizado)" strokeWidth={2.5} isAnimationActive={false} />
        <Line yAxisId="lotacao" dataKey="lotacao_cab_ha_prevista" name="Lotação prevista (cab/ha)"
          stroke="var(--cor-planejado)" strokeWidth={2} strokeDasharray="6 4" isAnimationActive={false} />
      </ComposedChart>
    </QuadroAnalitico>
  );
}
