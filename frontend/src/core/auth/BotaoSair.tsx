import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { Icone } from "../ui/Icone";
import { apagarToken } from "./token";

export function BotaoSair() {
  const navegar = useNavigate();
  const queryClient = useQueryClient();

  function sair() {
    apagarToken();
    queryClient.clear(); // não deixa na memória dados que eram do usuário que saiu
    navegar("/login");
  }

  return (
    <button type="button" className="botao-sair" aria-label="Sair" onClick={sair}>
      <Icone nome="sair" tamanho={15} />
      <span className="rotulo-do-botao">Sair</span>
    </button>
  );
}
