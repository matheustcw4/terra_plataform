import bezerro from "../../assets/bi/bezerro.png";
import soma from "../../assets/bi/soma.png";
import type { Movimentacao } from "../../core/api/tipos";
import { useArea } from "../../core/auth/AreaAutenticada";
import { Aviso } from "../../core/ui/Aviso";
import { GraficoDeColunas } from "../../core/ui/GraficoDeColunas";
import { Moldura } from "../../core/ui/Moldura";
import { Linha, Painel } from "../../core/ui/Painel";
import { numero, percentual } from "../../logic/formatar";
import { mesCurto } from "../../logic/meses";
import { useMovimentacao } from "./api";

// A página "Movimentação do Gado" do BI: quatro quadros (rebanho médio, nascimentos, mortes, compras e vendas), o
// estoque final mês a mês e o estoque final por categoria com o rebanho final ao lado.
export function MovimentacaoPagina() {
  const { consulta } = useArea();
  const pagina = useMovimentacao(consulta);
  return (
    <Moldura caminho="/rebanho/movimentacao">
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

function Conteudo({ dados }: { dados: Movimentacao }) {
  const estoqueMensal = dados.estoque_mensal.map((mes) => ({ rotulo: mesCurto(mes.mes), valor: mes.estoque_final }));
  const porCategoria = dados.estoque_por_categoria.map((linha) => ({
    rotulo: linha.categoria,
    valor: linha.estoque_final,
  }));
  return (
    <>
      <div className="paineis-4">
        <Painel titulo="REBANHO MÉDIO" icone={bezerro}>
          <Linha rotulo="Rebanho Médio Cab" valor={numero(dados.rebanho_medio_cab)} />
          <Linha rotulo="Rebanho Médio UA" valor={numero(dados.rebanho_medio_ua)} />
          <Linha rotulo="Lotação Cab" valor={numero(dados.lotacao_cab_ha, 2)} />
          <Linha rotulo="Lotação UA" valor={numero(dados.lotacao_ua_ha, 2)} />
        </Painel>
        <Painel titulo="NASCIMENTOS" icone={soma}>
          <Linha rotulo="Nascimentos" valor={numero(dados.nascimentos.realizado)} />
          <Linha rotulo="% Em Relação a Meta" valor={percentual(dados.nascimentos.percentual_da_meta)} />
        </Painel>
        <Painel titulo="MORTES" icone={soma}>
          <Linha rotulo="Mortes" valor={numero(dados.mortes.realizado)} />
          <Linha rotulo="% Em Relação a Meta" valor={percentual(dados.mortes.percentual_da_meta)} />
          <Linha rotulo="Índ. Mortalidade" valor={percentual(dados.indice_mortalidade, 2)} />
        </Painel>
        <Painel titulo="COMPRAS | VENDAS" icone={soma}>
          <Linha rotulo="Compras" valor={numero(dados.compras.realizado)} />
          <Linha rotulo="% Em Relação a Meta" valor={percentual(dados.compras.percentual_da_meta)} />
          <Linha rotulo="Vendas" valor={numero(dados.vendas.realizado)} />
          <Linha rotulo="% Em Relação a Meta" valor={percentual(dados.vendas.percentual_da_meta)} />
        </Painel>
      </div>
      <GraficoDeColunas titulo="ESTOQUE FINAL MENSAL" colunas={estoqueMensal} />
      <div className="estoque-por-categoria">
        <GraficoDeColunas titulo="ESTOQUE POR CATEGORIA" colunas={porCategoria} />
        <div className="rebanho-final">
          <strong>{numero(dados.estoque_final)}</strong>
          <span>REBANHO FINAL</span>
        </div>
      </div>
    </>
  );
}
