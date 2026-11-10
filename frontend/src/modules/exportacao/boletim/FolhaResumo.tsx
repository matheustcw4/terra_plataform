import type { ReactNode } from "react";
import logoBranco from "../../../assets/boletim/logo_terra_branco.png";
import type { BoletimAnalitico, Comparacao, GrupoDoPrevisto, SecaoDeLotes } from "../../../core/api/tipos";
import {
  ateAReferencia,
  cabeONumeroDoPlanejado,
  diferencaCompacta,
  diferencaDoResultado,
  doisDigitos,
  ehParteDoDesembolso,
  grupoDaLetra,
  type Identificacao,
  LEMA_DA_TERRA,
  linhaDoIndicador,
  mesComAno,
  mesDoEixo,
  naUnidade,
  nomeDaClassificacao,
  percentualDaMeta,
  reaisCurtos,
  rotuloDaPagina,
  secaoDeVenda,
  semMoeda,
  SITE_DA_TERRA,
  unidadeDosValores,
  variacaoComSinal,
} from "../../../logic/boletim";
import { dinheiro, numero, percentual } from "../../../logic/formatar";
import { mesCurto } from "../../../logic/meses";
import { BarrasDeitadas } from "./BarrasDeitadas";
import { Colunas } from "./Colunas";
import { Bolinha, ComStatus, LegendaDoBoletim } from "./Indicador";

type Props = { boletim: BoletimAnalitico; identificacao: Identificacao; numero: number; total: number };

// A folha 01 do boletim de resultados, como a do gerador oficial: na lateral marinho, a fazenda e os quatro números do
// período (resultado, receitas × desembolso, rebanho e vendas × compras); ao lado, o Previsto × Realizado do caixa, o
// fluxo de caixa mês a mês, o desembolso por grupo e as cabeças vendidas e compradas mês a mês.
export function FolhaResumo({ boletim, identificacao, numero: numeroDaFolha, total }: Props) {
  return (
    <section className="boletim-folha boletim-resumo" aria-label="Resumo">
      <LateralDoResumo boletim={boletim} identificacao={identificacao} />
      <main className="boletim-resumo-conteudo">
        <div className="boletim-resumo-topo">
          <div className="boletim-resumo-titulo">
            <span className="boletim-selo">{doisDigitos(numeroDaFolha)}</span>
            <h2>Previsto × Realizado</h2>
          </div>
          <div className="boletim-legenda">
            <span><Bolinha status="verde" /> Dentro da meta</span>
            <span><Bolinha status="amarelo" /> Até 3% acima</span>
            <span><Bolinha status="vermelho" /> Acima de 3%</span>
            <span className="boletim-resumo-pagina">{rotuloDaPagina(numeroDaFolha, total)}</span>
          </div>
        </div>
        <div className="boletim-resumo-alto">
          <TabelaDoCaixa boletim={boletim} identificacao={identificacao} />
          <FluxoDeCaixa boletim={boletim} />
        </div>
        <div className="boletim-resumo-baixo">
          <DesembolsoPorGrupo boletim={boletim} />
          <VendaAbate boletim={boletim} />
          <Compras boletim={boletim} />
        </div>
      </main>
    </section>
  );
}

