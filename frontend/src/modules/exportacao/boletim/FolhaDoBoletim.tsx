import type { ReactNode } from "react";
import logoBranco from "../../../assets/boletim/logo_terra_branco.png";
import { doisDigitos, type Identificacao, LEMA_DA_TERRA, rotuloDaPagina, SITE_DA_TERRA } from "../../../logic/boletim";

type Props = {
  numero: number | null; // a nota técnica não é numerada
  total: number;
  titulo: string;
  identificacao: Identificacao;
  nota?: string; // a observação do rodapé, antes da cidade e da data
  children: ReactNode;
};

// Uma folha do boletim de resultados (do Financeiro em diante), como no gerador oficial: a faixa marinho com o logo, o
// fio, o selo marrom com o número e o título, e à direita a fazenda, o período e a página; embaixo, a tira com o site,
// o lema da Terra e a cidade e a data.
export function FolhaDoBoletim({ numero, total, titulo, identificacao, nota, children }: Props) {
  let direita = `${identificacao.titulo} · ${identificacao.rotuloDoPeriodo} · ${identificacao.periodo}`;
  if (numero !== null) {
    direita += ` · ${rotuloDaPagina(numero, total)}`;
  }
  return (
    <section className="boletim-folha" aria-label={titulo}>
      <header className="boletim-faixa">
        <div className="boletim-faixa-esquerda">
          <img className="boletim-faixa-logo" src={logoBranco} alt="Terra Desenvolvimento Agropecuário" />
          <span className="boletim-faixa-fio" />
          <div className="boletim-faixa-titulo">
            {numero !== null && <span className="boletim-selo">{doisDigitos(numero)}</span>}
            <h1>{titulo}</h1>
          </div>
        </div>
        <span className="boletim-faixa-direita">{direita}</span>
      </header>
      {children}
      <RodapeDoBoletim identificacao={identificacao} nota={nota} />
    </section>
  );
}

function RodapeDoBoletim({ identificacao, nota }: { identificacao: Identificacao; nota?: string }) {
  let direita = identificacao.localEData;
  if (nota !== undefined && nota !== "") {
    direita = `${nota} · ${identificacao.localEData}`;
  }
  return (
    <footer className="boletim-rodape">
      <strong>{SITE_DA_TERRA}</strong>
      <em>{LEMA_DA_TERRA}</em>
      <span>{direita}</span>
    </footer>
  );
}

// O título de uma parte da folha (04 Movimentação, 05 Mortes...): o número no selo marrom e o nome.
export function TituloDaParte({ numero, children }: { numero: string; children: ReactNode }) {
  return (
    <h2 className="boletim-colt">
      <i>{numero}</i>
      {children}
    </h2>
  );
}
