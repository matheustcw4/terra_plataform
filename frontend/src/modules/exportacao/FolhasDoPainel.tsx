import { useArea } from "../../core/auth/AreaAutenticada";
import { CAPA } from "../../core/ui/paginasDoBoletim";
import { cabecalhoDoBoletim } from "../../logic/analitico";
import { FolhaDaNota } from "./analitico/FolhaDaNota";
import { Capa } from "./Capa";
import { PAGINA_DO_PDF } from "./paginasDoPdf";

type Props = { paginas: string[]; cidade: string; notaInicial: string; notaFinal: string };

// As folhas do modo Padrão: a capa, a nota técnica do começo, as páginas do painel como estão na tela e a nota do fim.
export function FolhasDoPainel({ paginas, cidade, notaInicial, notaFinal }: Props) {
  const { escopo, filtro } = useArea();
  const cabecalho = cabecalhoDoBoletim(filtro, escopo.fazendas);
  return (
    <>
      {paginas.includes(CAPA) && (
        <div className="folha-pdf folha-capa">
          <Capa cidade={cidade} />
        </div>
      )}
      <FolhaDaNota texto={notaInicial} cabecalho={cabecalho} />
      {paginas
        .filter((chave) => chave !== CAPA)
        .map((chave) => (
          <div key={chave} className="folha-pdf">
            {PAGINA_DO_PDF[chave]}
          </div>
        ))}
      <FolhaDaNota texto={notaFinal} cabecalho={cabecalho} />
    </>
  );
}
