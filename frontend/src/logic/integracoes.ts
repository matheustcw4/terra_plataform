import type { CargaDaIntegracao, SituacaoDaCarga, UnidadeDaCarga } from "../core/api/tipos";

// A tela de integrações (só o admin): o histórico das cargas de cada API, como o Metryx. A API manda tudo pronto; aqui
// só os rótulos, o selo e as contas de exibição (duração, resumo dos clientes).

const ROTULOS_DA_CARGA: Record<SituacaoDaCarga, string> = {
  pendente: "Na fila",
  processando: "Rodando",
  concluido: "Concluída",
  concluido_com_avisos: "Concluída, com avisos",
  erro: "Com erro",
};

export function rotuloDaCarga(situacao: SituacaoDaCarga): string {
  return ROTULOS_DA_CARGA[situacao];
}

// O selo: verde quando tudo entrou, laranja quando há o que conferir, vermelho quando nada entrou.
export function classeDaCarga(situacao: SituacaoDaCarga): string {
  if (situacao === "concluido") {
    return "selo selo-ok";
  }
  if (situacao === "concluido_com_avisos") {
    return "selo selo-aviso";
  }
  if (situacao === "erro") {
    return "selo selo-erro";
  }
  return "selo selo-andamento";
}

export function cargaRodando(carga: CargaDaIntegracao): boolean {
  return carga.status === "pendente" || carga.status === "processando";
}

// Enquanto alguma roda, a tela pergunta de novo a cada poucos segundos.
export function algumaRodando(cargas: CargaDaIntegracao[]): boolean {
  return cargas.some(cargaRodando);
}

// "45 s", "2 min 05 s"; "—" enquanto não terminou.
export function duracaoDaCarga(carga: CargaDaIntegracao): string {
  if (carga.iniciado_em === null || carga.finalizado_em === null) {
    return "—";
  }
  const segundos = Math.max(0, Math.round((Date.parse(carga.finalizado_em) - Date.parse(carga.iniciado_em)) / 1000));
  if (segundos < 60) {
    return `${segundos} s`;
  }
  const minutos = Math.floor(segundos / 60);
  const resto = String(segundos % 60).padStart(2, "0");
  return `${minutos} min ${resto} s`;
}

// A lista de erros e avisos vazia: a carga ainda roda, não teve nenhum ou os dela já saíram (cada carga nova de um
// cliente troca os avisos da anterior, como em Pendências: ficam os da última).
export function textoSemAvisos(carga: CargaDaIntegracao): string {
  if (cargaRodando(carga)) {
    return "A carga ainda está rodando: o resultado aparece quando ela terminar.";
  }
  if (carga.status === "concluido") {
    return "Nenhum erro ou aviso nesta carga.";
  }
  return "Os avisos desta carga já saíram: cada carga nova de um cliente troca os da anterior (ficam os da última).";
}

// Quem pediu: o admin pelo "Atualizar agora" ou, sem usuário, a agenda (ou a linha de comando).
export function origemDoPedido(carga: CargaDaIntegracao): string {
  if (carga.pedida_por === null) {
    return "pela agenda";
  }
  return `pedida por ${carga.pedida_por}`;
}

type ContagemDosClientes = { carregados: number; semMudanca: number; comErro: number; naoEntraram: number };

function contarClientes(unidades: UnidadeDaCarga[]): ContagemDosClientes {
  const contagem = { carregados: 0, semMudanca: 0, comErro: 0, naoEntraram: 0 };
  for (const unidade of unidades) {
    if (unidade.status === "carregada" || unidade.status === "carregada_com_avisos") {
      contagem.carregados += 1;
    } else if (unidade.status === "inalterada") {
      contagem.semMudanca += 1;
    } else if (unidade.status === "erro") {
      contagem.comErro += 1;
    } else {
      contagem.naoEntraram += 1;
    }
  }
  return contagem;
}

// "3 clientes: 2 carregados · 1 com erro"; "nenhum cliente" quando a carga nem chegou a listá-los.
export function resumoDosClientes(unidades: UnidadeDaCarga[]): string {
  if (unidades.length === 0) {
    return "nenhum cliente";
  }
  const contagem = contarClientes(unidades);
  const partes: string[] = [];
  if (contagem.carregados > 0) {
    partes.push(plural(contagem.carregados, "carregado", "carregados"));
  }
  if (contagem.semMudanca > 0) {
    partes.push(`${contagem.semMudanca} sem mudança`);
  }
  if (contagem.comErro > 0) {
    partes.push(`${contagem.comErro} com erro`);
  }
  if (contagem.naoEntraram > 0) {
    partes.push(plural(contagem.naoEntraram, "não entrou", "não entraram"));
  }
  return `${plural(unidades.length, "cliente", "clientes")}: ${partes.join(" · ")}`;
}

function plural(quantidade: number, singular: string, varios: string): string {
  if (quantidade === 1) {
    return `1 ${singular}`;
  }
  return `${quantidade} ${varios}`;
}
