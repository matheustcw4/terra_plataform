import { useState } from "react";
import type { GrupoDoPrevisto, PrevistoRealizado } from "../../core/api/tipos";
import { alternarItem } from "../../logic/listas";
import { mesCurto } from "../../logic/meses";
import { CelulasDaComparacao } from "./CelulasDaComparacao";

// A matriz do BI: cada classificação numa linha que abre as contas dela (clicando), as colunas MENSAL (último mês do
// período) e ACUMULADO (o período todo) e, no fim, o resultado. Começa com as classificações fechadas, como o BI.
export function TabelaDoPrevisto({ dados }: { dados: PrevistoRealizado }) {
  const [abertos, trocarAbertos] = useState<string[]>([]);
  return (
    <div className="painel-grafico tabela-rolavel">
      <table className="tabela-previsto">
        <thead>
          <tr>
            <th scope="col" rowSpan={2}>Classificação / conta</th>
            <th scope="colgroup" colSpan={3} className="inicio-do-bloco">MENSAL · {mesCurto(dados.ultimo_mes)}</th>
            <th scope="colgroup" colSpan={3} className="inicio-do-bloco">
              ACUMULADO · {mesCurto(dados.periodo.inicio)} a {mesCurto(dados.periodo.fim)}
            </th>
          </tr>
          <tr>
            <th scope="col" className="inicio-do-bloco">Realizado</th>
            <th scope="col">Planejado</th>
            <th scope="col">% Variação</th>
            <th scope="col" className="inicio-do-bloco">Realizado</th>
            <th scope="col">Planejado</th>
            <th scope="col">% Variação</th>
          </tr>
        </thead>
        <tbody>
          {dados.grupos.map((grupo) => (
            <LinhasDoGrupo key={grupo.classificacao} grupo={grupo} aberto={abertos.includes(grupo.classificacao)}
              alternar={() => trocarAbertos(alternarItem(abertos, grupo.classificacao))} />
          ))}
        </tbody>
        <tfoot>
          <tr className="linha-resultado">
            <th scope="row">RESULTADO</th>
            <CelulasDaComparacao comparacao={dados.resultado.mensal} inicioDoBloco />
            <CelulasDaComparacao comparacao={dados.resultado.acumulado} inicioDoBloco />
          </tr>
        </tfoot>
      </table>
    </div>
  );
}

type GrupoProps = { grupo: GrupoDoPrevisto; aberto: boolean; alternar: () => void };

// A linha da classificação e, quando aberta, as contas. O desembolso é só subtotal (investimentos + custeio).
function LinhasDoGrupo({ grupo, aberto, alternar }: GrupoProps) {
  const temContas = grupo.contas.length > 0;
  return (
    <>
      <tr className="linha-grupo">
        <th scope="row">
          {temContas && (
            <button type="button" className="botao-abrir" onClick={alternar} aria-expanded={aberto}>
              {aberto ? "−" : "+"}
            </button>
          )}
          {!temContas && <span className="espaco-do-botao" />}
          {grupo.classificacao}
        </th>
        <CelulasDaComparacao comparacao={grupo.total.mensal} inicioDoBloco />
        <CelulasDaComparacao comparacao={grupo.total.acumulado} inicioDoBloco />
      </tr>
      {aberto &&
        grupo.contas.map((conta) => (
          <tr key={conta.nome} className="linha-conta">
            <th scope="row">{conta.nome}</th>
            <CelulasDaComparacao comparacao={conta.mensal} inicioDoBloco />
            <CelulasDaComparacao comparacao={conta.acumulado} inicioDoBloco />
          </tr>
        ))}
    </>
  );
}
