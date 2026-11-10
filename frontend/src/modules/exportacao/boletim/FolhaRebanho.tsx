import type { BoletimAnalitico, MortalidadeDoGrupo, SecaoDeLotes } from "../../../core/api/tipos";
import {
  ateAReferencia,
  cabeONumeroDoPlanejado,
  type Identificacao,
  linhaDoIndicador,
  mesDoEixo,
  nomeLegivel,
  percentualDaMeta,
  temMovimento,
} from "../../../logic/boletim";
import { dinheiro, numero, percentual } from "../../../logic/formatar";
import { mesCurto } from "../../../logic/meses";
import { BarrasDeitadas } from "./BarrasDeitadas";
import { Colunas } from "./Colunas";
import { FolhaDoBoletim, TituloDaParte } from "./FolhaDoBoletim";
import { ComStatus, Indicador, LegendaDoBoletim } from "./Indicador";
import { TabelaDosMeses } from "./TabelaDosMeses";

type Props = { boletim: BoletimAnalitico; identificacao: Identificacao; numero: number; total: number };

const NOMES_DOS_GRUPOS: Record<string, string> = {
  BEZERROS: "Bezerros", JOVENS: "Jovens", ADULTOS: "Adultos", GERAL: "Geral",
};

// A folha do Rebanho, como a do gerador oficial: rebanho médio, lotação, rebanho final, mortes e compras × vendas e,
// em três colunas, a movimentação do estoque, as mortes (por faixa, por causa e por mês) e os nascimentos e
// transferências (ou o quadro que diz que não houve).
export function FolhaRebanho({ boletim, identificacao, numero: numeroDaFolha, total }: Props) {
  return (
    <FolhaDoBoletim numero={numeroDaFolha} total={total} titulo="Rebanho" identificacao={identificacao}>
      <main className="boletim-corpo apertado">
        <NumerosDoRebanho boletim={boletim} identificacao={identificacao} />
        <section className="boletim-rebanho">
          <Movimentacao boletim={boletim} />
          <Mortes boletim={boletim} />
          <div className="boletim-coluna-estreita">
            <Nascimentos secao={boletim.nascimentos} mesDeReferencia={boletim.mes_referencia} />
            <Transferencias boletim={boletim} />
          </div>
        </section>
      </main>
    </FolhaDoBoletim>
  );
}

function NumerosDoRebanho({ boletim, identificacao }: { boletim: BoletimAnalitico; identificacao: Identificacao }) {
  const lotacao = boletim.lotacao;
  const mortes = linhaDoIndicador(boletim.placar_zootecnico.linhas, "Mortes")?.acumulado;
  const mortalidade = linhaDoIndicador(boletim.placar_zootecnico.linhas, "Mortalidade")?.acumulado;
  const resumo = boletim.resumo;
  let corDasMortes = "var(--cor-status-verde)";
  let statusDasMortes = "verde";
  if ((mortes?.realizado ?? 0) > (mortes?.previsto ?? 0)) {
    corDasMortes = "var(--cor-status-vermelho)";
    statusDasMortes = "vermelho";
  }
  let rebanhoEmUa = identificacao.periodo;
  if (lotacao.rebanho_medio_ua !== null) {
    rebanhoEmUa = `${numero(lotacao.rebanho_medio_ua)} UA`;
  }
  let lotacaoEmUa = "UA não informada";
  if (lotacao.lotacao_ua_ha !== null) {
    lotacaoEmUa = `${numero(lotacao.lotacao_ua_ha, 2)} UA/ha`;
  }
  let lotacaoEmCabecas = "—";
  if (lotacao.lotacao_cab_ha !== null) {
    lotacaoEmCabecas = `${numero(lotacao.lotacao_cab_ha, 2)} cab/ha`;
  }
  return (
    <section className="boletim-grade-5">
      <Indicador rotulo="Rebanho médio" valor={`${numero(lotacao.rebanho_medio_cab)} cab`} cor="var(--cor-marinho)">
        {rebanhoEmUa}
      </Indicador>
      <Indicador rotulo="Lotação" valor={lotacaoEmCabecas} cor="var(--cor-marinho)">{lotacaoEmUa}</Indicador>
      <Indicador rotulo="Rebanho final" valor={`${numero(lotacao.estoque_final)} cab`} cor="var(--cor-marinho)">
        Estoque ao fim do período
      </Indicador>
      <Indicador rotulo="Mortes" valor={`${numero(mortes?.realizado ?? null)} cab`} cor={corDasMortes}>
        <ComStatus status={statusDasMortes}>{percentualDaMeta(mortes?.percentual_da_meta ?? null)}</ComStatus> da meta
        · mortalidade {percentual(mortalidade?.realizado ?? null, 2)}
      </Indicador>
      <Indicador rotulo="Compras · Vendas" cor="var(--cor-marrom)"
        valor={`${numero(resumo.compras.realizado)} · ${numero(resumo.vendas.realizado)}`}>
        {percentualDaMeta(resumo.compras.percentual_da_meta)} e {percentualDaMeta(resumo.vendas.percentual_da_meta)} da
        meta
      </Indicador>
    </section>
  );
}

