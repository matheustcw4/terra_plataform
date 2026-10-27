import type { Pendencia } from "../../../core/api/tipos";
import { dataEHora } from "../../../logic/formatar";
import type { GrupoDePendencias } from "../agrupar";

// As pendências de um arquivo: onde está cada linha, o que está escrito nela e como corrigir.
export function GrupoDaOrigem({ grupo }: { grupo: GrupoDePendencias }) {
  return (
    <section className="painel">
      <h2>
        {grupo.fazenda} <span className="apagado">· {grupo.origem}</span>
      </h2>
      {grupo.salvoEm && <p className="apagado legenda">Arquivo salvo em {dataEHora(grupo.salvoEm)}</p>}
      <div className="rolagem">
        <table className="tabela pendencias">
          <thead>
            <tr>
              <th scope="col">Situação</th>
              <th scope="col">Onde</th>
              <th scope="col">Problema</th>
              <th scope="col">O que está na linha</th>
            </tr>
          </thead>
          <tbody>
            {grupo.itens.map((item, posicao) => (
              <LinhaDePendencia key={`${item.codigo}-${item.local}-${posicao}`} item={item} />
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function LinhaDePendencia({ item }: { item: Pendencia }) {
  const naoEntrou = item.situacao === "nao_entrou";
  return (
    <tr>
      <td>
        <span className={naoEntrou ? "selo selo-erro" : "selo selo-aviso"}>
          {naoEntrou ? "Não entrou" : "Confira"}
        </span>
        {item.quem_corrige === "equipe" && <span className="selo">Equipe Terra</span>}
      </td>
      <td>{item.local ?? "—"}</td>
      <td className="quebra">
        <strong>{item.problema}</strong>
        <div>{item.detalhe}</div>
        <div className="apagado">{item.como_corrigir}</div>
      </td>
      <td className="quebra apagado">{item.valores.join(" · ")}</td>
    </tr>
  );
}
