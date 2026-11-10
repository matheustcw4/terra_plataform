import { alternarSituacao, situacoesDasFazendas, situacoesEmUso, SITUACOES } from "../../logic/filtro";
import { useArea } from "../auth/AreaAutenticada";

// O status dos lançamentos do financeiro (pedido do usuário, 10/11/2026), no MENU e no topo das páginas Previsto ×
// Realizado e Financeiro: conciliado, pago e em aberto, de seleção múltipla (sem escolha, os pagos, conciliados ou
// não). Só aparece quando as fazendas do filtro têm mais de uma situação (a planilha só tem o pago). É do filtro:
// vale nas duas páginas e no PDF.
export function FiltroDoStatus() {
  const { escopo, filtro, consulta, trocarFiltro } = useArea();
  const doFiltro = escopo.fazendas.filter((fazenda) => consulta.fazendas.includes(fazenda.id));
  let existentes = situacoesDasFazendas(doFiltro);
  if (existentes.length < 2 && filtro.situacoes.length === 0) {
    return null;
  }
  // uma escolha que veio de outro filtro (pelo link) continua desfazível, mesmo onde não há o que filtrar
  if (existentes.length < 2) {
    existentes = SITUACOES.map((opcao) => opcao.valor);
  }
  const emUso = situacoesEmUso(filtro);
  return (
    <fieldset className="campo filtro-do-status">
      <legend>Status dos lançamentos</legend>
      <div className="filtro-do-status-opcoes">
        {SITUACOES.filter((opcao) => existentes.includes(opcao.valor)).map((opcao) => (
          <label key={opcao.valor}>
            <input type="checkbox" checked={emUso.includes(opcao.valor)}
              onChange={() => trocarFiltro({ ...filtro, situacoes: alternarSituacao(filtro, opcao.valor) })} />
            {opcao.rotulo}
          </label>
        ))}
      </div>
    </fieldset>
  );
}
