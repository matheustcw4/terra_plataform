import type { BoletimAnalitico, SecaoDeLotes } from "../../../core/api/tipos";
import {
  ateAReferencia,
  cabecasOuTraco,
  type Identificacao,
  linhaDoIndicador,
  secaoDoBloco,
  temMovimento,
  variacaoComSinal,
} from "../../../logic/boletim";
import { numero, percentual } from "../../../logic/formatar";
import { mesPorExtenso } from "../../../logic/exportacao";
import { BarrasDeitadas } from "./BarrasDeitadas";
import { Colunas } from "./Colunas";
import { FolhaDoBoletim, QuadroDoBoletim } from "./FolhaDoBoletim";
import { ComStatus, Indicador } from "./Indicador";
import { TabelaDosMeses } from "./TabelaDosMeses";
import { ValoresDoLote } from "./ValoresDoLote";

type Props = { boletim: BoletimAnalitico; identificacao: Identificacao; numero: number; total: number };

const CAUSAS_NA_FOLHA = 9;

// A folha do Rebanho: os números do período (rebanho médio, lotação, rebanho final, mortes, compras e vendas) e, em
// três colunas, a movimentação do estoque, as mortes e as transferências, com o que não teve movimento resumido.
export function FolhaRebanho({ boletim, identificacao, numero: numeroDaFolha, total }: Props) {
  return (
    <FolhaDoBoletim numero={numeroDaFolha} total={total} titulo="Rebanho" identificacao={identificacao}>
      <NumerosDoRebanho boletim={boletim} />
      <div className="boletim-rebanho">
        <Movimentacao boletim={boletim} />
        <Mortes boletim={boletim} />
        <div className="boletim-coluna-estreita">
          <Transferencias boletim={boletim} />
          <Nascimentos secao={boletim.nascimentos} />
          <SemMovimento boletim={boletim} />
        </div>
      </div>
    </FolhaDoBoletim>
  );
}

function NumerosDoRebanho({ boletim }: { boletim: BoletimAnalitico }) {
  const lotacao = boletim.lotacao;
  const mortes = linhaDoIndicador(boletim.placar_zootecnico.linhas, "Mortes")?.acumulado;
  const mortalidade = linhaDoIndicador(boletim.placar_zootecnico.linhas, "Mortalidade")?.acumulado;
  const compras = linhaDoIndicador(boletim.compras.resumo, "Cabeças")?.acumulado;
  const vendas = linhaDoIndicador(secaoDoBloco(boletim, "abate").resumo, "Cabeças")?.acumulado;
  return (
    <div className="boletim-linha-5">
      <Indicador rotulo="Rebanho médio" valor={`${numero(lotacao.rebanho_medio_cab)} cab`}>
        {numero(lotacao.rebanho_medio_ua)} UA
      </Indicador>
      <Indicador rotulo="Lotação" valor={`${numero(lotacao.lotacao_cab_ha, 2)} cab/ha`}>
        {numero(lotacao.lotacao_ua_ha, 2)} UA/ha · prevista {numero(lotacao.lotacao_cab_ha_prevista, 2)} cab/ha
      </Indicador>
      <Indicador rotulo="Rebanho final" valor={`${numero(lotacao.estoque_final)} cab`}>
        {lotacao.mes_do_pico !== null && (
          <>Pico de {numero(lotacao.pico_do_rebanho)} em {mesPorExtenso(lotacao.mes_do_pico)}</>
        )}
      </Indicador>
      <Indicador rotulo="Mortes" valor={`${numero(mortes?.realizado ?? null)} cab`} status={mortes?.status}>
        Meta {numero(mortes?.previsto ?? null)} · mortalidade{" "}
        <ComStatus status={mortalidade?.status}>{percentual(mortalidade?.realizado ?? null, 2)}</ComStatus>
      </Indicador>
      <Indicador rotulo="Compras · Venda abate"
        valor={`${cabecasOuTraco(compras?.realizado ?? null)} · ${cabecasOuTraco(vendas?.realizado ?? null)}`}>
        <ComStatus status={compras?.status}>{variacaoComSinal(compras?.variacao_percentual ?? null)}</ComStatus> e{" "}
        <ComStatus status={vendas?.status}>{variacaoComSinal(vendas?.variacao_percentual ?? null)}</ComStatus> sobre a
        meta até aqui
      </Indicador>
    </div>
  );
}

