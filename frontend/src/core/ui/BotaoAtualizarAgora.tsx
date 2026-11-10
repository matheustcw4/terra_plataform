import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { usePedirAtualizacao, useSituacaoDaAtualizacao } from "../api/atualizacao";
import { dicaDaAtualizacao, estadoDaAtualizacao, type EstadoDaAtualizacao } from "../../logic/atualizacao";
import { Icone } from "./Icone";

// "Atualizar agora", só para o admin, no topo de todas as telas: pede ao worker a carga do Metryx, gira enquanto ele
// trabalha e, quando a carga pedida termina, faz todas as páginas relerem os números. As planilhas não passam por
// aqui: chegam pela tela de importação. Com o Metryx desligado não há o que puxar, e o botão não aparece (a API diz
// pelo `disponivel`).
export function BotaoAtualizarAgora() {
  const cliente = useQueryClient();
  const [pedidaEm, trocarPedidaEm] = useState<string | null>(null);
  const situacao = useSituacaoDaAtualizacao(pedidaEm);
  const pedir = usePedirAtualizacao();

  let estado: EstadoDaAtualizacao = "parado";
  if (situacao.data !== undefined) {
    estado = estadoDaAtualizacao(situacao.data, pedidaEm);
  }

  useEffect(() => {
    if (estado === "concluida") {
      trocarPedidaEm(null);
      cliente.invalidateQueries();
    }
  }, [estado, cliente]);

  function atualizar() {
    pedir.mutate(undefined, {
      onSuccess: (pedido) => trocarPedidaEm(pedido.pedida_em),
      // 409: já tem carga rodando; a situação relida mostra o botão girando
      onSettled: () => situacao.refetch(),
    });
  }

  if (situacao.data?.disponivel !== true) {
    return null;
  }

  const ocupado = pedir.isPending || estado === "na_fila" || estado === "rodando";
  let dica = dicaDaAtualizacao(estado, situacao.data);
  let aviso: string | null = null;
  if (estado === "sem_resposta") {
    aviso = "Sem resposta";
  }
  if (pedir.isError && pedir.error.message !== "" && !ocupado) {
    dica = `Não deu para atualizar: ${pedir.error.message}`;
    aviso = "Não atualizou";
  }

  let classes = "botao-atualizar";
  if (ocupado) {
    classes += " girando";
  }
  if (aviso !== null) {
    classes += " com-aviso";
  }

  return (
    <button type="button" className={classes} onClick={atualizar} disabled={ocupado} title={dica} aria-label={dica}>
      <Icone nome="atualizar" tamanho={16} />
      {aviso !== null && <span className="botao-atualizar-aviso">{aviso}</span>}
    </button>
  );
}
