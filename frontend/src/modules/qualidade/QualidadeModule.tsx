import type { RouteObject } from "react-router";
import { PendenciasPagina } from "./PendenciasPagina";

// Páginas de qualidade dos dados (entram dentro da área logada, em src/rotas.tsx).
export const rotasDaQualidade: RouteObject[] = [{ path: "pendencias", element: <PendenciasPagina /> }];
