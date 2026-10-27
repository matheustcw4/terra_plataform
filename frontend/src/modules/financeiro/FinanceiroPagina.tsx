import type { Financeiro } from "../../core/api/tipos";
import { useArea } from "../../core/auth/AreaAutenticada";
import { Aviso } from "../../core/ui/Aviso";
import { GraficoDeBarras } from "../../core/ui/GraficoDeBarras";
import { Moldura } from "../../core/ui/Moldura";
import { Linha, Painel } from "../../core/ui/Painel";
import { Velocimetro } from "../../core/ui/Velocimetro";
import { dinheiro, dinheiroCompacto } from "../../logic/formatar";
import { useFinanceiro } from "./api";
import { GraficoDeFluxoDeCaixa } from "./GraficoDeFluxoDeCaixa";
import { GraficoMensalDoFinanceiro } from "./GraficoMensalDoFinanceiro";

// A página "Financeiro" do BI: velocímetros de desembolso e custeio por cabeça por mês e do preço da @ vendida, o
// desembolso e as receitas do período, o desembolso por centro de custo e os gráficos mês a mês.
export function FinanceiroPagina() {
  const { consulta } = useArea();
  const pagina = useFinanceiro(consulta);
  return (
    <Moldura caminho="/financeiro">
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

// "R$ 32,90" nos velocímetros; sem valor, o traço.
function reaisComCentavos(valor: number | null): string {
  return dinheiro(valor, 2);
}

function Conteudo({ dados }: { dados: Financeiro }) {
  const centros = dados.desembolso_por_centro.map((centro) => ({ rotulo: centro.centro_custo, valor: centro.valor }));
  return (
    <>
      <div className="paineis-4">
        <Velocimetro titulo="DESEMBOLSO CABEÇA MÊS" valores={dados.desembolso_por_cabeca_mes}
          formatar={reaisComCentavos} />
        <Velocimetro titulo="CUSTEIO CABEÇA MÊS" valores={dados.custeio_por_cabeca_mes} formatar={reaisComCentavos} />
        <Velocimetro titulo="VALOR DE VENDA @" valores={dados.preco_arroba_venda} formatar={reaisComCentavos} />
        <Painel titulo="DESEMBOLSO">
          <Linha rotulo="Desembolso" valor={dinheiro(dados.desembolso)} destaque />
          <Linha rotulo="Receitas" valor={dinheiro(dados.receitas)} destaque />
        </Painel>
      </div>
      <div className="financeiro-corpo">
        <div className="coluna-graficos">
          <GraficoDeBarras titulo="RELAÇÃO DESEMBOLSO TOTAL" barras={centros} formatar={dinheiroCompacto}
            semDados="Nenhum desembolso no período." />
          <GraficoDeFluxoDeCaixa serie={dados.serie_mensal} />
        </div>
        <div className="coluna-graficos">
          <GraficoMensalDoFinanceiro titulo="REALIZADO X PLANEJADO - DESEMBOLSO/CAB/MÊS" serie={dados.serie_mensal}
            realizado="desembolso_por_cabeca" planejado="desembolso_por_cabeca_planejado"
            formatar={(valor) => dinheiro(valor, 2)} />
          <GraficoMensalDoFinanceiro titulo="REALIZADO X PLANEJADO - DESEMBOLSO" serie={dados.serie_mensal}
            realizado="desembolso" planejado="desembolso_planejado" formatar={(valor) => dinheiro(valor)} />
          <GraficoMensalDoFinanceiro titulo="REALIZADO X PLANEJADO - RECEITAS" serie={dados.serie_mensal}
            realizado="receitas" planejado="receitas_planejadas" formatar={(valor) => dinheiro(valor)} />
        </div>
      </div>
    </>
  );
}
