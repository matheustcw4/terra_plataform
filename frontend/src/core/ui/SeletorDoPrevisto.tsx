import { useSearchParams } from "react-router";
import { urlComTipo, urlComVersao } from "../../logic/previsto";
import type { EscolhaDoPrevisto } from "../api/tipos";

type Props = { escolha: EscolhaDoPrevisto };

// De qual orçamento vem o planejado do financeiro (Previsto × Realizado e Financeiro; pedido do usuário, 29/10/2026).
// As opções vêm prontas da API, só com o que existe nas fazendas do filtro; a versão aparece quando há mais de uma.
// A escolha fica na URL: vale nas duas páginas e vai junto no PDF. É a única escolha fora do MENU.
export function SeletorDoPrevisto({ escolha }: Props) {
  const [parametros, setParametros] = useSearchParams();
  if (escolha.tipos.length === 0) {
    return null;
  }
  return (
    <div className="seletor-do-previsto">
      <label className="campo">
        <span>Planejado do financeiro</span>
        <select value={escolha.tipo ?? ""}
          onChange={(evento) => setParametros(urlComTipo(parametros, evento.target.value), { replace: true })}>
          {escolha.tipos.map((tipo) => (
            <option key={tipo.codigo} value={tipo.codigo}>{tipo.rotulo}</option>
          ))}
        </select>
      </label>
      {escolha.versoes.length > 1 && (
        <label className="campo">
          <span>Versão do planejamento</span>
          <select value={escolha.versao ?? ""}
            onChange={(evento) => setParametros(urlComVersao(parametros, evento.target.value), { replace: true })}>
            <option value="">Mais recente de cada safra</option>
            {escolha.versoes.map((versao) => (
              <option key={versao.id} value={versao.id}>{versao.rotulo}</option>
            ))}
          </select>
        </label>
      )}
    </div>
  );
}
