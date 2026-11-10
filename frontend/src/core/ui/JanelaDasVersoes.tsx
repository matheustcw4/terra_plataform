import { createPortal } from "react-dom";
import { jeitoDaEscolha } from "../../logic/versaoDoPlano";
import type { VersoesDaFazenda } from "../api/tipos";

// O que cada caixa da janela faz com a escolha da fazenda (quem guarda no filtro é a EscolhaDasVersoes).
export type AcoesDaJanela = {
  maisRecente: (fazenda: VersoesDaFazenda) => void;
  alternarVersao: (fazenda: VersoesDaFazenda, versao: string) => void;
  nenhum: (fazenda: VersoesDaFazenda) => void;
  maisRecenteEmTodas: () => void;
};

type Props = { fazendas: VersoesDaFazenda[]; acoes: AcoesDaJanela; aoFechar: () => void };

// A janela da versão do plano de cada fazenda (pedido do usuário, 10/11/2026): uma linha por fazenda do filtro, com
// caixas de seleção múltipla: "Mais recente" (o padrão), cada versão (as marcadas somam) e "Nenhum planejamento". A
// escolha vale na hora (os números atrás da janela se refazem).
// Vai direto no <body>: dentro do topo da página, as regras dos campos de lá esticavam as linhas da janela.
export function JanelaDasVersoes({ fazendas, acoes, aoFechar }: Props) {
  return createPortal(
    <div className="dialogo-fundo" onKeyDown={(evento) => evento.key === "Escape" && aoFechar()}>
      <div className="dialogo janela-das-versoes" role="dialog" aria-modal="true" aria-labelledby="titulo-das-versoes">
        <h2 id="titulo-das-versoes">Versão do planejamento por fazenda</h2>
        <p>
          Vale nas metas de todas as páginas, no planejado do financeiro e no PDF. Sem escolha, entra a versão mais
          recente de cada safra; com mais de uma marcada, as versões somam.
        </p>
        <div className="janela-das-versoes-lista">
          {fazendas.map((fazenda) => (
            <VersoesDeUmaFazenda key={fazenda.fazenda_id} fazenda={fazenda} acoes={acoes} />
          ))}
        </div>
        <div className="dialogo-botoes">
          <button type="button" onClick={acoes.maisRecenteEmTodas}>
            Mais recente em todas
          </button>
          <button type="button" className="primario" onClick={aoFechar}>
            Fechar
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}

type PropsDaFazenda = { fazenda: VersoesDaFazenda; acoes: AcoesDaJanela };

// Uma linha da janela: o nome da fazenda à esquerda e as caixas à direita. Com uma versão só, a caixa dela é o
// "tem planejamento" (desmarcar = nenhum); com várias, há também a "Mais recente".
function VersoesDeUmaFazenda({ fazenda, acoes }: PropsDaFazenda) {
  const [maisRecente] = fazenda.versoes;
  if (maisRecente === undefined) {
    return (
      <div className="janela-das-versoes-linha">
        <span className="janela-das-versoes-fazenda">{fazenda.fazenda}</span>
        <span className="janela-das-versoes-unica">Sem planejamento no período</span>
      </div>
    );
  }
  const jeito = jeitoDaEscolha(fazenda);
  const umaSo = fazenda.versoes.length === 1;
  return (
    <div className="janela-das-versoes-linha">
      <span className="janela-das-versoes-fazenda">{fazenda.fazenda}</span>
      <div className="janela-das-versoes-caixas" role="group" aria-label={`Versões de ${fazenda.fazenda}`}>
        {!umaSo && (
          <Caixa marcada={jeito === "mais_recente"} aoTrocar={() => acoes.maisRecente(fazenda)}>
            Mais recente ({maisRecente.rotulo})
          </Caixa>
        )}
        {fazenda.versoes.map((versao) => (
          <Caixa key={versao.id} marcada={marcadaNaLinha(fazenda, versao.id)}
            aoTrocar={() => alternarNaLinha(fazenda, versao.id, acoes)}>
            {versao.rotulo}
          </Caixa>
        ))}
        <Caixa marcada={jeito === "nenhum"}
          aoTrocar={() => (jeito === "nenhum" ? acoes.maisRecente(fazenda) : acoes.nenhum(fazenda))}>
          Nenhum planejamento
        </Caixa>
      </div>
    </div>
  );
}

// Com uma versão só, ela vale sempre que a fazenda não está "sem planejamento"; com várias, só quando marcada.
function marcadaNaLinha(fazenda: VersoesDaFazenda, versao: string): boolean {
  if (fazenda.versoes.length === 1) {
    return !fazenda.sem_plano;
  }
  return fazenda.escolhidas.includes(versao);
}

function alternarNaLinha(fazenda: VersoesDaFazenda, versao: string, acoes: AcoesDaJanela) {
  if (fazenda.versoes.length > 1) {
    acoes.alternarVersao(fazenda, versao);
  } else if (fazenda.sem_plano) {
    acoes.maisRecente(fazenda);
  } else {
    acoes.nenhum(fazenda);
  }
}

function Caixa({ marcada, aoTrocar, children }: { marcada: boolean; aoTrocar: () => void; children: string[] | string }) {
  return (
    <label>
      <input type="checkbox" checked={marcada} onChange={aoTrocar} />
      {children}
    </label>
  );
}
