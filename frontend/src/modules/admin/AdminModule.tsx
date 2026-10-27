import type { RouteObject } from "react-router";
import { Redirecionar } from "../../core/ui/Redirecionar";
import { CategoriasPagina } from "./CategoriasPagina";
import { ContasPagina } from "./ContasPagina";
import { FuncoesPagina } from "./FuncoesPagina";
import { UsuariosPagina } from "./UsuariosPagina";

// Telas de administração (entram dentro da área logada, em src/rotas.tsx); /admin abre os de-paras de categoria.
export const rotasDoAdmin: RouteObject[] = [
  { path: "admin", element: <Redirecionar para="/admin/categorias" /> },
  { path: "admin/categorias", element: <CategoriasPagina /> },
  { path: "admin/contas", element: <ContasPagina /> },
  { path: "admin/usuarios", element: <UsuariosPagina /> },
  { path: "admin/funcoes", element: <FuncoesPagina /> },
];
