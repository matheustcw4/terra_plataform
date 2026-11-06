import type { ReactNode } from "react";
import { useSearchParams } from "react-router";
import { urlComVersao } from "../../logic/previsto";
import type { EscolhaDaVersao } from "../api/tipos";

type Props = {
  escolha: EscolhaDaVersao;
  children?: ReactNode; // campos que vêm antes da versão (o tipo do orçamento, no Previsto × Realizado e no Financeiro)
};

// A versão do planejamento (pedido do usuário, 04/11/2026): quando alguma fazenda do filtro tem mais de uma, a página
// deixa escolher; sempre diz qual versão está valendo. As opções vêm prontas da API. A escolha fica na URL: vale nas
// metas de todas as páginas e vai junto no PDF.
export function SeletorDaVersao({ escolha, children }: Props) {
  const [parametros, setParametros] = useSearchParams();
  const temEscolha = escolha.versoes.length > 1;
  if (!children && !temEscolha && escolha.em_uso.length === 0) {
    return null;
  }
  return (
    <div className="seletor-do-previsto">
      {children}
      {temEscolha && (
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
      {escolha.em_uso.length > 0 && (
        <p className="versao-em-uso">
          <span>Planejamento em uso</span>
          {escolha.em_uso.join("; ")}
        </p>
      )}
    </div>
  );
}
