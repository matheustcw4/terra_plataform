import logoBranco from "../../../assets/boletim/logo_terra_branco.png";
import simboloBranco from "../../../assets/boletim/simbolo_terra_branco.png";
import {
  doisDigitos,
  type Identificacao,
  LEMA_DA_TERRA,
  SERVICOS_DA_TERRA,
  SITE_DA_TERRA,
} from "../../../logic/boletim";
import { mesPorExtenso } from "../../../logic/exportacao";

type Props = {
  identificacao: Identificacao;
  conteudo: string[]; // o que vem depois da capa, na ordem (as folhas do analítico, as páginas ou os assuntos)
  mesDaAnalise: string; // "AAAA-MM": hoje
};

// Com mais itens que isto, o conteúdo fica em linhas mais baixas, para caber no marrom (o modo Padrão tem 9 páginas).
const ITENS_DO_CONTEUDO_LARGO = 5;

// A capa do boletim de resultados, como a do gerador oficial, nos três modos do PDF: à esquerda, no marinho com o
// símbolo da Terra ao fundo, o ano ou a safra em letras grandes e quando foi a análise; à direita, no marrom, a
// fazenda, o cliente, o período, o planejamento, o sistema e o conteúdo.
export function CapaDoBoletim({ identificacao, conteudo, mesDaAnalise }: Props) {
  const [tituloDoPeriodo, valorDoPeriodo] = identificacao.rotuloDoPeriodo.split(" ");
  return (
    <section className="boletim-capa" aria-label="Capa">
      <div className="boletim-capa-meio">
        <div className="boletim-capa-esquerda">
          <img className="boletim-capa-simbolo" src={simboloBranco} alt="" />
          <img className="boletim-capa-logo" src={logoBranco} alt="Terra Desenvolvimento Agropecuário" />
          <div className="boletim-capa-periodo">
            <span className="boletim-capa-etiqueta">BOLETIM DE RESULTADOS</span>
            <span className="boletim-capa-rotulo-do-periodo">{tituloDoPeriodo}</span>
            <h1>{valorDoPeriodo}</h1>
            <div className="boletim-capa-linha">
              <span />
              <span />
            </div>
            <span className="boletim-capa-analise">
              Análise de <b>{mesPorExtenso(mesDaAnalise)}</b> · dados de {identificacao.periodo.toLowerCase()}
            </span>
          </div>
          <ul className="boletim-capa-servicos">
            {SERVICOS_DA_TERRA.map((servico) => (
              <li key={servico}>{servico}</li>
            ))}
          </ul>
        </div>
        <aside className="boletim-capa-direita">
          <span className="boletim-capa-rotulo">PROPRIEDADE</span>
          <h2 className={classeDoNome(identificacao.titulo)}>{identificacao.titulo}</h2>
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
          {conteudo.length > 0 && (
            <div className="boletim-capa-conteudo">
              <span className="boletim-capa-rotulo">CONTEÚDO</span>
              <ol className={conteudo.length > ITENS_DO_CONTEUDO_LARGO ? "compacto" : undefined}>
                {conteudo.map((titulo, posicao) => (
                  <li key={titulo}>
                    <b>{doisDigitos(posicao + 1)}</b>
                    {titulo}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </aside>
      </div>
      <footer className="boletim-capa-rodape">
        <strong>{SITE_DA_TERRA}</strong>
        <em>{LEMA_DA_TERRA}</em>
        <strong>{identificacao.localEData}</strong>
      </footer>
    </section>
  );
}

// O tamanho do nome pelo comprimento, como no gerador (56, 46 ou 38 px), e menor ainda para os nomes de um grupo.
function classeDoNome(nome: string): string {
  if (nome.length <= 9) {
    return "boletim-capa-nome";
  }
  if (nome.length <= 12) {
    return "boletim-capa-nome medio";
  }
  if (nome.length <= 30) {
    return "boletim-capa-nome longo";
  }
  return "boletim-capa-nome muito-longo";
}
