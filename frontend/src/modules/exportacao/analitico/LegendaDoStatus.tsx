import { Status } from "./Status";

// O que cada cor do status quer dizer, embaixo das tabelas que o usam. A tolerância é o limiar do semáforo
// (`dim.parametro`), o mesmo da página Previsto × Realizado.
export function LegendaDoStatus() {
  return (
    <p className="legenda-do-status">
      <Status status="verde" /> no rumo do previsto
      <Status status="amarelo" /> perto do previsto, dentro da tolerância
      <Status status="vermelho" /> fora do previsto, no lado ruim
      <span className="apagado">Sem status: sem previsto, ou indicador sem lado certo (rebanho, lotação).</span>
    </p>
  );
}
