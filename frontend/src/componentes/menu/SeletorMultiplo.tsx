import { useEffect, useRef, useState } from "react";
import { alternarItem } from "../../logic/filtro";

export type Opcao = { valor: string; rotulo: string };

type Props = {
  nome: string; // o nome do campo, para quem usa leitor de tela ("Mês", "Fazenda")
  opcoes: Opcao[];
  marcados: string[]; // os valores marcados; vazio = todos
  rotuloDeTodos: string; // a primeira caixa, que desmarca o resto ("Todos", "Todas (grupo)")
  resumo: string; // o que o campo mostra fechado
  colunas?: 1 | 2; // meses cabem em duas colunas; nomes de fazenda, em uma
  aoTrocar: (marcados: string[]) => void;
};

// Campo de seleção múltipla do MENU (meses e fazendas), como os filtros do BI: uma lista de caixas que abre sob o
// campo e fecha ao clicar fora dele. Marcar todas as caixas é o mesmo que "todos" (logic/filtro.ts, alternarItem).
export function SeletorMultiplo({ nome, opcoes, marcados, rotuloDeTodos, resumo, colunas = 2, aoTrocar }: Props) {
  const [aberto, setAberto] = useState(false);
  const caixa = useRef<HTMLDivElement>(null);
  const valores = opcoes.map((opcao) => opcao.valor);

  useEffect(() => {
    if (!aberto) {
      return undefined;
    }
    function fecharAoClicarFora(evento: MouseEvent) {
      if (caixa.current !== null && !caixa.current.contains(evento.target as Node)) {
        setAberto(false);
      }
    }
    document.addEventListener("mousedown", fecharAoClicarFora);
    return () => document.removeEventListener("mousedown", fecharAoClicarFora);
  }, [aberto]);

  let classesDaLista = "seletor-multiplo-lista";
  if (colunas === 1) {
    classesDaLista += " uma-coluna";
  }

  return (
    <div className="seletor-multiplo" ref={caixa}>
      <button type="button" className="seletor-multiplo-botao" aria-expanded={aberto} aria-label={`${nome}: ${resumo}`}
        title={resumo} onClick={() => setAberto(!aberto)}>
        {resumo}
      </button>
      {aberto && (
        <div className={classesDaLista} role="group" aria-label={nome}>
          <label className="seletor-multiplo-todos">
            <input type="checkbox" checked={marcados.length === 0} onChange={() => aoTrocar([])} />
            {rotuloDeTodos}
          </label>
          {opcoes.map((opcao) => (
            <label key={opcao.valor}>
              <input type="checkbox" checked={marcados.includes(opcao.valor)}
                onChange={() => aoTrocar(alternarItem(marcados, opcao.valor, valores))} />
              {opcao.rotulo}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
