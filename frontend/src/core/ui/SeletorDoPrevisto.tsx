import { useSearchParams } from "react-router";
import { urlComTipo } from "../../logic/previsto";
import type { EscolhaDoPrevisto } from "../api/tipos";
import { SeletorDaVersao } from "./SeletorDaVersao";

type Props = { escolha: EscolhaDoPrevisto };

// De qual orçamento vem o planejado do financeiro (Previsto × Realizado e Financeiro; pedido do usuário, 29/10/2026):
// o tipo e, quando há mais de uma, a versão do plano (a mesma das metas das outras páginas), com a versão em uso.
// As opções vêm prontas da API, só com o que existe nas fazendas do filtro. A escolha fica na URL.
export function SeletorDoPrevisto({ escolha }: Props) {
  const [parametros, setParametros] = useSearchParams();
  if (escolha.tipos.length === 0) {
    return null;
  }
  return (
    <SeletorDaVersao escolha={escolha}>
      <label className="campo">
        <span>Planejado do financeiro</span>
        <select value={escolha.tipo ?? ""}
          onChange={(evento) => setParametros(urlComTipo(parametros, evento.target.value), { replace: true })}>
          {escolha.tipos.map((tipo) => (
            <option key={tipo.codigo} value={tipo.codigo}>{tipo.rotulo}</option>
          ))}
        </select>
      </label>
    </SeletorDaVersao>
  );
}
