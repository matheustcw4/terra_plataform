import { useArea } from "../../../core/auth/AreaAutenticada";
import { CAPA, rotuloDaFolha } from "../../../core/ui/paginasDoBoletim";
import { cabecalhoDoBoletim, mesDeReferencia } from "../../../logic/analitico";
import { identificacaoDoBoletim } from "../../../logic/boletim";
import { mesAtual, mesCurto } from "../../../logic/meses";
import type { ParteDoAssunto } from "../../../logic/personalizado";
import { useBoletimAnalitico } from "../api";
import { CapaDoBoletim } from "../boletim/CapaDoBoletim";
import type { Rotulos } from "./FolhaAnalitica";
import { PaginasPersonalizadas } from "./PaginasPersonalizadas";

type Props = {
  paginas: string[];
  partes: ParteDoAssunto[];
  cidade: string;
  notaInicial: string;
  notaFinal: string;
};

// As folhas do modo Personalizado, todas de uma chamada só à API: a capa (a do boletim de resultados, a mesma dos
// outros modos), as notas e os blocos escolhidos encaixados em folhas A4. Se a API falhar, deixa a mensagem num
// `data-erro` para a exportação parar e mostrar. (O Boletim Resumido usa as folhas do boletim de resultados, em
// `../boletim/`.)
export function FolhasAnaliticas({ paginas, partes, cidade, notaInicial, notaFinal }: Props) {
  const { escopo, filtro, consulta } = useArea();
  const mes = mesDeReferencia(filtro, escopo.fazendas);
  const boletim = useBoletimAnalitico(consulta, mes, filtro.visao);
  if (boletim.isError) {
    return <p className="exportacao-falha" data-erro={boletim.error.message}>{boletim.error.message}</p>;
  }
  if (boletim.data === undefined) {
    return null;
  }
  const cabecalho = { ...cabecalhoDoBoletim(filtro, escopo.fazendas), planejamento: boletim.data.plano.em_uso.join("; ") };
  const rotulos: Rotulos = {
    mes: mesCurto(mes),
    inicio: mesCurto(boletim.data.inicio_do_periodo),
    meta: cabecalho.rotuloDaMeta,
  };
  const assuntos = paginas.filter((chave) => chave !== CAPA);
  const hoje = mesAtual();
  const identificacao = identificacaoDoBoletim(filtro, escopo.fazendas, boletim.data, cidade, hoje);
  return (
    <>
      {paginas.includes(CAPA) && (
        <div className="folha-pdf folha-boletim">
          <CapaDoBoletim identificacao={identificacao} mesDaAnalise={hoje}
            conteudo={assuntos.map((chave) => rotuloDaFolha("personalizado", chave))} />
        </div>
      )}
      <PaginasPersonalizadas assuntos={assuntos} partes={partes} boletim={boletim.data} cabecalho={cabecalho}
        rotulos={rotulos} notaInicial={notaInicial} notaFinal={notaFinal} />
    </>
  );
}
