import type { ReactNode } from "react";
import type { BoletimAnalitico, LinhaDoPlacar, QuadroDoLote, SecaoDeLotes } from "../../../core/api/tipos";
import {
  ateAReferencia,
  cabecasOuTraco,
  type Identificacao,
  linhaDoIndicador,
  naUnidade,
  quadroDoSexo,
  reaisCurtos,
  secaoDeVenda,
  temMovimento,
  unidadeDosValores,
  variacaoComSinal,
  vendeuOsDoisSexos,
} from "../../../logic/boletim";
import { dinheiro, numero, percentual } from "../../../logic/formatar";
import { mesCurto } from "../../../logic/meses";
import { Colunas } from "./Colunas";
import { FolhaDoBoletim, TituloDaParte } from "./FolhaDoBoletim";
import { ComStatus, LegendaDoBoletim } from "./Indicador";
import { TabelaDosMeses } from "./TabelaDosMeses";

type Props = { boletim: BoletimAnalitico; identificacao: Identificacao; numero: number; total: number };

// A folha da Comercialização, como a do gerador oficial: a venda abate (com a venda em pé numa faixa embaixo) e as
// compras e reposição, lado a lado, cada uma com os números do acumulado, o placar, o valor mês a mês e as cabeças.
export function FolhaComercializacao({ boletim, identificacao, numero: numeroDaFolha, total }: Props) {
  return (
    <FolhaDoBoletim numero={numeroDaFolha} total={total} titulo="Comercialização" identificacao={identificacao}>
      <main className="boletim-comercializacao">
        <VendaAbate boletim={boletim} />
        <ComprasEReposicao boletim={boletim} />
      </main>
    </FolhaDoBoletim>
  );
}

function VendaAbate({ boletim }: { boletim: BoletimAnalitico }) {
  const abate = secaoDeVenda(boletim, "abate");
  const cabecas = linhaDoIndicador(abate.resumo, "Cabeças")?.acumulado;
  const faturamento = linhaDoIndicador(abate.resumo, "Faturamento")?.acumulado;
  const arroba = linhaDoIndicador(abate.resumo, "Preço da @")?.acumulado;
  return (
    <section className="boletim-card boletim-quadro">
      <TituloDaParte numero="08">Venda abate</TituloDaParte>
      <div className="boletim-grade-3 pequena">
        <Chip rotulo="Cabeças" valor={numero(cabecas?.realizado ?? null)}>
          plan. {numero(cabecas?.previsto ?? null)}
        </Chip>
        <Chip rotulo="Faturamento" valor={reaisCurtos(faturamento?.realizado ?? null)}>
          <ComStatus status={faturamento?.status}>{variacaoComSinal(faturamento?.variacao_percentual ?? null)}</ComStatus>
        </Chip>
        <Chip rotulo="Valor da @" valor={dinheiro(arroba?.realizado ?? null, 2)}>
          plan. {numero(arroba?.previsto ?? null, 2)}
        </Chip>
      </div>
      {vendeuOsDoisSexos(abate.por_sexo) && <TabelaPorSexo quadros={abate.por_sexo} />}
      {!vendeuOsDoisSexos(abate.por_sexo) && <TabelaDaVenda resumo={abate.resumo} />}
      <ValorPorMes titulo="Faturamento por mês" secao={abate} mesDeReferencia={boletim.mes_referencia}
        cor="var(--cor-realizado)" />
      <FaixaDaVendaEmPe secao={secaoDeVenda(boletim, "em_pe")} />
    </section>
  );
}

function Chip({ rotulo, valor, children }: { rotulo: string; valor: string; children: ReactNode }) {
  return (
    <div className="boletim-chip">
      <span className="boletim-lbl">{rotulo}</span>
      <div>
        <span className="boletim-big">{valor}</span> <span className="boletim-sub">{children}</span>
      </div>
    </div>
  );
}

// As linhas da venda: o nome na tabela, o campo do quadro por sexo, o indicador do resumo e como se escreve.
type LinhaDaVenda = { nome: string; campo: keyof QuadroDoLote["realizado"]; indicador: string; formato: Formato };
type Formato = "cabecas" | "kg" | "rendimento" | "preco" | "reais";

const LINHAS_DA_VENDA: LinhaDaVenda[] = [
  { nome: "Cabeças", campo: "cabecas", indicador: "Cabeças", formato: "cabecas" },
  { nome: "Peso médio", campo: "peso_medio_kg", indicador: "Peso médio", formato: "kg" },
  { nome: "Rend. carcaça", campo: "rendimento_carcaca", indicador: "Rendimento de carcaça", formato: "rendimento" },
  { nome: "Valor da @ (R$)", campo: "preco_arroba", indicador: "Preço da @", formato: "preco" },
  { nome: "Faturamento (R$)", campo: "valor", indicador: "Faturamento", formato: "reais" },
];

