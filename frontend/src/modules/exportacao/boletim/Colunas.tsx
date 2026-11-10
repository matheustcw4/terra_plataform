import { alturaDaColuna, maiorValor, mesDoEixo } from "../../../logic/boletim";

export type SerieDeColunas = {
  nome: string;
  valores: (number | null)[]; // um por mês; vazio = mês sem dado (depois do mês de referência)
  cor: string; // variável de cor (var(--cor-...))
  rotulo?: (valor: number | null) => string; // o número em cima da coluna; sem ele, a coluna vai sem número
};

type Props = {
  meses: string[]; // "AAAA-MM-DD"
  series: SerieDeColunas[];
  meta?: number | null; // a linha tracejada da meta, na escala das colunas
  corDaUltima?: string; // a coluna do mês de referência em destaque (só com uma série)
  altura?: number;
};

// As colunas do boletim de resultados, mês a mês, com o número em cima: em HTML, e não em SVG, para a folha sair
// igual na tela e na imagem do PDF. A escala é a maior coluna de todas as séries (e a meta, se houver).
export function Colunas({ meses, series, meta = null, corDaUltima, altura = 190 }: Props) {
  const maior = maiorValor([...series.map((serie) => serie.valores), [meta]]);
  const ultimoComDado = ultimoMesComDado(series);
  return (
    <div className="boletim-colunas">
      <div className="boletim-colunas-area" style={{ height: altura, gridTemplateColumns: `repeat(${meses.length}, 1fr)` }}>
        {meta !== null && meta > 0 && (
          <span className="boletim-colunas-meta" style={{ bottom: `${alturaDaColuna(meta, maior)}%` }} />
        )}
        {meses.map((mes, posicao) => (
          <div key={mes} className="boletim-colunas-mes">
            {series.map((serie) => (
              <div key={serie.nome} className="boletim-coluna-lugar">
                <Coluna valor={serie.valores[posicao] ?? null} maior={maior}
                  cor={corDaColuna(serie, posicao === ultimoComDado, corDaUltima)} rotulo={serie.rotulo} />
              </div>
            ))}
          </div>
        ))}
      </div>
      <div className="boletim-colunas-eixo" style={{ gridTemplateColumns: `repeat(${meses.length}, 1fr)` }}>
        {meses.map((mes) => (
          <span key={mes}>{mesDoEixo(mes)}</span>
        ))}
      </div>
    </div>
  );
}

type ColunaProps = { valor: number | null; maior: number; cor: string; rotulo?: (valor: number | null) => string };

function Coluna({ valor, maior, cor, rotulo }: ColunaProps) {
  if (valor === null) {
    return null;
  }
  return (
    <span className="boletim-coluna" style={{ height: `${alturaDaColuna(valor, maior)}%`, background: cor }}>
      {rotulo !== undefined && <span className="boletim-coluna-rotulo">{rotulo(valor)}</span>}
    </span>
  );
}

function corDaColuna(serie: SerieDeColunas, ehAUltima: boolean, corDaUltima: string | undefined): string {
  if (ehAUltima && corDaUltima !== undefined) {
    return corDaUltima;
  }
  return serie.cor;
}

// O último mês com dado na primeira série (o mês de referência): é ele que ganha a cor de destaque.
function ultimoMesComDado(series: SerieDeColunas[]): number {
  const primeira = series[0];
  if (primeira === undefined) {
    return -1;
  }
  const valores = primeira.valores;
  let ultimo = -1;
  for (let posicao = 0; posicao < valores.length; posicao += 1) {
    if (valores[posicao] !== null) {
      ultimo = posicao;
    }
  }
  return ultimo;
}
