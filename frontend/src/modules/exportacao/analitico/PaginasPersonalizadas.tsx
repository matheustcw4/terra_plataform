import { useLayoutEffect, useRef, useState } from "react";
import type { BoletimAnalitico } from "../../../core/api/tipos";
import { paragrafosDaNota } from "../../../logic/analitico";
import {
  assuntoTemConteudo,
  type MedidasDaFolha,
  mostra,
  paginar,
  type ParteDoAssunto,
  recortar,
  type TrechoDoBloco,
} from "../../../logic/personalizado";
import { ConteudoDoAssunto, textosDoAssunto } from "./assuntos";
import { BlocoDoAssunto } from "./BlocoDoAssunto";
import { type Cabecalho, FolhaAnalitica, type Rotulos } from "./FolhaAnalitica";
import { TITULO_DA_NOTA } from "./FolhaDaNota";

// As medidas da folha A4 em estilos.css: a altura mínima da .folha-analitica, os espaços de cima e de baixo e entre
// o cabeçalho e o corpo; entre dois blocos (o espaço do corpo mais a margem do bloco), entre dois quadros (o espaço
// do corpo do bloco) e entre o título do bloco e o resto.
const ALTURA_DA_FOLHA = 1754;
const MARGENS_DA_FOLHA = 44 + 48 + 16;
const ENTRE_BLOCOS = 16 + 12;
const ENTRE_PECAS = 16;
const DEPOIS_DO_TITULO = 12;
const TITULO = "Boletim mensal";

// As notas técnicas entram no fluxo como blocos, antes e depois dos assuntos.
const NOTA_INICIAL = "nota_inicial";
const NOTA_FINAL = "nota_final";

type Props = {
  assuntos: string[];
  partes: ParteDoAssunto[];
  boletim: BoletimAnalitico;
  cabecalho: Cabecalho;
  rotulos: Rotulos;
  notaInicial: string;
  notaFinal: string;
};

// O modo Personalizado: a nota técnica do começo, cada assunto escolhido (só com as partes marcadas) e a nota do fim
// viram blocos, encaixados um depois do outro em folhas A4, quebrando entre dois quadros (ou dois parágrafos da nota)
// quando o bloco não cabe no resto da folha. Primeiro os blocos são desenhados numa folha de medição (fora do PDF);
// com a altura de cada peça, eles são repartidos.
export function PaginasPersonalizadas(props: Props) {
  const { assuntos, partes, boletim, cabecalho, rotulos, notaInicial, notaFinal } = props;
  const medicao = useRef<HTMLDivElement>(null);
  const [folhas, trocarFolhas] = useState<TrechoDoBloco[][] | null>(null);
  const blocos = blocosDoBoletim(assuntosComConteudo(assuntos, partes, boletim), notaInicial, notaFinal);
  const notas: Record<string, string> = { [NOTA_INICIAL]: notaInicial, [NOTA_FINAL]: notaFinal };

  useLayoutEffect(() => {
    if (folhas !== null || medicao.current === null) {
      return;
    }
    trocarFolhas(paginar(alturasDosBlocos(medicao.current), medidasDaFolha(medicao.current)));
  }, [folhas]);

  if (blocos.length === 0) {
    return (
      <div className="folha-pdf folha-a4">
        <FolhaAnalitica titulo={TITULO} cabecalho={cabecalho} leitura={[]}>
          <p className="nota">Nenhum dos assuntos escolhidos tem as partes marcadas.</p>
        </FolhaAnalitica>
      </div>
    );
  }
  if (folhas === null) {
    return (
      <div className="medicao-das-folhas" ref={medicao}>
        <FolhaAnalitica titulo={TITULO} cabecalho={cabecalho} leitura={[]}>
          {blocos.map((chave) => (
            <Trecho key={chave} chave={chave} notas={notas} boletim={boletim} partes={partes} rotulos={rotulos} />
          ))}
        </FolhaAnalitica>
      </div>
    );
  }
  return (
    <>
      {folhas.map((trechos) => (
        <div key={chaveDaFolha(trechos)} className="folha-pdf folha-a4">
          <FolhaAnalitica titulo={TITULO} cabecalho={cabecalho} leitura={[]}>
            {trechos.map((trecho) => (
              <Trecho key={`${trecho.bloco}-${trecho.de}`} chave={blocos[trecho.bloco] ?? ""} trecho={trecho}
                notas={notas} boletim={boletim} partes={partes} rotulos={rotulos} />
            ))}
          </FolhaAnalitica>
        </div>
      ))}
    </>
  );
}

// Cada assunto escolhido vira exatamente um bloco: as alturas medidas casam com as posições desta lista.
function assuntosComConteudo(assuntos: string[], partes: ParteDoAssunto[], boletim: BoletimAnalitico): string[] {
  const escolhidos = [];
  for (const chave of assuntos) {
    if (assuntoTemConteudo(chave, partes) && textosDoAssunto(chave, boletim) !== null) {
      escolhidos.push(chave);
    }
  }
  return escolhidos;
}

