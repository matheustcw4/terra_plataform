import { useState } from "react";
import type { ContaDeOrigem, ContasDeOrigem, OpcaoDeConta } from "../../core/api/tipos";
import { Aviso } from "../../core/ui/Aviso";
import { agruparPor, type Grupo } from "../../logic/agrupar";
import { dataEHora, dinheiro, numero } from "../../logic/formatar";
import { useClassificarConta, useContas } from "./api";
import { FiltroDaLista } from "./FiltroDaLista";
import { ROTULO_DA_FONTE } from "./fontes";
import { MolduraDoAdmin } from "./MolduraDoAdmin";

// De-para de contas: cada conta (centro e subcentro) como a fonte escreve vira um centro de custo do plano
// unificado. Sem centro, a conta aparece como "A classificar" no DRE (decisão Q1); classificar muda o DRE na hora.
export function ContasPagina() {
  const [soPendentes, trocarSoPendentes] = useState(true);
  const [busca, trocarBusca] = useState("");
  const lista = useContas(soPendentes, busca);
  const classificar = useClassificarConta();
  let gravando: string | undefined;
  if (classificar.isPending) {
    gravando = classificar.variables.id;
  }
  return (
    <MolduraDoAdmin titulo="CONTAS">
      <p className="explicacao">
        A conta fora do plano unificado entra nos totais como "A classificar". Escolha o centro de custo: o DRE de todas
        as fazendas que usam a conta é reclassificado, inclusive o histórico.
      </p>
      <FiltroDaLista soPendentes={soPendentes} trocarSoPendentes={trocarSoPendentes} buscar={trocarBusca}
        dica="centro ou subcentro" />
      {lista.isPending && <Aviso>Carregando…</Aviso>}
      {lista.isError && <Aviso tipo="erro">Não foi possível carregar a lista: {lista.error.message}</Aviso>}
      {classificar.isError && <Aviso tipo="erro">Não foi possível gravar: {classificar.error.message}</Aviso>}
      {lista.data && (
        <TabelaDeContas dados={lista.data} gravando={gravando}
          classificar={(id, centro) => classificar.mutate({ id, centro })} />
      )}
    </MolduraDoAdmin>
  );
}

type TabelaProps = {
  dados: ContasDeOrigem;
  gravando: string | undefined; // a conta que está sendo gravada
  classificar: (id: string, centro: number | null) => void;
};

function TabelaDeContas({ dados, gravando, classificar }: TabelaProps) {
  const grupos = agruparPor(dados.opcoes, (opcao) => opcao.classificacao);
  return (
    <section className="painel-grafico tabela-rolavel">
      <h2>{numero(dados.pendentes)} conta(s) a classificar no total</h2>
      <table className="tabela-admin">
        <thead>
          <tr>
            <th scope="col">Conta na fonte (centro / subcentro)</th>
            <th scope="col">Fonte</th>
            <th scope="col">Fazendas</th>
            <th scope="col">Lançamentos</th>
            <th scope="col">Valor realizado</th>
            <th scope="col">Centro de custo</th>
            <th scope="col">Classificada por</th>
          </tr>
        </thead>
        <tbody>
          {dados.itens.map((item) => (
            <LinhaDaConta key={item.id} item={item} grupos={grupos} gravando={gravando === item.id}
              classificar={(centro) => classificar(item.id, centro)} />
          ))}
        </tbody>
      </table>
      {dados.itens.length === 0 && <p className="explicacao">Nada a mostrar com este filtro.</p>}
    </section>
  );
}

type LinhaProps = {
  item: ContaDeOrigem;
  grupos: Grupo<OpcaoDeConta>[]; // os centros de custo, separados por classificação do DRE
  gravando: boolean;
  classificar: (centro: number | null) => void;
};

function LinhaDaConta({ item, grupos, gravando, classificar }: LinhaProps) {
  return (
    <tr className={item.centro_custo_id === null ? "pendente" : undefined}>
      <td>
        {item.centro}
        {item.subcentro !== null && <span className="sugestao">{item.subcentro}</span>}
      </td>
      <td>{ROTULO_DA_FONTE[item.fonte] ?? item.fonte}</td>
      <td className="numero">{numero(item.fazendas)}</td>
      <td className="numero">
        {numero(item.lancamentos)}
        {item.orcamentos > 0 && <span className="sugestao">{numero(item.orcamentos)} de orçamento</span>}
      </td>
      <td className="numero">{dinheiro(item.valor)}</td>
      <td>
        <select value={item.centro_custo_id ?? ""} disabled={gravando} aria-label={`Centro de custo de ${item.centro}`}
          onChange={(evento) => classificar(evento.target.value === "" ? null : Number(evento.target.value))}>
          <option value="">— A classificar —</option>
          {grupos.map((grupo) => (
            <optgroup key={grupo.chave} label={grupo.chave}>
              {grupo.itens.map((opcao) => (
                <option key={opcao.id} value={opcao.id}>{opcao.nome}</option>
              ))}
            </optgroup>
          ))}
        </select>
      </td>
      <td className="apagado">
        {item.confirmado_por ?? "—"}
        {item.confirmado_em !== null && <span className="sugestao">{dataEHora(item.confirmado_em)}</span>}
      </td>
    </tr>
  );
}
