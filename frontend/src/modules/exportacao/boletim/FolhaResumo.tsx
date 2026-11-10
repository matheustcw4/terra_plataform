import logoBranco from "../../../assets/bi/terra-logo-branco.png";
import type { BoletimAnalitico, Comparacao, LinhaDoPrevisto, SecaoDeLotes } from "../../../core/api/tipos";
import {
  ateAReferencia,
  cabecasOuTraco,
  celulaEmMilhoes,
  diferencaEmReais,
  doisDigitos,
  ehParteDoDesembolso,
  grupoDaLetra,
  type Identificacao,
  LEMA_DA_TERRA,
  linhaDoIndicador,
  nomeDaClassificacao,
  reaisCurtos,
  rotuloDaPagina,
  SITE_DA_TERRA,
  variacaoComSinal,
} from "../../../logic/boletim";
import { numero } from "../../../logic/formatar";
import { mesCurto } from "../../../logic/meses";
import { BarrasDeitadas } from "./BarrasDeitadas";
import { Colunas } from "./Colunas";
import { LegendaDoBoletim, QuadroDoBoletim } from "./FolhaDoBoletim";
import { ComStatus } from "./Indicador";
import { TabelaDosMeses } from "./TabelaDosMeses";

type Props = { boletim: BoletimAnalitico; identificacao: Identificacao; numero: number; total: number };

const CENTROS_NO_RESUMO = 8;

// A folha 01 do boletim de resultados: na lateral marinho, a fazenda e os quatro números do período (resultado,
// receitas × desembolso, rebanho e vendas × compras); ao lado, o Previsto × Realizado do caixa, o fluxo de caixa mês a
// mês, o desembolso por grupo e as vendas e compras em cabeças.
export function FolhaResumo({ boletim, identificacao, numero: numeroDaFolha, total }: Props) {
  return (
    <section className="boletim-folha boletim-resumo" aria-label="Resumo">
      <LateralDoResumo boletim={boletim} identificacao={identificacao} />
      <div className="boletim-resumo-conteudo">
        <header className="boletim-resumo-topo">
          <span className="boletim-selo">{doisDigitos(numeroDaFolha)}</span>
          <h1>Previsto × Realizado</h1>
          <LegendaDoBoletim itens={[
            { nome: "Dentro da meta", cor: "var(--cor-status-verde)" },
            { nome: "Até 3% fora", cor: "var(--cor-status-amarelo)" },
            { nome: "Mais de 3% fora", cor: "var(--cor-status-vermelho)" },
          ]} />
          <strong className="boletim-resumo-pagina">{rotuloDaPagina(numeroDaFolha, total)}</strong>
        </header>
        <div className="boletim-resumo-alto">
          <TabelaDoCaixa boletim={boletim} />
          <FluxoDeCaixa boletim={boletim} />
        </div>
        <div className="boletim-resumo-baixo">
          <DesembolsoPorGrupo boletim={boletim} />
          <CabecasDoMes titulo="Venda abate · cab" secao={vendaAbate(boletim)} mesDeReferencia={boletim.mes_referencia}
            cor="var(--cor-realizado)" />
          <CabecasDoMes titulo="Compras · cab" secao={boletim.compras} mesDeReferencia={boletim.mes_referencia}
            cor="var(--cor-marrom)" />
        </div>
      </div>
    </section>
  );
}

function vendaAbate(boletim: BoletimAnalitico): SecaoDeLotes {
  const abate = boletim.vendas.find((secao) => secao.tipo === "abate");
  if (abate === undefined) {
    throw new Error("o boletim veio sem as vendas abate");
  }
  return abate;
}