function blocosDoBoletim(assuntos: string[], notaInicial: string, notaFinal: string): string[] {
  const blocos = [];
  if (paragrafosDaNota(notaInicial).length > 0) {
    blocos.push(NOTA_INICIAL);
  }
  for (const assunto of assuntos) {
    blocos.push(assunto);
  }
  if (paragrafosDaNota(notaFinal).length > 0) {
    blocos.push(NOTA_FINAL);
  }
  return blocos;
}

// As alturas das peças de cada bloco: a primeira é o título com a leitura (até o começo dos quadros); depois, cada
// quadro (ou parágrafo da nota).
function alturasDosBlocos(folha: HTMLElement): number[][] {
  const blocos = [];
  for (const bloco of folha.querySelectorAll<HTMLElement>(".bloco-do-assunto")) {
    const corpo = bloco.querySelector<HTMLElement>(":scope > .folha-analitica-corpo");
    if (corpo === null) {
      continue;
    }
    const cabeca = corpo.getBoundingClientRect().top - bloco.getBoundingClientRect().top;
    const quadros = Array.from(corpo.children).map((quadro) => (quadro as HTMLElement).offsetHeight);
    blocos.push([cabeca, ...quadros]);
  }
  return blocos;
}

function medidasDaFolha(folha: HTMLElement): MedidasDaFolha {
  const topo = folha.querySelector<HTMLElement>(".folha-analitica-topo")?.offsetHeight ?? 0;
  const titulo = folha.querySelector<HTMLElement>(".bloco-do-assunto-titulo")?.offsetHeight ?? 0;
  return {
    alturaUtil: ALTURA_DA_FOLHA - MARGENS_DA_FOLHA - topo,
    entreBlocos: ENTRE_BLOCOS,
    entrePecas: ENTRE_PECAS,
    tituloRepetido: titulo + DEPOIS_DO_TITULO,
  };
}

function chaveDaFolha(trechos: TrechoDoBloco[]): string {
  return trechos.map((trecho) => `${trecho.bloco}-${trecho.de}`).join("_");
}

// As peças de conteúdo do trecho: a peça 0 do trecho é o título; o conteúdo começa na peça 1. Sem trecho, tudo.
function faixaDoTrecho(trecho: TrechoDoBloco | undefined): [number, number] | undefined {
  if (trecho === undefined) {
    return undefined;
  }
  return [Math.max(trecho.de, 1) - 1, trecho.ate - 1];
}

function tituloDoTrecho(titulo: string, trecho: TrechoDoBloco | undefined): string {
  if (trecho !== undefined && trecho.de > 0) {
    return `${titulo} (continuação)`;
  }
  return titulo;
}

type TrechoProps = {
  chave: string;
  trecho?: TrechoDoBloco; // sem trecho, o bloco inteiro (na folha de medição)
  notas: Record<string, string>;
  boletim: BoletimAnalitico;
  partes: ParteDoAssunto[];
  rotulos: Rotulos;
};

// Um bloco inteiro ou um pedaço dele. O pedaço que continua de uma folha anterior leva "(continuação)" no título e
// não repete a leitura.
function Trecho({ chave, trecho, notas, boletim, partes, rotulos }: TrechoProps) {
  const nota = notas[chave];
  if (nota !== undefined) {
    return <TrechoDaNota texto={nota} trecho={trecho} />;
  }
  const textos = textosDoAssunto(chave, boletim);
  if (textos === null) {
    return null;
  }
  let leitura = mostra(partes, "leitura") ? textos.leitura : [];
  if (trecho !== undefined && trecho.de > 0) {
    leitura = [];
  }
  return (
    <BlocoDoAssunto titulo={tituloDoTrecho(textos.titulo, trecho)} leitura={leitura}>
      <ConteudoDoAssunto chave={chave} boletim={boletim} partes={partes} rotulos={rotulos}
        faixa={faixaDoTrecho(trecho)} />
    </BlocoDoAssunto>
  );
}

// A nota técnica como bloco: cada parágrafo é uma peça, para a folha poder quebrar entre eles.
function TrechoDaNota({ texto, trecho }: { texto: string; trecho?: TrechoDoBloco }) {
  const paragrafos = paragrafosDaNota(texto).map((paragrafo, posicao) => (
    <p key={posicao} className="nota-tecnica-paragrafo">
      {paragrafo}
    </p>
  ));
  return (
    <BlocoDoAssunto titulo={tituloDoTrecho(TITULO_DA_NOTA, trecho)} leitura={[]}>
      {recortar(paragrafos, faixaDoTrecho(trecho))}
    </BlocoDoAssunto>
  );
}
