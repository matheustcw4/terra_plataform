import type { SituacaoDaAtualizacao } from "../core/api/tipos";
import { dataEHora } from "./formatar";

// O botão "Atualizar agora" do admin. A API só põe a carga na fila; quem carrega é o worker. A tela acompanha pela
// situação que a API devolve (a trava das cargas e a carga mais recente) e pela hora do pedido.
export type EstadoDaAtualizacao =
  | "parado" //       nada pedido (ou já acabou e a tela releu os dados)
  | "na_fila" //      pedida, o worker ainda não começou
  | "rodando" //      alguma carga está rodando (a pedida ou a da agenda)
  | "concluida" //    a carga pedida começou e já terminou: hora de reler os dados
  | "sem_resposta"; // pedida há mais de 2 minutos e nada começou: o worker deve estar parado

export const ESPERA_MAXIMA_DA_FILA_S = 120;

// `pedidaEm` é a hora do pedido no relógio do banco (a resposta do POST), como `agora` e `iniciado_em`.
export function estadoDaAtualizacao(situacao: SituacaoDaAtualizacao, pedidaEm: string | null): EstadoDaAtualizacao {
  if (situacao.rodando) {
    return "rodando";
  }
  if (pedidaEm === null) {
    return "parado";
  }
  const iniciadaEm = situacao.ultima?.iniciado_em ?? null;
  if (iniciadaEm !== null && Date.parse(iniciadaEm) >= Date.parse(pedidaEm)) {
    return "concluida";
  }
  const esperaS = (Date.parse(situacao.agora) - Date.parse(pedidaEm)) / 1000;
  if (esperaS > ESPERA_MAXIMA_DA_FILA_S) {
    return "sem_resposta";
  }
  return "na_fila";
}

// Enquanto espera o worker, a tela pergunta de novo a cada poucos segundos; parada, não pergunta.
export function precisaAcompanhar(estado: EstadoDaAtualizacao): boolean {
  return estado === "na_fila" || estado === "rodando";
}

export const ACOMPANHAR_A_CADA_MS = 4000;

// O `refetchInterval` da situação: milissegundos até perguntar de novo, ou false para não perguntar.
export function intervaloDeAcompanhamento(situacao: SituacaoDaAtualizacao | undefined,
  pedidaEm: string | null): number | false {
  if (situacao === undefined) {
    return false;
  }
  if (precisaAcompanhar(estadoDaAtualizacao(situacao, pedidaEm))) {
    return ACOMPANHAR_A_CADA_MS;
  }
  return false;
}

// O texto do botão ao passar o mouse (o botão é só o ícone).
export function dicaDaAtualizacao(estado: EstadoDaAtualizacao, situacao: SituacaoDaAtualizacao | undefined): string {
  if (estado === "na_fila") {
    return "Atualização pedida: esperando o worker começar";
  }
  if (estado === "rodando") {
    return "Carga rodando: os números atualizam quando ela terminar";
  }
  if (estado === "sem_resposta") {
    return "A atualização não começou em 2 minutos: confira se o worker está no ar";
  }
  const ultima = situacao?.ultima ?? null;
  if (ultima === null) {
    return "Atualizar os dados agora";
  }
  return `Atualizar os dados agora (última carga: ${dataEHora(ultima.finalizado_em ?? ultima.iniciado_em)})`;
}
