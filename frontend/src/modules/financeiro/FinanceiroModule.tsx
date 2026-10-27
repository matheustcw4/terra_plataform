import type { RouteObject } from "react-router";
import { FinanceiroPagina } from "./FinanceiroPagina";

// Página do módulo Financeiro (entra dentro da área logada, em src/rotas.tsx).
export const rotasDoFinanceiro: RouteObject[] = [{ path: "financeiro", element: <FinanceiroPagina /> }];
