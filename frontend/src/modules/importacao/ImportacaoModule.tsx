import type { RouteObject } from "react-router";
import { ImportacaoPagina } from "./ImportacaoPagina";

// A importação de planilhas (entra dentro da área logada, em src/rotas.tsx); todo usuário logado entra.
export const rotasDaImportacao: RouteObject[] = [{ path: "importacao", element: <ImportacaoPagina /> }];