function Movimentacao({ boletim }: { boletim: BoletimAnalitico }) {
  const meses = ateAReferencia(boletim.lotacao.meses, boletim.mes_referencia);
  const categorias = boletim.estoque.distribuicao_final.map((fatia) => ({
    nome: nomeLegivel(fatia.categoria), valor: fatia.cabecas, texto: numero(fatia.cabecas),
  }));
  return (
    <div className="boletim-card boletim-quadro">
      <TituloDaParte numero="04">Movimentação</TituloDaParte>
      <span className="boletim-lbl marinho">Estoque final mensal · cab</span>
      <Colunas eixo={meses.map((mes) => mesCurto(mes.mes))} altura={180} series={[
        { nome: "Estoque final", valores: meses.map((mes) => mes.estoque_final), cor: "var(--cor-realizado)",
          rotulo: (valor) => numero(valor) },
      ]} />
      <div className="boletim-quadro-topo">
        <span className="boletim-lbl marinho">Estoque por categoria · cab</span>
        <span className="boletim-sub">Total <b>{numero(boletim.lotacao.estoque_final)}</b></span>
      </div>
      <BarrasDeitadas barras={categorias} colunas="130px 1fr 50px" />
    </div>
  );
}

function Mortes({ boletim }: { boletim: BoletimAnalitico }) {
  const mortes = boletim.mortes;
  const meses = ateAReferencia(mortes.meses, boletim.mes_referencia);
  const causas = mortes.causas.map((causa) => ({
    nome: nomeLegivel(causa.causa), valor: causa.total, texto: numero(causa.total),
  }));
  const realizadas = meses.map((mes) => mes.realizado);
  const previstas = meses.map((mes) => mes.previsto);
  const rotuloDoPlanejado = cabeONumeroDoPlanejado(meses.length) ? mortesDoMes : undefined;
  return (
    <div className="boletim-card boletim-quadro">
      <TituloDaParte numero="05">Mortes</TituloDaParte>
      <div className="boletim-mortes-grupos">
        {mortes.por_grupo.map((grupo) => (
          <MortesDoGrupo key={grupo.grupo} grupo={grupo} />
        ))}
      </div>
      <div className="boletim-mortes-meio">
        <div>
          <span className="boletim-lbl marinho">Causa da morte · cab</span>
          <BarrasDeitadas barras={causas} colunas="150px 1fr 26px" tom="marrom" />
        </div>
        <div>
          <div className="boletim-quadro-topo">
            <span className="boletim-lbl marinho">Por mês</span>
            <LegendaDoBoletim itens={[{ nome: "Real", cor: "var(--cor-marrom)" },
              { nome: "Plan.", cor: "var(--cor-planejado)" }]} />
          </div>
          <Colunas eixo={meses.map((mes) => mesDoEixo(mes.mes))} altura={150} series={[
            { nome: "Real", valores: realizadas, cor: "var(--cor-marrom)", rotulo: mortesDoMes,
              destaques: meses.map((mes) => (mes.realizado ?? 0) > mes.previsto) },
            { nome: "Plan.", valores: previstas, cor: "var(--cor-planejado)", rotulo: rotuloDoPlanejado,
              corDoRotulo: "var(--boletim-cinza)" },
          ]} />
        </div>
      </div>
      <TabelaDosMeses titulo="Acumulado" meses={meses.map((mes) => mes.mes)} linhas={[
        { nome: "Realizado", valores: meses.map((mes) => mortesDoMes(mes.realizado_acumulado ?? 0)) },
        { nome: "Planejado", valores: meses.map((mes) => mortesDoMes(mes.previsto_acumulado)), apagado: true },
      ]} />
    </div>
  );
}

// a meta de mortes do mês pode ter casa decimal (10,3); a morte realizada, não
function mortesDoMes(valor: number): string {
  if (Number.isInteger(valor)) {
    return numero(valor);
  }
  return numero(valor, 1);
}

// A caixinha de uma faixa (bezerros, jovens, adultos, geral): fica vermelha quando as mortes passam da meta.
function MortesDoGrupo({ grupo }: { grupo: MortalidadeDoGrupo }) {
  let classes = "boletim-morte";
  if (grupo.mortes > grupo.mortes_previstas) {
    classes += " acima";
  }
  return (
    <div className={classes}>
      <span className="boletim-lbl">{NOMES_DOS_GRUPOS[grupo.grupo] ?? grupo.grupo}</span>
      <span className="boletim-big">{numero(grupo.mortes)}</span>
      <span className="boletim-sub">
        meta {mortesDoMes(grupo.mortes_previstas)} · {percentual(grupo.realizado, 2)}
      </span>
    </div>
  );
}

