import { useLocation, useNavigate } from "react-router";
import { useArea } from "../core/auth/AreaAutenticada";
import { BotaoSair } from "../core/auth/BotaoSair";
import { BotaoExportarPdf } from "../core/ui/BotaoExportarPdf";
import { Casca } from "../core/ui/Casca";
import { Painel } from "../core/ui/Painel";
import { gruposDoBoletim } from "../core/ui/paginasDoBoletim";
import { SeletorMultiplo } from "../componentes/menu/SeletorMultiplo";
import {
  anoDoMes,
  anosDisponiveis,
  clientesDoEscopo,
  consultaDoFiltro,
  fazendasDaOrigem,
  fazendasDoCliente,
  filtroDaOrigem,
  filtroDoCliente,
  mesesDoPeriodo,
  mesesEscolhidos,
  nomeDaSelecao,
  ORIGENS,
  rotuloDoAno,
  rotuloDosMeses,
  type Origem,
  type Visao,
} from "../logic/filtro";
import { mesCurto } from "../logic/meses";

// A tela de filtros, como o MENU do BI: cliente, fazendas e meses (os dois de seleção múltipla), forma de visualização
// (safra ou civil) e safra ou ano, na mesma casca das outras páginas.
// O filtro vale para todas as páginas; "Acessar" abre o boletim. "Origem" é temporário (ver logic/filtro.ts).
export function MenuPagina() {
  const { escopo, filtro, trocarFiltro } = useArea();
  const navegar = useNavigate();
  const { search } = useLocation();
  const daOrigem = fazendasDaOrigem(escopo.fazendas, filtro.origem);
  const doCliente = fazendasDoCliente(daOrigem, filtro.cliente);
  const anos = anosDisponiveis(doCliente, filtro.visao);
  const meses = mesesDoPeriodo(filtro.visao, filtro.ano);

  function trocarOrigem(origem: Origem) {
    const novo = filtroDaOrigem(escopo.fazendas, origem);
    if (novo !== null) {
      trocarFiltro(novo);
    }
  }

  function trocarCliente(cliente: string) {
    trocarFiltro(filtroDoCliente(escopo.fazendas, filtro.origem, cliente));
  }

  function trocarFazendas(marcadas: string[]) {
    trocarFiltro({ ...filtro, fazendas: marcadas });
  }

  // Ao trocar safra <-> civil, fica no período que contém o último mês escolhido; os meses marcados só ficam se ainda
  // couberem.
  function trocarVisao(visao: Visao) {
    const ano = anoDoMes(consultaDoFiltro(filtro, escopo.fazendas).fim, visao);
    trocarFiltro({ ...filtro, visao, ano, meses: mesesEscolhidos(filtro.meses, mesesDoPeriodo(visao, ano)) });
  }

  function trocarAno(valor: string) {
    trocarFiltro({ ...filtro, ano: Number(valor), meses: [] });
  }

  function trocarMeses(marcados: string[]) {
    trocarFiltro({ ...filtro, meses: marcados });
  }

  const opcoesDeFazenda = doCliente.map((fazenda) => ({ valor: fazenda.id, rotulo: fazenda.nome }));
  let resumoDasFazendas = "Todas (grupo)";
  if (filtro.fazendas.length > 0) {
    resumoDasFazendas = nomeDaSelecao(filtro, doCliente);
  }
  const opcoesDeMes = meses.map((mes) => ({ valor: mes, rotulo: mesCurto(mes) }));
  let resumoDosMeses = "Todos";
  if (filtro.meses.length > 0) {
    resumoDosMeses = rotuloDosMeses(filtro.meses);
  }

  const controles = (
    <>
      <BotaoExportarPdf />
      <span className="topo-usuario">{escopo.usuario.nome}</span>
      <BotaoSair />
    </>
  );

  return (
    <Casca secao="Boletim" grupos={gruposDoBoletim(escopo.usuario.eh_admin)} titulo="Filtros (MENU)" icone="filtro"
      subtitulo="O que for escolhido aqui vale para todas as páginas do boletim e para o PDF." controles={controles}>
      <div className="menu-filtros">
        <Painel titulo="Cliente e fazenda">
          <div className="menu-bi-campos">
            <label className="menu-bi-campo">
              <span>Origem</span>
              <select value={filtro.origem} onChange={(evento) => trocarOrigem(evento.target.value as Origem)}>
                {ORIGENS.map((opcao) => (
                  <option key={opcao.valor} value={opcao.valor}>
                    {opcao.rotulo}
                  </option>
                ))}
              </select>
            </label>
            <label className="menu-bi-campo">
              <span>Cliente</span>
              <select value={filtro.cliente} onChange={(evento) => trocarCliente(evento.target.value)}>
                {clientesDoEscopo(daOrigem).map((cliente) => (
                  <option key={cliente} value={cliente}>
                    {cliente}
                  </option>
                ))}
              </select>
            </label>
            <div className="menu-bi-campo">
              <span>Fazenda</span>
              <SeletorMultiplo nome="Fazenda" opcoes={opcoesDeFazenda} marcados={filtro.fazendas}
                rotuloDeTodos="Todas (grupo)" resumo={resumoDasFazendas} colunas={1} aoTrocar={trocarFazendas} />
            </div>
          </div>
        </Painel>

        <Painel titulo="Período">
          <div className="menu-bi-campos">
            <div className="menu-bi-campo">
              <span>Forma de visualização</span>
              <div className="abas" role="group" aria-label="Forma de visualização">
                <button type="button" className={filtro.visao === "safra" ? "active" : undefined}
                  aria-pressed={filtro.visao === "safra"} onClick={() => trocarVisao("safra")}>
                  Safra
                </button>
                <button type="button" className={filtro.visao === "civil" ? "active" : undefined}
                  aria-pressed={filtro.visao === "civil"} onClick={() => trocarVisao("civil")}>
                  Cívil
                </button>
              </div>
            </div>
            <label className="menu-bi-campo">
              <span>{filtro.visao === "safra" ? "Safra" : "Ano"}</span>
              <select value={filtro.ano} onChange={(evento) => trocarAno(evento.target.value)}>
                {anos.map((ano) => (
                  <option key={ano} value={ano}>
                    {rotuloDoAno(ano, filtro.visao)}
                  </option>
                ))}
              </select>
            </label>
            <div className="menu-bi-campo">
              <span>Mês</span>
              <SeletorMultiplo nome="Mês" opcoes={opcoesDeMes} marcados={filtro.meses} rotuloDeTodos="Todos"
                resumo={resumoDosMeses} aoTrocar={trocarMeses} />
            </div>
          </div>
        </Painel>
      </div>

      <div className="menu-bi-rodape">
        <button type="button" className="botao" onClick={() => navegar({ pathname: "/rebanho/movimentacao", search })}>
          Acessar o boletim
        </button>
      </div>
    </Casca>
  );
}
