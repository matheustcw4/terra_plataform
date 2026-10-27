import type { LinhaDoPlacar } from "../../../core/api/tipos";
import { mostra, type ParteDoAssunto, recortar } from "../../../logic/personalizado";
import { QuadroAnalitico, type Rotulos } from "./FolhaAnalitica";
import { LegendaDoStatus } from "./LegendaDoStatus";
import { TabelaDoPlacar } from "./TabelaDoPlacar";

type Props = { linhas: LinhaDoPlacar[]; partes: ParteDoAssunto[]; rotulos: Rotulos; faixa?: [number, number] };

// O placar zootécnico: todos os indicadores do mês e do acumulado contra o previsto, com o status e a meta (uma peça).
export function ConteudoPlacar({ linhas, partes, rotulos, faixa }: Props) {
  const pecas = [];
  if (mostra(partes, "previsto")) {
    pecas.push(
      <QuadroAnalitico key="placar" titulo="Previsto × realizado">
        <TabelaDoPlacar linhas={linhas} rotuloDoMes={rotulos.mes} rotuloDaMeta={rotulos.meta} />
        {mostra(partes, "notas") && <LegendaDoStatus />}
      </QuadroAnalitico>,
    );
  }
  return <>{recortar(pecas, faixa)}</>;
}
