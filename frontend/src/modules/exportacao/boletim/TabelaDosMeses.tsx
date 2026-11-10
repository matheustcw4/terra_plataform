import { mesDoEixo } from "../../../logic/boletim";

export type LinhaDosMeses = {
  nome: string;
  valores: string[]; // já escritos, um por mês
  classe?: string; // "planejado" (cinza), "acumulado" (faixa bege), "destaque" (marrom)
};

type Props = {
  meses: string[]; // "AAAA-MM-DD"
  linhas: LinhaDosMeses[];
  cabecalho?: "escuro" | "marrom" | "nenhum";
};

// A tabela de meses embaixo dos gráficos do boletim de resultados (Real, Plan., Acum.), com o mês no cabeçalho.
export function TabelaDosMeses({ meses, linhas, cabecalho = "escuro" }: Props) {
  return (
    <table className={`boletim-tabela-meses cabecalho-${cabecalho}`}>
      {cabecalho !== "nenhum" && (
        <thead>
          <tr>
            <th scope="col">Mês</th>
            {meses.map((mes) => (
              <th key={mes} scope="col">
                {mesDoEixo(mes)}
              </th>
            ))}
          </tr>
        </thead>
      )}
      <tbody>
        {linhas.map((linha) => (
          <tr key={linha.nome} className={linha.classe}>
            <th scope="row">{linha.nome}</th>
            {linha.valores.map((valor, posicao) => (
              <td key={meses[posicao]}>{valor}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