function Nascimentos({ secao, mesDeReferencia }: { secao: SecaoDeLotes; mesDeReferencia: string }) {
  if (!temMovimento(secao)) {
    return (
      <div className="boletim-card boletim-quadro crescer sem-movimento">
        <span className="boletim-lbl marinho">Sem nascimentos no período</span>
        <div className="boletim-quadro-topo">
          <span className="boletim-sub">Nascimentos</span>
          <b>0 · plan. 0</b>
        </div>
        <span className="boletim-sub boletim-ate-o-fim">
          Seção resumida: não houve nascimentos realizados nem planejados.
        </span>
      </div>
    );
  }
  const femeas = linhaDoIndicador(secao.resumo, "Fêmeas")?.acumulado;
  const machos = linhaDoIndicador(secao.resumo, "Machos")?.acumulado;
  const nascidos = linhaDoIndicador(secao.resumo, "Total")?.acumulado;
  const meses = ateAReferencia(secao.meses, mesDeReferencia);
  const rotuloDoPlanejado = cabeONumeroDoPlanejado(meses.length) ? numeroInteiro : undefined;
  return (
    <div className="boletim-card boletim-quadro crescer">
      <TituloDaParte numero="06">Nascimentos</TituloDaParte>
      <table className="boletim-tb">
        <thead>
          <tr>
            <th scope="col" className="esquerda">Sexo</th>
            <th scope="col">Real</th>
            <th scope="col">Plan.</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td className="nome">Fêmeas</td>
            <td>{numero(femeas?.realizado ?? null)}</td>
            <td className="apagado">{numero(femeas?.previsto ?? null)}</td>
          </tr>
          <tr>
            <td className="nome">Machos</td>
            <td>{numero(machos?.realizado ?? null)}</td>
            <td className="apagado">{numero(machos?.previsto ?? null)}</td>
          </tr>
          <tr className="total">
            <td className="nome">Total</td>
            <td>{numero(nascidos?.realizado ?? null)}</td>
            <td>{numero(nascidos?.previsto ?? null)}</td>
          </tr>
        </tbody>
      </table>
      <span className="boletim-sub">
        <ComStatus status={nascidos?.status}>{percentualDaMeta(nascidos?.percentual_da_meta ?? null)}</ComStatus> da meta
      </span>
      <Colunas eixo={meses.map((mes) => mesDoEixo(mes.mes))} altura={130} series={[
        { nome: "Real", valores: meses.map((mes) => mes.realizado), cor: "var(--cor-realizado)",
          rotulo: numeroInteiro },
        { nome: "Plan.", valores: meses.map((mes) => mes.previsto), cor: "var(--cor-planejado)",
          rotulo: rotuloDoPlanejado, corDoRotulo: "var(--boletim-cinza)" },
      ]} />
    </div>
  );
}

function numeroInteiro(valor: number): string {
  return numero(valor);
}

// Entradas e saídas por transferência no período, ou a frase de que não houve.
function Transferencias({ boletim }: { boletim: BoletimAnalitico }) {
  const secoes = [boletim.transferencias.entradas, boletim.transferencias.saidas].filter(temMovimento);
  return (
    <div className="boletim-card boletim-quadro">
      <TituloDaParte numero="07">Transferências</TituloDaParte>
      {secoes.length === 0 && <span className="boletim-sub">Sem transferências no período.</span>}
      {secoes.map((secao) => (
        <Transferencia key={secao.tipo} secao={secao} />
      ))}
    </div>
  );
}

function Transferencia({ secao }: { secao: SecaoDeLotes }) {
  const cabecas = linhaDoIndicador(secao.resumo, "Cabeças")?.acumulado;
  const peso = linhaDoIndicador(secao.resumo, "Peso médio")?.acumulado;
  const arroba = linhaDoIndicador(secao.resumo, "Valor da @")?.acumulado;
  let planejado = "não planejada";
  if (cabecas?.previsto) {
    planejado = `plan. ${numero(cabecas.previsto)} cab`;
  }
  return (
    <>
      <div className="boletim-transferencia">
        <span>{secao.titulo}</span>
        <b>{numero(cabecas?.realizado ?? null)} cab</b>
      </div>
      <span className="boletim-sub">
        {numero(peso?.realizado ?? null, 1)} kg · @ {dinheiro(arroba?.realizado ?? null, 2)} · {planejado}
      </span>
    </>
  );
}
