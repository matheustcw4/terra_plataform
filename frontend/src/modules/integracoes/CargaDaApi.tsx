import type { AvisoDaCarga, CargaDaIntegracao, UnidadeDaCarga } from "../../core/api/tipos";
import { dataEHora, numero } from "../../logic/formatar";
import { classeDaSituacao, rotuloDaSituacao } from "../../logic/importacao";
import {
  classeDaCarga,
  duracaoDaCarga,
  origemDoPedido,
  resumoDosClientes,
  rotuloDaCarga,
  textoSemAvisos,
} from "../../logic/integracoes";

type Props = { carga: CargaDaIntegracao; aberta: boolean };

// Uma carga da API: a linha de resumo (quando, situação, quem pediu, os clientes) e, aberta, o resultado de cada
// cliente e os erros e avisos agrupados pelo código.
export function CargaDaApi({ carga, aberta }: Props) {
  return (
    <details className="carga-da-api" open={aberta}>
      <summary>
        <span className={classeDaCarga(carga.status)}>{rotuloDaCarga(carga.status)}</span>
        <strong>{dataEHora(carga.iniciado_em)}</strong>
        <span className="sugestao">
          {origemDoPedido(carga)} · {duracaoDaCarga(carga)}
        </span>
        <span className="carga-da-api-clientes">{resumoDosClientes(carga.unidades)}</span>
      </summary>
      <div className="carga-da-api-detalhe">
        {carga.unidades.length > 0 && <ClientesDaCarga unidades={carga.unidades} />}
        <AvisosDaCarga carga={carga} />
      </div>
    </details>
  );
}

// A coluna do motivo só aparece quando algum cliente não carregou.
function ClientesDaCarga({ unidades }: { unidades: UnidadeDaCarga[] }) {
  const comMotivo = unidades.some((unidade) => unidade.erro !== null);
  return (
    <div className="tabela-rolavel">
      <table className="tabela-admin">
        <thead>
          <tr>
            <th scope="col">Cliente</th>
            <th scope="col">Situação</th>
            <th scope="col" className="numero">Avisos</th>
            {comMotivo && <th scope="col">Motivo</th>}
          </tr>
        </thead>
        <tbody>
          {unidades.map((unidade) => (
            <tr key={unidade.nome}>
              <td>{unidade.nome}</td>
              <td>
                <span className={classeDaSituacao(unidade.status)}>{rotuloDaSituacao(unidade.status)}</span>
              </td>
              <td className="numero">{numero(unidade.avisos)}</td>
              {comMotivo && <td className="importacao-mensagem">{unidade.erro ?? ""}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Os avisos das fazendas (valor fora do padrão, conta a classificar) também ficam em Pendências, fazenda por fazenda.
function AvisosDaCarga({ carga }: { carga: CargaDaIntegracao }) {
  if (carga.avisos.length === 0) {
    return <p className="explicacao">{textoSemAvisos(carga)}</p>;
  }
  return (
    <ul className="avisos-da-carga">
      {carga.avisos.map((aviso: AvisoDaCarga) => (
        <li key={`${aviso.nivel}-${aviso.codigo}`}>
          <span className={aviso.nivel === "erro" ? "selo selo-erro" : "selo selo-aviso"}>
            {aviso.nivel === "erro" ? "Erro" : "Aviso"}
          </span>
          <span className="avisos-da-carga-texto">
            <strong>{aviso.problema}</strong> × {numero(aviso.quantidade)}{" "}
            <span className="sugestao">({aviso.codigo})</span>
            <span className="avisos-da-carga-exemplo">{aviso.exemplo}</span>
          </span>
        </li>
      ))}
    </ul>
  );
}
