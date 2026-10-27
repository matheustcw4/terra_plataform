import adulto from "../../assets/bi/adulto.png";
import bezerro from "../../assets/bi/bezerro.png";
import jovem from "../../assets/bi/jovem.png";
import soma from "../../assets/bi/soma.png";
import { GraficoAcumuladoDaContagem, GraficoMensalDaContagem } from "../../componentes/contagens/GraficosDaContagem";
import type { Mortes, MortesDoGrupo } from "../../core/api/tipos";
import { useArea } from "../../core/auth/AreaAutenticada";
import { Aviso } from "../../core/ui/Aviso";
import { GraficoDeBarras } from "../../core/ui/GraficoDeBarras";
import { Moldura } from "../../core/ui/Moldura";
import { Linha, Painel } from "../../core/ui/Painel";
import { numero, percentual } from "../../logic/formatar";
import { doRecorte } from "../../logic/recortes";
import { useMortes } from "./api";

// Os quatro quadros do topo, na ordem do BI (da esquerda para a direita).
const GRUPOS = [
  { recorte: "BEZERROS", titulo: "BEZERROS", icone: bezerro },
  { recorte: "JOVENS", titulo: "JOVENS", icone: jovem },
  { recorte: "ADULTOS", titulo: "ADULTOS", icone: adulto },
  { recorte: "GERAL", titulo: "GERAL", icone: soma },
];

// A página "Mortes" do BI: quadros Bezerros / Jovens / Adultos / Geral (mortes, mortalidade sobre o rebanho médio e
// meta; nos bezerros, também sobre os nascimentos), os gráficos acumulado e mensal e as mortes por causa.
export function MortesPagina() {
  const { consulta } = useArea();
  const pagina = useMortes(consulta);
  return (
    <Moldura caminho="/mortes">
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

function Conteudo({ dados }: { dados: Mortes }) {
  const causas = dados.causas.map((causa) => ({ rotulo: causa.causa, valor: causa.cabecas }));
  return (
    <>
      <div className="paineis-4">
        {GRUPOS.map((grupo) => (
          <QuadroDeMortes key={grupo.recorte} titulo={grupo.titulo} icone={grupo.icone}
            quadro={doRecorte(dados.quadro, grupo.recorte)} />
        ))}
      </div>
      <div className="mortes-corpo">
        <div className="coluna-graficos">
          <GraficoAcumuladoDaContagem titulo="REALIZADO X PLANEJADO - ACUMULADO GERAL" serie={dados.serie_mensal}
            forma="colunas" />
          <GraficoMensalDaContagem titulo="MORTES - REALIZADO X PLANEJADO - MENSAL" serie={dados.serie_mensal}
            comAcumulado />
        </div>
        <GraficoDeBarras titulo="CAUSA MORTE" barras={causas} semDados="Nenhuma morte no período." />
      </div>
    </>
  );
}

type QuadroProps = { titulo: string; icone: string; quadro: MortesDoGrupo | undefined };

function QuadroDeMortes({ titulo, icone, quadro }: QuadroProps) {
  if (quadro === undefined) {
    return null;
  }
  return (
    <Painel titulo={titulo} icone={icone}>
      <Linha rotulo="Mortes" valor={`${numero(quadro.realizado)} cab`} destaque />
      <Linha rotulo="Mortalidade sobre Rebanho Médio" valor={percentual(quadro.sobre_rebanho_medio, 2)} />
      {quadro.recorte === "BEZERROS" && (
        <Linha rotulo="Mortalidade sobre Nascimento" valor={percentual(quadro.sobre_nascimentos, 2)} />
      )}
      <Linha rotulo="Meta" valor={numero(quadro.planejado)} />
    </Painel>
  );
}
