import type { BoletimAnalitico, LinhaDoPlacar, SecaoDeLotes } from "../../../core/api/tipos";
import { valorComUnidade } from "../../../logic/analitico";
import {
  ateAReferencia,
  type BlocoDeComercializacao,
  cabecasOuTraco,
  celulaEmMilhoes,
  type Identificacao,
  linhaDoIndicador,
  reaisCurtos,
  secaoDoBloco,
  variacaoComSinal,
  variacaoDaLinha,
} from "../../../logic/boletim";
import { dinheiro, percentual } from "../../../logic/formatar";
import { Colunas } from "./Colunas";
import { FolhaDoBoletim, LegendaDoBoletim } from "./FolhaDoBoletim";
import { ComStatus, Indicador } from "./Indicador";
import { TabelaDosMeses } from "./TabelaDosMeses";

type Props = {
  boletim: BoletimAnalitico;
  identificacao: Identificacao;
  blocos: BlocoDeComercializacao[];
  numero: number;
  total: number;
};

type JeitoDoBloco = { titulo: string; valor: string; grafico: string; cor: string; indicadores: string[] };

// Como cada bloco se chama e se escreve: o valor do lote é faturamento na venda e investimento na compra. O placar
// mostra os cinco indicadores que decidem o negócio (os outros estão na página do painel).
const DO_BLOCO: Record<BlocoDeComercializacao, JeitoDoBloco> = {
  abate: { titulo: "Venda abate", valor: "Faturamento", grafico: "Faturamento por mês · R$ mi",
    cor: "var(--cor-realizado)",
    indicadores: ["Cabeças", "Peso médio", "Rendimento de carcaça", "Preço da @", "Faturamento"] },
  em_pe: { titulo: "Venda em pé", valor: "Faturamento", grafico: "Faturamento por mês · R$ mi",
    cor: "var(--cor-realizado)", indicadores: ["Cabeças", "Peso médio", "Preço do kg", "Preço da @", "Faturamento"] },
  compras: { titulo: "Compras e reposição", valor: "Investimento", grafico: "Desembolso de compras por mês · R$ mi",
    cor: "var(--cor-marrom)", indicadores: ["Cabeças", "Peso médio", "Preço do kg", "Preço da @", "Investimento"] },
};

// A folha da Comercialização: até dois blocos (venda abate, venda em pé, compras), cada um com os números do
// acumulado, o placar realizado × planejado e o valor mês a mês. Sem venda nem compra no período, a folha diz isso.
export function FolhaComercializacao({ boletim, identificacao, blocos, numero: numeroDaFolha, total }: Props) {
  return (
    <FolhaDoBoletim numero={numeroDaFolha} total={total} titulo="Comercialização" identificacao={identificacao}>
      {blocos.length === 0 && (
        <p className="boletim-vazio grande">Nenhuma venda nem compra de animais, realizada ou planejada, no período.</p>
      )}
      <div className="boletim-linha-2">
        {blocos.map((bloco) => (
          <BlocoDeLotes key={bloco} bloco={bloco} boletim={boletim} />
        ))}
      </div>
    </FolhaDoBoletim>
  );
}

function BlocoDeLotes({ bloco, boletim }: { bloco: BlocoDeComercializacao; boletim: BoletimAnalitico }) {
  const secao = secaoDoBloco(boletim, bloco);
  const jeito = DO_BLOCO[bloco];
  const meses = ateAReferencia(secao.meses, boletim.mes_referencia);
  const datas = meses.map((mes) => mes.mes);
  return (
    <section className="boletim-quadro boletim-bloco">
      <h2 className="boletim-subtitulo">{jeito.titulo}</h2>
      <NumerosDoBloco bloco={bloco} boletim={boletim} secao={secao} />
      <PlacarDoBloco linhas={linhasDoPlacar(secao.resumo, jeito.indicadores)} />
      <div className="boletim-quadro-topo">
        <h2>{jeito.grafico}</h2>
        <LegendaDoBoletim itens={[{ nome: "Realizado", cor: jeito.cor }, { nome: "Planejado", cor: "var(--cor-planejado)" }]} />
      </div>
      <Colunas meses={datas} altura={105} series={[
        { nome: "Realizado", valores: meses.map((mes) => mes.valor), cor: jeito.cor },
        { nome: "Planejado", valores: meses.map((mes) => mes.valor_previsto), cor: "var(--cor-planejado)" },
      ]} />
      <TabelaDosMeses meses={datas} cabecalho="marrom" linhas={[
        { nome: "Cab real", valores: meses.map((mes) => cabecasOuTraco(mes.realizado)) },
        { nome: "Cab plan.", valores: meses.map((mes) => cabecasOuTraco(mes.previsto)), classe: "planejado" },
        { nome: "R$ mi real", valores: meses.map((mes) => celulaEmMilhoes(mes.valor)) },
        { nome: "R$ mi plan.", valores: meses.map((mes) => celulaEmMilhoes(mes.valor_previsto)), classe: "planejado" },
      ]} />
      {secao.leitura.length > 0 && <p className="boletim-nota">{secao.leitura.join(" ")}</p>}
    </section>
  );
}

