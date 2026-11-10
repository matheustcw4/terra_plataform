import globoBranco from "../../../assets/bi/terra-globo-branco.png";
import logoBranco from "../../../assets/bi/terra-logo-branco.png";
import {
  doisDigitos,
  type FolhaNumerada,
  type Identificacao,
  LEMA_DA_TERRA,
  SERVICOS_DA_TERRA,
  SITE_DA_TERRA,
  TITULO_DA_FOLHA,
} from "../../../logic/boletim";
import { mesPorExtenso } from "../../../logic/exportacao";
import { mesCurto } from "../../../logic/meses";

type Props = {
  identificacao: Identificacao;
  folhas: FolhaNumerada[];
  mesDaAnalise: string; // "AAAA-MM": hoje
  inicio: string; // o começo do período ("AAAA-MM-DD")
  mesDeReferencia: string;
};

// A capa do boletim de resultados: à esquerda, no marinho com o globo da Terra ao fundo, o período em letras grandes
// e quando foi a análise; à direita, no marrom, a fazenda, o cliente, o período, o planejamento e o conteúdo.
export function CapaDoBoletim({ identificacao, folhas, mesDaAnalise, inicio, mesDeReferencia }: Props) {
  const [tituloDoPeriodo, valorDoPeriodo] = identificacao.rotuloDoPeriodo.split(" ");
  return (
    <section className="boletim-capa" aria-label="Capa">
      <div className="boletim-capa-esquerda">
        <img className="boletim-capa-globo" src={globoBranco} alt="" />
        <img className="boletim-capa-logo" src={logoBranco} alt="Terra Desenvolvimento Agropecuário" />
        <div className="boletim-capa-periodo">
          <span className="boletim-capa-etiqueta">Boletim de resultados</span>
          <p className="boletim-capa-titulo-do-periodo">{tituloDoPeriodo}</p>
          <p className="boletim-capa-ano">{valorDoPeriodo}</p>
          <span className="boletim-capa-linha" />
          <p className="boletim-capa-analise">
            Análise de <strong>{mesPorExtenso(mesDaAnalise)}</strong> · dados de {mesCurto(inicio)} a{" "}
            {mesCurto(mesDeReferencia)}
          </p>
        </div>
        <ul className="boletim-capa-servicos">
          {SERVICOS_DA_TERRA.map((servico) => (
            <li key={servico}>{servico}</li>
          ))}
        </ul>
      </div>
      <div className="boletim-capa-direita">
        <p className="boletim-capa-rotulo">Propriedade</p>
        <h1 className={classeDoNome(identificacao.titulo)}>{identificacao.titulo}</h1>
        <p className="boletim-capa-cliente">{identificacao.cliente}</p>
        {identificacao.variasFazendas && <p className="boletim-capa-fazendas">{identificacao.fazendas}</p>}
        <dl className="boletim-capa-dados">
          <div>
            <dt>Período</dt>
            <dd>{identificacao.periodo}</dd>
          </div>
          <div>
            <dt>Meses</dt>
            <dd>{identificacao.meses}</dd>
          </div>
          <div>
            <dt>Planejamento</dt>
            <dd>{identificacao.planejamento}</dd>
          </div>
          <div>
            <dt>Sistema</dt>
            <dd>{identificacao.sistema}</dd>
          </div>
        </dl>
        {folhas.length > 0 && (
          <div className="boletim-capa-conteudo">
            <p className="boletim-capa-rotulo">Conteúdo</p>
            <ol>
              {itensDoConteudo(folhas).map((folha) => (
                <li key={folha.numero}>
                  <strong>{doisDigitos(folha.numero)}</strong>
                  {TITULO_DA_FOLHA[folha.chave]}
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>
      <footer className="boletim-capa-rodape">
        <strong>{SITE_DA_TERRA}</strong>
        <em>{LEMA_DA_TERRA}</em>
        <span>{identificacao.localEData}</span>
      </footer>
    </section>
  );
}

// A Comercialização que ocupa duas folhas aparece uma vez só no conteúdo.
function itensDoConteudo(folhas: FolhaNumerada[]): FolhaNumerada[] {
  const itens: FolhaNumerada[] = [];
  for (const folha of folhas) {
    if (!itens.some((item) => item.chave === folha.chave)) {
      itens.push(folha);
    }
  }
  return itens;
}

// Nome comprido (várias fazendas) usa letra menor.
function classeDoNome(nome: string): string {
  if (nome.length > 40) {
    return "boletim-capa-nome longo";
  }
  if (nome.length > 18) {
    return "boletim-capa-nome medio";
  }
  return "boletim-capa-nome";
}
