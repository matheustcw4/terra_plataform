import { useState } from "react";
import type { GrupoDoPrevisto, PrevistoRealizado } from "../../core/api/tipos";
import { alternarItem } from "../../logic/listas";
import { mesCurto } from "../../logic/meses";
import { CelulasDaComparacao } from "./CelulasDaComparacao";

// A matriz do BI: cada classificação numa linha com as contas dela embaixo, as colunas MENSAL (último mês do período)
// e ACUMULADO (o período todo) e, no fim, o resultado. Começa com as classificações abertas, na tela e no PDF (pedido
// do usuário, 10/11/2026; o BI começa fechado); clicar fecha e abre. Guarda as fechadas, e não as abertas, para que
// uma classificação que aparece ao trocar o filtro também chegue aberta.
export function TabelaDoPrevisto({ dados }: { dados: PrevistoRealizado }) {
  const [fechados, trocarFechados] = useState<string[]>([]);
  return (
    <div className="painel-grafico tabela-rolavel">
      <table className="tabela-previsto">
        <thead>
          <tr>
            <th scope="col" rowSpan={2}>Classificação / conta</th>
            <th scope="colgroup" colSpan={3} className="inicio-do-bloco bloco-mensal">
              MENSAL · {mesCurto(dados.ultimo_mes)}
            </th>
            <th scope="colgroup" colSpan={3} className="inicio-do-bloco bloco-acumulado">
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
            <LinhasDoGrupo key={grupo.classificacao} grupo={grupo} aberto={!fechados.includes(grupo.classificacao)}
              alternar={() => trocarFechados(alternarItem(fechados, grupo.classificacao))} />
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
