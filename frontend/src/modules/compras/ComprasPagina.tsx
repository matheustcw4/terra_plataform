import soma from "../../assets/bi/soma.png";
import { GraficoMensalDoLote } from "../../componentes/lotes/GraficoMensalDoLote";
import { QuadroDoSexo } from "../../componentes/lotes/QuadroDoSexo";
import { quadroDo, SEXOS } from "../../componentes/lotes/sexos";
import type { Compras } from "../../core/api/tipos";
import { useArea } from "../../core/auth/AreaAutenticada";
import { Aviso } from "../../core/ui/Aviso";
import { Moldura } from "../../core/ui/Moldura";
import { Linha, Painel } from "../../core/ui/Painel";
import { dinheiro, numero, percentual } from "../../logic/formatar";
import { useCompras } from "./api";

// A página "Compras" do BI: quadros Fêmea / Macho / Geral (cabeças compradas, peso médio e preço do kg, realizado e
// planejado), o preço da @ de compra e o ágio, o investimento de cada um com a meta, e os gráficos mês a mês.
export function ComprasPagina() {
  const { consulta } = useArea();
  const pagina = useCompras(consulta);
  return (
    <Moldura caminho="/compras">
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

function Conteudo({ dados }: { dados: Compras }) {
  return (
    <>
      <div className="paineis-4">
        {SEXOS.map((sexo) => (
          <QuadroDoSexo key={sexo.recorte} titulo={sexo.titulo} icone={sexo.icone} tipo="compra"
            quadro={quadroDo(dados.quadro, sexo.recorte)} />
        ))}
        <Painel titulo="REPOSIÇÃO" icone={soma}>
          <Linha rotulo="Preço de @ de Compra" valor={dinheiro(dados.preco_arroba_compra, 2)} destaque />
          <Linha rotulo="Ágio" valor={percentual(dados.agio)} destaque />
          <Linha rotulo="@ vendida (abate + em pé)" valor={dinheiro(dados.preco_arroba_venda, 2)} />
        </Painel>
      </div>
      <div className="vendas-corpo">
        <div className="coluna-faturamento">
          {SEXOS.map((sexo) => {
            const quadro = quadroDo(dados.quadro, sexo.recorte);
            return (
              <Painel key={sexo.recorte} titulo={sexo.titulo} icone={sexo.icone}>
                <Linha rotulo="Inv. Realizado" valor={dinheiro(quadro.realizado.valor)} destaque />
                <Linha rotulo="Inv. Planejado" valor={dinheiro(quadro.planejado.valor)} destaque />
              </Painel>
            );
          })}
        </div>
        <div className="coluna-graficos">
          <GraficoMensalDoLote titulo="RELAÇÃO DESEMBOLSO DE COMPRAS" serie={dados.serie_mensal} realizado="valor"
            planejado="valor_planejado" linha={{ campo: "preco_arroba", nome: "Preço da @" }}
            formatar={(valor) => dinheiro(valor)} />
          <GraficoMensalDoLote titulo="RELAÇÃO CABEÇAS COMPRADAS" serie={dados.serie_mensal} realizado="cabecas"
            planejado="cabecas_planejadas" linha={{ campo: "cabecas_acumuladas", nome: "Acumulado" }}
            formatar={(valor) => numero(valor)} />
        </div>
      </div>
    </>
  );
}
