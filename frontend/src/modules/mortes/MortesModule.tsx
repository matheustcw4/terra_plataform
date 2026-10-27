import type { RouteObject } from "react-router";
import { MortesPagina } from "./MortesPagina";

// Página do módulo Mortes (entra dentro da área logada, em src/rotas.tsx).
export const rotasDasMortes: RouteObject[] = [{ path: "mortes", element: <MortesPagina /> }];