function LateralDoResumo({ boletim, identificacao }: { boletim: BoletimAnalitico; identificacao: Identificacao }) {
  const caixa = boletim.caixa.previsto_realizado;
  const resultado = caixa.resultado.acumulado;
  const receitas = grupoDaLetra(caixa.grupos, "A")?.total.acumulado ?? null;
  const desembolso = grupoDaLetra(caixa.grupos, "B")?.total.acumulado ?? null;
  const lotacao = boletim.lotacao;
  const vendas = linhaDoIndicador(vendaAbate(boletim).resumo, "Cabeças");
  const compras = linhaDoIndicador(boletim.compras.resumo, "Cabeças");
  return (
    <aside className="boletim-resumo-lateral">
      <img className="boletim-resumo-logo" src={logoBranco} alt="Terra Desenvolvimento Agropecuário" />
      <p className="boletim-resumo-rotulo">Boletim mensal · {identificacao.rotuloDoPeriodo}</p>
      <h2 className="boletim-resumo-nome">{identificacao.titulo}</h2>
      <p className="boletim-resumo-sobre">
        {identificacao.cliente} · {identificacao.periodo} ({identificacao.meses} meses) · {identificacao.planejamento}
      </p>
      <dl className="boletim-resumo-numeros">
        <div>
          <dt>Resultado acumulado</dt>
          <dd>{reaisCurtos(resultado.realizado)}</dd>
          <dd className="sub">
            Plan. {reaisCurtos(resultado.planejado)} · <strong>{diferencaEmReais(resultado.diferenca)}</strong>
          </dd>
        </div>
        <div>
          <dt>Receitas · Desembolso</dt>
          <dd>{reaisCurtos(receitas?.realizado ?? null)} · {reaisCurtos(desembolso?.realizado ?? null)}</dd>
          <dd className="sub">
            <ComStatus status={receitas?.semaforo}>{variacaoComSinal(receitas?.variacao ?? null)}</ComStatus> e{" "}
            <ComStatus status={desembolso?.semaforo}>{variacaoComSinal(desembolso?.variacao ?? null)}</ComStatus>{" "}
            sobre o planejado
          </dd>
        </div>
        <div>
          <dt>Rebanho final</dt>
          <dd>{numero(lotacao.estoque_final)} cab</dd>
          <dd className="sub">
            Médio {numero(lotacao.rebanho_medio_cab)} cab · {numero(lotacao.rebanho_medio_ua)} UA · lotação{" "}
            {numero(lotacao.lotacao_cab_ha, 2)} cab/ha
          </dd>
        </div>
        <div>
          <dt>Venda abate · Compras</dt>
          <dd>
            {cabecasOuTraco(vendas?.acumulado.realizado ?? null)} · {cabecasOuTraco(compras?.acumulado.realizado ?? null)} cab
          </dd>
          <dd className="sub">
            <ComStatus status={vendas?.acumulado.status}>
              {variacaoComSinal(vendas?.acumulado.variacao_percentual ?? null)}
            </ComStatus>{" "}
            e{" "}
            <ComStatus status={compras?.acumulado.status}>
              {variacaoComSinal(compras?.acumulado.variacao_percentual ?? null)}
            </ComStatus>{" "}
            sobre a meta até aqui
          </dd>
        </div>
      </dl>
      <footer className="boletim-resumo-pe">
        <em>{LEMA_DA_TERRA}</em>
        <span>
          {SITE_DA_TERRA} · {identificacao.localEData}
        </span>
      </footer>
    </aside>
  );
}

// O Previsto × Realizado do caixa, só os totais de cada classificação: o mês de referência e o acumulado.
function TabelaDoCaixa({ boletim }: { boletim: BoletimAnalitico }) {
  const caixa = boletim.caixa.previsto_realizado;
  return (
    <QuadroDoBoletim titulo="Previsto × Realizado" className="boletim-caixa"
      nota={boletim.caixa.leitura.slice(0, 2).join(" ")}>
      <table className="boletim-tabela-caixa">
        <thead>
          <tr className="faixas">
            <th scope="col" />
            <th scope="colgroup" colSpan={3} className="faixa-mes">Mensal · {mesCurto(caixa.ultimo_mes)}</th>
            <th scope="colgroup" colSpan={3} className="faixa-acumulado">
              Acumulado · {mesCurto(caixa.periodo.inicio)} a {mesCurto(caixa.ultimo_mes)}
            </th>
          </tr>
          <tr>
            <th scope="col">Conta (R$)</th>
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
            <tr key={grupo.classificacao} className={ehParteDoDesembolso(grupo.classificacao) ? "parte" : undefined}>
              <th scope="row">{nomeDaClassificacao(grupo.classificacao)}</th>
              <CelulasDoCaixa comparacao={grupo.total.mensal} />
              <CelulasDoCaixa comparacao={grupo.total.acumulado} />
            </tr>
          ))}
        </tbody>
        <tfoot>
          <LinhaDoResultado resultado={caixa.resultado} />
        </tfoot>
      </table>
    </QuadroDoBoletim>
  );
}

