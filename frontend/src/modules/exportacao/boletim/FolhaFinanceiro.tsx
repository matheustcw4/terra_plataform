import type { BoletimAnalitico, LinhaDoPlacar } from "../../../core/api/tipos";
import {
  type Identificacao,
  linhaDoIndicador,
  maiorValor,
  naUnidade,
  reaisCurtos,
  unidadeDosValores,
  variacaoComSinal,
} from "../../../logic/boletim";
import { dinheiro, numero, percentual } from "../../../logic/formatar";
import { mesCurto } from "../../../logic/meses";
import { BarrasDeitadas } from "./BarrasDeitadas";
import { Colunas } from "./Colunas";
import { FolhaDoBoletim } from "./FolhaDoBoletim";
import { ComStatus, corDoStatus, Indicador } from "./Indicador";

type Props = { boletim: BoletimAnalitico; identificacao: Identificacao; numero: number; total: number };

const NOTA_DOS_INDICADORES = "Indicadores cab/mês e @ conforme o sistema";

// A folha do Financeiro, como a do gerador oficial: desembolso e custeio por cabeça por mês e o valor da @ vendida
// contra a meta, o desembolso e as receitas do período, os três gráficos mês a mês e todos os grupos de desembolso
// (centros de custo) com a participação.
export function FolhaFinanceiro({ boletim, identificacao, numero: numeroDaFolha, total }: Props) {
  const placar = boletim.financeiro.placar;
  return (
    <FolhaDoBoletim numero={numeroDaFolha} total={total} titulo="Financeiro" identificacao={identificacao}
      nota={NOTA_DOS_INDICADORES}>
      <main className="boletim-corpo">
        <section className="boletim-grade-4">
          <IndicadorEmReais rotulo="Desembolso cab/mês" linha={linhaDoIndicador(placar, "Desembolso por cabeça")} />
          <IndicadorEmReais rotulo="Custeio cab/mês" linha={linhaDoIndicador(placar, "Custeio por cabeça")} />
          <IndicadorEmReais rotulo="Valor de venda @" linha={linhaDoIndicador(placar, "Preço da @ vendida")} />
          <TotaisDoPeriodo placar={placar} />
        </section>
        <GraficosDoMes boletim={boletim} />
        <DesembolsoPorGrupo boletim={boletim} />
      </main>
    </FolhaDoBoletim>
  );
}

function IndicadorEmReais({ rotulo, linha }: { rotulo: string; linha: LinhaDoPlacar | null }) {
  const acumulado = linha?.acumulado;
  return (
    <Indicador rotulo={rotulo} valor={dinheiro(acumulado?.realizado ?? null, 2)}
      cor={corDoStatus(acumulado?.status, "var(--cor-marrom)")}>
      Meta {dinheiro(acumulado?.previsto ?? null, 2)} ·{" "}
      <ComStatus status={acumulado?.status}>{variacaoComSinal(acumulado?.variacao_percentual ?? null)}</ComStatus>
    </Indicador>
  );
}

function TotaisDoPeriodo({ placar }: { placar: LinhaDoPlacar[] }) {
  const desembolso = linhaDoIndicador(placar, "Desembolso")?.acumulado.realizado ?? null;
  const receitas = linhaDoIndicador(placar, "Receitas")?.acumulado.realizado ?? null;
  return (
    <div className="boletim-card boletim-totais" style={{ borderTop: "4px solid var(--cor-marrom)" }}>
      <div>
        <span className="boletim-lbl">Desembolso</span>
        <span className="boletim-big">{dinheiro(desembolso)}</span>
      </div>
      <div>
        <span className="boletim-lbl">Receitas</span>
        <span className="boletim-big receitas">{dinheiro(receitas)}</span>
      </div>
    </div>
  );
}

function GraficosDoMes({ boletim }: { boletim: BoletimAnalitico }) {
  const meses = boletim.financeiro.meses;
  const eixo = meses.map((mes) => mesCurto(mes.mes));
  const desembolso = meses.map((mes) => mes.desembolso);
  const receitas = meses.map((mes) => mes.receitas);
  const unidade = unidadeDosValores([desembolso, receitas]);
  const porCabeca = meses.map((mes) => mes.desembolso_por_cabeca);
  const meta = linhaDoIndicador(boletim.financeiro.placar, "Desembolso por cabeça")?.acumulado.previsto ?? null;
  return (
    <section className="boletim-grade-3">
      <div className="boletim-card boletim-quadro">
        <div className="boletim-quadro-topo">
          <span className="boletim-lbl marinho">Desembolso por cabeça/mês · R$</span>
          <span className="boletim-meta">- - meta {dinheiro(meta, 2)}</span>
        </div>
        <Colunas eixo={eixo} altura={220} meta={meta} series={[
          { nome: "Desembolso por cabeça", valores: porCabeca, cor: "var(--cor-realizado)", rotulo: valorPorCabeca,
            destaques: porCabeca.map((valor) => acimaDaMeta(valor, meta)) },
        ]} />
      </div>
      <div className="boletim-card boletim-quadro">
        <span className="boletim-lbl marinho">Desembolso total por mês · {unidade.rotulo}</span>
        <Colunas eixo={eixo} altura={220} series={[
          { nome: "Desembolso", valores: desembolso, cor: "var(--cor-despesa)",
            rotulo: (valor) => naUnidade(valor, unidade) },
        ]} />
      </div>
      <div className="boletim-card boletim-quadro">
        <span className="boletim-lbl marinho">Receitas por mês · {unidade.rotulo}</span>
        <Colunas eixo={eixo} altura={220} series={[
          { nome: "Receitas", valores: receitas, cor: "var(--cor-receita)", rotulo: (valor) => naUnidade(valor, unidade) },
        ]} />
      </div>
    </section>
  );
}

// "945" ou "945,3": abaixo de mil, uma casa (como o gerador)
function valorPorCabeca(valor: number): string {
  if (Math.abs(valor) < 1000) {
    return numero(valor, 1);
  }
  return numero(valor);
}

// o mês acima da meta tem o número em vermelho
function acimaDaMeta(valor: number | null, meta: number | null): boolean {
  if (valor === null || meta === null) {
    return false;
  }
  return valor > meta;
}

function DesembolsoPorGrupo({ boletim }: { boletim: BoletimAnalitico }) {
  const barras = boletim.financeiro.centros.map((centro) => ({
    nome: centro.centro_custo, valor: centro.valor_acumulado, texto: numero(centro.valor_acumulado / 1000, 1),
    participacao: percentual(centro.participacao, 1),
  }));
  const metade = Math.ceil(barras.length / 2);
  const escala = maiorValor([barras.map((barra) => barra.valor)]);
  return (
    <section className="boletim-card boletim-quadro boletim-grupos">
      <div className="boletim-quadro-topo">
        <span className="boletim-lbl marinho">Desembolso por grupo · acumulado</span>
        <span className="boletim-sub">
          Total <b>{reaisCurtos(boletim.resumo.desembolso_total)}</b> · R$ mil e participação
        </span>
      </div>
      <div className="boletim-duas-colunas">
        <BarrasDeitadas barras={barras.slice(0, metade)} colunas="230px 1fr 70px" escala={escala} />
        <BarrasDeitadas barras={barras.slice(metade)} colunas="230px 1fr 70px" escala={escala} primeira={metade} />
      </div>
    </section>
  );
}