function LateralDoResumo({ boletim, identificacao }: { boletim: BoletimAnalitico; identificacao: Identificacao }) {
  const caixa = boletim.caixa.previsto_realizado;
  const resultado = caixa.resultado.acumulado;
  const receitas = grupoDaLetra(caixa.grupos, "A")?.total.acumulado ?? null;
  const desembolso = grupoDaLetra(caixa.grupos, "B")?.total.acumulado ?? null;
  const lotacao = boletim.lotacao;
  const resumo = boletim.resumo;
  let lotacaoNoTexto = "";
  if (lotacao.lotacao_cab_ha !== null) {
    lotacaoNoTexto = ` · lotação ${numero(lotacao.lotacao_cab_ha, 2)} cab/ha`;
  }
  let classeDoNome: string | undefined = undefined;
  if (identificacao.titulo.length > 10) {
    classeDoNome = "longo";
  }
  return (
    <aside className="boletim-resumo-lateral">
      <img className="boletim-resumo-logo" src={logoBranco} alt="Terra Desenvolvimento Agropecuário" />
      <div className="boletim-resumo-nome">
        <span className="boletim-resumo-rotulo">BOLETIM MENSAL · {identificacao.rotuloDoPeriodo}</span>
        <h1 className={classeDoNome}>{identificacao.titulo}</h1>
        <p>
          {identificacao.cliente} · {identificacao.periodo} ({identificacao.meses} meses) · {identificacao.planejamento}
        </p>
      </div>
      <div className="boletim-resumo-numeros">
        <NumeroDaLateral rotulo="Resultado acumulado" valor={reaisCurtos(resultado.realizado)} tamanho="grande">
          Plan. {reaisCurtos(resultado.planejado)} ·{" "}
          <ComStatus status={resumo.status_do_resultado_acumulado}>{diferencaDoResultado(resultado.diferenca)}</ComStatus>
        </NumeroDaLateral>
        <NumeroDaLateral rotulo="Receitas · Desembolso" tamanho="medio"
          valor={`${reaisCurtos(receitas?.realizado ?? null)} · ${reaisCurtos(desembolso?.realizado ?? null)}`}>
          <ComStatus status={receitas?.semaforo}>{variacaoComSinal(receitas?.variacao ?? null)}</ComStatus> e{" "}
          <ComStatus status={desembolso?.semaforo}>{variacaoComSinal(desembolso?.variacao ?? null)}</ComStatus> sobre o
          planejado
        </NumeroDaLateral>
        <NumeroDaLateral rotulo="Rebanho final" valor={`${numero(lotacao.estoque_final)} cab`}>
          Médio {numero(lotacao.rebanho_medio_cab)} cab{lotacaoNoTexto}
        </NumeroDaLateral>
        <NumeroDaLateral rotulo="Vendas · Compras"
          valor={`${numero(resumo.vendas.realizado)} · ${numero(resumo.compras.realizado)} cab`}>
          {percentualDaMeta(resumo.vendas.percentual_da_meta)} e {percentualDaMeta(resumo.compras.percentual_da_meta)}{" "}
          da meta
        </NumeroDaLateral>
      </div>
      <div className="boletim-resumo-pe">
        <em>{LEMA_DA_TERRA}</em>
        <span>{SITE_DA_TERRA} · {identificacao.localEData}</span>
      </div>
    </aside>
  );
}

type NumeroProps = { rotulo: string; valor: string; tamanho?: "grande" | "medio"; children: ReactNode };

function NumeroDaLateral({ rotulo, valor, tamanho, children }: NumeroProps) {
  let classes = "boletim-big";
  if (tamanho !== undefined) {
    classes += ` ${tamanho}`;
  }
  return (
    <div className="boletim-kp">
      <span className="boletim-kp-rotulo">{rotulo}</span>
      <span className={classes}>{valor}</span>
      <span className="boletim-kp-sub">{children}</span>
    </div>
  );
}

