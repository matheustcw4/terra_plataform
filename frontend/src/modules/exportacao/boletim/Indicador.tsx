import type { ReactNode } from "react";

type Props = {
  rotulo: string;
  valor: string;
  status?: string | null; // verde | amarelo | vermelho (da API); sem status, a faixa fica marinho
  children?: ReactNode; // a linha de baixo: a meta, a variação, o complemento
  pequeno?: boolean; // o cartãozinho dentro de um bloco (fundo bege, sem faixa)
};

// O cartão de indicador do boletim de resultados: a faixa no alto com a cor do status, o rótulo em caixa alta, o
// número grande e a linha de complemento.
export function Indicador({ rotulo, valor, status = null, children, pequeno = false }: Props) {
  let classes = "boletim-indicador";
  if (pequeno) {
    classes += " pequeno";
  }
  if (status !== null && status !== undefined) {
    classes += ` tom-${status}`;
  }
  return (
    <section className={classes}>
      <h2>{rotulo}</h2>
      <strong>{valor}</strong>
      {children !== undefined && <p>{children}</p>}
    </section>
  );
}

// O número com a cor do status ("+7,2%" em verde), dentro da linha de complemento.
export function ComStatus({ status, children }: { status: string | null | undefined; children: ReactNode }) {
  let classes = "com-status";
  if (status !== null && status !== undefined) {
    classes += ` tom-${status}`;
  }
  return <span className={classes}>{children}</span>;
}