function escrito(valor: number | null | undefined, formato: Formato): string {
  if (valor === null || valor === undefined) {
    return "—";
  }
  if (formato === "kg") {
    return `${numero(valor, 1)} kg`;
  }
  if (formato === "rendimento") {
    return percentual(valor, 1);
  }
  if (formato === "preco") {
    return numero(valor, 2);
  }
  return numero(valor);
}

// Com os dois sexos: Fêmea, Macho e Geral, cada um realizado e planejado.
function TabelaPorSexo({ quadros }: { quadros: QuadroDoLote[] }) {
  const sexos = [quadroDoSexo(quadros, "FÊMEA"), quadroDoSexo(quadros, "MACHO"), quadroDoSexo(quadros, "GERAL")];
  return (
    <table className="boletim-tb">
      <thead>
        <tr>
          <th scope="col" />
          <th scope="colgroup" colSpan={2} className="faixa-mes">Fêmea</th>
          <th scope="colgroup" colSpan={2} className="faixa-mes">Macho</th>
          <th scope="colgroup" colSpan={2} className="faixa-acumulado">Geral</th>
        </tr>
        <tr>
          <th scope="col" className="esquerda">Indicador</th>
          <th scope="col">Real</th>
          <th scope="col">Plan.</th>
          <th scope="col">Real</th>
          <th scope="col">Plan.</th>
          <th scope="col">Real</th>
          <th scope="col">Plan.</th>
        </tr>
      </thead>
      <tbody>
        {LINHAS_DA_VENDA.map((linha) => (
          <tr key={linha.nome} className={linha.formato === "reais" ? "total" : undefined}>
            <td className="nome">{linha.nome}</td>
            {sexos.map((quadro, posicao) => (
              <CelulasDoSexo key={posicao} quadro={quadro} linha={linha} />
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function CelulasDoSexo({ quadro, linha }: { quadro: QuadroDoLote | null; linha: LinhaDaVenda }) {
  return (
    <>
      <td>{escrito(quadro?.realizado[linha.campo], linha.formato)}</td>
      <td className="apagado">{escrito(quadro?.planejado[linha.campo], linha.formato)}</td>
    </>
  );
}

// Com um sexo só: Realizado, Planejado e a variação.
function TabelaDaVenda({ resumo }: { resumo: LinhaDoPlacar[] }) {
  return (
    <table className="boletim-tb">
      <thead>
        <tr>
          <th scope="col" className="esquerda">Indicador</th>
          <th scope="col">Realizado</th>
          <th scope="col">Planejado</th>
          <th scope="col">Var.</th>
        </tr>
      </thead>
      <tbody>
        {LINHAS_DA_VENDA.map((linha) => (
          <LinhaDoResumo key={linha.nome} nome={linha.nome} formato={linha.formato}
            linha={linhaDoIndicador(resumo, linha.indicador)} />
        ))}
      </tbody>
    </table>
  );
}

type LinhaDoResumoProps = { nome: string; formato: Formato; linha: LinhaDoPlacar | null };

function LinhaDoResumo({ nome, formato, linha }: LinhaDoResumoProps) {
  return (
    <tr className={formato === "reais" ? "total" : undefined}>
      <td className="nome">{nome}</td>
      <td>{escrito(linha?.acumulado.realizado, formato)}</td>
      <td className={formato === "reais" ? undefined : "apagado"}>{escrito(linha?.acumulado.previsto, formato)}</td>
      <td>{variacaoComSinal(linha?.acumulado.variacao_percentual ?? null)}</td>
    </tr>
  );
}

type ValorPorMesProps = { titulo: string; secao: SecaoDeLotes; mesDeReferencia: string; cor: string };

// O valor do lote mês a mês (faturamento ou desembolso de compras) e a tabela das cabeças por mês.
function ValorPorMes({ titulo, secao, mesDeReferencia, cor }: ValorPorMesProps) {
  const meses = ateAReferencia(secao.meses, mesDeReferencia);
  const realizado = meses.map((mes) => mes.valor);
  const previsto = meses.map((mes) => mes.valor_previsto);
  const unidade = unidadeDosValores([realizado, previsto]);
  return (
    <>
      <div className="boletim-quadro-topo">
        <span className="boletim-lbl marinho">{titulo} · {unidade.rotulo}</span>
        <LegendaDoBoletim itens={[{ nome: "Realizado", cor }, { nome: "Planejado", cor: "var(--cor-planejado)" }]} />
      </div>
      <Colunas eixo={meses.map((mes) => mesCurto(mes.mes))} altura={170} series={[
        { nome: "Realizado", valores: realizado, cor, rotulo: (valor) => naUnidade(valor, unidade) },
        { nome: "Planejado", valores: previsto, cor: "var(--cor-planejado)", rotulo: (valor) => naUnidade(valor, unidade),
          corDoRotulo: "var(--boletim-cinza)" },
      ]} />
      <TabelaDosMeses titulo="Cab · mês" meses={meses.map((mes) => mes.mes)} marrom linhas={[
        { nome: "Real", valores: meses.map((mes) => cabecasOuTraco(mes.realizado)) },
        { nome: "Plan.", valores: meses.map((mes) => cabecasOuTraco(mes.previsto)), apagado: true },
      ]} />
    </>
  );
}

// A venda em pé numa faixa só, embaixo da venda abate: o que vendeu contra o plano, ou que não houve venda.
function FaixaDaVendaEmPe({ secao }: { secao: SecaoDeLotes }) {
  if (!temMovimento(secao)) {
    return (
      <div className="boletim-faixa-de-texto boletim-ate-o-fim">
        <b>Venda em pé:</b> sem vendas no período.
      </div>
    );
  }
  const cabecas = linhaDoIndicador(secao.resumo, "Cabeças")?.acumulado;
  const peso = linhaDoIndicador(secao.resumo, "Peso médio")?.acumulado;
  const precoDoKg = linhaDoIndicador(secao.resumo, "Preço do kg")?.acumulado;
  const arroba = linhaDoIndicador(secao.resumo, "Preço da @")?.acumulado;
  const faturamento = linhaDoIndicador(secao.resumo, "Faturamento")?.acumulado;
  return (
    <div className="boletim-faixa-de-texto boletim-ate-o-fim">
      <b>Venda em pé:</b> {numero(cabecas?.realizado ?? null)} cab (plan. {numero(cabecas?.previsto ?? null)}) ·{" "}
      {escrito(peso?.realizado, "kg")} · R$ {escrito(precoDoKg?.realizado, "preco")}/kg · @ R${" "}
      {escrito(arroba?.realizado, "preco")} (plan. {escrito(arroba?.previsto, "preco")}) ·{" "}
      {dinheiro(faturamento?.realizado ?? null)} (plan. {dinheiro(faturamento?.previsto ?? null)}).
    </div>
  );
}

function ComprasEReposicao({ boletim }: { boletim: BoletimAnalitico }) {
  const compras = boletim.compras;
  const cabecas = linhaDoIndicador(compras.resumo, "Cabeças");
  const peso = linhaDoIndicador(compras.resumo, "Peso médio");
  const precoDoKg = linhaDoIndicador(compras.resumo, "Preço do kg");
  const arroba = linhaDoIndicador(compras.resumo, "Preço da @")?.acumulado;
  const investimento = linhaDoIndicador(compras.resumo, "Investimento");
  return (
    <section className="boletim-card boletim-quadro">
      <TituloDaParte numero="09">Compras e reposição</TituloDaParte>
      <div className="boletim-grade-3 pequena">
        <Chip rotulo="Cabeças" valor={numero(cabecas?.acumulado.realizado ?? null)}>
          plan. {numero(cabecas?.acumulado.previsto ?? null)}
        </Chip>
        <Chip rotulo="Investimento" valor={reaisCurtos(investimento?.acumulado.realizado ?? null)}>
          <ComStatus status={investimento?.acumulado.status}>
            {variacaoComSinal(investimento?.acumulado.variacao_percentual ?? null)}
          </ComStatus>
        </Chip>
        <Chip rotulo="@ compra · ágio" valor={dinheiro(arroba?.realizado ?? null, 2)}>
          <b>{percentual(compras.agio, 1)}</b>
        </Chip>
      </div>
      <table className="boletim-tb">
        <thead>
          <tr>
            <th scope="col" className="esquerda">Indicador</th>
            <th scope="col">Realizado</th>
            <th scope="col">Planejado</th>
            <th scope="col">Var.</th>
          </tr>
        </thead>
        <tbody>
          <LinhaDoResumo nome="Cabeças compradas" formato="cabecas" linha={cabecas} />
          <LinhaDoResumo nome="Peso médio" formato="kg" linha={peso} />
          <LinhaDoResumo nome="Preço do kg (R$)" formato="preco" linha={precoDoKg} />
          <tr>
            <td className="nome">@ vendida (abate + em pé)</td>
            <td>{escrito(compras.preco_arroba_venda, "preco")}</td>
            <td className="apagado">—</td>
            <td className="apagado">—</td>
          </tr>
          <LinhaDoResumo nome="Investimento (R$)" formato="reais" linha={investimento} />
        </tbody>
      </table>
      <ValorPorMes titulo="Desembolso de compras por mês" secao={compras} mesDeReferencia={boletim.mes_referencia}
        cor="var(--cor-marrom)" />
      {compras.leitura.length > 0 && (
        <div className="boletim-faixa-de-texto boletim-ate-o-fim">{compras.leitura.join(" ")}</div>
      )}
    </section>
  );
}
