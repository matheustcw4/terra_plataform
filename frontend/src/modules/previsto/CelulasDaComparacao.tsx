import type { Comparacao } from "../../core/api/tipos";
import { dinheiro, percentual } from "../../logic/formatar";

const NOME_DO_SEMAFORO: Record<string, string> = { verde: "dentro da meta", amarelo: "perto da meta",
  vermelho: "fora da meta" };

// As três colunas de um bloco da matriz (Realizado, Planejado, % Variação), com o semáforo que a API decidiu.
export function CelulasDaComparacao({ comparacao, inicioDoBloco }: { comparacao: Comparacao; inicioDoBloco: boolean }) {
  return (
    <>
      <td className={inicioDoBloco ? "inicio-do-bloco" : undefined}>{dinheiro(comparacao.realizado)}</td>
      <td>{dinheiro(comparacao.planejado)}</td>
      <td className="variacao">
        {percentual(comparacao.variacao)}
        {comparacao.semaforo !== null && (
          <span className={`semaforo semaforo-${comparacao.semaforo}`} role="img"
            aria-label={NOME_DO_SEMAFORO[comparacao.semaforo] ?? comparacao.semaforo} />
        )}
      </td>
    </>
  );
}
