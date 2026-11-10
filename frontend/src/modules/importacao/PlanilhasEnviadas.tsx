import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import type { Importacao } from "../../core/api/tipos";
import { Aviso } from "../../core/ui/Aviso";
import { algumaEmAndamento, terminouAlguma } from "../../logic/importacao";
import { useImportacoes } from "./api";
import { EnvioDePlanilhas } from "./EnvioDePlanilhas";
import { ListaDeImportacoes } from "./ListaDeImportacoes";

// A aba Planilhas das integrações: a pessoa envia os RELATÓRIO*.xlsm e o servidor os carrega, um por vez, e a lista
// mostra o resultado de cada um. Não usa o filtro do MENU: a fazenda vem de dentro da planilha.
export function PlanilhasEnviadas({ ehAdmin }: { ehAdmin: boolean }) {
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

  return (
    <>
      <section className="painel-grafico">
        <h2>ENVIAR PLANILHAS</h2>
        <Explicacao ehAdmin={ehAdmin} />
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
    </>
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
