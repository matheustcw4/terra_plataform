import { GraficoAcumuladoDaContagem, GraficoMensalDaContagem } from "../../componentes/contagens/GraficosDaContagem";
import { SEXOS } from "../../componentes/lotes/sexos";
import type { Nascimentos, NascimentosDoSexo } from "../../core/api/tipos";
import { useArea } from "../../core/auth/AreaAutenticada";
import { Aviso } from "../../core/ui/Aviso";
import { Moldura } from "../../core/ui/Moldura";
import { Linha, Painel } from "../../core/ui/Painel";
import { numero, percentual } from "../../logic/formatar";
import { doRecorte } from "../../logic/recortes";
import { useNascimentos } from "./api";

// A página "Nascimentos" do BI: quadros Fêmea / Macho / Geral com os nascimentos realizados e planejados (nos
// sexos, a parte de cada um no total; no geral, o % da meta) e os gráficos mensal e acumulado.
export function NascimentosPagina() {
  const { consulta } = useArea();
  const pagina = useNascimentos(consulta);
  return (
    <Moldura caminho="/nascimentos">
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

function Conteudo({ dados }: { dados: Nascimentos }) {
  return (
    <>
      <div className="paineis-3">
        {SEXOS.map((sexo) => (
          <QuadroDeNascimentos key={sexo.recorte} titulo={sexo.titulo} icone={sexo.icone}
            quadro={doRecorte(dados.quadro, sexo.recorte)} />
        ))}
      </div>
      <GraficoMensalDaContagem titulo="NASCIMENTOS - REALIZADO X PLANEJADO - MENSAL" serie={dados.serie_mensal} />
      <GraficoAcumuladoDaContagem titulo="NASCIMENTOS - REALIZADO X PLANEJADO - ACUMULADO" serie={dados.serie_mensal}
        forma="linhas" />
    </>
  );
}

type QuadroProps = { titulo: string; icone: string; quadro: NascimentosDoSexo | undefined };

// Realizado | Planejado e, embaixo, o percentual do quadro: a parte do sexo no total ou, no Geral, o % da meta.
function QuadroDeNascimentos({ titulo, icone, quadro }: QuadroProps) {
  if (quadro === undefined) {
    return null;
  }
  let percentualDoQuadro = <Linha rotulo="% do Total" valor={percentual(quadro.participacao_no_total)} destaque />;
  if (quadro.recorte === "GERAL") {
    percentualDoQuadro = <Linha rotulo="% da Meta" valor={percentual(quadro.percentual_da_meta)} destaque />;
  }
  return (
    <Painel titulo={titulo} icone={icone}>
      <table className="tabela-bi">
        <thead>
          <tr>
            <th scope="col" />
            <th scope="col">Realizado</th>
            <th scope="col">Planejado</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">Nascimentos</th>
            <td>{numero(quadro.realizado)}</td>
            <td>{numero(quadro.planejado)}</td>
          </tr>
        </tbody>
      </table>
      {percentualDoQuadro}
    </Painel>
  );
}
