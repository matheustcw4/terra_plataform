import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router";
import { useArea } from "../../core/auth/AreaAutenticada";
import { CAPA, ordemDoModo, type PedidoDePdf } from "../../core/ui/paginasDoBoletim";
import { mesDeReferencia } from "../../logic/analitico";
import { nomeDoArquivo, nomeDoArquivoDoMes } from "../../logic/exportacao";
import { TODAS_AS_PARTES } from "../../logic/personalizado";
import { FolhasAnaliticas } from "./analitico/FolhasAnaliticas";
import { FolhasDoPainel } from "./FolhasDoPainel";
import { PAGINA_DO_PDF } from "./paginasDoPdf";
import { esperarAsPaginas, gerarPdf } from "./pdf";

// Gera o PDF pedido no "Exportar PDF": desenha a capa e as páginas escolhidas, uma abaixo da outra e com o filtro do
// MENU (por trás do aviso de progresso), espera os dados e os gráficos, fotografa cada folha e baixa o arquivo.
// Depois volta para a página de onde a pessoa pediu. Sem pedido (link aberto direto), vai para o MENU.
// Nos modos Analítico e Personalizado as folhas são as A4 do boletim analítico (`analitico/`), em vez das páginas do
// painel; no personalizado, a quantidade de folhas depende de como os blocos se encaixam.
export function ExportacaoPagina() {
  const { state, search } = useLocation();
  const pedido = state as PedidoDePdf | null;
  if (pedido === null || pedido.paginas.length === 0) {
    return <Navigate to={{ pathname: "/menu", search }} replace />;
  }
  return <GerarPdf pedido={pedido} />;
}

function GerarPdf({ pedido }: { pedido: PedidoDePdf }) {
  const { escopo, filtro } = useArea();
  const cliente = useQueryClient();
  const navegar = useNavigate();
  const folhas = useRef<HTMLDivElement>(null);
  const [prontas, setProntas] = useState(0);
  const [total, setTotal] = useState(0);
  const [erro, setErro] = useState<string | null>(null);
  const modo = pedido.modo;
  const doMes = modo === "analitico" || modo === "personalizado";
  let arquivo = nomeDoArquivo(filtro, escopo.fazendas);
  let paginas = pedido.paginas.filter((chave) => chave === CAPA || chave in PAGINA_DO_PDF);
  if (doMes) {
    const tipo = modo === "personalizado" ? "Boletim personalizado" : "Boletim analítico";
    arquivo = nomeDoArquivoDoMes(tipo, filtro, escopo.fazendas, mesDeReferencia(filtro, escopo.fazendas));
    paginas = pedido.paginas.filter((chave) => ordemDoModo(modo).includes(chave));
  }

  useEffect(() => {
    // no modo de desenvolvimento o React monta duas vezes: a primeira montagem é cancelada e não gera nada
    let cancelado = false;
    async function exportar() {
      await esperarAsPaginas(cliente);
      if (cancelado || folhas.current === null) {
        return;
      }
      const falha = folhas.current.querySelector<HTMLElement>("[data-erro]");
      if (falha !== null) {
        throw new Error(falha.dataset.erro);
      }
      const elementos = Array.from(folhas.current.querySelectorAll<HTMLElement>(".folha-pdf"));
      setTotal(elementos.length);
      await gerarPdf(elementos, arquivo, (quantas) => setProntas(quantas));
      if (!cancelado) {
        navegar(-1);
      }
    }
    exportar().catch((falha: unknown) => setErro(falha instanceof Error ? falha.message : String(falha)));
    return () => {
      cancelado = true;
    };
  }, [cliente, arquivo, navegar]);

  let mensagem = "Gerando o PDF… carregando as páginas.";
  if (prontas > 0) {
    mensagem = `Gerando o PDF… ${prontas} de ${total} páginas.`;
  }

  return (
    <div className="exportacao">
      <div className="exportacao-aviso" role="status">
        {erro === null && <p>{mensagem}</p>}
        {erro !== null && (
          <>
            <p>Não foi possível gerar o PDF: {erro}</p>
            <button type="button" onClick={() => navegar(-1)}>Voltar</button>
          </>
        )}
      </div>
      <div className="exportacao-folhas" ref={folhas}>
        {doMes && (
          <FolhasAnaliticas personalizado={modo === "personalizado"} paginas={paginas}
            partes={pedido.partes ?? TODAS_AS_PARTES} cidade={pedido.cidade} notaInicial={pedido.notaInicial}
            notaFinal={pedido.notaFinal} />
        )}
        {!doMes && (
          <FolhasDoPainel paginas={paginas} cidade={pedido.cidade} notaInicial={pedido.notaInicial}
            notaFinal={pedido.notaFinal} />
        )}
      </div>
    </div>
  );
}
