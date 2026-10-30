import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: {
    port: 5173,
    // Em desenvolvimento o Vite repassa /api para a API local (porta 8010: a 8000 costuma estar ocupada por outros
    // projetos; com a 8010 ocupada também, TERRA_API_PORTA aponta para outra). O navegador vê um endereço só, sem CORS.
    proxy: { "/api": `http://127.0.0.1:${loadEnv(mode, ".", "TERRA_").TERRA_API_PORTA ?? "8010"}` },
  },
  test: {
    environment: "jsdom",
  },
}));
