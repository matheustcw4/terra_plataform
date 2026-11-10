import type { BoletimAnalitico, LinhaDoPlacar } from "../../../core/api/tipos";
import {
  emMilhoes,
  type Identificacao,
  linhaDoIndicador,
  maiorValor,
  reaisCurtos,
  variacaoComSinal,
} from "../../../logic/boletim";
import { dinheiro, numero, percentual } from "../../../logic/formatar";
import { BarrasDeitadas } from "./BarrasDeitadas";
import { Colunas } from "./Colunas";
import { FolhaDoBoletim, QuadroDoBoletim } from "./FolhaDoBoletim";
import { ComStatus, Indicador } from "./Indicador";

type Props = { boletim: BoletimAnalitico; identificacao: Identificacao; numero: number; total: number };

// A folha do Financeiro: desembolso e custeio por cabeça por mês e o preço da @ vendida contra a meta, o desembolso e
// as receitas do período, os três gráficos mês a mês e o desembolso por grupo (centro de custo) com a participação.
export function FolhaFinanceiro({ boletim, identificacao, numero: numeroDaFolha, total }: Props) {
  const placar = boletim.financeiro.placar;
  const porCabeca = linhaDoIndicador(placar, "Desembolso por cabeça");
  const leitura = boletim.financeiro.leitura;
  return (
    <FolhaDoBoletim numero={numeroDaFolha} total={total} titulo="Financeiro" identificacao={identificacao}>
      <div className="boletim-linha-4">
        <IndicadorEmReais rotulo="Desembolso cab/mês" linha={porCabeca} />
        <IndicadorEmReais rotulo="Custeio cab/mês" linha={linhaDoIndicador(placar, "Custeio por cabeça")} />
        <IndicadorEmReais rotulo="Valor de venda @" linha={linhaDoIndicador(placar, "Preço da @ vendida")} />
        <TotaisDoPeriodo placar={placar} />
      </div>
      <div className="boletim-linha-3">
        <DesembolsoPorCabeca boletim={boletim} meta={porCabeca?.acumulado.previsto ?? null} nota={leitura[1]} />
        <QuadroDoBoletim titulo="Desembolso total por mês · R$ mi" nota={leitura[0]}>
          <Colunas meses={boletim.financeiro.meses.map((mes) => mes.mes)} altura={165} series={[
            { nome: "Desembolso", valores: boletim.financeiro.meses.map((mes) => mes.desembolso),
              cor: "var(--cor-despesa)", rotulo: emMilhoes },
          ]} />
        </QuadroDoBoletim>
        <QuadroDoBoletim titulo="Receitas por mês · R$ mi">
          <Colunas meses={boletim.financeiro.meses.map((mes) => mes.mes)} altura={165} series={[
            { nome: "Receitas", valores: boletim.financeiro.meses.map((mes) => mes.receitas),
              cor: "var(--cor-receita)", rotulo: emMilhoes },
          ]} />
        </QuadroDoBoletim>
      </div>
      <DesembolsoPorGrupo boletim={boletim} nota={leitura[2]} />
    </FolhaDoBoletim>
  );
}

function IndicadorEmReais({ rotulo, linha }: { rotulo: string; linha: LinhaDoPlacar | null }) {
  const acumulado = linha?.acumulado;
  return (
    <Indicador rotulo={rotulo} valor={dinheiro(acumulado?.realizado ?? null, 2)} status={acumulado?.status}>
      Meta {dinheiro(acumulado?.previsto ?? null, 2)} ·{" "}
      <ComStatus status={acumulado?.status}>{variacaoComSinal(acumulado?.variacao_percentual ?? null)}</ComStatus>
    </Indicador>
  );
}

function TotaisDoPeriodo({ placar }: { placar: LinhaDoPlacar[] }) {
  const desembolso = linhaDoIndicador(placar, "Desembolso")?.acumulado;
  const receitas = linhaDoIndicador(placar, "Receitas")?.acumulado;
  return (
    <section className="boletim-indicador boletim-totais">
      <dl>
        <div>
          <dt>Desembolso</dt>
          <dd>{dinheiro(desembolso?.realizado ?? null)}</dd>
        </div>
        <div>
          <dt>Receitas</dt>
          <dd className="receitas">{dinheiro(receitas?.realizado ?? null)}</dd>
        </div>
      </dl>
      <p>
        Planejado: {reaisCurtos(desembolso?.previsto ?? null)} de desembolso e {reaisCurtos(receitas?.previsto ?? null)}{" "}
        de receitas
      </p>
    </section>
  );
}

type PorCabecaProps = { boletim: BoletimAnalitico; meta: number | null; nota: string | undefined };

function DesembolsoPorCabeca({ boletim, meta, nota }: PorCabecaProps) {
  const meses = boletim.financeiro.meses;
  return (
    <QuadroDoBoletim titulo="Desembolso por cabeça/mês" nota={nota}
      direita={<span className="boletim-meta">- - meta {dinheiro(meta, 2)}</span>}>
      <Colunas meses={meses.map((mes) => mes.mes)} meta={meta} altura={165} series={[
        { nome: "Desembolso por cabeça", valores: meses.map((mes) => mes.desembolso_por_cabeca),
          cor: "var(--cor-realizado)", rotulo: numeroInteiro },
      ]} />
    </QuadroDoBoletim>
  );
}

function numeroInteiro(valor: number | null): string {
  return numero(valor);
}

function DesembolsoPorGrupo({ boletim, nota }: { boletim: BoletimAnalitico; nota: string | undefined }) {
  const barras = boletim.financeiro.centros.map((centro) => ({
    rotulo: centro.centro_custo, valor: centro.valor_acumulado, texto: reaisCurtos(centro.valor_acumulado),
    extra: percentual(centro.participacao, 1),
  }));
  const metade = Math.ceil(barras.length / 2);
  const escala = maiorValor([barras.map((barra) => barra.valor)]);
  const total = linhaDoIndicador(boletim.financeiro.placar, "Desembolso")?.acumulado.realizado ?? null;
  return (
    <QuadroDoBoletim titulo="Desembolso por grupo · acumulado" className="boletim-grupos" nota={nota}
      direita={<span>Total <strong>{reaisCurtos(total)}</strong> · valor e participação</span>}>
      <div className="boletim-duas-colunas">
        <BarrasDeitadas barras={barras.slice(0, metade)} escala={escala} />
        <BarrasDeitadas barras={barras.slice(metade)} escala={escala} primeira={metade} />
      </div>
    </QuadroDoBoletim>
  );
}
