import { useState } from "react";
import type { CategoriaDeOrigem, OpcaoDeCategoria } from "../../core/api/tipos";
import { Aviso } from "../../core/ui/Aviso";
import { dataEHora, numero } from "../../logic/formatar";
import { useCategorias, useClassificarCategoria } from "./api";
import { FiltroDaLista } from "./FiltroDaLista";
import { ROTULO_DA_FONTE } from "./fontes";
import { MolduraDoAdmin } from "./MolduraDoAdmin";

// De-para de categorias: cada categoria como a fonte escreve vira uma das 15 categorias BI. Pendente fica fora do
// estoque e do rebanho médio; ao classificar, o estoque das fazendas que a usam é recalculado na hora.
export function CategoriasPagina() {
  const [soPendentes, trocarSoPendentes] = useState(true);
  const [busca, trocarBusca] = useState("");
  const lista = useCategorias(soPendentes, busca);
  const classificar = useClassificarCategoria();
  let gravando: string | undefined;
  if (classificar.isPending) {
    gravando = classificar.variables.id;
  }
  return (
    <MolduraDoAdmin titulo="CATEGORIAS">
      <p className="explicacao">
        A categoria da planilha ou do Metryx que ainda não tem categoria BI fica fora do estoque e do rebanho médio.
        Escolha a categoria BI: o histórico é reclassificado e o estoque das fazendas que a usam é recalculado.
      </p>
      <FiltroDaLista soPendentes={soPendentes} trocarSoPendentes={trocarSoPendentes} buscar={trocarBusca}
        dica="categoria, fazenda ou cliente" />
      {lista.isPending && <Aviso>Carregando…</Aviso>}
      {lista.isError && <Aviso tipo="erro">Não foi possível carregar a lista: {lista.error.message}</Aviso>}
      {classificar.isError && <Aviso tipo="erro">Não foi possível gravar: {classificar.error.message}</Aviso>}
      {lista.data && (
        <section className="painel-grafico tabela-rolavel">
          <h2>{numero(lista.data.pendentes)} pendente(s) no total</h2>
          <table className="tabela-admin">
            <thead>
              <tr>
                <th scope="col">Cliente</th>
                <th scope="col">Fazenda</th>
                <th scope="col">Categoria na fonte</th>
                <th scope="col">Fonte</th>
                <th scope="col">Usos</th>
                <th scope="col">Categoria BI</th>
                <th scope="col">Classificada por</th>
              </tr>
            </thead>
            <tbody>
              {lista.data.itens.map((item) => (
                <LinhaDaCategoria key={item.id} item={item} opcoes={lista.data.opcoes} gravando={gravando === item.id}
                  classificar={(categoria) => classificar.mutate({ id: item.id, categoria })} />
              ))}
            </tbody>
          </table>
          {lista.data.itens.length === 0 && <p className="explicacao">Nada a mostrar com este filtro.</p>}
        </section>
      )}
    </MolduraDoAdmin>
  );
}

type LinhaProps = {
  item: CategoriaDeOrigem;
  opcoes: OpcaoDeCategoria[];
  gravando: boolean;
  classificar: (categoria: number | null) => void;
};

function LinhaDaCategoria({ item, opcoes, gravando, classificar }: LinhaProps) {
  const sugerida = opcoes.find((opcao) => opcao.id === item.categoria_bi_sugerida_id);
  return (
    <tr className={item.categoria_bi_id === null ? "pendente" : undefined}>
      <td>{item.cliente ?? "—"}</td>
      <td>{item.fazenda ?? "todas do cliente"}</td>
      <td>{item.nome_origem}</td>
      <td>{ROTULO_DA_FONTE[item.fonte] ?? item.fonte}</td>
      <td className="numero">{numero(item.lancamentos)}</td>
      <td>
        <select value={item.categoria_bi_id ?? ""} disabled={gravando} aria-label={`Categoria BI de ${item.nome_origem}`}
          onChange={(evento) => classificar(evento.target.value === "" ? null : Number(evento.target.value))}>
          <option value="">— pendente —</option>
          {opcoes.map((opcao) => (
            <option key={opcao.id} value={opcao.id}>
              {opcao.nome} ({opcao.sexo.toLowerCase()}, {opcao.grupo.toLowerCase()})
            </option>
          ))}
        </select>
        {sugerida !== undefined && item.categoria_bi_id === null && (
          <span className="sugestao">sugestão da fonte: {sugerida.nome}</span>
        )}
      </td>
      <td className="apagado">
        {item.confirmado_por ?? "—"}
        {item.confirmado_em !== null && <span className="sugestao">{dataEHora(item.confirmado_em)}</span>}
      </td>
    </tr>
  );
}
