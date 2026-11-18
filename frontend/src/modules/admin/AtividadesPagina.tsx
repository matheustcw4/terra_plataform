import { useState } from "react";
import type { AtividadeDeOrigem, AtividadesDeOrigem, OpcaoDeTipoDeAtividade } from "../../core/api/tipos";
import { Aviso } from "../../core/ui/Aviso";
import { dinheiro, numero } from "../../logic/formatar";
import { useAtividades, useClassificarAtividade } from "./api";
import { FiltroDaLista } from "./FiltroDaLista";
import { ROTULO_DA_FONTE } from "./fontes";
import { MolduraDoAdmin } from "./MolduraDoAdmin";

// De-para de atividades (pedido do usuário, 18/11/2026): cada atividade como a fonte escreve ("Pecuária Campo",
// "Agricultura Permanente"; no plano do Metryx, o tipo "Pecuária") entra num tipo de atividade, que é o filtro do
// financeiro. Sem tipo, a atividade aparece como "A classificar" no filtro; classificar muda o filtro na hora.
export function AtividadesPagina() {
  const [soPendentes, trocarSoPendentes] = useState(true);
  const [busca, trocarBusca] = useState("");
  const lista = useAtividades(soPendentes, busca);
  const classificar = useClassificarAtividade();
  let gravando: number | undefined;
  if (classificar.isPending) {
    gravando = classificar.variables.id;
  }
  return (
    <MolduraDoAdmin titulo="ATIVIDADES">
      <p className="explicacao">
        O filtro de tipo de atividade do financeiro junta as atividades da fonte pelo tipo. A atividade sem tipo entra
        nos totais e aparece como "A classificar" no filtro. Escolha o tipo: o filtro de todas as fazendas que usam a
        atividade muda, inclusive o histórico.
      </p>
      <FiltroDaLista soPendentes={soPendentes} trocarSoPendentes={trocarSoPendentes} buscar={trocarBusca}
        dica="nome da atividade" />
      {lista.isPending && <Aviso>Carregando…</Aviso>}
      {lista.isError && <Aviso tipo="erro">Não foi possível carregar a lista: {lista.error.message}</Aviso>}
      {classificar.isError && <Aviso tipo="erro">Não foi possível gravar: {classificar.error.message}</Aviso>}
      {lista.data && (
        <TabelaDeAtividades dados={lista.data} gravando={gravando}
          classificar={(id, tipo) => classificar.mutate({ id, tipo })} />
      )}
    </MolduraDoAdmin>
  );
}

type TabelaProps = {
  dados: AtividadesDeOrigem;
  gravando: number | undefined; // a atividade que está sendo gravada
  classificar: (id: number, tipo: number | null) => void;
};

function TabelaDeAtividades({ dados, gravando, classificar }: TabelaProps) {
  return (
    <section className="painel-grafico tabela-rolavel">
      <h2>{numero(dados.pendentes)} atividade(s) sem tipo no total</h2>
      <table className="tabela-admin">
        <thead>
          <tr>
            <th scope="col">Atividade na fonte</th>
            <th scope="col">Fonte</th>
            <th scope="col">Lançamentos</th>
            <th scope="col">Valor realizado</th>
            <th scope="col">Tipo de atividade</th>
          </tr>
        </thead>
        <tbody>
          {dados.itens.map((item) => (
            <LinhaDaAtividade key={item.id} item={item} opcoes={dados.opcoes} gravando={gravando === item.id}
              classificar={(tipo) => classificar(item.id, tipo)} />
          ))}
        </tbody>
      </table>
      {dados.itens.length === 0 && <p className="explicacao">Nada a mostrar com este filtro.</p>}
    </section>
  );
}

type LinhaProps = {
  item: AtividadeDeOrigem;
  opcoes: OpcaoDeTipoDeAtividade[];
  gravando: boolean;
  classificar: (tipo: number | null) => void;
};

function LinhaDaAtividade({ item, opcoes, gravando, classificar }: LinhaProps) {
  return (
    <tr className={item.tipo_atividade_id === null ? "pendente" : undefined}>
      <td>{item.nome}</td>
      <td>{ROTULO_DA_FONTE[item.fonte] ?? item.fonte}</td>
      <td className="numero">
        {numero(item.lancamentos)}
        {item.orcamentos > 0 && <span className="sugestao">{numero(item.orcamentos)} de orçamento</span>}
      </td>
      <td className="numero">{dinheiro(item.valor)}</td>
      <td>
        <select value={item.tipo_atividade_id ?? ""} disabled={gravando} aria-label={`Tipo de ${item.nome}`}
          onChange={(evento) => classificar(evento.target.value === "" ? null : Number(evento.target.value))}>
          <option value="">— A classificar —</option>
          {opcoes.map((opcao) => (
            <option key={opcao.id} value={opcao.id}>{opcao.nome}</option>
          ))}
        </select>
      </td>
    </tr>
  );
}