type NumerosProps = { bloco: BlocoDeComercializacao; boletim: BoletimAnalitico; secao: SecaoDeLotes };

function NumerosDoBloco({ bloco, boletim, secao }: NumerosProps) {
  const cabecas = linhaDoIndicador(secao.resumo, "Cabeças")?.acumulado;
  const valor = linhaDoIndicador(secao.resumo, bloco === "compras" ? "Investimento" : "Faturamento")?.acumulado;
  const arroba = linhaDoIndicador(secao.resumo, "Preço da @")?.acumulado;
  return (
    <div className="boletim-linha-3 compacta">
      <Indicador rotulo="Cabeças" valor={cabecasOuTraco(cabecas?.realizado ?? null)} pequeno>
        plan. {cabecasOuTraco(cabecas?.previsto ?? null)} ·{" "}
        <ComStatus status={cabecas?.status}>{variacaoComSinal(cabecas?.variacao_percentual ?? null)}</ComStatus>
      </Indicador>
      <Indicador rotulo={DO_BLOCO[bloco].valor} valor={reaisCurtos(valor?.realizado ?? null)} pequeno>
        plan. {reaisCurtos(valor?.previsto ?? null)} ·{" "}
        <ComStatus status={valor?.status}>{variacaoComSinal(valor?.variacao_percentual ?? null)}</ComStatus>
      </Indicador>
      {bloco === "compras" && (
        <Indicador rotulo="@ compra · ágio" valor={dinheiro(arroba?.realizado ?? null, 2)} pequeno>
          ágio {percentual(boletim.compras.agio, 1)} sobre a @ vendida ({dinheiro(boletim.compras.preco_arroba_venda, 2)})
        </Indicador>
      )}
      {bloco !== "compras" && (
        <Indicador rotulo="Valor da @" valor={dinheiro(arroba?.realizado ?? null, 2)} pequeno>
          plan. {dinheiro(arroba?.previsto ?? null, 2)} ·{" "}
          <ComStatus status={arroba?.status}>{variacaoComSinal(arroba?.variacao_percentual ?? null)}</ComStatus>
        </Indicador>
      )}
    </div>
  );
}

// Os indicadores escolhidos, na ordem da lista (o que a API não mandou fica de fora).
function linhasDoPlacar(resumo: LinhaDoPlacar[], indicadores: string[]): LinhaDoPlacar[] {
  const linhas: LinhaDoPlacar[] = [];
  for (const indicador of indicadores) {
    const linha = linhaDoIndicador(resumo, indicador);
    if (linha !== null) {
      linhas.push(linha);
    }
  }
  return linhas;
}

// O placar do lote no acumulado: cada indicador realizado × planejado, com a variação na unidade que se lê melhor.
function PlacarDoBloco({ linhas }: { linhas: LinhaDoPlacar[] }) {
  return (
    <table className="boletim-tabela-placar">
      <thead>
        <tr>
          <th scope="col">Indicador</th>
          <th scope="col">Realizado</th>
          <th scope="col">Planejado</th>
          <th scope="col">Var.</th>
        </tr>
      </thead>
      <tbody>
        {linhas.map((linha) => (
          <tr key={linha.indicador} className={linha.unidade === "R$" ? "total" : undefined}>
            <th scope="row">{linha.indicador}</th>
            <td>{comUnidade(linha.acumulado.realizado, linha.unidade)}</td>
            <td className="planejado">{comUnidade(linha.acumulado.previsto, linha.unidade)}</td>
            <td>
              <ComStatus status={linha.acumulado.status}>{variacaoDaLinha(linha)}</ComStatus>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// "553,1 kg", "R$ 356,04", "57,6%", "1.723"
function comUnidade(valor: number | null, unidade: string): string {
  const texto = valorComUnidade(valor, unidade);
  if (valor === null || unidade === "cab" || unidade === "%" || unidade.startsWith("R$")) {
    return texto;
  }
  return `${texto} ${unidade}`;
}
