import type { ReactNode } from "react";

type Props = {
  titulo: string;
  icone?: string;
  children: ReactNode;
};

// Um quadro da página (os quadros do BI, no desenho de cartão do AgTechLab): cabeçalho com o ícone e o título, e o
// conteúdo.
export function Painel({ titulo, icone, children }: Props) {
  return (
    <section className="painel-bi">
      <header className="painel-bi-titulo">
        {icone && (
          <span className="painel-bi-icone">
            <img src={icone} alt="" />
          </span>
        )}
        <h2>{titulo}</h2>
      </header>
      <div className="painel-bi-conteudo">{children}</div>
    </section>
  );
}

type LinhaProps = {
  rotulo: string;
  valor: string; // já formatado
  destaque?: boolean; // valor grande e verde, como o faturamento no BI
};

// "Rótulo ........ valor", como os pares de cartões do BI.
export function Linha({ rotulo, valor, destaque = false }: LinhaProps) {
  return (
    <div className={destaque ? "linha-bi destaque" : "linha-bi"}>
      <span>{rotulo}</span>
      <strong>{valor}</strong>
    </div>
  );
}
