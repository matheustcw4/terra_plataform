import type { SecaoTransferencias } from "../../../core/api/tipos";
import { mostra, type ParteDoAssunto, recortar } from "../../../logic/personalizado";
import { GraficoPorMes, TabelaDeLotes } from "./ConteudoDeLotes";
import { QuadroAnalitico, type Rotulos } from "./FolhaAnalitica";
import { TabelaDoPlacar } from "./TabelaDoPlacar";

type Props = { secao: SecaoTransferencias; partes: ParteDoAssunto[]; rotulos: Rotulos; faixa?: [number, number] };

// Transferências: as entradas e as saídas do mês (de qual fazenda vieram, para qual foram), as cabeças mês a mês de
// cada lado e o resumo do acumulado, em blocos ENTRADAS e SAÍDAS. Cada quadro é uma peça; `faixa` escolhe as peças.
export function ConteudoTransferencias({ secao, partes, rotulos, faixa }: Props) {
  const pecas = [];
  if (mostra(partes, "lancamentos")) {
    pecas.push(
      <QuadroAnalitico key="entradas" titulo={`Entradas de ${rotulos.mes}`}>
        <TabelaDeLotes secao={secao.entradas} />
      </QuadroAnalitico>,
    );
    pecas.push(
      <QuadroAnalitico key="saidas" titulo={`Saídas de ${rotulos.mes}`}>
        <TabelaDeLotes secao={secao.saidas} />
      </QuadroAnalitico>,
    );
  }
  if (mostra(partes, "graficos")) {
    pecas.push(
      <div key="graficos" className="graficos-lado-a-lado">
        <QuadroAnalitico titulo="Entradas por mês: previsto × realizado">
          <GraficoPorMes meses={secao.entradas.meses} />
        </QuadroAnalitico>
        <QuadroAnalitico titulo="Saídas por mês: previsto × realizado">
          <GraficoPorMes meses={secao.saidas.meses} />
        </QuadroAnalitico>
      </div>,
    );
  }
  if (mostra(partes, "previsto")) {
    pecas.push(
      <QuadroAnalitico key="previsto" titulo="Previsto × realizado">
        <TabelaDoPlacar linhas={[...secao.entradas.resumo, ...secao.saidas.resumo]} rotuloDoMes={rotulos.mes}
          rotuloDaMeta={rotulos.meta} />
      </QuadroAnalitico>,
    );
  }
  return <>{recortar(pecas, faixa)}</>;
}
