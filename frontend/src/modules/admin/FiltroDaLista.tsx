import { useState, type FormEvent } from "react";

type Props = {
  soPendentes: boolean;
  trocarSoPendentes: (soPendentes: boolean) => void;
  buscar: (busca: string) => void;
  dica: string; // o que a busca procura
};

// O filtro das listas de de-para: só os pendentes (ou todos) e uma busca por texto, aplicada ao clicar em Buscar
// (e não a cada letra, que faria uma consulta por tecla).
export function FiltroDaLista({ soPendentes, trocarSoPendentes, buscar, dica }: Props) {
  const [texto, trocarTexto] = useState("");

  function aoBuscar(evento: FormEvent) {
    evento.preventDefault();
    buscar(texto);
  }

  return (
    <form className="filtro-da-lista" onSubmit={aoBuscar}>
      <label className="filtro-da-lista-marcar">
        <input type="checkbox" checked={soPendentes} onChange={(evento) => trocarSoPendentes(evento.target.checked)} />
        Só os pendentes
      </label>
      <input type="search" value={texto} onChange={(evento) => trocarTexto(evento.target.value)} placeholder={dica}
        aria-label="Buscar" />
      <button type="submit" className="botao">Buscar</button>
    </form>
  );
}
