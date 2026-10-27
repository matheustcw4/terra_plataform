import type { ReactNode } from "react";
import logo from "../../../assets/bi/terra-logo.png";
import type { Cabecalho } from "../../../logic/analitico";

export type { Cabecalho };

// Os meses e a meta como aparecem nos títulos dos quadros: "set/26", "jul/26" e "Meta da safra".
export type Rotulos = { mes: string; inicio: string; meta: string };

type Props = {
  titulo: string;
  cabecalho: Cabecalho;
  leitura: string[]; // as frases que a API escreveu a partir dos números
  children: ReactNode;
};

// Uma folha A4 do boletim analítico (o "Exportar PDF" no modo Analítico): título, fazenda, mês e período, o logo,
// a "Leitura do mês" que explica os números e os quadros da folha.
export function FolhaAnalitica({ titulo, cabecalho, leitura, children }: Props) {
  return (
    <section className="folha-analitica" aria-label={titulo}>
      <header className="folha-analitica-topo">
        <div>
          <h1>{titulo}</h1>
          <dl>
            <dt>Fazenda(s)</dt>
            <dd>{cabecalho.fazendas}</dd>
            <dt>Mês de referência</dt>
            <dd>{cabecalho.mesDeReferencia}</dd>
            <dt>Período</dt>
            <dd>{cabecalho.periodo}</dd>
          </dl>
        </div>
        <img src={logo} alt="Terra Desenvolvimento Agropecuário" />
      </header>
      {leitura.length > 0 && (
        <aside className="leitura-do-mes">
          <h2>Leitura do mês</h2>
          <ul>
            {leitura.map((frase) => (
              <li key={frase}>{frase}</li>
            ))}
          </ul>
        </aside>
      )}
      <div className="folha-analitica-corpo">{children}</div>
    </section>
  );
}

// Um quadro com título dentro da folha.
export function QuadroAnalitico({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <section className="quadro-analitico">
      <h3>{titulo}</h3>
      {children}
    </section>
  );
}
