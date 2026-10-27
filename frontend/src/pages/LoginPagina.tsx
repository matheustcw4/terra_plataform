import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import logo from "../assets/bi/terra-logo.png";
import { chamarApi } from "../core/api/cliente";
import type { RespostaLogin } from "../core/api/tipos";
import { apagarToken, guardarToken } from "../core/auth/token";
import { Aviso } from "../core/ui/Aviso";

export function LoginPagina() {
  const navegar = useNavigate();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");

  const login = useMutation({
    mutationFn: () =>
      chamarApi<RespostaLogin>("/auth/login", { method: "POST", body: JSON.stringify({ email, senha }) }),
    onSuccess: (resposta) => {
      guardarToken(resposta.token);
      navegar("/menu");
    },
  });

  function entrar(evento: FormEvent) {
    evento.preventDefault();
    apagarToken(); // um token antigo não vai junto no pedido de login
    login.mutate();
  }

  return (
    <main className="login">
      <form className="login-caixa" onSubmit={entrar}>
        <img src={logo} alt="Terra Desenvolvimento Agropecuário" />
        <h1>Boletim mensal</h1>
        <label className="campo">
          <span>E-mail</span>
          <input type="email" autoComplete="username" required value={email}
            onChange={(evento) => setEmail(evento.target.value)} />
        </label>
        <label className="campo">
          <span>Senha</span>
          <input type="password" autoComplete="current-password" required value={senha}
            onChange={(evento) => setSenha(evento.target.value)} />
        </label>
        {login.isError && <Aviso tipo="erro">{login.error.message}</Aviso>}
        <button type="submit" className="botao" disabled={login.isPending}>
          {login.isPending ? "Entrando…" : "Entrar"}
        </button>
      </form>
    </main>
  );
}
