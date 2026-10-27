import type { RouteObject } from "react-router";
import { NascimentosPagina } from "./NascimentosPagina";

// Página do módulo Nascimentos (entra dentro da área logada, em src/rotas.tsx).
export const rotasDosNascimentos: RouteObject[] = [{ path: "nascimentos", element: <NascimentosPagina /> }];
