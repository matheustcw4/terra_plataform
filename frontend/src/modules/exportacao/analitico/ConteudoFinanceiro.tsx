import type { SecaoFinanceiro } from "../../../core/api/tipos";
import { dinheiro } from "../../../logic/formatar";
import { mostra, type ParteDoAssunto, recortar } from "../../../logic/personalizado";
import { QuadroAnalitico, type Rotulos } from "./FolhaAnalitica";
import { LegendaDoStatus } from "./LegendaDoStatus";
import { TabelaDoPlacar } from "./TabelaDoPlacar";

type Props = { secao: SecaoFinanceiro; partes: ParteDoAssunto[]; rotulos: Rotulos; faixa?: [number, number] };

// Financeiro: o placar (receitas, desembolso, caixa, custo por cabeça, preço da @) e para onde foi o dinheiro, centro
// de custo a centro de custo, no mês e no acumulado. Cada quadro é uma peça; `faixa` escolhe as peças.
export function ConteudoFinanceiro({ secao, partes, rotulos, faixa }: Props) {
  const pecas = [];
  if (mostra(partes, "previsto")) {
    pecas.push(<PlacarFinanceiro key="previsto" secao={secao} partes={partes} rotulos={rotulos} />);
  }
  if (mostra(partes, "resumo")) {
    pecas.push(<CentrosDeCusto key="centros" secao={secao} rotulos={rotulos} />);
  }
  return <>{recortar(pecas, faixa)}</>;
}

function PlacarFinanceiro({ secao, partes, rotulos }: Props) {
  return (
    <QuadroAnalitico titulo="Previsto × realizado">
      <TabelaDoPlacar linhas={secao.placar} rotuloDoMes={rotulos.mes} rotuloDaMeta={rotulos.meta} />
      {mostra(partes, "notas") && <LegendaDoStatus />}
      {mostra(partes, "notas") && (
        <p className="nota">
          O desembolso é o da página Financeiro: as contas marcadas como desembolso no plano de contas, que podem
          incluir financiamentos pagos. Na folha do caixa os financiamentos ficam em Outros débitos, por isso o
          desembolso de lá pode ser menor. O saldo do caixa não tem previsto (o BI não planeja o saldo).
        </p>
      )}
    </QuadroAnalitico>
  );
}

function CentrosDeCusto({ secao, rotulos }: { secao: SecaoFinanceiro; rotulos: Rotulos }) {
  return (
    <QuadroAnalitico titulo="Desembolso por centro de custo">
      {secao.centros.length === 0 && <p className="nota">Nenhum desembolso lançado no período.</p>}
      {secao.centros.length > 0 && (
        <table className="tabela-analitica tabela-centros">
          <thead>
            <tr>
              <th scope="col">Centro de custo</th>
              <th scope="col">{rotulos.mes}</th>
              <th scope="col">Acumulado</th>
              <th scope="col">R$/cab/mês (acumulado)</th>
            </tr>
          </thead>
          <tbody>
            {secao.centros.map((centro) => (
              <tr key={centro.centro_custo}>
                <th scope="row">{centro.centro_custo}</th>
                <td>{centro.valor_mes === 0 ? "" : dinheiro(centro.valor_mes)}</td>
                <td className="destaque">{dinheiro(centro.valor_acumulado)}</td>
                <td>{dinheiro(centro.por_cabeca_mes ?? null, 2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </QuadroAnalitico>
  );
}
