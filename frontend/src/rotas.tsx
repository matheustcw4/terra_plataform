import { createBrowserRouter } from "react-router";
import { AreaAutenticada } from "./core/auth/AreaAutenticada";
import { Redirecionar } from "./core/ui/Redirecionar";
import { rotasDoAdmin } from "./modules/admin/AdminModule";
import { rotasDasCompras } from "./modules/compras/ComprasModule";
import { rotasDaExportacao } from "./modules/exportacao/ExportacaoModule";
import { rotasDoFinanceiro } from "./modules/financeiro/FinanceiroModule";
import { rotasDoPrevisto } from "./modules/previsto/PrevistoModule";
import { rotasDasMortes } from "./modules/mortes/MortesModule";
import { rotasDosNascimentos } from "./modules/nascimentos/NascimentosModule";
import { rotasDaQualidade } from "./modules/qualidade/QualidadeModule";
import { rotasDoRebanho } from "./modules/rebanho/RebanhoModule";
import { rotasDasTransferencias } from "./modules/transferencias/TransferenciasModule";
import { rotasDasVendas } from "./modules/vendas/VendasModule";
import { LoginPagina } from "./pages/LoginPagina";
import { MenuPagina } from "./pages/MenuPagina";
import { NaoEncontradaPagina } from "./pages/NaoEncontradaPagina";

// Mapa das páginas. Tudo dentro de AreaAutenticada exige login e recebe o filtro escolhido no MENU.
export const rotas = createBrowserRouter([
  { path: "/login", element: <LoginPagina /> },
  {
    path: "/",
    element: <AreaAutenticada />,
    children: [
      // Como no BI, o boletim abre pelo MENU, onde ficam os filtros.
      { index: true, element: <Redirecionar para="/menu" /> },
      { path: "menu", element: <MenuPagina /> },
      ...rotasDoPrevisto,
      ...rotasDoFinanceiro,
      ...rotasDoRebanho,
      ...rotasDasVendas,
      ...rotasDasCompras,
      ...rotasDosNascimentos,
      ...rotasDasMortes,
      ...rotasDasTransferencias,
      ...rotasDaQualidade,
      ...rotasDaExportacao,
      ...rotasDoAdmin,
    ],
  },
  { path: "*", element: <NaoEncontradaPagina /> },
]);
