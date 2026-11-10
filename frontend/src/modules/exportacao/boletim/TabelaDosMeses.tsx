import { mesDaTabela } from "../../../logic/boletim";

export type LinhaDosMeses = {
  nome: string;
  valores: string[]; // já escritos, um por mês
  apagado?: boolean; // o planejado, em cinza
};

type Props = {
  titulo: string; // a primeira célula do cabeçalho ("Acumulado", "Cab · mês")
  meses: string[]; // "AAAA-MM-DD"
  linhas: LinhaDosMeses[];
  marrom?: boolean; // o cabeçalho marrom das tabelas de cabeças por mês da comercialização
};

// A tabela de meses embaixo dos gráficos do boletim (Realizado e Planejado), com o mês no cabeçalho.
export function TabelaDosMeses({ titulo, meses, linhas, marrom = false }: Props) {
  let classes = "boletim-tb";
  if (marrom) {
    classes += " miuda cabecalho-marrom";
  }
  return (
    <table className={classes}>
      <thead>
        <tr>
          <th scope="col" className="esquerda">{titulo}</th>
          {meses.map((mes) => (
            <th key={mes} scope="col">{mesDaTabela(mes)}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {linhas.map((linha) => (
          <tr key={linha.nome}>
            <td className="nome">{linha.nome}</td>
            {linha.valores.map((valor, posicao) => (
              <td key={meses[posicao]} className={linha.apagado ? "apagado" : undefined}>{valor}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
