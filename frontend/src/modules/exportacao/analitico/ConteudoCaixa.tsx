import type { Comparacao, GrupoDoPrevisto, SecaoCaixa } from "../../../core/api/tipos";
import { dinheiro, percentual } from "../../../logic/formatar";
import { mostra, type ParteDoAssunto, recortar } from "../../../logic/personalizado";
import { QuadroAnalitico, type Rotulos } from "./FolhaAnalitica";
import { LegendaDoStatus } from "./LegendaDoStatus";
import { Status } from "./Status";

type Props = { secao: SecaoCaixa; partes: ParteDoAssunto[]; rotulos: Rotulos; faixa?: [number, number] };

// Fluxo de caixa: a matriz do Previsto × Realizado com todas as contas abertas (no papel não dá para clicar), o mês
// de referência e o acumulado, com o semáforo de cada linha (uma peça; `faixa` escolhe as peças).
export function ConteudoCaixa({ secao, partes, rotulos, faixa }: Props) {
  const pecas = [];
  if (mostra(partes, "previsto")) {
    pecas.push(<MatrizDoCaixa key="matriz" secao={secao} partes={partes} rotulos={rotulos} />);
  }
  return <>{recortar(pecas, faixa)}</>;
}

function MatrizDoCaixa({ secao, partes, rotulos }: Props) {
  const dados = secao.previsto_realizado;
  return (
    <QuadroAnalitico titulo="Contas do mês e do acumulado">
      <table className="tabela-analitica tabela-caixa">
        <thead>
          <tr>
            <th rowSpan={2} scope="col">Classificação / conta</th>
            <th colSpan={4} scope="colgroup" className="inicio-do-bloco">{rotulos.mes}</th>
            <th colSpan={4} scope="colgroup" className="inicio-do-bloco">Acumulado</th>
          </tr>
          <tr>
            <CabecalhoDaComparacao />
            <CabecalhoDaComparacao />
          </tr>
        </thead>
        <tbody>
          {dados.grupos.map((grupo) => (
            <LinhasDoGrupo key={grupo.classificacao} grupo={grupo} />
          ))}
          <tr className="linha-total">
            <th scope="row">RESULTADO</th>
            <CelulasDaComparacao comparacao={dados.resultado.mensal} />
            <CelulasDaComparacao comparacao={dados.resultado.acumulado} />
          </tr>
        </tbody>
      </table>
      {mostra(partes, "notas") && <LegendaDoStatus />}
    </QuadroAnalitico>
  );
}

function CabecalhoDaComparacao() {
  return (
    <>
      <th scope="col" className="inicio-do-bloco">Previsto</th>
      <th scope="col">Realizado</th>
      <th scope="col">%</th>
      <th scope="col">Status</th>
    </>
  );
}

function LinhasDoGrupo({ grupo }: { grupo: GrupoDoPrevisto }) {
  return (
    <>
      <tr className="linha-do-grupo-com-valores">
        <th scope="row">{grupo.classificacao}</th>
        <CelulasDaComparacao comparacao={grupo.total.mensal} />
        <CelulasDaComparacao comparacao={grupo.total.acumulado} />
      </tr>
      {grupo.contas.map((conta) => (
        <tr key={conta.nome} className="linha-da-conta">
          <th scope="row">{conta.nome}</th>
          <CelulasDaComparacao comparacao={conta.mensal} />
          <CelulasDaComparacao comparacao={conta.acumulado} />
        </tr>
      ))}
    </>
  );
}

function CelulasDaComparacao({ comparacao }: { comparacao: Comparacao }) {
  return (
    <>
      <td className="inicio-do-bloco">{dinheiro(comparacao.planejado)}</td>
      <td className="destaque">{dinheiro(comparacao.realizado)}</td>
      <td className="apagado">{percentual(comparacao.variacao ?? null, 1)}</td>
      <td className="status">
        <Status status={comparacao.semaforo} />
      </td>
    </>
  );
}
