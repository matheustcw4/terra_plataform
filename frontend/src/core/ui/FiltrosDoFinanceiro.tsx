import { SeletorMultiplo } from "../../componentes/menu/SeletorMultiplo";
import {
  classificacoesDasFazendas,
  contasDasFazendas,
  mostrarOFiltro,
  type Opcao,
  resumoDaEscolha,
  tiposDasFazendas,
} from "../../logic/filtrosDoFinanceiro";
import { useArea } from "../auth/AreaAutenticada";

type PropsDoCampo = {
  nome: string;
  opcoes: Opcao[];
  marcados: string[];
  rotuloDeTodos: string;
  aviso?: string;
  aoTrocar: (marcados: string[]) => void;
};

function CampoDoFiltro({ nome, opcoes, marcados, rotuloDeTodos, aviso, aoTrocar }: PropsDoCampo) {
  if (!mostrarOFiltro(opcoes, marcados)) {
    return null;
  }
  return (
    <div className="campo filtro-do-financeiro">
      <span>{nome}</span>
      <SeletorMultiplo nome={nome} opcoes={opcoes} marcados={marcados} rotuloDeTodos={rotuloDeTodos}
        resumo={resumoDaEscolha(marcados, opcoes, rotuloDeTodos)} colunas={1} aoTrocar={aoTrocar} />
      {aviso && marcados.length > 0 && <small className="filtro-do-financeiro-aviso">{aviso}</small>}
    </div>
  );
}

// O tipo de atividade, a classificação e a conta bancária do financeiro (pedido do usuário, 18/11/2026), no MENU e no
// topo das páginas Previsto × Realizado e Financeiro, como o status: são do filtro, valem nas duas páginas e no PDF.
// Cada um só aparece quando as fazendas do filtro têm mais de uma opção.
export function FiltrosDoFinanceiro() {
  const { escopo, filtro, consulta, trocarFiltro } = useArea();
  const doFiltro = escopo.fazendas.filter((fazenda) => consulta.fazendas.includes(fazenda.id));
  const tipos = tiposDasFazendas(doFiltro, escopo.opcoes_do_financeiro.tipos_de_atividade);
  const classificacoes = classificacoesDasFazendas(doFiltro, escopo.opcoes_do_financeiro.classificacoes);
  return (
    <>
      <CampoDoFiltro nome="Tipo de atividade" opcoes={tipos} marcados={filtro.atividades} rotuloDeTodos="Todos"
        aoTrocar={(marcados) => trocarFiltro({ ...filtro, atividades: marcados })} />
      <CampoDoFiltro nome="Classificação" opcoes={classificacoes} marcados={filtro.classificacoes} rotuloDeTodos="Todas"
        aoTrocar={(marcados) => trocarFiltro({ ...filtro, classificacoes: marcados })} />
      <CampoDoFiltro nome="Conta bancária" opcoes={contasDasFazendas(doFiltro)} marcados={filtro.contas}
        rotuloDeTodos="Todas" aviso="O planejado não tem conta bancária: o filtro recorta só o realizado."
        aoTrocar={(marcados) => trocarFiltro({ ...filtro, contas: marcados })} />
    </>
  );
}
