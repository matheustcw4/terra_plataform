import type { SecaoDeLotes } from "../../../core/api/tipos";
import { valorComUnidade } from "../../../logic/analitico";
import { linhaDoIndicador } from "../../../logic/boletim";

type Props = { secao: SecaoDeLotes; indicadores: string[] };

// Alguns indicadores de um lote no acumulado, realizado e planejado (transferências e nascimentos).
export function ValoresDoLote({ secao, indicadores }: Props) {
  return (
    <dl className="boletim-valores">
      {indicadores.map((indicador) => (
        <ValorDoIndicador key={indicador} secao={secao} indicador={indicador} />
      ))}
    </dl>
  );
}

function ValorDoIndicador({ secao, indicador }: { secao: SecaoDeLotes; indicador: string }) {
  const linha = linhaDoIndicador(secao.resumo, indicador);
  if (linha === null) {
    return null;
  }
  return (
    <div>
      <dt>{indicador}</dt>
      <dd>
        <strong>{valorComUnidade(linha.acumulado.realizado, linha.unidade)}</strong>
        {linha.acumulado.previsto !== null && (
          <span> · plan. {valorComUnidade(linha.acumulado.previsto, linha.unidade)}</span>
        )}
      </dd>
    </div>
  );
}
