import { useSearchParams } from "react-router";
import { urlComTipo } from "../../logic/previsto";
import type { EscolhaDoPrevisto } from "../api/tipos";
import { EscolhaDasVersoes } from "./EscolhaDasVersoes";
import { FiltroDoStatus } from "./FiltroDoStatus";

type Props = { escolha: EscolhaDoPrevisto };

// O topo das páginas do financeiro (Previsto × Realizado e Financeiro): de qual orçamento vem o planejado (o tipo,
// pedido do usuário de 29/10/2026), o status dos lançamentos do realizado e a versão do plano de cada fazenda (as
// mesmas das metas das outras páginas; pedidos de 10/11/2026), com a versão em uso. As opções vêm prontas da API, só
// com o que existe nas fazendas do filtro. As escolhas ficam na URL.
export function SeletorDoPrevisto({ escolha }: Props) {
  const [parametros, setParametros] = useSearchParams();
  if (escolha.tipos.length === 0) {
    return (
      <div className="seletor-do-previsto">
        <FiltroDoStatus />
      </div>
    );
  }
  return (
    <EscolhaDasVersoes escolha={escolha}>
      <label className="campo">
        <span>Planejado do financeiro</span>
        <select value={escolha.tipo ?? ""}
          onChange={(evento) => setParametros(urlComTipo(parametros, evento.target.value), { replace: true })}>
          {escolha.tipos.map((tipo) => (
            <option key={tipo.codigo} value={tipo.codigo}>{tipo.rotulo}</option>
          ))}
        </select>
      </label>
      <FiltroDoStatus />
    </EscolhaDasVersoes>
  );
}
