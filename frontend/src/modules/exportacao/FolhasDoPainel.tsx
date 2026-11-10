import { useArea } from "../../core/auth/AreaAutenticada";
import { CAPA, rotuloDaPaginaDoPdf } from "../../core/ui/paginasDoBoletim";
import { cabecalhoDoBoletim } from "../../logic/analitico";
import { identificacaoDoBoletim } from "../../logic/boletim";
import { mesAtual } from "../../logic/meses";
import { useMovimentacao } from "../rebanho/api";
import { FolhaDaNota } from "./analitico/FolhaDaNota";
import { CapaDoBoletim } from "./boletim/CapaDoBoletim";
import { PAGINA_DO_PDF } from "./paginasDoPdf";

type Props = { paginas: string[]; cidade: string; notaInicial: string; notaFinal: string };

// As folhas do modo Padrão: a capa do boletim de resultados (a mesma do Boletim Resumido), a nota técnica do começo, as
// páginas do painel como estão na tela e a nota do fim.
export function FolhasDoPainel({ paginas, cidade, notaInicial, notaFinal }: Props) {
  const { escopo, filtro } = useArea();
  const cabecalho = cabecalhoDoBoletim(filtro, escopo.fazendas);
  const paginasDoPainel = paginas.filter((chave) => chave !== CAPA);
  return (
    <>
      {paginas.includes(CAPA) && (
        <CapaDoPainel cidade={cidade} conteudo={paginasDoPainel.map(rotuloDaPaginaDoPdf)} />
      )}
      <FolhaDaNota texto={notaInicial} cabecalho={cabecalho} />
      {paginasDoPainel.map((chave) => (
        <div key={chave} className="folha-pdf">
          {PAGINA_DO_PDF[chave]}
        </div>
      ))}
      <FolhaDaNota texto={notaFinal} cabecalho={cabecalho} />
    </>
  );
}

// O planejamento em uso vem da Movimentação (a mesma consulta da página, que o PDF já pede quando ela vai junto).
function CapaDoPainel({ cidade, conteudo }: { cidade: string; conteudo: string[] }) {
  const { escopo, filtro, consulta } = useArea();
  const movimentacao = useMovimentacao(consulta);
  if (movimentacao.data === undefined) {
    return null;
  }
  const hoje = mesAtual();
  const datas = { inicio_do_periodo: `${consulta.inicio}-01`, mes_referencia: `${consulta.fim}-01`,
    plano: movimentacao.data.plano };
  const identificacao = identificacaoDoBoletim(filtro, escopo.fazendas, datas, cidade, hoje);
  return (
    <div className="folha-pdf folha-boletim">
      <CapaDoBoletim identificacao={identificacao} conteudo={conteudo} mesDaAnalise={hoje} />
    </div>
  );
}
