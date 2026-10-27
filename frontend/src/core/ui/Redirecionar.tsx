import { Navigate, useLocation } from "react-router";

// Redireciona levando junto o filtro que está na URL (?cliente=...&fazendas=...).
export function Redirecionar({ para }: { para: string }) {
  const { search } = useLocation();
  return <Navigate to={{ pathname: para, search }} replace />;
}
