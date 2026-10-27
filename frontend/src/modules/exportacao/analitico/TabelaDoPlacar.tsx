import type { Comparado, LinhaDoPlacar } from "../../../core/api/tipos";
import { blocosDoPlacar, valorComUnidade, variacaoComUnidade } from "../../../logic/analitico";
import { percentual } from "../../../logic/formatar";
import { Status } from "./Status";

type Props = {
  linhas: LinhaDoPlacar[];
  rotuloDoMes: string; // "set/26"
  rotuloDaMeta: string; // "Meta da safra"
  semGrupo?: boolean; // um bloco só (o resumo das vendas): sem a linha do grupo
};

// O placar (como no boletim de exemplo): cada indicador com previsto, realizado, variação e status no mês e no
// acumulado, e a meta do período. Os blocos seguem o grupo do indicador (REBANHO, VENDAS ABATE...).
export function TabelaDoPlacar({ linhas, rotuloDoMes, rotuloDaMeta, semGrupo = false }: Props) {
  return (
    <table className="tabela-analitica tabela-placar">
      <thead>
        <tr>
          <th rowSpan={2} scope="col">Indicador</th>
          <th rowSpan={2} scope="col">Unid.</th>
          <th colSpan={5} scope="colgroup" className="inicio-do-bloco">{rotuloDoMes}</th>
          <th colSpan={5} scope="colgroup" className="inicio-do-bloco">Acumulado</th>
          <th rowSpan={2} scope="col" className="inicio-do-bloco">{rotuloDaMeta}</th>
        </tr>
        <tr>
          <CabecalhoDoRecorte />
          <CabecalhoDoRecorte />
        </tr>
      </thead>
      <tbody>
        {blocosDoPlacar(linhas).map((bloco) => (
          <BlocoDoPlacar key={bloco.grupo} grupo={bloco.grupo} linhas={bloco.linhas} semGrupo={semGrupo} />
        ))}
      </tbody>
    </table>
  );
}

function CabecalhoDoRecorte() {
  return (
    <>
      <th scope="col" className="inicio-do-bloco">Previsto</th>
      <th scope="col">Realizado</th>
      <th scope="col">Variação</th>
      <th scope="col">%</th>
      <th scope="col">Status</th>
    </>
  );
}

function BlocoDoPlacar({ grupo, linhas, semGrupo }: { grupo: string; linhas: LinhaDoPlacar[]; semGrupo: boolean }) {
  return (
    <>
      {!semGrupo && (
        <tr className="linha-do-grupo">
          <th colSpan={13} scope="rowgroup">{grupo}</th>
        </tr>
      )}
      {linhas.map((linha) => (
        <tr key={`${linha.grupo}-${linha.indicador}`}>
          <th scope="row">{linha.indicador}</th>
          <td className="unidade">{linha.unidade}</td>
          <CelulasDoRecorte valores={linha.mes} unidade={linha.unidade} />
          <CelulasDoRecorte valores={linha.acumulado} unidade={linha.unidade} />
          <td className="inicio-do-bloco">{valorComUnidade(linha.meta_periodo, linha.unidade)}</td>
        </tr>
      ))}
    </>
  );
}

function CelulasDoRecorte({ valores, unidade }: { valores: Comparado; unidade: string }) {
  return (
    <>
      <td className="inicio-do-bloco">{valorComUnidade(valores.previsto, unidade)}</td>
      <td className="destaque">{valorComUnidade(valores.realizado, unidade)}</td>
      <td className="apagado">{variacaoComUnidade(valores.variacao, unidade)}</td>
      <td className="apagado">{percentual(valores.variacao_percentual ?? null, 1)}</td>
      <td className="status">
        <Status status={valores.status} />
      </td>
    </>
  );
}
