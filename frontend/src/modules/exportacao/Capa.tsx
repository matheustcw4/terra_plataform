import fundo from "../../assets/bi/capa-fundo.png";
import globo from "../../assets/bi/terra-globo.png";
import { useArea } from "../../core/auth/AreaAutenticada";
import {
  localEData,
  mesPorExtenso,
  nomesDaCapa,
  periodoDaCapa,
  tamanhoDoLocal,
  tamanhoDosNomes,
} from "../../logic/exportacao";
import { mesAtual } from "../../logic/meses";

// A capa do PDF, sobre a arte da capa do boletim (1920×1080, sem o "SAFRA" impresso, para servir também ao ano
// civil): safra (ou ano) do filtro, a fazenda ou as fazendas do grupo, o mês analisado e a cidade digitada na hora.
// O modo Analítico passa o mês de referência; o padrão analisa até hoje. A cidade e a data do rodapé são as de hoje.
export function Capa({ cidade, mesDaAnalise = mesAtual() }: { cidade: string; mesDaAnalise?: string }) {
  const { escopo, filtro } = useArea();
  const periodo = periodoDaCapa(filtro);
  const nomes = nomesDaCapa(filtro, escopo.fazendas);
  const hoje = mesAtual();
  const local = localEData(cidade, hoje);
  return (
    <section className="capa" aria-label="Capa">
      <img className="capa-fundo" src={fundo} alt="" />
      <p className="capa-titulo">{periodo.titulo}</p>
      <p className="capa-periodo">{periodo.valor}</p>
      <div className="capa-analise">
        <span>Análise :</span>
        <strong>{mesPorExtenso(mesDaAnalise)}</strong>
      </div>
      <p className="capa-nomes" style={{ fontSize: `${tamanhoDosNomes(nomes)}px` }}>
        {nomes}
      </p>
      <div className="capa-rodape">
        <span className="capa-globo">
          <img src={globo} alt="" />
        </span>
        <strong>terradesenvolvimento.com.br</strong>
        <strong className="capa-local" style={{ fontSize: `${tamanhoDoLocal(local)}px` }}>
          {local}
        </strong>
      </div>
    </section>
  );
}
