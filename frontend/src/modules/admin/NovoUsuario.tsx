import { useState, type FormEvent } from "react";
import { Link, useLocation } from "react-router";
import { Aviso } from "../../core/ui/Aviso";
import { Painel } from "../../core/ui/Painel";
import { opcoesDeFuncao } from "../../logic/funcoes";
import { useCriarUsuario, useFuncoes } from "./api";

// Cadastro de um usuário novo: nome, e-mail, senha inicial (no mínimo 8 caracteres; a API guarda só o hash) e a
// função, escolhida no cadastro de funções. Depois de criado, ele abre para escolher as fazendas que vê.
export function NovoUsuario({ criado }: { criado: (usuarioId: string) => void }) {
  const [nome, trocarNome] = useState("");
  const [email, trocarEmail] = useState("");
  const [senha, trocarSenha] = useState("");
  const [funcaoId, trocarFuncaoId] = useState("");
  const [ehAdmin, trocarEhAdmin] = useState(false);
  const criar = useCriarUsuario();
  const funcoes = useFuncoes();
  const { search } = useLocation();
  const opcoes = opcoesDeFuncao(funcoes.data ?? []);

  function aoCriar(evento: FormEvent) {
    evento.preventDefault();
    criar.mutate({ nome, email, senha, funcao_id: Number(funcaoId), eh_admin: ehAdmin }, {
      onSuccess: (usuario) => {
        trocarNome("");
        trocarEmail("");
        trocarSenha("");
        trocarFuncaoId("");
        trocarEhAdmin(false);
        criado(usuario.id);
      },
    });
  }

  return (
    <Painel titulo="NOVO USUÁRIO">
      <form className="formulario-admin" onSubmit={aoCriar}>
        <label className="campo">
          <span>Nome</span>
          <input value={nome} onChange={(evento) => trocarNome(evento.target.value)} required />
        </label>
        <label className="campo">
          <span>E-mail</span>
          <input type="email" value={email} onChange={(evento) => trocarEmail(evento.target.value)} required />
        </label>
        <label className="campo">
          <span>Senha inicial (mínimo 8 caracteres)</span>
          <input type="password" value={senha} minLength={8} autoComplete="new-password"
            onChange={(evento) => trocarSenha(evento.target.value)} required />
        </label>
        <label className="campo">
          <span>Função</span>
          <select value={funcaoId} onChange={(evento) => trocarFuncaoId(evento.target.value)} required>
            <option value="">Escolha a função</option>
            {opcoes.map((funcao) => (
              <option key={funcao.id} value={funcao.id}>
                {funcao.nome}
              </option>
            ))}
          </select>
        </label>
        {funcoes.data !== undefined && opcoes.length === 0 && (
          <Aviso>
            Nenhuma função ativa: cadastre as funções em{" "}
            <Link to={{ pathname: "/admin/funcoes", search }}>Funções</Link> antes de criar o usuário.
          </Aviso>
        )}
        <label className="filtro-da-lista-marcar">
          <input type="checkbox" checked={ehAdmin} onChange={(evento) => trocarEhAdmin(evento.target.checked)} />
          Administrador (vê todas as fazendas e entra nesta área)
        </label>
        <button type="submit" className="botao" disabled={criar.isPending}>Criar usuário</button>
        {criar.isError && <Aviso tipo="erro">Não foi possível criar: {criar.error.message}</Aviso>}
      </form>
    </Painel>
  );
}