function CelulasDoCaixa({ comparacao }: { comparacao: Comparacao }) {
  return (
    <>
      <td>{numero(comparacao.realizado)}</td>
      <td className="planejado">{numero(comparacao.planejado)}</td>
      <td>
        <ComStatus status={comparacao.semaforo}>{variacaoComSinal(comparacao.variacao)}</ComStatus>
      </td>
    </>
  );
}

// No resultado vale a diferença em reais, sem a cor do semáforo: com o planejado negativo, o % (e o semáforo, que é o
// do BI) inverte o sentido, e um resultado melhor que o planejado sairia vermelho.
function LinhaDoResultado({ resultado }: { resultado: LinhaDoPrevisto }) {
  return (
    <tr>
      <th scope="row">Resultado</th>
      <td>{numero(resultado.mensal.realizado)}</td>
      <td className="planejado">{numero(resultado.mensal.planejado)}</td>
      <td>{diferencaEmReais(resultado.mensal.diferenca)}</td>
      <td>{numero(resultado.acumulado.realizado)}</td>
      <td className="planejado">{numero(resultado.acumulado.planejado)}</td>
      <td>{diferencaEmReais(resultado.acumulado.diferenca)}</td>
    </tr>
  );
}

function FluxoDeCaixa({ boletim }: { boletim: BoletimAnalitico }) {
  const meses = boletim.financeiro.meses;
  const datas = meses.map((mes) => mes.mes);
  const receitas = meses.map((mes) => mes.receitas);
  const desembolso = meses.map((mes) => mes.desembolso);
  return (
    <QuadroDoBoletim titulo="Fluxo de caixa mensal" nota="R$ milhões."
      direita={<LegendaDoBoletim itens={[{ nome: "Receitas", cor: "var(--cor-realizado)" },
        { nome: "Desembolso", cor: "var(--cor-despesa)" }]} />}>
      <Colunas meses={datas} altura={150} series={[
        { nome: "Receitas", valores: receitas, cor: "var(--cor-realizado)" },
        { nome: "Desembolso", valores: desembolso, cor: "var(--cor-despesa)" },
      ]} />
      <TabelaDosMeses meses={datas} cabecalho="nenhum" linhas={[
        { nome: "Receitas", valores: receitas.map(celulaEmMilhoes) },
        { nome: "Desembolso", valores: desembolso.map(celulaEmMilhoes), classe: "destaque" },
      ]} />
    </QuadroDoBoletim>
  );
}

function DesembolsoPorGrupo({ boletim }: { boletim: BoletimAnalitico }) {
  const centros = boletim.financeiro.centros;
  const total = linhaDoIndicador(boletim.financeiro.placar, "Desembolso")?.acumulado.realizado ?? null;
  const barras = centros.slice(0, CENTROS_NO_RESUMO).map((centro) => ({
    rotulo: centro.centro_custo, valor: centro.valor_acumulado, texto: reaisCurtos(centro.valor_acumulado),
  }));
  let nota = `Total ${reaisCurtos(total)}.`;
  if (centros.length > CENTROS_NO_RESUMO) {
    nota += ` Mais ${centros.length - CENTROS_NO_RESUMO} grupos na folha do Financeiro.`;
  }
  return (
    <QuadroDoBoletim titulo="Desembolso por grupo · acumulado" nota={nota}>
      <BarrasDeitadas barras={barras} />
    </QuadroDoBoletim>
  );
}

type CabecasProps = { titulo: string; secao: SecaoDeLotes; mesDeReferencia: string; cor: string };

// As cabeças vendidas (ou compradas) mês a mês, realizado × planejado, e a frase do acumulado.
function CabecasDoMes({ titulo, secao, mesDeReferencia, cor }: CabecasProps) {
  const meses = ateAReferencia(secao.meses, mesDeReferencia);
  const cabecas = linhaDoIndicador(secao.resumo, "Cabeças");
  const direita = (
    <span className="boletim-de">
      <strong>{cabecasOuTraco(cabecas?.acumulado.realizado ?? null)}</strong> de{" "}
      {cabecasOuTraco(cabecas?.acumulado.previsto ?? null)}
    </span>
  );
  return (
    <QuadroDoBoletim titulo={titulo} direita={direita} nota={secao.leitura.slice(-1).join(" ")}>
      <Colunas meses={meses.map((mes) => mes.mes)} altura={170} series={[
        { nome: "Realizado", valores: meses.map((mes) => mes.realizado), cor },
        { nome: "Planejado", valores: meses.map((mes) => mes.previsto), cor: "var(--cor-planejado)" },
      ]} />
    </QuadroDoBoletim>
  );
}
