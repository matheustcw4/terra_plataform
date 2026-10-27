import type { ReactNode } from "react";
import { Link, useLocation } from "react-router";
import { nomeDaSelecao, rotuloDaOrigem, rotuloDoFiltro } from "../../logic/filtro";
import { useArea } from "../auth/AreaAutenticada";
import { BotaoSair } from "../auth/BotaoSair";
import { BotaoExportarPdf } from "./BotaoExportarPdf";
import { Casca } from "./Casca";
import { Icone } from "./Icone";
import { gruposDoBoletim, PAGINAS_DO_BOLETIM } from "./paginasDoBoletim";

type Props = {
  caminho: string; // a página no menu (PAGINAS_DO_BOLETIM): dá o título e o ícone, na tela e na folha do PDF
  children: ReactNode;
};

// A moldura das páginas do boletim: a casca com o menu das páginas, o filtro em uso no topo (os filtros continuam só
// no MENU; o "Trocar" leva para lá) e o "Exportar PDF". A página vem do caminho dela, e não da URL: na exportação a
// URL é a do PDF.
export function Moldura({ caminho, children }: Props) {
  const { escopo, filtro } = useArea();
  const { search } = useLocation();
  const pagina = PAGINAS_DO_BOLETIM.find((candidata) => candidata.caminho === caminho);
  const selecao = nomeDaSelecao(filtro, escopo.fazendas);
  const subtitulo = `${selecao} · ${filtro.cliente} · ${rotuloDaOrigem(filtro.origem)} · ${rotuloDoFiltro(filtro)}`;
  const controles = (
    <>
      <Link className="filtro-em-uso" to={{ pathname: "/menu", search }} title="Trocar o filtro no MENU">
        <Icone nome="filtro" tamanho={15} />
        <span>
          {selecao} · {rotuloDoFiltro(filtro)}
        </span>
        <strong>Trocar</strong>
      </Link>
      <BotaoExportarPdf />
      <span className="topo-usuario">{escopo.usuario.nome}</span>
      <BotaoSair />
    </>
  );
  return (
    <Casca secao="Boletim" grupos={gruposDoBoletim(escopo.usuario.eh_admin)}
      titulo={pagina?.rotulo ?? "Boletim"} subtitulo={subtitulo} icone={pagina?.icone} controles={controles}>
      {children}
    </Casca>
  );
}
