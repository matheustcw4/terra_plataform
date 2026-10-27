import type { RouteObject } from "react-router";
import { TransferenciasPagina } from "./TransferenciasPagina";

// Página do módulo Transferências (entra dentro da área logada, em src/rotas.tsx).
export const rotasDasTransferencias: RouteObject[] = [{ path: "transferencias", element: <TransferenciasPagina /> }];
