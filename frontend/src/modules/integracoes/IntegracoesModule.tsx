import type { RouteObject } from "react-router";
import { Redirecionar } from "../../core/ui/Redirecionar";
import { IntegracoesPagina } from "./IntegracoesPagina";

// As integrações (entram dentro da área logada, em src/rotas.tsx): todo usuário logado entra na aba das planilhas; as
// abas das APIs são do admin. O endereço antigo da importação leva para a aba das planilhas.
export const rotasDasIntegracoes: RouteObject[] = [
  { path: "integracoes", element: <IntegracoesPagina /> },
  { path: "integracoes/:fonte", element: <IntegracoesPagina /> },
  { path: "importacao", element: <Redirecionar para="/integracoes" /> },
];
