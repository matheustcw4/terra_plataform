import { useState, type ReactNode } from "react";
import { Link, NavLink, useLocation } from "react-router";
import globoBranco from "../../assets/bi/terra-globo-branco.png";
import logoBranco from "../../assets/bi/terra-logo-branco.png";
import logo from "../../assets/bi/terra-logo.png";
import { useArea } from "../auth/AreaAutenticada";
import { BotaoAtualizarAgora } from "./BotaoAtualizarAgora";
import { Icone } from "./Icone";
import { lembrarRailRecolhido, railRecolhidoLembrado } from "./preferencias";

export type ItemDoMenu = { caminho: string; rotulo: string; icone: string };
export type GrupoDoMenu = { titulo: string; itens: ItemDoMenu[] };

type Props = {
  secao: string; // a primeira migalha do topo ("Boletim", "Administração")
  grupos: GrupoDoMenu[];
  titulo: string;
  subtitulo?: string;
  icone?: string; // o desenho do menu ao lado do título (nome em core/ui/Icone)
  controles?: ReactNode; // o que fica à direita do topo
  children: ReactNode;
};

// A casca das telas, com a base visual do AgTechLab nas cores da Terra: menu lateral (recolhível; no celular vira
// gaveta), topo com as migalhas e os controles, e o cabeçalho da página. O logo só aparece no cabeçalho do PDF (no
// painel ele já está no menu lateral). O "Atualizar agora" do admin fica aqui para estar em todas as telas.
export function Casca({ secao, grupos, titulo, subtitulo, icone, controles, children }: Props) {
  const { search } = useLocation(); // os links levam o filtro junto
  const { escopo } = useArea();
  const [recolhido, trocarRecolhido] = useState(railRecolhidoLembrado);
  const [gavetaAberta, trocarGavetaAberta] = useState(false);
  const expandido = !recolhido || gavetaAberta;

  function alternarRail() {
    trocarRecolhido(!recolhido);
    lembrarRailRecolhido(!recolhido);
  }

  let classesDoRail = "rail";
  if (recolhido && !gavetaAberta) {
    classesDoRail += " recolhido";
  }
  if (gavetaAberta) {
    classesDoRail += " aberto";
  }

  return (
    <div className="casca">
      <aside className={classesDoRail} aria-label={`Menu: ${secao}`}>
        <Link className="rail-marca" to={{ pathname: "/menu", search }} title="Voltar ao MENU">
          <img src={expandido ? logoBranco : globoBranco} alt="Terra Desenvolvimento Agropecuário"
            className={expandido ? "rail-logo" : "rail-globo"} />
        </Link>
        <nav className="rail-nav">
          {grupos.map((grupo) => (
            <div key={grupo.titulo} className="rail-grupo">
              <span className="rail-grupo-titulo">{grupo.titulo}</span>
              {grupo.itens.map((item) => (
                <NavLink key={item.caminho} to={{ pathname: item.caminho, search }} className="rail-item"
                  title={item.rotulo} onClick={() => trocarGavetaAberta(false)}>
                  <Icone nome={item.icone} />
                  <span>{item.rotulo}</span>
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <button type="button" className="rail-recolher" onClick={alternarRail} aria-expanded={!recolhido}
          title={recolhido ? "Expandir o menu" : "Reduzir o menu"}>
          <Icone nome="recolher" />
          <span>{recolhido ? "Expandir" : "Reduzir"}</span>
        </button>
      </aside>
      <button type="button" className={gavetaAberta ? "gaveta-fundo ativo" : "gaveta-fundo"} aria-label="Fechar o menu"
        onClick={() => trocarGavetaAberta(false)} />
      <div className="casca-principal">
        <header className="topo">
          <button type="button" className="topo-menu" aria-label="Abrir o menu" onClick={() => trocarGavetaAberta(true)}>
            <Icone nome="menu" tamanho={20} />
          </button>
          <div className="topo-migalhas">
            <span>{secao}</span>
            <span className="separador">/</span>
            <strong>{titulo}</strong>
          </div>
          <div className="topo-controles">
            {escopo.usuario.eh_admin && <BotaoAtualizarAgora />}
            {controles}
          </div>
        </header>
        <main className="area-da-pagina">
          <header className="cabecalho-da-pagina">
            <img className="cabecalho-logo-pdf" src={logo} alt="" />
            {icone && (
              <span className="cabecalho-icone">
                <Icone nome={icone} tamanho={24} />
              </span>
            )}
            <div className="cabecalho-textos">
              <h1>{titulo}</h1>
              {subtitulo && <p>{subtitulo}</p>}
            </div>
          </header>
          {children}
        </main>
      </div>
    </div>
  );
}
