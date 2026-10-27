import type { ReactNode } from "react";

type Props = {
  titulo: string;
  leitura: string[]; // vazio quando a "Leitura do mês" não foi escolhida
  children: ReactNode;
};

// Um assunto no modo Personalizado: título, a leitura em frases (se escolhida) e os quadros. Vários blocos dividem a
// mesma folha A4.
export function BlocoDoAssunto({ titulo, leitura, children }: Props) {
  return (
    <section className="bloco-do-assunto" aria-label={titulo}>
      <h2 className="bloco-do-assunto-titulo">{titulo}</h2>
      {leitura.length > 0 && (
        <aside className="leitura-do-mes">
          <h3>Leitura do mês</h3>
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
