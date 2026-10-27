import type { ReactNode } from "react";

type Props = {
  tipo?: "info" | "erro";
  children: ReactNode;
};

// Mensagem no lugar do conteúdo: carregando, erro ou "nada para mostrar".
export function Aviso({ tipo = "info", children }: Props) {
  return (
    <p className={`aviso aviso-${tipo}`} role={tipo === "erro" ? "alert" : "status"}>
      {children}
    </p>
  );
}
