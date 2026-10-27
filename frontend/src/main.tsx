import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router";
import { rotas } from "./rotas";
import "@fontsource-variable/figtree";
import "./estilos.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // os números só mudam quando uma carga roda; 5 min sem pedir de novo é seguro
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const raiz = document.getElementById("raiz");
if (raiz === null) {
  throw new Error("index.html sem o elemento #raiz");
}

createRoot(raiz).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={rotas} />
    </QueryClientProvider>
  </StrictMode>,
);
