import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import type { Importacao } from "../../core/api/tipos";
import { useArea } from "../../core/auth/AreaAutenticada";
import { BotaoSair } from "../../core/auth/BotaoSair";
import { Aviso } from "../../core/ui/Aviso";
import { Casca } from "../../core/ui/Casca";
import { gruposDoBoletim, IMPORTACAO } from "../../core/ui/paginasDoBoletim";
import { algumaEmAndamento, terminouAlguma } from "../../logic/importacao";
import { useImportacoes } from "./api";
import { EnvioDePlanilhas } from "./EnvioDePlanilhas";
import { ListaDeImportacoes } from "./ListaDeImportacoes";

// Importação de planilhas (no lugar da pasta do Google Drive): a pessoa envia os RELATÓRIO*.xlsm e o servidor os
// carrega, um por vez. Não usa o filtro do MENU: a fazenda vem de dentro da planilha.
export function ImportacaoPagina() {
  const { escopo } = useArea();
  const cliente = useQueryClient();
  const lista = useImportacoes();
  const leituraAnterior = useRef<Importacao[]>([]);

  // terminou uma carga: os números, as pendências e até o escopo (fazenda nova) podem ter mudado
  useEffect(() => {
    if (lista.data === undefined) {
      return;
    }
    if (terminouAlguma(leituraAnterior.current, lista.data)) {
      cliente.invalidateQueries();
    }
    leituraAnterior.current = lista.data;
  }, [lista.data, cliente]);

  const controles = (
    <>
      <span className="topo-usuario">{escopo.usuario.nome}</span>
      <BotaoSair />
    </>
  );
  return (
    <Casca secao="Dados" grupos={gruposDoBoletim(escopo.usuario.eh_admin)} titulo={IMPORTACAO.rotulo}
      icone={IMPORTACAO.icone} subtitulo="As planilhas das fazendas entram por aqui" controles={controles}>
      <div className="pagina">
        <section className="painel-grafico">
          <h2>ENVIAR PLANILHAS</h2>
          <Explicacao ehAdmin={escopo.usuario.eh_admin} />
          <EnvioDePlanilhas />
        </section>
        <section className="painel-grafico tabela-rolavel">
          <h2>
            IMPORTAÇÕES RECENTES
            {lista.data && algumaEmAndamento(lista.data) && <span className="selo selo-andamento">carregando</span>}
          </h2>
          {lista.isPending && <Aviso>Carregando…</Aviso>}
          {lista.isError && <Aviso tipo="erro">Não foi possível carregar a lista: {lista.error.message}</Aviso>}
          {lista.data && <ListaDeImportacoes lista={lista.data} />}
        </section>
      </div>
    </Casca>
  );
}

function Explicacao({ ehAdmin }: { ehAdmin: boolean }) {
  let fazendaNova = "A primeira planilha de uma fazenda nova é importada pelo administrador.";
  if (ehAdmin) {
    fazendaNova = "Como administrador, você também importa a primeira planilha de uma fazenda nova (ela é cadastrada "
      + "a partir da planilha) e depois dá o acesso aos técnicos.";
  }
  return (
    <p className="explicacao">
      Cada arquivo entra na fila e o servidor carrega um de cada vez (um ou dois minutos por planilha); a lista abaixo
      mostra o resultado. A planilha substitui os números do período dela em diante, como antes, e o que estiver errado
      nela aparece em Pendências. Você importa só as planilhas das fazendas a que tem acesso. {fazendaNova}
    </p>
  );
}
