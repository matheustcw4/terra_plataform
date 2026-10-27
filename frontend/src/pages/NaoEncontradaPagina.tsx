import { Link } from "react-router";

export function NaoEncontradaPagina() {
  return (
    <main className="login">
      <div className="login-caixa">
        <h1>Página não encontrada</h1>
        <Link to="/">Voltar ao início</Link>
      </div>
    </main>
  );
}
