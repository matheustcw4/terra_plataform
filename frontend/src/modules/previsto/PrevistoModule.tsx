import type { RouteObject } from "react-router";
import { PrevistoPagina } from "./PrevistoPagina";

// Página do módulo Previsto × Realizado (entra dentro da área logada, em src/rotas.tsx).
export const rotasDoPrevisto: RouteObject[] = [{ path: "previsto_realizado", element: <PrevistoPagina /> }];
