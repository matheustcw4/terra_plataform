import { maiorValor } from "../../../logic/boletim";

export type BarraDeitada = {
  nome: string;
  valor: number;
  texto: string; // o valor já escrito ("11,04 mi", "7")
  participacao?: string; // "45,9%", na coluna da direita
};

type Props = {
  barras: BarraDeitada[]; // da maior para a menor
  colunas: string; // as larguras do nome, da barra e do valor ("150px 1fr 60px"), como no gerador
  tom?: "marinho" | "marrom";
  escala?: number; // a maior barra de todas, quando a lista vem dividida em colunas (a mesma escala nas duas)
  primeira?: number; // a posição da primeira barra na lista inteira (o tom continua clareando na segunda coluna)
};

// As barras deitadas do boletim (desembolso por grupo, estoque por categoria, causa da morte), como as do gerador
// oficial (`hbarras`): o nome, a barra na escala da maior e o valor; as primeiras escuras, as de baixo mais claras.
export function BarrasDeitadas({ barras, colunas, tom = "marinho", escala, primeira = 0 }: Props) {
  if (barras.length === 0) {
    return <span className="boletim-sub">Sem dados no período.</span>;
  }
  let maior = maiorValor([barras.map((barra) => barra.valor)]);
  if (escala !== undefined) {
    maior = escala;
  }
  let gradeDasColunas = colunas;
  if (barras.some((barra) => barra.participacao !== undefined)) {
    gradeDasColunas = `${colunas} 46px`;
  }
  return (
    <div className="boletim-barras" style={{ gridTemplateColumns: gradeDasColunas }}>
      {barras.map((barra, posicao) => (
        <LinhaDaBarra key={barra.nome} barra={barra} largura={larguraDaBarra(barra.valor, maior)}
          cor={corDaBarra(primeira + posicao, tom)} />
      ))}
    </div>
  );
}

function LinhaDaBarra({ barra, largura, cor }: { barra: BarraDeitada; largura: number; cor: string }) {
  return (
    <>
      <span>{barra.nome}</span>
      <div className="boletim-barras-barra" style={{ width: `${largura.toFixed(1)}%`, background: cor }} />
      <span className="boletim-barras-valor">{barra.texto}</span>
      {barra.participacao !== undefined && <span className="boletim-barras-participacao">{barra.participacao}</span>}
    </>
  );
}

// a barra muito pequena ainda aparece como um traço
function larguraDaBarra(valor: number, maior: number): number {
  if (maior <= 0) {
    return 0.4;
  }
  return Math.max(0.4, (valor / maior) * 100);
}

// os tons do gerador: no marinho, as 2 primeiras escuras, até a 5ª média, até a 9ª clara e o resto cinza; no marrom
// (as causas da morte), a 1ª escura, até a 4ª média e o resto clara
function corDaBarra(posicao: number, tom: "marinho" | "marrom"): string {
  if (tom === "marrom") {
    return corMarrom(posicao);
  }
  if (posicao < 2) {
    return "var(--cor-marinho)";
  }
  if (posicao < 5) {
    return "var(--cor-marinho-medio)";
  }
  if (posicao < 9) {
    return "var(--cor-marinho-claro)";
  }
  return "var(--boletim-eixo)";
}

function corMarrom(posicao: number): string {
  if (posicao < 1) {
    return "var(--cor-marrom)";
  }
  if (posicao < 4) {
    return "var(--cor-marrom-claro)";
  }
  return "var(--cor-marrom-suave)";
}
