import { useState } from "react";
import { useArea } from "../../core/auth/AreaAutenticada";
import { Aviso } from "../../core/ui/Aviso";
import { numero } from "../../logic/formatar";
import { useUsuarios } from "./api";
import { GerenciarUsuario } from "./GerenciarUsuario";
import { MolduraDoAdmin } from "./MolduraDoAdmin";
import { NovoUsuario } from "./NovoUsuario";

// Usuários e acesso: a lista de usuários, o cadastro de um novo (nome, e-mail, senha e função) e, ao abrir um
// usuário, a função, o que ele pode fazer e quais fazendas vê (core.usuario_fazenda: um usuário vê várias fazendas;
// uma fazenda é vista por vários usuários).
export function UsuariosPagina() {
  const { escopo } = useArea();
  const usuarios = useUsuarios();
  const [abertoId, trocarAbertoId] = useState<string | null>(null);
  const aberto = usuarios.data?.find((usuario) => usuario.id === abertoId);
  return (
    <MolduraDoAdmin titulo="USUÁRIOS">
      {usuarios.isPending && <Aviso>Carregando…</Aviso>}
      {usuarios.isError && <Aviso tipo="erro">Não foi possível carregar os usuários: {usuarios.error.message}</Aviso>}
      {usuarios.data && (
        <div className="usuarios-corpo">
          <div className="coluna-graficos">
            <section className="painel-grafico tabela-rolavel">
              <h2>USUÁRIOS</h2>
              <table className="tabela-admin tabela-compacta">
                <thead>
                  <tr>
                    <th scope="col">Nome</th>
                    <th scope="col">E-mail</th>
                    <th scope="col">Função</th>
                    <th scope="col">Perfil</th>
                    <th scope="col">Fazendas</th>
                    <th scope="col" />
                  </tr>
                </thead>
                <tbody>
                  {usuarios.data.map((usuario) => (
                    <tr key={usuario.id} className={usuario.ativo ? undefined : "inativo"}>
                      <td>{usuario.nome}</td>
                      <td className="email">{usuario.email}</td>
                      <td>{usuario.funcao ?? "—"}</td>
                      <td>
                        {usuario.eh_admin ? "Administrador" : "Usuário"}
                        {!usuario.ativo && <span className="selo selo-erro">inativo</span>}
                      </td>
                      <td className="numero">{usuario.eh_admin ? "todas" : numero(usuario.fazendas)}</td>
                      <td>
                        <button type="button" className="botao-sair" onClick={() => trocarAbertoId(usuario.id)}>
                          Abrir
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
            <NovoUsuario criado={trocarAbertoId} />
          </div>
          {aberto !== undefined && (
            <GerenciarUsuario key={aberto.id} usuario={aberto} souEu={aberto.id === escopo.usuario.id} />
          )}
          {aberto === undefined && (
            <Aviso>Abra um usuário para mudar a função, o perfil, a senha e as fazendas que ele vê.</Aviso>
          )}
        </div>
      )}
    </MolduraDoAdmin>
  );
}
