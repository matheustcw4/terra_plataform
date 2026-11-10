import type { ReactNode } from "react";

// A cor de um status da API (verde, amarelo ou vermelho); sem status, a cor que o cartão usa no lugar.
export function corDoStatus(status: string | null | undefined, semStatus: string): string {
  if (status === "verde") {
    return "var(--cor-status-verde)";
  }
  if (status === "amarelo") {
    return "var(--cor-status-amarelo)";
  }
  if (status === "vermelho") {
    return "var(--cor-status-vermelho)";
  }
  return semStatus;
}

type Props = {
  rotulo: string;
  valor: string;
  cor: string; // a faixa do alto (a cor do status, ou marinho e marrom nos indicadores sem meta)
  children?: ReactNode; // a linha de baixo: a meta, a variação, o complemento
};

// O cartão de indicador do gerador oficial (`kpi`): a faixa do alto na cor do status, o rótulo em caixa alta, o número
// grande em Archivo e a linha de complemento.
export function Indicador({ rotulo, valor, cor, children }: Props) {
  return (
    <section className="boletim-card boletim-kpi" style={{ borderTopColor: cor }}>
      <span className="boletim-lbl">{rotulo}</span>
      <span className="boletim-big">{valor}</span>
      {children !== undefined && <span className="boletim-sub">{children}</span>}
    </section>
  );
}

// O número com a cor do status ("+7,2%" em verde), dentro de uma linha de texto.
export function ComStatus({ status, children }: { status: string | null | undefined; children: ReactNode }) {
  let classes = "com-status";
  if (status !== null && status !== undefined) {
    classes += ` tom-${status}`;
  }
  return <b className={classes}>{children}</b>;
}

// A bolinha do semáforo, depois da variação nas tabelas.
export function Bolinha({ status }: { status: string | null | undefined }) {
  let classes = "boletim-bolinha";
  if (status !== null && status !== undefined) {
    classes += ` tom-${status}`;
  }
  return <span className={classes} />;
}

// A legenda das séries ("● Realizado ● Planejado").
export function LegendaDoBoletim({ itens }: { itens: { nome: string; cor: string }[] }) {
  return (
    <span className="boletim-legenda">
      {itens.map((item) => (
        <span key={item.nome}>
          <span className="boletim-bolinha" style={{ background: item.cor }} />
          {item.nome}
        </span>
      ))}
    </span>
  );
}
