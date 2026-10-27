import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, XAxis, YAxis } from "recharts";
import type { MesComparado, SecaoDeLotes } from "../../../core/api/tipos";
import { COLUNA, EIXO, GRADE, LEGENDA } from "../../../core/ui/estiloDosGraficos";
import { colunasDoLote, dataCurta } from "../../../logic/analitico";
import { dinheiro, numero, percentual } from "../../../logic/formatar";
import { mesCurto } from "../../../logic/meses";
import { mostra, type ParteDoAssunto, recortar } from "../../../logic/personalizado";
import { QuadroAnalitico, type Rotulos } from "./FolhaAnalitica";
import { TabelaDoPlacar } from "./TabelaDoPlacar";

const LARGURA_DO_GRAFICO = 520; // metade da largura útil da folha A4

type Props = {
  secao: SecaoDeLotes;
  partes: ParteDoAssunto[];
  rotulos: Rotulos;
  tituloDosLancamentos: string;
  faixa?: [number, number];
};

// Lotes (nascimentos, compras ou vendas): os lançamentos do mês, as cabeças previstas × realizadas mês a mês e
// acumuladas, e o resumo do acumulado (preço da @, peso, rendimento...) contra o previsto e a meta. Cada quadro é uma
// peça; `faixa` escolhe as peças.
export function ConteudoDeLotes({ secao, partes, rotulos, tituloDosLancamentos, faixa }: Props) {
  const pecas = [];
  if (mostra(partes, "lancamentos")) {
    pecas.push(
      <QuadroAnalitico key="lancamentos" titulo={tituloDosLancamentos}>
        <TabelaDeLotes secao={secao} />
      </QuadroAnalitico>,
    );
  }
  if (mostra(partes, "graficos")) {
    pecas.push(
      <div key="graficos" className="graficos-lado-a-lado">
        <QuadroAnalitico titulo="Cabeças por mês: previsto × realizado">
          <GraficoPorMes meses={secao.meses} />
        </QuadroAnalitico>
        <QuadroAnalitico titulo="Cabeças acumuladas: previsto × realizado">
          <GraficoAcumulado meses={secao.meses} />
        </QuadroAnalitico>
      </div>,
    );
  }
  if (mostra(partes, "previsto")) {
    pecas.push(
      <QuadroAnalitico key="previsto" titulo="Previsto × realizado">
        <TabelaDoPlacar linhas={secao.resumo} rotuloDoMes={rotulos.mes} rotuloDaMeta={rotulos.meta} semGrupo />
      </QuadroAnalitico>,
    );
  }
  return <>{recortar(pecas, faixa)}</>;
}

// Os lançamentos do mês; as colunas dependem do tipo (quem é a outra parte, se tem peso, carcaça e preço).
export function TabelaDeLotes({ secao }: { secao: SecaoDeLotes }) {
  const colunas = colunasDoLote(secao.tipo);
  if (secao.lancamentos.length === 0) {
    return <p className="nota">{colunas.semLancamento}</p>;
  }
  return (
    <table className="tabela-analitica tabela-lotes">
      <thead>
        <tr>
          <th scope="col">Data</th>
          <th scope="col">Categoria</th>
          {colunas.contraparte !== null && <th scope="col">{colunas.contraparte}</th>}
          <th scope="col">Cab.</th>
          {colunas.pesos && <th scope="col">kg vivo</th>}
          {colunas.carcaca && <th scope="col">kg carcaça</th>}
          {colunas.pesos && <th scope="col">@</th>}
          {colunas.carcaca && <th scope="col">% RC</th>}
          {colunas.precos && <th scope="col">R$/@</th>}
          {colunas.precos && <th scope="col">R$/cab</th>}
          {colunas.precos && <th scope="col">R$/kg</th>}
          {colunas.precos && <th scope="col">R$ total</th>}
        </tr>
      </thead>
      <tbody>
        {secao.lancamentos.map((lote, posicao) => (
          <tr key={`${lote.data}-${posicao}`}>
            <td>{dataCurta(lote.data)}</td>
            <th scope="row">{lote.categoria}</th>
            {colunas.contraparte !== null && <td className="texto">{lote.contraparte ?? "—"}</td>}
            <td>{numero(lote.cabecas)}</td>
            {colunas.pesos && <td>{numero(lote.kg_vivo ?? null)}</td>}
            {colunas.carcaca && <td>{numero(lote.kg_carcaca ?? null)}</td>}
            {colunas.pesos && <td>{numero(lote.arrobas ?? null, 1)}</td>}
            {colunas.carcaca && <td>{percentual(lote.rendimento_carcaca ?? null)}</td>}
            {colunas.precos && <td>{dinheiro(lote.preco_arroba ?? null, 2)}</td>}
            {colunas.precos && <td>{dinheiro(lote.valor_por_cabeca ?? null, 2)}</td>}
            {colunas.precos && <td>{dinheiro(lote.preco_kg ?? null, 2)}</td>}
            {colunas.precos && <td className="destaque">{dinheiro(lote.valor ?? null)}</td>}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function GraficoPorMes({ meses }: { meses: MesComparado[] }) {
  return (
    <BarChart width={LARGURA_DO_GRAFICO} height={240} data={meses} margin={{ top: 12, right: 20, bottom: 0, left: 0 }}>
      <CartesianGrid {...GRADE} />
      <XAxis dataKey="mes" tickFormatter={mesCurto} {...EIXO} interval={0} />
      <YAxis {...EIXO} tickFormatter={(valor) => numero(Number(valor))} />
      <Legend {...LEGENDA} />
      <Bar {...COLUNA} dataKey="previsto" name="Previsto" fill="var(--cor-planejado)" isAnimationActive={false} />
      <Bar {...COLUNA} dataKey="realizado" name="Realizado" fill="var(--cor-realizado)" isAnimationActive={false} />
    </BarChart>
  );
}

function GraficoAcumulado({ meses }: { meses: MesComparado[] }) {
  return (
    <LineChart width={LARGURA_DO_GRAFICO} height={240} data={meses} margin={{ top: 12, right: 20, bottom: 0, left: 0 }}>
      <CartesianGrid {...GRADE} />
      <XAxis dataKey="mes" tickFormatter={mesCurto} {...EIXO} interval={0} />
      <YAxis {...EIXO} tickFormatter={(valor) => numero(Number(valor))} />
      <Legend {...LEGENDA} />
      <Line dataKey="previsto_acumulado" name="Previsto" stroke="var(--cor-planejado)" strokeWidth={2}
        strokeDasharray="6 4" dot={false} isAnimationActive={false} />
      <Line dataKey="realizado_acumulado" name="Realizado" stroke="var(--cor-realizado)" strokeWidth={2.5}
        isAnimationActive={false} />
    </LineChart>
  );
}
