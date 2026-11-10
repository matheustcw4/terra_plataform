import type { BoletimAnalitico } from "../../../core/api/tipos";
import { useArea } from "../../../core/auth/AreaAutenticada";
import { CAPA } from "../../../core/ui/paginasDoBoletim";
import { mesDeReferencia, paragrafosDaNota } from "../../../logic/analitico";
import {
  blocosComMovimento,
  type FolhaNumerada,
  folhasDoBoletim,
  type Identificacao,
  identificacaoDoBoletim,
} from "../../../logic/boletim";
import { mesAtual } from "../../../logic/meses";
import { useBoletimAnalitico } from "../api";
import { CapaDoBoletim } from "./CapaDoBoletim";
import { FolhaComercializacao } from "./FolhaComercializacao";
import { FolhaDoBoletim } from "./FolhaDoBoletim";
import { FolhaFinanceiro } from "./FolhaFinanceiro";
import { FolhaRebanho } from "./FolhaRebanho";
import { FolhaResumo } from "./FolhaResumo";

type Props = {
  paginas: string[]; // a capa e as folhas marcadas (resumo, financeiro, rebanho, comercializacao)
  cidade: string;
  notaInicial: string;
  notaFinal: string;
};

// As folhas do modo Analítico, no desenho do boletim de resultados da Terra (folhas de paisagem), todas de uma chamada
// só à API: a capa, a nota técnica do começo, Resumo, Financeiro, Rebanho, Comercialização e a nota do fim. Se a API
// falhar, deixa a mensagem num `data-erro` para a exportação parar e mostrar.
export function FolhasDoBoletim({ paginas, cidade, notaInicial, notaFinal }: Props) {
  const { escopo, filtro, consulta } = useArea();
  const mes = mesDeReferencia(filtro, escopo.fazendas);
  const boletim = useBoletimAnalitico(consulta.fazendas, mes, filtro.visao, consulta.versao);
  if (boletim.isError) {
    return <p className="exportacao-falha" data-erro={boletim.error.message}>{boletim.error.message}</p>;
  }
  if (boletim.data === undefined) {
    return null;
  }
  const hoje = mesAtual();
  const identificacao = identificacaoDoBoletim(filtro, escopo.fazendas, boletim.data, cidade, hoje);
  const folhas = folhasDoBoletim(paginas, blocosComMovimento(boletim.data));
  return (
    <>
      {paginas.includes(CAPA) && (
        <div className="folha-pdf folha-boletim">
          <CapaDoBoletim identificacao={identificacao} folhas={folhas} mesDaAnalise={hoje}
            inicio={boletim.data.inicio_do_periodo} mesDeReferencia={boletim.data.mes_referencia} />
        </div>
      )}
      <NotaDoBoletim texto={notaInicial} identificacao={identificacao} />
      {folhas.map((folha) => (
        <div key={folha.numero} className="folha-pdf folha-boletim">
          <FolhaDaChave folha={folha} total={folhas.length} boletim={boletim.data} identificacao={identificacao} />
        </div>
      ))}
      <NotaDoBoletim texto={notaFinal} identificacao={identificacao} />
    </>
  );
}

type FolhaProps = { folha: FolhaNumerada; total: number; boletim: BoletimAnalitico; identificacao: Identificacao };

function FolhaDaChave({ folha, total, boletim, identificacao }: FolhaProps) {
  if (folha.chave === "resumo") {
    return <FolhaResumo boletim={boletim} identificacao={identificacao} numero={folha.numero} total={total} />;
  }
  if (folha.chave === "financeiro") {
    return <FolhaFinanceiro boletim={boletim} identificacao={identificacao} numero={folha.numero} total={total} />;
  }
  if (folha.chave === "rebanho") {
    return <FolhaRebanho boletim={boletim} identificacao={identificacao} numero={folha.numero} total={total} />;
  }
  return (
    <FolhaComercializacao boletim={boletim} identificacao={identificacao} blocos={folha.blocos} numero={folha.numero}
      total={total} />
  );
}

// A nota técnica digitada na exportação, numa folha própria; nota vazia não gera folha.
function NotaDoBoletim({ texto, identificacao }: { texto: string; identificacao: Identificacao }) {
  const paragrafos = paragrafosDaNota(texto);
  if (paragrafos.length === 0) {
    return null;
  }
  return (
    <div className="folha-pdf folha-boletim">
      <FolhaDoBoletim numero={null} total={0} titulo="Nota técnica" identificacao={identificacao}>
        <section className="boletim-quadro boletim-nota-tecnica">
          {paragrafos.map((paragrafo, posicao) => (
            <p key={posicao}>{paragrafo}</p>
          ))}
        </section>
      </FolhaDoBoletim>
    </div>
  );
}
