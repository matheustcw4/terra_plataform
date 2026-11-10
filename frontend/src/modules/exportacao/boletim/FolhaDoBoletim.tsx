import type { ReactNode } from "react";
import logoBranco from "../../../assets/bi/terra-logo-branco.png";
import { doisDigitos, type Identificacao, LEMA_DA_TERRA, rotuloDaPagina, SITE_DA_TERRA } from "../../../logic/boletim";

type Props = {
  numero: number | null; // a nota técnica não é numerada
  total: number;
  titulo: string;
  identificacao: Identificacao;
  children: ReactNode;
};

// Uma folha do boletim de resultados (do Financeiro em diante): a faixa marinho com o logo, o selo marrom com o
// número e o título, e à direita quem e quando; embaixo, a tira com o site, o lema da Terra e a cidade e a data.
export function FolhaDoBoletim({ numero, total, titulo, identificacao, children }: Props) {
  let direita = `${identificacao.titulo} · ${identificacao.rotuloDoPeriodo} · ${identificacao.periodo}`;
  if (numero !== null) {
    direita += ` · ${rotuloDaPagina(numero, total)}`;
  }
  return (
    <section className="boletim-folha" aria-label={titulo}>
      <header className="boletim-faixa">
        <img className="boletim-faixa-logo" src={logoBranco} alt="Terra Desenvolvimento Agropecuário" />
        {numero !== null && <span className="boletim-selo">{doisDigitos(numero)}</span>}
        <h1>{titulo}</h1>
        <p className="boletim-faixa-direita">{direita}</p>
      </header>
      <div className="boletim-corpo">{children}</div>
      <RodapeDoBoletim identificacao={identificacao} />
    </section>
  );
}

export function RodapeDoBoletim({ identificacao }: { identificacao: Identificacao }) {
  return (
    <footer className="boletim-rodape">
      <strong>{SITE_DA_TERRA}</strong>
      <em>{LEMA_DA_TERRA}</em>
      <span>{identificacao.localEData}</span>
    </footer>
  );
}

type QuadroProps = {
  titulo: string;
  direita?: ReactNode; // o que fica à direita do título (o total, a legenda)
  nota?: ReactNode; // a frase de leitura, embaixo
  className?: string;
  children: ReactNode;
};

// Um quadro branco da folha, com o título em caixa alta e, embaixo, a frase que explica o número.
export function QuadroDoBoletim({ titulo, direita, nota, className, children }: QuadroProps) {
  let classes = "boletim-quadro";
  if (className !== undefined) {
    classes += ` ${className}`;
  }
  return (
    <section className={classes}>
      <header className="boletim-quadro-topo">
        <h2>{titulo}</h2>
        {direita !== undefined && <div className="boletim-quadro-direita">{direita}</div>}
      </header>
      <div className="boletim-quadro-conteudo">{children}</div>
      {nota !== undefined && <p className="boletim-nota">{nota}</p>}
    </section>
  );
}

// O título de uma parte dentro da folha (Movimentação, Mortes...), com o quadradinho marrom.
export function SubtituloDoBoletim({ children }: { children: ReactNode }) {
  return <h3 className="boletim-subtitulo">{children}</h3>;
}

// A legenda das séries ("● Realizado ● Planejado").
export function LegendaDoBoletim({ itens }: { itens: { nome: string; cor: string }[] }) {
  return (
    <span className="boletim-legenda">
      {itens.map((item) => (
        <span key={item.nome}>
          <i style={{ background: item.cor }} />
          {item.nome}
        </span>
      ))}
    </span>
  );
}
