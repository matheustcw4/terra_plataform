import type { VersoesDaFazenda } from "../core/api/tipos";

// A versão do plano de cada fazenda (pedido do usuário, 10/11/2026): com todas as fazendas de um cliente no filtro,
// cada uma tem a sua escolha, de seleção múltipla. O filtro guarda as versões marcadas (as de uma fazenda somam) e as
// fazendas marcadas "nenhum planejamento"; a fazenda que não está em nenhuma das duas listas fica com a mais recente
// de cada safra. As opções de cada fazenda vêm prontas da API.

export type EscolhaDoPlano = {
  versoes: string[]; // as versões marcadas, de todas as fazendas
  semPlano: string[]; // as fazendas marcadas "nenhum planejamento"
};

// O jeito da escolha de uma fazenda, como a API devolve.
export type JeitoDaEscolha = "mais_recente" | "marcadas" | "nenhum";

export function jeitoDaEscolha(fazenda: VersoesDaFazenda): JeitoDaEscolha {
  if (fazenda.sem_plano) {
    return "nenhum";
  }
  if (fazenda.escolhidas.length > 0) {
    return "marcadas";
  }
  return "mais_recente";
}

// A fazenda volta para a mais recente: saem as versões marcadas dela e o "nenhum planejamento".
export function comMaisRecente(escolha: EscolhaDoPlano, fazenda: VersoesDaFazenda): EscolhaDoPlano {
  const daFazenda = fazenda.versoes.map((opcao) => opcao.id);
  return {
    versoes: escolha.versoes.filter((id) => !daFazenda.includes(id)),
    semPlano: escolha.semPlano.filter((id) => id !== fazenda.fazenda_id),
  };
}

// Marca ou desmarca uma versão da fazenda (as marcadas somam). Desmarcar a última volta para a mais recente.
export function comVersaoAlternada(escolha: EscolhaDoPlano, fazenda: VersoesDaFazenda, versao: string): EscolhaDoPlano {
  const semAsDaFazenda = comMaisRecente(escolha, fazenda);
  let marcadas = [...fazenda.escolhidas, versao];
  if (fazenda.escolhidas.includes(versao)) {
    marcadas = fazenda.escolhidas.filter((id) => id !== versao);
  }
  return { versoes: [...semAsDaFazenda.versoes, ...marcadas], semPlano: semAsDaFazenda.semPlano };
}

// A fazenda fica sem planejamento: saem as versões marcadas dela.
export function semPlanejamento(escolha: EscolhaDoPlano, fazenda: VersoesDaFazenda): EscolhaDoPlano {
  const semAsDaFazenda = comMaisRecente(escolha, fazenda);
  return { versoes: semAsDaFazenda.versoes, semPlano: [...semAsDaFazenda.semPlano, fazenda.fazenda_id] };
}

// Todas as fazendas da janela de volta para a mais recente (as escolhas de fazendas fora dela ficam).
export function maisRecenteEmTodas(escolha: EscolhaDoPlano, fazendas: VersoesDaFazenda[]): EscolhaDoPlano {
  let restante = escolha;
  for (const fazenda of fazendas) {
    restante = comMaisRecente(restante, fazenda);
  }
  return restante;
}

// O texto do botão: quantas fazendas têm escolha (ou, sem escolha, que vale a mais recente).
export function resumoDasVersoes(fazendas: VersoesDaFazenda[]): string {
  const comEscolha = fazendas.filter((fazenda) => jeitoDaEscolha(fazenda) !== "mais_recente").length;
  if (comEscolha === 0 && fazendas.length === 1) {
    return "Mais recente";
  }
  if (comEscolha === 0) {
    return "Mais recente em todas as fazendas";
  }
  if (comEscolha === 1) {
    return "1 fazenda com escolha própria";
  }
  return `${comEscolha} fazendas com escolha própria`;
}