// O Previsto × Realizado do caixa, só os totais de cada classificação: o mês de referência e o acumulado.
function TabelaDoCaixa({ boletim, identificacao }: { boletim: BoletimAnalitico; identificacao: Identificacao }) {
  const caixa = boletim.caixa.previsto_realizado;
  const observacao = boletim.caixa.leitura[0];
  return (
    <div className="boletim-card boletim-resumo-caixa">
      <table className="boletim-tb">
        <thead>
          <tr>
            <th scope="col" />
            <th scope="colgroup" colSpan={3} className="faixa-mes">Mensal · {mesComAno(caixa.ultimo_mes)}</th>
            <th scope="colgroup" colSpan={3} className="faixa-acumulado">Acumulado · {identificacao.periodo}</th>
          </tr>
          <tr>
            <th scope="col" className="esquerda">Conta (R$)</th>
            <th scope="col">Realizado</th>
            <th scope="col">Planejado</th>
            <th scope="col">Var.</th>
            <th scope="col">Realizado</th>
            <th scope="col">Planejado</th>
            <th scope="col">Var.</th>
          </tr>
        </thead>
        <tbody>
          {caixa.grupos.map((grupo) => (
            <LinhaDoCaixa key={grupo.classificacao} grupo={grupo} />
          ))}
          <tr className="total">
            <td className="nome">Resultado</td>
            <CelulasDoResultado comparacao={caixa.resultado.mensal}
              status={boletim.resumo.status_do_resultado_mes} />
            <CelulasDoResultado comparacao={caixa.resultado.acumulado}
              status={boletim.resumo.status_do_resultado_acumulado} />
          </tr>
        </tbody>
      </table>
      {observacao !== undefined && <p>{observacao}</p>}
    </div>
  );
}

function LinhaDoCaixa({ grupo }: { grupo: GrupoDoPrevisto }) {
  let classeDoNome = "nome";
  if (ehParteDoDesembolso(grupo.classificacao)) {
    classeDoNome = "nome parte";
  }
  return (
    <tr>
      <td className={classeDoNome}>{nomeDaClassificacao(grupo.classificacao)}</td>
      <CelulasDoCaixa comparacao={grupo.total.mensal} />
      <CelulasDoCaixa comparacao={grupo.total.acumulado} />
    </tr>
  );
}

function CelulasDoCaixa({ comparacao }: { comparacao: Comparacao }) {
  return (
    <>
      <td>{numero(comparacao.realizado)}</td>
      <td className="apagado">{numero(comparacao.planejado)}</td>
      {comparacao.variacao === null && <td className="apagado">—</td>}
      {comparacao.variacao !== null && (
        <td>
          {percentual(comparacao.variacao, 1)}
          <Bolinha status={comparacao.semaforo} />
        </td>
      )}
    </>
  );
}

// No resultado vale a diferença em reais, e a bolinha é a do boletim: verde quando o realizado chega ao planejado.
function CelulasDoResultado({ comparacao, status }: { comparacao: Comparacao; status: string | null }) {
  return (
    <>
      <td>{numero(comparacao.realizado)}</td>
      <td>{numero(comparacao.planejado)}</td>
      <td>
        {diferencaCompacta(comparacao.diferenca)}
        <Bolinha status={status} />
      </td>
    </>
  );
}

function FluxoDeCaixa({ boletim }: { boletim: BoletimAnalitico }) {
  const meses = boletim.financeiro.meses;
  const receitas = meses.map((mes) => mes.receitas);
  const despesas = meses.map((mes) => mes.desembolso);
  const unidade = unidadeDosValores([receitas, despesas]);
  return (
    <div className="boletim-card boletim-quadro boletim-resumo-fluxo">
      <div className="boletim-quadro-topo">
        <span className="boletim-lbl marinho">Fluxo de caixa mensal · {unidade.rotulo}</span>
        <LegendaDoBoletim itens={[{ nome: "Receitas", cor: "var(--cor-realizado)" },
          { nome: "Despesas", cor: "var(--cor-despesa)" }]} />
      </div>
      <Colunas eixo={meses.map((mes) => mesCurto(mes.mes))} altura={210} series={[
        { nome: "Receitas", valores: receitas, cor: "var(--cor-realizado)",
          rotulo: (valor) => naUnidade(valor, unidade) },
        { nome: "Despesas", valores: despesas, cor: "var(--cor-despesa)", rotulo: (valor) => naUnidade(valor, unidade) },
      ]} />
    </div>
  );
}

