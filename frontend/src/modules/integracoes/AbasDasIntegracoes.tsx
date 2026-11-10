import { NavLink, useLocation } from "react-router";
import type { IntegracaoPorApi } from "../../core/api/tipos";
import { INTEGRACOES } from "../../core/ui/paginasDoBoletim";

// As abas: as planilhas enviadas pela tela e uma por API que a API do painel lista (hoje, o Metryx). Quem não é
// admin não vê as APIs e fica só com as planilhas, sem abas.
export function AbasDasIntegracoes({ apis }: { apis: IntegracaoPorApi[] }) {
  const { search } = useLocation();
  if (apis.length === 0) {
    return null;
  }
  return (
    <nav className="abas abas-das-integracoes" aria-label="Integrações">
      <NavLink to={{ pathname: INTEGRACOES.caminho, search }} end>
        Planilhas
      </NavLink>
      {apis.map((api) => (
        <NavLink key={api.fonte} to={{ pathname: `${INTEGRACOES.caminho}/${api.fonte}`, search }}>
          {api.rotulo}
        </NavLink>
      ))}
    </nav>
  );
}