function Movimentacao({ boletim }: { boletim: BoletimAnalitico }) {
  const meses = ateAReferencia(boletim.lotacao.meses, boletim.mes_referencia);
  const categorias = boletim.estoque.distribuicao_final.map((fatia) => ({
    rotulo: fatia.categoria, valor: fatia.cabecas, texto: numero(fatia.cabecas),
  }));
  return (
    <section className="boletim-parte">
      <h2 className="boletim-subtitulo">Movimentação</h2>
      <QuadroDoBoletim titulo="Estoque final mensal · cab" nota={boletim.estoque.leitura[0]}>
        <Colunas meses={meses.map((mes) => mes.mes)} corDaUltima="var(--cor-marrom)" altura={160} series={[
          { nome: "Estoque final", valores: meses.map((mes) => mes.estoque_final), cor: "var(--cor-realizado)",
            rotulo: numeroInteiro },
        ]} />
      </QuadroDoBoletim>
      <QuadroDoBoletim titulo="Estoque por categoria · cab"
        direita={<span>Total <strong>{numero(boletim.lotacao.estoque_final)}</strong></span>}>
        <BarrasDeitadas barras={categorias} />
      </QuadroDoBoletim>
    </section>
  );
}

function numeroInteiro(valor: number | null): string {
  return numero(valor);
}

function Mortes({ boletim }: { boletim: BoletimAnalitico }) {
  const mortes = boletim.mortes;
  const meses = ateAReferencia(mortes.meses, boletim.mes_referencia);
  const causas = mortes.causas.slice(0, CAUSAS_NA_FOLHA).map((causa) => ({
    rotulo: causa.causa, valor: causa.total, texto: numero(causa.total),
  }));
  let notaDasCausas = mortes.leitura[0];
  if (mortes.causas.length > CAUSAS_NA_FOLHA) {
    notaDasCausas = `Mais ${mortes.causas.length - CAUSAS_NA_FOLHA} causas com menos mortes.`;
  }
  return (
    <section className="boletim-parte">
      <h2 className="boletim-subtitulo">Mortes</h2>
      <div className="boletim-grupos-de-morte">
        {mortes.por_grupo.map((grupo) => (
          <Indicador key={grupo.grupo} rotulo={grupo.grupo} valor={numero(grupo.mortes)} pequeno>
            meta {numero(grupo.mortes_previstas)} · {percentual(grupo.realizado, 2)}
          </Indicador>
        ))}
      </div>
      <QuadroDoBoletim titulo="Causa da morte · cab" nota={notaDasCausas}>
        {causas.length > 0 && <BarrasDeitadas barras={causas} tom="marrom" />}
        {causas.length === 0 && <p className="boletim-vazio">Nenhuma morte no período.</p>}
      </QuadroDoBoletim>
      <TabelaDosMeses meses={meses.map((mes) => mes.mes)} linhas={[
        { nome: "Real", valores: meses.map((mes) => numero(mes.realizado)) },
        { nome: "Plan.", valores: meses.map((mes) => numero(mes.previsto, 1)), classe: "planejado" },
        { nome: "Acum.", valores: meses.map((mes) => numero(mes.realizado_acumulado)), classe: "acumulado" },
      ]} />
    </section>
  );
}

// Entradas e saídas por transferência, quando houve alguma no período.
function Transferencias({ boletim }: { boletim: BoletimAnalitico }) {
  const secoes = [boletim.transferencias.entradas, boletim.transferencias.saidas].filter(temMovimento);
  if (secoes.length === 0) {
    return null;
  }
  return (
    <section className="boletim-parte">
      <h2 className="boletim-subtitulo">Transferências</h2>
      {secoes.map((secao) => (
        <QuadroDoBoletim key={secao.tipo} titulo={secao.titulo}>
          <ValoresDoLote secao={secao} indicadores={["Cabeças", "Peso médio", "Valor da @"]} />
        </QuadroDoBoletim>
      ))}
      {boletim.transferencias.leitura.length > 0 && (
        <p className="boletim-nota">{boletim.transferencias.leitura.join(" ")}</p>
      )}
    </section>
  );
}

function Nascimentos({ secao }: { secao: SecaoDeLotes }) {
  if (!temMovimento(secao)) {
    return null;
  }
  return (
    <section className="boletim-parte">
      <h2 className="boletim-subtitulo">Nascimentos</h2>
      <QuadroDoBoletim titulo="Nascimentos · cab" nota={secao.leitura.join(" ")}>
        <ValoresDoLote secao={secao} indicadores={["Total", "Machos", "Fêmeas"]} />
      </QuadroDoBoletim>
    </section>
  );
}

// O que não teve lote nem meta no período sai numa lista só, em vez de um quadro vazio.
function SemMovimento({ boletim }: { boletim: BoletimAnalitico }) {
  const candidatas = [boletim.nascimentos, secaoDoBloco(boletim, "em_pe"), boletim.transferencias.entradas,
    boletim.transferencias.saidas];
  const paradas = candidatas.filter((secao) => !temMovimento(secao));
  if (paradas.length === 0) {
    return null;
  }
  return (
    <section className="boletim-quadro boletim-sem-movimento">
      <h2>Sem movimento no período</h2>
      <ul>
        {paradas.map((secao) => (
          <li key={secao.tipo}>
            <span>{secao.titulo}</span>
            <strong>0 · plan. 0</strong>
          </li>
        ))}
      </ul>
    </section>
  );
}
