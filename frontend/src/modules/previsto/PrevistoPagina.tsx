import { useSearchParams } from "react-router";
import { useArea } from "../../core/auth/AreaAutenticada";
import { Aviso } from "../../core/ui/Aviso";
import { Moldura } from "../../core/ui/Moldura";
import { SeletorDoPrevisto } from "../../core/ui/SeletorDoPrevisto";
import { pedidoDaUrl } from "../../logic/previsto";
import { usePrevistoRealizado } from "./api";
import { TabelaDoPrevisto } from "./TabelaDoPrevisto";

// A página "Previsto x Realizado" do BI: o DRE por classificação e conta, realizado × planejado no último mês e no
// acumulado do período, com o semáforo. O planejado vem do orçamento escolhido no topo da página (tipo e versão).
export function PrevistoPagina() {
  const { consulta } = useArea();
  const [parametros] = useSearchParams();
  const pagina = usePrevistoRealizado(consulta, pedidoDaUrl(parametros));
  return (
    <Moldura caminho="/previsto_realizado">
      {pagina.isPending && <Aviso>Carregando…</Aviso>}
      {pagina.isError && <Aviso tipo="erro">Não foi possível carregar a página: {pagina.error.message}</Aviso>}
      {pagina.data && <SeletorDoPrevisto escolha={pagina.data.previsto} />}
      {pagina.data && pagina.data.grupos.length === 0 && <Aviso>Nenhum lançamento financeiro no período.</Aviso>}
      {pagina.data && pagina.data.grupos.length > 0 && (
        <div className={pagina.isPlaceholderData ? "pagina atualizando" : "pagina"}>
          <TabelaDoPrevisto dados={pagina.data} />
          <p className="explicacao">
            Resultado = receitas + outros créditos − (investimentos + custeio + outros débitos). Semáforo: nas receitas,
            verde acima de 3% da meta e vermelho abaixo de −3%; nas despesas, verde até a meta, amarelo até 3% acima e
            vermelho além disso.
          </p>
        </div>
      )}
    </Moldura>
  );
}
