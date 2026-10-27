import type { QuadroDoLote } from "../../core/api/tipos";
import { Painel } from "../../core/ui/Painel";
import { indicadoresDoTipo, type TipoDeLote } from "./indicadores";

type Props = {
  titulo: string; // FÊMEA, MACHO ou GERAL
  icone: string;
  quadro: QuadroDoLote;
  tipo: TipoDeLote;
};

// Um dos três quadros do topo das páginas de venda e de compra do BI: as linhas do tipo em Realizado | Planejado.
export function QuadroDoSexo({ titulo, icone, quadro, tipo }: Props) {
  return (
    <Painel titulo={titulo} icone={icone}>
      <table className="tabela-bi">
        <thead>
          <tr>
            <th scope="col" />
            <th scope="col">Realizado</th>
            <th scope="col">Planejado</th>
          </tr>
        </thead>
        <tbody>
          {indicadoresDoTipo(tipo).map((indicador) => (
            <tr key={indicador.titulo}>
              <th scope="row">{indicador.titulo}</th>
              <td>{indicador.mostrar(quadro.realizado)}</td>
              <td>{indicador.mostrar(quadro.planejado)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Painel>
  );
}