function DesembolsoPorGrupo({ boletim }: { boletim: BoletimAnalitico }) {
  const barras = boletim.resumo.desembolso_por_grupo.map((grupo) => ({
    nome: grupo.nome, valor: grupo.valor, texto: semMoeda(grupo.valor),
  }));
  return (
    <div className="boletim-card boletim-quadro">
      <span className="boletim-lbl marinho">Desembolso por grupo · acumulado</span>
      <BarrasDeitadas barras={barras} colunas="150px 1fr 60px" />
      <span className="boletim-sub rodape-do-quadro">Total {reaisCurtos(boletim.resumo.desembolso_total)}</span>
    </div>
  );
}

function VendaAbate({ boletim }: { boletim: BoletimAnalitico }) {
  const abate = secaoDeVenda(boletim, "abate");
  const faturamento = linhaDoIndicador(abate.resumo, "Faturamento")?.acumulado;
  const arroba = linhaDoIndicador(abate.resumo, "Preço da @")?.acumulado;
  return (
    <CabecasDoMes titulo="Venda abate · cab" secao={abate} mesDeReferencia={boletim.mes_referencia}
      cor="var(--cor-realizado)">
      Faturamento <b>{reaisCurtos(faturamento?.realizado ?? null)}</b> (
      {variacaoComSinal(faturamento?.variacao_percentual ?? null)}) · @ {dinheiro(arroba?.realizado ?? null, 2)} vs{" "}
      {numero(arroba?.previsto ?? null, 2)}
    </CabecasDoMes>
  );
}

function Compras({ boletim }: { boletim: BoletimAnalitico }) {
  const compras = boletim.compras;
  const investimento = linhaDoIndicador(compras.resumo, "Investimento")?.acumulado;
  const arroba = linhaDoIndicador(compras.resumo, "Preço da @")?.acumulado;
  return (
    <CabecasDoMes titulo="Compras · cab" secao={compras} mesDeReferencia={boletim.mes_referencia}
      cor="var(--cor-marrom)">
      Investido <b>{reaisCurtos(investimento?.realizado ?? null)}</b> (
      {variacaoComSinal(investimento?.variacao_percentual ?? null)}) · @ compra {dinheiro(arroba?.realizado ?? null, 2)}{" "}
      · ágio {percentual(compras.agio, 1)}
    </CabecasDoMes>
  );
}

type CabecasProps = { titulo: string; secao: SecaoDeLotes; mesDeReferencia: string; cor: string; children: ReactNode };

// As cabeças vendidas (ou compradas) mês a mês, realizado × planejado, com o acumulado no alto e o valor embaixo.
function CabecasDoMes({ titulo, secao, mesDeReferencia, cor, children }: CabecasProps) {
  const meses = ateAReferencia(secao.meses, mesDeReferencia);
  const cabecas = linhaDoIndicador(secao.resumo, "Cabeças")?.acumulado;
  const rotuloDoPlanejado = cabeONumeroDoPlanejado(meses.length) ? numeroInteiro : undefined;
  return (
    <div className="boletim-card boletim-quadro">
      <div className="boletim-quadro-topo">
        <span className="boletim-lbl marinho">{titulo}</span>
        <span className="boletim-sub">
          <b>{numero(cabecas?.realizado ?? null)}</b> de {numero(cabecas?.previsto ?? null)}
        </span>
      </div>
      <Colunas eixo={meses.map((mes) => mesDoEixo(mes.mes))} altura={160} series={[
        { nome: "Realizado", valores: meses.map((mes) => mes.realizado), cor, rotulo: numeroInteiro },
        { nome: "Planejado", valores: meses.map((mes) => mes.previsto), cor: "var(--cor-planejado)",
          rotulo: rotuloDoPlanejado, corDoRotulo: "var(--boletim-cinza)" },
      ]} />
      <span className="boletim-sub legenda-do-quadro">{children}</span>
    </div>
  );
}

function numeroInteiro(valor: number): string {
  return numero(valor);
}
