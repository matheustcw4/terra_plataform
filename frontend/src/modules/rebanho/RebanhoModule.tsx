import type { RouteObject } from "react-router";
import { MovimentacaoPagina } from "./MovimentacaoPagina";

// Páginas do módulo Rebanho (entram dentro da área logada, em src/rotas.tsx).
export const rotasDoRebanho: RouteObject[] = [{ path: "rebanho/movimentacao", element: <MovimentacaoPagina /> }];
