import { useArea } from "../../../core/auth/AreaAutenticada";
import { CAPA } from "../../../core/ui/paginasDoBoletim";
import { cabecalhoDoBoletim, mesDeReferencia } from "../../../logic/analitico";
import { mesCurto } from "../../../logic/meses";
import type { ParteDoAssunto } from "../../../logic/personalizado";
import { Capa } from "../Capa";
import { useBoletimAnalitico } from "../api";
import type { Rotulos } from "./FolhaAnalitica";
import { PaginasPersonalizadas } from "./PaginasPersonalizadas";

type Props = {
  paginas: string[];
  partes: ParteDoAssunto[];
  cidade: string;
  notaInicial: string;
  notaFinal: string;
};

// As folhas do modo Personalizado, todas de uma chamada só à API: a capa (a mesma do padrão, com o mês de referência),
// as notas e os blocos escolhidos encaixados em folhas A4. Se a API falhar, deixa a mensagem num `data-erro` para a
// exportação parar e mostrar. (O modo Analítico usa as folhas do boletim de resultados, em `../boletim/`.)
export function FolhasAnaliticas({ paginas, partes, cidade, notaInicial, notaFinal }: Props) {
  const { escopo, filtro, consulta } = useArea();
  const mes = mesDeReferencia(filtro, escopo.fazendas);
  const boletim = useBoletimAnalitico(consulta.fazendas, mes, filtro.visao, consulta.versao);
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
  return (
    <>
      {paginas.includes(CAPA) && (
        <div className="folha-pdf folha-capa">
          <Capa cidade={cidade} mesDaAnalise={mes} />
        </div>
      )}
      <PaginasPersonalizadas assuntos={assuntos} partes={partes} boletim={boletim.data} cabecalho={cabecalho}
        rotulos={rotulos} notaInicial={notaInicial} notaFinal={notaFinal} />
    </>
  );
}
