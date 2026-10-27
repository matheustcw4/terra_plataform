import { GraficoMensalDoLote } from "../../componentes/lotes/GraficoMensalDoLote";
import { QuadroDoSexo } from "../../componentes/lotes/QuadroDoSexo";
import { quadroDo, SEXOS } from "../../componentes/lotes/sexos";
import type { Vendas } from "../../core/api/tipos";
import { useArea } from "../../core/auth/AreaAutenticada";
import { Aviso } from "../../core/ui/Aviso";
import { Moldura } from "../../core/ui/Moldura";
import { Linha, Painel } from "../../core/ui/Painel";
import { dinheiro, numero } from "../../logic/formatar";
import { useVendas, type TipoDeVenda } from "./api";

// As páginas "Venda Abate" e "Venda em Pé" do BI: quadros Fêmea / Macho / Geral (realizado e planejado), o
// faturamento de cada um com a meta, e os gráficos mês a mês de faturamento e de cabeças.
export function VendasPagina({ tipo }: { tipo: TipoDeVenda }) {
  const { consulta } = useArea();
  const pagina = useVendas(consulta, tipo);
  return (
    <Moldura caminho={`/vendas/${tipo}`}>
      {pagina.isPending && <Aviso>Carregando…</Aviso>}
      {pagina.isError && <Aviso tipo="erro">Não foi possível carregar a página: {pagina.error.message}</Aviso>}
      {pagina.data && (
        <div className={pagina.isPlaceholderData ? "pagina atualizando" : "pagina"}>
          <Conteudo dados={pagina.data} tipo={tipo} />
        </div>
      )}
    </Moldura>
  );
}

function Conteudo({ dados, tipo }: { dados: Vendas; tipo: TipoDeVenda }) {
  return (
    <>
      <div className="paineis-3">
        {SEXOS.map((sexo) => (
          <QuadroDoSexo key={sexo.recorte} titulo={sexo.titulo} icone={sexo.icone} tipo={tipo}
            quadro={quadroDo(dados.quadro, sexo.recorte)} />
        ))}
      </div>
      <div className="vendas-corpo">
        <div className="coluna-faturamento">
          {SEXOS.map((sexo) => {
            const quadro = quadroDo(dados.quadro, sexo.recorte);
            return (
              <Painel key={sexo.recorte} titulo={sexo.titulo} icone={sexo.icone}>
                <Linha rotulo="Faturamento" valor={dinheiro(quadro.realizado.valor)} destaque />
                <Linha rotulo="Faturamento Planejado" valor={dinheiro(quadro.planejado.valor)} destaque />
              </Painel>
            );
          })}
        </div>
        <div className="coluna-graficos">
          <GraficoMensalDoLote titulo="RELAÇÃO MENSAL - FATURAMENTO" serie={dados.serie_mensal} realizado="valor"
            planejado="valor_planejado" formatar={(valor) => dinheiro(valor)} />
          <GraficoMensalDoLote titulo="RELAÇÃO MENSAL - VENDA EM CABEÇAS" serie={dados.serie_mensal}
            realizado="cabecas" planejado="cabecas_planejadas"
            linha={{ campo: "cabecas_acumuladas", nome: "Acumulado" }} formatar={(valor) => numero(valor)} />
        </div>
      </div>
    </>
  );
}
