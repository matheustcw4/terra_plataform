import { useState } from "react";
import { DialogoDeExportacao } from "./DialogoDeExportacao";
import { Icone } from "./Icone";

// O botão "Exportar PDF", presente em todas as páginas do boletim e no MENU.
export function BotaoExportarPdf() {
  const [aberto, setAberto] = useState(false);
  return (
    <>
      <button type="button" className="botao-exportar" aria-label="Exportar PDF" onClick={() => setAberto(true)}>
        <Icone nome="baixar" tamanho={15} />
        <span className="rotulo-do-botao">Exportar PDF</span>
      </button>
      {aberto && <DialogoDeExportacao aoFechar={() => setAberto(false)} />}
    </>
  );
}
