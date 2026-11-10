import { maiorValor } from "../../../logic/boletim";

export type BarraDeitada = {
  rotulo: string;
  valor: number;
  texto: string; // o valor já escrito ("11,0 mi", "7")
  extra?: string; // a participação, à direita do valor
};

type Props = {
  barras: BarraDeitada[]; // da maior para a menor
  tom?: "marinho" | "marrom";
  escala?: number; // a maior barra de todas, quando a lista vem dividida em colunas (a mesma escala nas duas)
  primeira?: number; // a posição da primeira barra na lista inteira (o tom continua clareando na segunda coluna)
};

// As barras deitadas do boletim de resultados (desembolso por grupo, estoque por categoria, causa da morte): o nome, a
// barra na escala da maior e o valor. As primeiras ficam escuras e as de baixo vão clareando, como na apresentação.
export function BarrasDeitadas({ barras, tom = "marinho", escala, primeira = 0 }: Props) {
  let maior = maiorValor([barras.map((barra) => barra.valor)]);
  if (escala !== undefined) {
    maior = escala;
  }
  return (
    <ul className="boletim-barras">
      {barras.map((barra, posicao) => (
        <li key={barra.rotulo}>
          <span className="boletim-barras-nome">{barra.rotulo}</span>
          <span className="boletim-barras-trilho">
            <span className="boletim-barras-barra"
              style={{ width: `${larguraDaBarra(barra.valor, maior)}%`,
                background: corDaBarra(primeira + posicao, tom) }} />
          </span>
          <strong className="boletim-barras-valor">{barra.texto}</strong>
          {barra.extra !== undefined && <span className="boletim-barras-extra">{barra.extra}</span>}
        </li>
      ))}
    </ul>
  );
}

// a barra muito pequena ainda aparece como um traço
function larguraDaBarra(valor: number, maior: number): number {
  if (maior <= 0 || valor <= 0) {
    return 0;
  }
  return Math.max((valor / maior) * 100, 0.8);
}

type Tons = { escuro: string; medio: string; claro: string; suave: string };

const TONS: Record<"marinho" | "marrom", Tons> = {
  marinho: { escuro: "var(--cor-marinho)", medio: "var(--cor-marinho-medio)", claro: "var(--cor-marinho-claro)",
    suave: "var(--cor-marinho-claro)" },
  marrom: { escuro: "var(--cor-marrom)", medio: "var(--cor-marrom-claro)", claro: "var(--cor-marrom-claro)",
    suave: "var(--cor-bege)" },
};

function corDaBarra(posicao: number, tom: "marinho" | "marrom"): string {
  const cores = TONS[tom];
  if (posicao < 2) {
    return cores.escuro;
  }
  if (posicao < 3) {
    return cores.medio;
  }
  if (posicao < 6) {
    return cores.claro;
  }
  return cores.suave;
}
