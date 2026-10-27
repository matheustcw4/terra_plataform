import { useState, type FormEvent } from "react";
import type { UsuarioDoAdmin } from "../../core/api/tipos";
import { Aviso } from "../../core/ui/Aviso";
import { Painel } from "../../core/ui/Painel";
import { opcoesDeFuncao } from "../../logic/funcoes";
import { AcessoAsFazendas } from "./AcessoAsFazendas";
import { useAlterarUsuario, useFuncoes } from "./api";

type Props = {
  usuario: UsuarioDoAdmin;
  souEu: boolean; // o admin não tira o próprio acesso de admin nem se desativa (a API também recusa)
};

// Um usuário aberto: nome, função, ativar/desativar, dar/tirar admin, trocar a senha e escolher as fazendas que ele
// vê. O nome se corrige aqui (ex.: o nome provisório tirado do e-mail na importação da equipe).
export function GerenciarUsuario({ usuario, souEu }: Props) {
  const alterar = useAlterarUsuario();
  const funcoes = useFuncoes();
  const [nome, trocarNome] = useState(usuario.nome);
  const [senha, trocarSenha] = useState("");
  const opcoes = opcoesDeFuncao(funcoes.data ?? [], usuario.funcao_id);

  function aoTrocarNome(evento: FormEvent) {
    evento.preventDefault();
    alterar.mutate({ id: usuario.id, alteracao: { nome } });
  }

  function aoTrocarFuncao(valor: string) {
    if (valor !== "") {
      alterar.mutate({ id: usuario.id, alteracao: { funcao_id: Number(valor) } });
    }
  }

  function aoTrocarSenha(evento: FormEvent) {
    evento.preventDefault();
    alterar.mutate({ id: usuario.id, alteracao: { senha } }, { onSuccess: () => trocarSenha("") });
  }

  return (
    <Painel titulo={usuario.nome.toUpperCase()}>
      <div className="gerenciar-usuario">
        <p className="explicacao">{usuario.email}</p>
        <form className="acoes-usuario" onSubmit={aoTrocarNome}>
          <input value={nome} required aria-label="Nome" onChange={(evento) => trocarNome(evento.target.value)} />
          <button type="submit" className="botao" disabled={alterar.isPending || nome.trim() === usuario.nome}>
            Gravar nome
          </button>
        </form>
        <label className="campo">
          <span>Função</span>
          <select value={usuario.funcao_id ?? ""} disabled={alterar.isPending}
            onChange={(evento) => aoTrocarFuncao(evento.target.value)}>
            {usuario.funcao_id === null && <option value="">Sem função: escolha uma</option>}
            {opcoes.map((funcao) => (
              <option key={funcao.id} value={funcao.id}>
                {funcao.ativo ? funcao.nome : `${funcao.nome} (inativa)`}
              </option>
            ))}
          </select>
        </label>
        {!souEu && (
          <div className="acoes-usuario">
            <button type="button" className="botao" disabled={alterar.isPending}
              onClick={() => alterar.mutate({ id: usuario.id, alteracao: { ativo: !usuario.ativo } })}>
              {usuario.ativo ? "Desativar" : "Reativar"}
            </button>
            <button type="button" className="botao" disabled={alterar.isPending}
              onClick={() => alterar.mutate({ id: usuario.id, alteracao: { eh_admin: !usuario.eh_admin } })}>
              {usuario.eh_admin ? "Tirar administrador" : "Tornar administrador"}
            </button>
          </div>
        )}
        <form className="acoes-usuario" onSubmit={aoTrocarSenha}>
          <input type="password" value={senha} minLength={8} autoComplete="new-password" required
            onChange={(evento) => trocarSenha(evento.target.value)} placeholder="nova senha (mínimo 8)"
            aria-label="Nova senha" />
          <button type="submit" className="botao" disabled={alterar.isPending}>Trocar senha</button>
        </form>
        {alterar.isError && <Aviso tipo="erro">Não foi possível gravar: {alterar.error.message}</Aviso>}
        {alterar.isSuccess && <Aviso>Gravado.</Aviso>}
        {usuario.eh_admin && <Aviso>Administrador vê todas as fazendas; a lista abaixo só vale se deixar de ser admin.</Aviso>}
        <h3>Fazendas que vê</h3>
        <AcessoAsFazendas usuarioId={usuario.id} />
      </div>
    </Painel>
  );
}
