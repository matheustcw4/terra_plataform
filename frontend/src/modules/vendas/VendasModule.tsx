import type { RouteObject } from "react-router";
import { Redirecionar } from "../../core/ui/Redirecionar";
import { VendasPagina } from "./VendasPagina";

// Páginas do módulo Vendas (entram dentro da área logada, em src/rotas.tsx). Uma rota por tipo de venda, como as
// páginas "Venda Abate" e "Venda em Pé" do BI; /vendas abre o abate.
export const rotasDasVendas: RouteObject[] = [
  { path: "vendas", element: <Redirecionar para="/vendas/abate" /> },
  { path: "vendas/abate", element: <VendasPagina tipo="abate" /> },
  { path: "vendas/em_pe", element: <VendasPagina tipo="em_pe" /> },
];
