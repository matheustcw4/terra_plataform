import { alturaDaColuna, maiorValor } from "../../../logic/boletim";

export type SerieDeColunas = {
  nome: string;
  valores: (number | null)[]; // um por mês
  cor: string; // variável de cor (var(--cor-...))
  rotulo?: (valor: number) => string; // o número em cima da coluna; sem ele, a coluna vai sem número
  corDoRotulo?: string; // o planejado escreve em cinza
  destaques?: boolean[]; // o mês em que o número sai vermelho (acima da meta)
};

type Props = {
  eixo: string[]; // o nome de cada mês embaixo ("jul/26" ou "jul")
  series: SerieDeColunas[];
  meta?: number | null; // a linha tracejada da meta, na escala das colunas
  altura?: number;
};

// Espaço em cima das colunas para o número (como o gerador: a área útil é a altura menos 18 px).
const ESPACO_DO_ROTULO = 18;

// As colunas mês a mês do boletim, como as do gerador oficial (`barras`): uma coluna por série em cada mês, o número em
// cima de todas (o traço quando é zero), a meta tracejada e o eixo dos meses. Em HTML, e não em SVG, para a folha sair
// igual na tela e na imagem do PDF.
export function Colunas({ eixo, series, meta = null, altura = 200 }: Props) {
  const maior = maiorValor([...series.map((serie) => serie.valores.map(absoluto)), [meta]]);
  const areaUtil = altura - ESPACO_DO_ROTULO;
  const colunasDoGrid = `repeat(${eixo.length}, minmax(0, 1fr))`;
  const largura = larguraDaColuna(eixo.length, series.length);
  const fonte = tamanhoDoRotulo(eixo.length);
  return (
    <div>
      <div className="boletim-colunas" style={{ height: altura }}>
        {meta !== null && meta > 0 && maior > 0 && (
          <span className="boletim-colunas-meta" style={{ bottom: Math.round((meta / maior) * areaUtil) }} />
        )}
        <div className="boletim-colunas-area" style={{ gridTemplateColumns: colunasDoGrid }}>
          {eixo.map((mes, posicao) => (
            <div key={mes} className="boletim-colunas-mes">
              {series.map((serie) => (
                <Coluna key={serie.nome} serie={serie} posicao={posicao} maior={maior} areaUtil={areaUtil}
                  largura={largura} fonte={fonte} />
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="boletim-colunas-eixo" style={{ gridTemplateColumns: colunasDoGrid }}>
        {eixo.map((mes) => (
          <span key={mes} className="boletim-eixo">{mes}</span>
        ))}
      </div>
    </div>
  );
}

type ColunaProps = {
  serie: SerieDeColunas;
  posicao: number;
  maior: number;
  areaUtil: number;
  largura: string;
  fonte: number;
};

function Coluna({ serie, posicao, maior, areaUtil, largura, fonte }: ColunaProps) {
  const valor = serie.valores[posicao] ?? null;
  let texto = "—";
  if (serie.rotulo === undefined) {
    texto = " "; // sem número, mas com a mesma altura, para as colunas do mês ficarem alinhadas
  } else if (valor !== null && valor !== 0) {
    texto = serie.rotulo(valor);
  }
  let cor = serie.corDoRotulo ?? "var(--boletim-rotulo)";
  if (serie.destaques?.[posicao] === true) {
    cor = "var(--cor-status-vermelho)";
  }
  return (
    <div className="boletim-coluna" style={{ width: largura }}>
      <span className="boletim-coluna-rotulo" style={{ fontSize: fonte, color: cor }}>{texto}</span>
      <div className="boletim-coluna-barra"
        style={{ height: alturaDaColuna(valor, maior, areaUtil), background: serie.cor }} />
    </div>
  );
}

function absoluto(valor: number | null): number | null {
  if (valor === null) {
    return null;
  }
  return Math.abs(valor);
}

// Um mês só: a coluna ocupa 40%; mais meses: as séries dividem 76% da largura do mês.
function larguraDaColuna(meses: number, series: number): string {
  if (meses <= 1) {
    return "40%";
  }
  return `${Math.floor(76 / Math.max(series, 1))}%`;
}

// Com mais de 6 meses o número fica menor, para caber em cima da coluna.
function tamanhoDoRotulo(meses: number): number {
  if (meses <= 6) {
    return 10;
  }
  return 8.5;
}
