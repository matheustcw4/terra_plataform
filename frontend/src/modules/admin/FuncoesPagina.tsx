import { useState, type FormEvent } from "react";
import { Aviso } from "../../core/ui/Aviso";
import { Painel } from "../../core/ui/Painel";
import { useCriarFuncao, useFuncoes } from "./api";
import { LinhaDaFuncao } from "./LinhaDaFuncao";
import { MolduraDoAdmin } from "./MolduraDoAdmin";

// Cadastro de funções: a lista de onde sai a função de cada usuário (o cadastro de usuário escolhe uma, não digita).
// Função que algum usuário tem não se apaga: desative-a, e ela some da lista dos cadastros novos.
export function FuncoesPagina() {
  const funcoes = useFuncoes();
  return (
    <MolduraDoAdmin titulo="FUNÇÕES">
      <p className="explicacao">
        As funções que aparecem no cadastro de usuário. Desativar tira a função da lista dos cadastros novos; quem já a
        tem continua com ela. Só dá para apagar a função que nenhum usuário tem.
      </p>
      <div className="usuarios-corpo">
        <section className="painel-grafico tabela-rolavel">
          <h2>FUNÇÕES</h2>
          {funcoes.isPending && <Aviso>Carregando…</Aviso>}
          {funcoes.isError && <Aviso tipo="erro">Não foi possível carregar as funções: {funcoes.error.message}</Aviso>}
          {funcoes.data && (
            <table className="tabela-admin tabela-compacta">
              <thead>
                <tr>
                  <th scope="col">Nome</th>
                  <th scope="col">Usuários</th>
                  <th scope="col">Situação</th>
                  <th scope="col" />
                </tr>
              </thead>
              <tbody>
                {funcoes.data.map((funcao) => <LinhaDaFuncao key={funcao.id} funcao={funcao} />)}
              </tbody>
            </table>
          )}
          {funcoes.data?.length === 0 && <p className="explicacao">Nenhuma função cadastrada ainda.</p>}
        </section>
        <NovaFuncao />
      </div>
    </MolduraDoAdmin>
  );
}

function NovaFuncao() {
  const [nome, trocarNome] = useState("");
  const criar = useCriarFuncao();

  function aoCriar(evento: FormEvent) {
    evento.preventDefault();
    criar.mutate(nome, { onSuccess: () => trocarNome("") });
  }

  return (
    <Painel titulo="NOVA FUNÇÃO">
      <form className="formulario-admin" onSubmit={aoCriar}>
        <label className="campo">
          <span>Nome</span>
          <input value={nome} maxLength={80} onChange={(evento) => trocarNome(evento.target.value)} required
            placeholder="ex.: Consultor" />
        </label>
        <button type="submit" className="botao" disabled={criar.isPending}>Cadastrar função</button>
        {criar.isError && <Aviso tipo="erro">Não foi possível cadastrar: {criar.error.message}</Aviso>}
      </form>
    </Painel>
  );
}
