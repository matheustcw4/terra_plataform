import { Link, useLocation } from "react-router";
import type { Importacao } from "../../core/api/tipos";
import { dataEHora } from "../../logic/formatar";
import { classeDaSituacao, resumoDaCarga, rotuloDaSituacao, tamanhoLegivel } from "../../logic/importacao";

// As planilhas enviadas (as de quem está logado e as das fazendas que ele acompanha), da mais recente para a mais
// antiga, com o que a carga fez de cada uma.
export function ListaDeImportacoes({ lista }: { lista: Importacao[] }) {
  if (lista.length === 0) {
    return <p className="explicacao">Nenhuma planilha enviada ainda.</p>;
  }
  return (
    <table className="tabela-admin tabela-importacoes">
      <thead>
        <tr>
          <th scope="col">Arquivo</th>
          <th scope="col">Fazenda</th>
          <th scope="col">Enviado por</th>
          <th scope="col">Enviado em</th>
          <th scope="col">Situação</th>
          <th scope="col">Resultado</th>
        </tr>
      </thead>
      <tbody>
        {lista.map((importacao) => (
          <LinhaDaImportacao key={importacao.id} importacao={importacao} />
        ))}
      </tbody>
    </table>
  );
}

function LinhaDaImportacao({ importacao }: { importacao: Importacao }) {
  let fazendas = "—";
  if (importacao.fazendas.length > 0) {
    fazendas = importacao.fazendas.join(", ");
  }
  let enviadoPor = importacao.enviado_por;
  if (importacao.minha) {
    enviadoPor = "Você";
  }
  return (
    <tr>
      <td>
        <span className="importacao-arquivo">{importacao.arquivo}</span>
        <span className="sugestao">{tamanhoLegivel(importacao.tamanho_bytes)}</span>
      </td>
      <td>{fazendas}</td>
      <td>{enviadoPor}</td>
      <td>{dataEHora(importacao.enviado_em)}</td>
      <td>
        <span className={classeDaSituacao(importacao.status)}>{rotuloDaSituacao(importacao.status)}</span>
      </td>
      <td>
        <Resultado importacao={importacao} />
      </td>
    </tr>
  );
}

// O motivo, quando não carregou; o que conferir, quando carregou com avisos (o detalhe está em Pendências).
function Resultado({ importacao }: { importacao: Importacao }) {
  const { search } = useLocation();
  if (importacao.mensagem) {
    return <span className="importacao-mensagem">{importacao.mensagem}</span>;
  }
  const resumo = resumoDaCarga(importacao);
  if (resumo === "") {
    return <span className="sugestao">—</span>;
  }
  return (
    <span>
      {resumo} · <Link to={{ pathname: "/pendencias", search }}>ver em Pendências</Link>
    </span>
  );
}
