import { Bar, CartesianGrid, ComposedChart, LabelList, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis }
  from "recharts";
import femea from "../../assets/bi/femea.png";
import macho from "../../assets/bi/macho.png";
import { indicadoresDoTipo } from "../../componentes/lotes/indicadores";
import type { MesDeTransferencia, QuadroDoLote, Transferencias } from "../../core/api/tipos";
import { useArea } from "../../core/auth/AreaAutenticada";
import { Aviso } from "../../core/ui/Aviso";
import { Moldura } from "../../core/ui/Moldura";
import { Painel } from "../../core/ui/Painel";
import { numero, rotuloDeColuna } from "../../logic/formatar";
import { mesCurto } from "../../logic/meses";
import { doRecorte } from "../../logic/recortes";
import { useTransferencias } from "./api";
import { CAIXA_DO_MOUSE, COLUNA, EIXO, GRADE, LEGENDA } from "../../core/ui/estiloDosGraficos";

// Os dois quadros do BI, Macho à esquerda e Fêmea à direita.
const SEXOS = [
  { recorte: "MACHO", titulo: "MACHO", icone: macho },
  { recorte: "FÊMEA", titulo: "FÊMEA", icone: femea },
];

// A página "Transferências" do BI: para machos e fêmeas, entrada e saída × realizado e planejado (quantidade, peso
// médio e valor da @), e o gráfico mês a mês das cabeças que entraram e saíram.
export function TransferenciasPagina() {
  const { consulta } = useArea();
  const pagina = useTransferencias(consulta);
  return (
    <Moldura caminho="/transferencias">
      {pagina.isPending && <Aviso>Carregando…</Aviso>}
      {pagina.isError && <Aviso tipo="erro">Não foi possível carregar a página: {pagina.error.message}</Aviso>}
      {pagina.data && (
        <div className={pagina.isPlaceholderData ? "pagina atualizando" : "pagina"}>
          <Conteudo dados={pagina.data} />
        </div>
      )}
    </Moldura>
  );
}

function Conteudo({ dados }: { dados: Transferencias }) {
  return (
    <>
      <div className="paineis-2">
        {SEXOS.map((sexo) => (
          <QuadroDeTransferencia key={sexo.recorte} titulo={sexo.titulo} icone={sexo.icone}
            entrada={doRecorte(dados.entrada, sexo.recorte)} saida={doRecorte(dados.saida, sexo.recorte)} />
        ))}
      </div>
      <GraficoDeEntradasESaidas serie={dados.serie_mensal} />
    </>
  );
}

type QuadroProps = {
  titulo: string;
  icone: string;
  entrada: QuadroDoLote | undefined;
  saida: QuadroDoLote | undefined;
};

// As linhas (quantidade, peso médio, valor da @) em Entrada | Saída, cada uma com Realizado | Planejado.
function QuadroDeTransferencia({ titulo, icone, entrada, saida }: QuadroProps) {
  if (entrada === undefined || saida === undefined) {
    return null;
  }
  return (
    <Painel titulo={titulo} icone={icone}>
      <table className="tabela-bi tabela-dupla">
        <thead>
          <tr>
            <th scope="col" />
            <th scope="colgroup" colSpan={2} className="grupo">Entrada</th>
            <th scope="colgroup" colSpan={2} className="grupo separador">Saída</th>
          </tr>
          <tr>
            <th scope="col" />
            <th scope="col">Realizado</th>
            <th scope="col">Planejado</th>
            <th scope="col" className="separador">Realizado</th>
            <th scope="col">Planejado</th>
          </tr>
        </thead>
        <tbody>
          {indicadoresDoTipo("transferencia").map((indicador) => (
            <tr key={indicador.titulo}>
              <th scope="row">{indicador.titulo}</th>
              <td>{indicador.mostrar(entrada.realizado)}</td>
              <td>{indicador.mostrar(entrada.planejado)}</td>
              <td className="separador">{indicador.mostrar(saida.realizado)}</td>
              <td>{indicador.mostrar(saida.planejado)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Painel>
  );
}

// "ENTRADAS X SAÍDAS - MENSAL": cabeças que chegaram e que saíram em cada mês (o realizado). Sem animação: o painel
// é para ler número.
function GraficoDeEntradasESaidas({ serie }: { serie: MesDeTransferencia[] }) {
  return (
    <section className="painel-grafico">
      <h2>ENTRADAS X SAÍDAS - MENSAL</h2>
      <ResponsiveContainer width="100%" height={340}>
        <ComposedChart data={serie} margin={{ top: 24, right: 8, bottom: 0, left: 8 }}>
          <CartesianGrid {...GRADE} />
          <XAxis dataKey="mes" tickFormatter={mesCurto} {...EIXO} />
          <YAxis hide />
          <Tooltip {...CAIXA_DO_MOUSE} labelFormatter={(mes) => mesCurto(String(mes))} formatter={(valor) => numero(Number(valor))} />
          <Legend {...LEGENDA} />
          <Bar {...COLUNA} dataKey="entradas" name="Entradas" fill="var(--cor-realizado)" isAnimationActive={false}>
            <LabelList dataKey="entradas" position="top" formatter={(valor) => rotuloDeColuna(Number(valor))}
              className="rotulo-de-coluna" />
          </Bar>
          <Bar {...COLUNA} dataKey="saidas" name="Saídas" fill="var(--cor-rebanho-final)" isAnimationActive={false}>
            <LabelList dataKey="saidas" position="top" formatter={(valor) => rotuloDeColuna(Number(valor))}
              className="rotulo-de-coluna" />
          </Bar>
        </ComposedChart>
      </ResponsiveContainer>
    </section>
  );
}
