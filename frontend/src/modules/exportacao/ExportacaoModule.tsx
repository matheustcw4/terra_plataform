import type { RouteObject } from "react-router";
import { ExportacaoPagina } from "./ExportacaoPagina";

// A página que gera o PDF (entra dentro da área logada, em src/rotas.tsx). Ela só é aberta pelo "Exportar PDF".
export const rotasDaExportacao: RouteObject[] = [{ path: "exportar", element: <ExportacaoPagina /> }];
