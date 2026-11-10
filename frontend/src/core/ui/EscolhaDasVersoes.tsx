import { type ReactNode, useState } from "react";
import {
  comMaisRecente,
  comVersaoAlternada,
  type EscolhaDoPlano,
  maisRecenteEmTodas,
  resumoDasVersoes,
  semPlanejamento,
} from "../../logic/versaoDoPlano";
import type { VersoesDaFazenda } from "../api/tipos";
import { useArea } from "../auth/AreaAutenticada";
import { type AcoesDaJanela, JanelaDasVersoes } from "./JanelaDasVersoes";

type Props = {
  escolha: { fazendas: VersoesDaFazenda[]; em_uso: string[] }; // o `plano` das páginas com meta ou o `previsto`
  children?: ReactNode; // campos que vêm antes (o tipo do orçamento e o status, nas páginas do financeiro)
};

// A versão do planejamento no topo das páginas com meta e no MENU: diz qual versão está valendo e um botão abre a
// janela com todas as fazendas do filtro e a escolha de cada uma, de seleção múltipla e com "nenhum planejamento"
// (pedido do usuário, 10/11/2026: escolher por fazenda sem encher a tela de campos). A escolha é do filtro: vale em
// todas as páginas.
export function EscolhaDasVersoes({ escolha, children }: Props) {
  const { filtro, trocarFiltro } = useArea();
  const [aberta, setAberta] = useState(false);
  const temEscolha = escolha.fazendas.some((fazenda) => fazenda.versoes.length > 0);
  if (!children && !temEscolha && escolha.em_uso.length === 0) {
    return null;
  }

  const atual: EscolhaDoPlano = { versoes: filtro.versoes, semPlano: filtro.semPlano };
  function guardar(nova: EscolhaDoPlano) {
    trocarFiltro({ ...filtro, versoes: nova.versoes, semPlano: nova.semPlano });
  }
  const acoes: AcoesDaJanela = {
    maisRecente: (fazenda) => guardar(comMaisRecente(atual, fazenda)),
    alternarVersao: (fazenda, versao) => guardar(comVersaoAlternada(atual, fazenda, versao)),
    nenhum: (fazenda) => guardar(semPlanejamento(atual, fazenda)),
    maisRecenteEmTodas: () => guardar(maisRecenteEmTodas(atual, escolha.fazendas)),
  };

  return (
    <div className="seletor-do-previsto">
      {children}
      {temEscolha && (
        <div className="campo">
          <span>Versão do planejamento</span>
          <button type="button" className="botao-das-versoes" onClick={() => setAberta(true)}>
            {resumoDasVersoes(escolha.fazendas)}
          </button>
        </div>
      )}
      {escolha.em_uso.length > 0 && (
        <p className="versao-em-uso">
          <span>Planejamento em uso</span>
          {escolha.em_uso.join("; ")}
        </p>
      )}
      {aberta && <JanelaDasVersoes fazendas={escolha.fazendas} acoes={acoes} aoFechar={() => setAberta(false)} />}
    </div>
  );
}
