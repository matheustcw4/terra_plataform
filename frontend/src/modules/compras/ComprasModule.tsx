import type { RouteObject } from "react-router";
import { ComprasPagina } from "./ComprasPagina";

// Página do módulo Compras (entra dentro da área logada, em src/rotas.tsx).
export const rotasDasCompras: RouteObject[] = [{ path: "compras", element: <ComprasPagina /> }];
