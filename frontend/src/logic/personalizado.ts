// O modo Personalizado do "Exportar PDF": a pessoa escolhe os assuntos e, em cada um, o que mostrar (a leitura em
// frases, o previsto × realizado, os lançamentos, os gráficos...). Os assuntos escolhidos viram blocos, encaixados um
// depois do outro em folhas A4.

export type ParteDoAssunto = "leitura" | "previsto" | "lancamentos" | "graficos" | "resumo" | "notas";

export const PARTES: { chave: ParteDoAssunto; rotulo: string; descricao: string }[] = [
  { chave: "leitura", rotulo: "Leitura do mês", descricao: "o resumo em frases, explicando os números" },
  { chave: "previsto", rotulo: "Previsto × realizado", descricao: "o mês, o acumulado, a meta e o status" },
  { chave: "lancamentos", rotulo: "Lançamentos do mês", descricao: "lotes, mortes e a movimentação por categoria" },
  { chave: "graficos", rotulo: "Gráficos", descricao: "mês a mês, previsto × realizado" },
  { chave: "resumo", rotulo: "Números do período", descricao: "cartões, distribuição, causas e centros de custo" },
  { chave: "notas", rotulo: "Notas e legendas", descricao: "as explicações das tabelas e a legenda do status" },
];

export const TODAS_AS_PARTES: ParteDoAssunto[] = PARTES.map((parte) => parte.chave);

// O que cada assunto tem para mostrar (as notas só acompanham as tabelas, não fazem um bloco sozinhas).
export const PARTES_DO_ASSUNTO: Record<string, ParteDoAssunto[]> = {
  estoque: ["leitura", "lancamentos", "resumo", "notas"],
  lotacao: ["leitura", "resumo", "graficos"],
  placar_zootecnico: ["leitura", "previsto", "notas"],
  nascimentos: ["leitura", "lancamentos", "graficos", "previsto"],
  compras: ["leitura", "lancamentos", "graficos", "previsto"],
  vendas_abate: ["leitura", "lancamentos", "graficos", "previsto"],
  vendas_em_pe: ["leitura", "lancamentos", "graficos", "previsto"],
  transferencias: ["leitura", "lancamentos", "graficos", "previsto"],
  mortes: ["leitura", "lancamentos", "graficos", "previsto", "resumo"],
  placar_financeiro: ["leitura", "previsto", "resumo", "notas"],
  caixa: ["leitura", "previsto", "notas"],
};

export function mostra(partes: ParteDoAssunto[], parte: ParteDoAssunto): boolean {
  return partes.includes(parte);
}

// O assunto só vira bloco se alguma parte escolhida existe nele: um título sozinho (ou só com notas) não informa nada.
export function assuntoTemConteudo(assunto: string, partes: ParteDoAssunto[]): boolean {
  const doAssunto = PARTES_DO_ASSUNTO[assunto] ?? [];
  for (const parte of partes) {
    if (parte !== "notas" && doAssunto.includes(parte)) {
      return true;
    }
  }
  return false;
}

// Um pedaço de um bloco numa folha: as peças [de, ate) do bloco. A peça 0 é o título com a leitura; as outras são os
// quadros, na ordem.
export type TrechoDoBloco = { bloco: number; de: number; ate: number };

export type MedidasDaFolha = {
  alturaUtil: number; // o espaço do corpo da folha
  entreBlocos: number; // entre o fim de um bloco e o título do próximo
  entrePecas: number; // entre dois quadros do mesmo bloco
  tituloRepetido: number; // o título "(continuação)" de um bloco que segue na folha seguinte
};

// Encaixa os blocos em folhas, peça a peça (as alturas em px). O que não cabe vai para a folha seguinte, quebrando
// entre dois quadros; o título nunca fica sozinho no fim da folha (vai junto com o primeiro quadro). Uma peça mais alta
// que a folha vai sozinha numa folha que cresce para baixo (o PDF acompanha a altura).
export function paginar(blocos: number[][], medidas: MedidasDaFolha): TrechoDoBloco[][] {
  const folhas: TrechoDoBloco[][] = [];
  let folha: TrechoDoBloco[] = [];
  let ocupado = 0;
  for (let bloco = 0; bloco < blocos.length; bloco++) {
    const pecas = blocos[bloco] ?? [];
    const inicioDoBloco = (pecas[0] ?? 0) + (pecas[1] ?? 0);
    const espacoAntes = folha.length > 0 ? medidas.entreBlocos : 0;
    if (folha.length > 0 && ocupado + espacoAntes + inicioDoBloco > medidas.alturaUtil) {
      folhas.push(folha);
      folha = [];
      ocupado = 0;
    } else {
      ocupado += espacoAntes;
    }
    let trecho: TrechoDoBloco = { bloco, de: 0, ate: Math.min(2, pecas.length) };
    folha.push(trecho);
    ocupado += inicioDoBloco;
    for (let peca = 2; peca < pecas.length; peca++) {
      const altura = pecas[peca] ?? 0;
      if (ocupado + medidas.entrePecas + altura > medidas.alturaUtil) {
        folhas.push(folha);
        trecho = { bloco, de: peca, ate: peca + 1 };
        folha = [trecho];
        ocupado = medidas.tituloRepetido + altura;
      } else {
        trecho.ate = peca + 1;
        ocupado += medidas.entrePecas + altura;
      }
    }
  }
  if (folha.length > 0) {
    folhas.push(folha);
  }
  return folhas;
}

// As peças de um trecho, ou todas (o analítico mostra o assunto inteiro).
export function recortar<Item>(itens: Item[], faixa: [number, number] | undefined): Item[] {
  if (faixa === undefined) {
    return itens;
  }
  return itens.slice(faixa[0], faixa[1]);
}
