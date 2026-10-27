import type { BoletimAnalitico } from "../../../core/api/tipos";
import { useArea } from "../../../core/auth/AreaAutenticada";
import { CAPA } from "../../../core/ui/paginasDoBoletim";
import { cabecalhoDoBoletim, mesDeReferencia } from "../../../logic/analitico";
import { consultaDoFiltro } from "../../../logic/filtro";
import { mesCurto } from "../../../logic/meses";
import { type ParteDoAssunto, TODAS_AS_PARTES } from "../../../logic/personalizado";
import { Capa } from "../Capa";
import { useBoletimAnalitico } from "../api";
import { ConteudoDoAssunto, textosDoAssunto } from "./assuntos";
import { type Cabecalho, FolhaAnalitica, type Rotulos } from "./FolhaAnalitica";
import { FolhaDaNota } from "./FolhaDaNota";
import { PaginasPersonalizadas } from "./PaginasPersonalizadas";

type Props = {
  personalizado: boolean;
  paginas: string[];
  partes: ParteDoAssunto[]; // no analítico, todas
  cidade: string;
  notaInicial: string;
  notaFinal: string;
};

// As folhas dos modos Analítico e Personalizado, todas de uma chamada só à API: a capa (a mesma do padrão, com o mês
// de referência) e, no analítico, a nota técnica do começo, uma folha A4 por assunto com tudo e a nota do fim; no
// personalizado, as notas e os blocos escolhidos encaixados em folhas. Se a API falhar, deixa a mensagem num
// `data-erro` para a exportação parar e mostrar.
export function FolhasAnaliticas({ personalizado, paginas, partes, cidade, notaInicial, notaFinal }: Props) {
  const { escopo, filtro } = useArea();
  const consulta = consultaDoFiltro(filtro, escopo.fazendas);
  const mes = mesDeReferencia(filtro, escopo.fazendas);
  const boletim = useBoletimAnalitico(consulta.fazendas, mes, filtro.visao);
  if (boletim.isError) {
    return <p className="exportacao-falha" data-erro={boletim.error.message}>{boletim.error.message}</p>;
  }
  if (boletim.data === undefined) {
    return null;
  }
  const cabecalho = cabecalhoDoBoletim(filtro, escopo.fazendas);
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
      {personalizado && (
        <PaginasPersonalizadas assuntos={assuntos} partes={partes} boletim={boletim.data} cabecalho={cabecalho}
          rotulos={rotulos} notaInicial={notaInicial} notaFinal={notaFinal} />
      )}
      {!personalizado && <FolhaDaNota texto={notaInicial} cabecalho={cabecalho} />}
      {!personalizado &&
        assuntos.map((chave) => (
          <div key={chave} className="folha-pdf folha-a4">
            <FolhaDoAssunto chave={chave} boletim={boletim.data} cabecalho={cabecalho} rotulos={rotulos} />
          </div>
        ))}
      {!personalizado && <FolhaDaNota texto={notaFinal} cabecalho={cabecalho} />}
    </>
  );
}

type FolhaProps = { chave: string; boletim: BoletimAnalitico; cabecalho: Cabecalho; rotulos: Rotulos };

// Uma folha do analítico: o assunto inteiro, com todas as partes.
function FolhaDoAssunto({ chave, boletim, cabecalho, rotulos }: FolhaProps) {
  const textos = textosDoAssunto(chave, boletim);
  if (textos === null) {
    return null;
  }
  return (
    <FolhaAnalitica titulo={textos.titulo} cabecalho={cabecalho} leitura={textos.leitura}>
      <ConteudoDoAssunto chave={chave} boletim={boletim} partes={TODAS_AS_PARTES} rotulos={rotulos} />
    </FolhaAnalitica>
  );
}
