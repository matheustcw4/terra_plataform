import type { ValoresDoVelocimetro } from "../api/tipos";
import { caminhoDoArco, fracaoDaEscala, pontoDoArco } from "../../logic/velocimetro";

type Props = {
  titulo: string;
  valores: ValoresDoVelocimetro;
  formatar: (valor: number | null) => string;
};

const CENTRO = { x: 100, y: 100 };
const RAIO = 80;

// O velocímetro do BI ("DESEMBOLSO CABEÇA MÊS", "Valor de Venda @"): o arco vai até o realizado, o traço marca a
// meta e a escala termina no máximo que a API manda. Verde dentro da meta, vermelho fora (a API diz qual é o caso).
export function Velocimetro({ titulo, valores, formatar }: Props) {
  const fracaoDoRealizado = fracaoDaEscala(valores.realizado, valores.maximo);
  const fracaoDaMeta = fracaoDaEscala(valores.planejado, valores.maximo);
  const pontaDaMarca = pontoDoArco(fracaoDaMeta, CENTRO, RAIO + 12);
  const baseDaMarca = pontoDoArco(fracaoDaMeta, CENTRO, RAIO - 12);
  let cor = "var(--cor-realizado)";
  if (valores.dentro_da_meta === true) {
    cor = "var(--cor-meta-ok)";
  }
  if (valores.dentro_da_meta === false) {
    cor = "var(--cor-meta-fora)";
  }
  return (
    <section className="painel-grafico velocimetro">
      <h2>{titulo}</h2>
      <svg viewBox="0 0 200 118" role="img" aria-label={`${titulo}: ${formatar(valores.realizado)}`}>
        <path d={caminhoDoArco(1, CENTRO, RAIO)} className="velocimetro-fundo" />
        {fracaoDoRealizado > 0 && <path d={caminhoDoArco(fracaoDoRealizado, CENTRO, RAIO)} stroke={cor}
          className="velocimetro-valor" />}
        {valores.planejado !== null && (
          <line x1={baseDaMarca.x} y1={baseDaMarca.y} x2={pontaDaMarca.x} y2={pontaDaMarca.y}
            className="velocimetro-meta" />
        )}
        <text x={CENTRO.x} y={CENTRO.y - 8} className="velocimetro-numero">{formatar(valores.realizado)}</text>
      </svg>
      <p className="velocimetro-legenda">
        Meta: <strong>{formatar(valores.planejado)}</strong>
      </p>
    </section>
  );
}
