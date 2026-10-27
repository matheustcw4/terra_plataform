import { useState, type FormEvent } from "react";
import type { Funcao } from "../../core/api/tipos";
import { Aviso } from "../../core/ui/Aviso";
import { numero } from "../../logic/formatar";
import { useAlterarFuncao, useApagarFuncao } from "./api";

// Uma função na lista: renomear, ativar/desativar e apagar (só se nenhum usuário a tiver; a API também confere).
export function LinhaDaFuncao({ funcao }: { funcao: Funcao }) {
  const [editando, trocarEditando] = useState(false);
  const [nome, trocarNome] = useState(funcao.nome);
  const alterar = useAlterarFuncao();
  const apagar = useApagarFuncao();
  const ocupada = alterar.isPending || apagar.isPending;

  function aoRenomear(evento: FormEvent) {
    evento.preventDefault();
    alterar.mutate({ id: funcao.id, alteracao: { nome } }, { onSuccess: () => trocarEditando(false) });
  }

  let erro: string | null = null;
  if (alterar.isError) {
    erro = alterar.error.message;
  }
  if (apagar.isError) {
    erro = apagar.error.message;
  }

  return (
    <tr className={funcao.ativo ? undefined : "inativo"}>
      <td>
        {!editando && funcao.nome}
        {editando && (
          <form className="acoes-usuario" onSubmit={aoRenomear}>
            <input value={nome} maxLength={80} required aria-label="Novo nome da função"
              onChange={(evento) => trocarNome(evento.target.value)} />
            <button type="submit" className="botao-sair" disabled={ocupada}>Gravar</button>
            <button type="button" className="botao-sair" onClick={() => trocarEditando(false)}>Cancelar</button>
          </form>
        )}
        {erro !== null && <Aviso tipo="erro">{erro}</Aviso>}
      </td>
      <td className="numero">{numero(funcao.usuarios)}</td>
      <td>
        {funcao.ativo && "Ativa"}
        {!funcao.ativo && <span className="selo selo-erro">inativa</span>}
      </td>
      <td className="acoes-da-funcao">
        <button type="button" className="botao-sair" disabled={ocupada} onClick={() => trocarEditando(true)}>
          Renomear
        </button>
        <button type="button" className="botao-sair" disabled={ocupada}
          onClick={() => alterar.mutate({ id: funcao.id, alteracao: { ativo: !funcao.ativo } })}>
          {funcao.ativo ? "Desativar" : "Reativar"}
        </button>
        {funcao.usuarios === 0 && (
          <button type="button" className="botao-sair" disabled={ocupada} onClick={() => apagar.mutate(funcao.id)}>
            Apagar
          </button>
        )}
      </td>
    </tr>
  );
}
