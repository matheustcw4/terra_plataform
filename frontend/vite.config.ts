import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Em desenvolvimento o Vite repassa /api para a API local (porta 8010: a 8000 costuma estar ocupada por outros
    // projetos). O navegador vê um endereço só, sem CORS.
    proxy: { "/api": "http://127.0.0.1:8010" },
  },
  test: {
    environment: "jsdom",
  },
});
