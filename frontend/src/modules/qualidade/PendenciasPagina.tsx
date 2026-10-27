import { useState } from "react";
import type { Pendencias } from "../../core/api/tipos";
import { useArea } from "../../core/auth/AreaAutenticada";
import { Aviso } from "../../core/ui/Aviso";
import { Moldura } from "../../core/ui/Moldura";
import { Linha, Painel } from "../../core/ui/Painel";
import { numero } from "../../logic/formatar";
import { agruparPorOrigem, FILTROS_DE_PENDENCIA, filtrarPendencias, type FiltroDePendencia } from "./agrupar";
import { usePendencias } from "./api";
import { GrupoDaOrigem } from "./componentes/GrupoDaOrigem";

// Página nova (o BI não tem): o que corrigir na planilha ou no sistema de origem.
export function PendenciasPagina() {
  const { consulta } = useArea();
  const pagina = usePendencias(consulta);
  return (
    <Moldura caminho="/pendencias">
      {pagina.isPending && <Aviso>Carregando…</Aviso>}
      {pagina.isError && <Aviso tipo="erro">Não foi possível carregar as pendências: {pagina.error.message}</Aviso>}
      {pagina.data && (
        <div className={pagina.isPlaceholderData ? "pagina atualizando" : "pagina"}>
          <Conteudo dados={pagina.data} />
        </div>
      )}
    </Moldura>
  );
}

function Conteudo({ dados }: { dados: Pendencias }) {
  const [mostrar, setMostrar] = useState<FiltroDePendencia>("todas");
  const grupos = agruparPorOrigem(filtrarPendencias(dados.itens, mostrar));
  return (
    <>
      <div className="paineis-pendencias">
        <Painel titulo="PENDÊNCIAS DE LANÇAMENTO">
          <p className="explicacao">
            Linhas que a última carga deixou fora dos números ou que parecem digitadas errado. Corrija na planilha
            (ou no sistema de origem): na próxima carga, a pendência corrigida sai daqui. Vale para o cliente e a
            fazenda do MENU, em qualquer período.
          </p>
        </Painel>
        <Painel titulo="RESUMO">
          <Linha rotulo="Linhas que não entraram nos números" valor={numero(dados.resumo.nao_entrou)} />
          <Linha rotulo="Entraram, mas confira" valor={numero(dados.resumo.confira)} />
          <Linha rotulo="Com a equipe Terra" valor={numero(dados.resumo.para_a_equipe)} />
        </Painel>
      </div>
      <nav className="abas" aria-label="Mostrar">
        {FILTROS_DE_PENDENCIA.map((opcao) => (
          <button key={opcao.valor} type="button" className={opcao.valor === mostrar ? "active" : undefined}
            onClick={() => setMostrar(opcao.valor)}>
            {opcao.rotulo}
          </button>
        ))}
      </nav>
      {grupos.length === 0 && <Aviso>Nenhuma pendência nas fazendas escolhidas.</Aviso>}
      {grupos.map((grupo) => (
        <GrupoDaOrigem key={grupo.chave} grupo={grupo} />
      ))}
    </>
  );
}
