import { Bar, CartesianGrid, ComposedChart, Legend, Line, XAxis, YAxis } from "recharts";
import type { SecaoMortes } from "../../../core/api/tipos";
import { COLUNA, EIXO, GRADE, LEGENDA } from "../../../core/ui/estiloDosGraficos";
import { dataCurta } from "../../../logic/analitico";
import { numero, percentual } from "../../../logic/formatar";
import { mesCurto } from "../../../logic/meses";
import { mostra, type ParteDoAssunto, recortar } from "../../../logic/personalizado";
import { QuadroAnalitico, type Rotulos } from "./FolhaAnalitica";

const LARGURA_DO_GRAFICO = 1100; // a largura útil do quadro na folha A4

type Props = { secao: SecaoMortes; partes: ParteDoAssunto[]; rotulos: Rotulos; faixa?: [number, number] };

// Mortes: as do mês (data, causa, local, categoria), as mortes mês a mês previstas × realizadas com a mortalidade
// acumulada, a mortalidade por grupo contra a meta e as causas por grupo no período. Cada quadro é uma peça (a
// mortalidade por grupo e as causas, lado a lado, contam como uma); `faixa` escolhe as peças.
export function ConteudoMortes({ secao, partes, rotulos, faixa }: Props) {
  const porGrupo = mostra(partes, "previsto");
  const causas = mostra(partes, "resumo");
  const pecas = [];
  if (mostra(partes, "lancamentos")) {
    pecas.push(
      <QuadroAnalitico key="lancamentos" titulo={`Mortes de ${rotulos.mes}`}>
        <MortesDoMes secao={secao} />
      </QuadroAnalitico>,
    );
  }
  if (mostra(partes, "graficos")) {
    pecas.push(
      <QuadroAnalitico key="grafico" titulo="Mortes por mês e mortalidade acumulada">
        <GraficoDasMortes secao={secao} />
      </QuadroAnalitico>,
    );
  }
  if (porGrupo && causas) {
    pecas.push(
      <div key="grupos" className="graficos-lado-a-lado">
        <MortalidadePorGrupo secao={secao} rotuloDaMeta={rotulos.meta} />
        <CausasNoPeriodo secao={secao} />
      </div>,
    );
  }
  if (porGrupo && !causas) {
    pecas.push(<MortalidadePorGrupo key="grupos" secao={secao} rotuloDaMeta={rotulos.meta} />);
  }
  if (!porGrupo && causas) {
    pecas.push(<CausasNoPeriodo key="causas" secao={secao} />);
  }
  return <>{recortar(pecas, faixa)}</>;
}

function MortesDoMes({ secao }: { secao: SecaoMortes }) {
  if (secao.lancamentos.length === 0) {
    return <p className="nota">Nenhuma morte no mês.</p>;
  }
  return (
    <table className="tabela-analitica tabela-lotes">
      <thead>
        <tr>
          <th scope="col">Data</th>
          <th scope="col">Causa</th>
          <th scope="col">Local</th>
          <th scope="col">Categoria</th>
          <th scope="col">Cab.</th>
          <th scope="col">Peso vivo total (kg)</th>
        </tr>
      </thead>
      <tbody>
        {secao.lancamentos.map((morte, posicao) => (
          <tr key={`${morte.data}-${posicao}`}>
            <td>{dataCurta(morte.data)}</td>
            <td className="texto">{morte.causa}</td>
            <td className="texto">{morte.local ?? "—"}</td>
            <th scope="row">{morte.categoria}</th>
            <td>{numero(morte.cabecas)}</td>
            <td>{numero(morte.peso_vivo_kg ?? null)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function GraficoDasMortes({ secao }: { secao: SecaoMortes }) {
  return (
    <ComposedChart width={LARGURA_DO_GRAFICO} height={260} data={secao.meses}
      margin={{ top: 12, right: 24, bottom: 0, left: 0 }}>
      <CartesianGrid {...GRADE} />
      <XAxis dataKey="mes" tickFormatter={mesCurto} {...EIXO} />
      <YAxis yAxisId="mortes" {...EIXO} tickFormatter={(valor) => numero(Number(valor))} />
      <YAxis yAxisId="taxa" orientation="right" {...EIXO} tickFormatter={(valor) => percentual(Number(valor), 1)} />
      <Legend {...LEGENDA} />
      <Bar {...COLUNA} yAxisId="mortes" dataKey="previsto" name="Mortes previstas" fill="var(--cor-planejado)"
        isAnimationActive={false} />
      <Bar {...COLUNA} yAxisId="mortes" dataKey="realizado" name="Mortes realizadas" fill="var(--cor-despesa)"
        isAnimationActive={false} />
      <Line yAxisId="taxa" dataKey="mortalidade_acumulada" name="Mortalidade acumulada"
        stroke="var(--cor-marinho)" strokeWidth={2.5} isAnimationActive={false} />
    </ComposedChart>
  );
}

function MortalidadePorGrupo({ secao, rotuloDaMeta }: { secao: SecaoMortes; rotuloDaMeta: string }) {
  return (
    <QuadroAnalitico titulo="Mortalidade por grupo">
      <table className="tabela-analitica">
        <thead>
          <tr>
            <th scope="col">Grupo</th>
            <th scope="col">Prevista</th>
            <th scope="col">Realizada</th>
            <th scope="col">{rotuloDaMeta}</th>
          </tr>
        </thead>
        <tbody>
          {secao.por_grupo.map((grupo) => (
            <tr key={grupo.grupo} className={grupo.grupo === "GERAL" ? "linha-total" : undefined}>
              <th scope="row">{grupo.grupo}</th>
              <td>{percentual(grupo.previsto ?? null, 2)}</td>
              <td className="destaque">{percentual(grupo.realizado ?? null, 2)}</td>
              <td>{percentual(grupo.meta_periodo ?? null, 2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </QuadroAnalitico>
  );
}

function CausasNoPeriodo({ secao }: { secao: SecaoMortes }) {
  return (
    <QuadroAnalitico titulo="Causas no período">
      <table className="tabela-analitica">
        <thead>
          <tr>
            <th scope="col">Causa</th>
            <th scope="col">Bezerros</th>
            <th scope="col">Jovens</th>
            <th scope="col">Adultos</th>
            <th scope="col">Total</th>
            <th scope="col">%</th>
          </tr>
        </thead>
        <tbody>
          {secao.causas.map((causa) => (
            <tr key={causa.causa}>
              <th scope="row">{causa.causa}</th>
              <td>{causa.bezerros ? numero(causa.bezerros) : ""}</td>
              <td>{causa.jovens ? numero(causa.jovens) : ""}</td>
              <td>{causa.adultos ? numero(causa.adultos) : ""}</td>
              <td className="destaque">{numero(causa.total)}</td>
              <td>{percentual(causa.participacao ?? null)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </QuadroAnalitico>
  );
}
