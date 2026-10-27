import type { LinhaDoEstoque, SecaoEstoque } from "../../../core/api/tipos";
import { numero, percentual } from "../../../logic/formatar";
import { mostra, type ParteDoAssunto, recortar } from "../../../logic/personalizado";
import { CartaoAnalitico } from "./CartaoAnalitico";
import { QuadroAnalitico, type Rotulos } from "./FolhaAnalitica";

type Props = { secao: SecaoEstoque; partes: ParteDoAssunto[]; rotulos: Rotulos; faixa?: [number, number] };

// Movimentação do estoque: a tabela do mês por categoria (entradas e saídas, como o relatório de inventário), o
// acumulado do período e a distribuição do rebanho final. Cada quadro é uma peça (o personalizado pode quebrar a
// folha entre elas); `faixa` escolhe as peças, e sem ela vão todas.
export function ConteudoEstoque({ secao, partes, rotulos, faixa }: Props) {
  const pecas = [];
  if (mostra(partes, "lancamentos")) {
    pecas.push(<MovimentacaoDoMes key="movimentacao" secao={secao} partes={partes} rotulos={rotulos} />);
  }
  if (mostra(partes, "resumo")) {
    pecas.push(<AcumuladoDoPeriodo key="acumulado" secao={secao} rotulos={rotulos} />);
    pecas.push(<DistribuicaoFinal key="distribuicao" secao={secao} />);
  }
  return <>{recortar(pecas, faixa)}</>;
}

type MovimentacaoProps = { secao: SecaoEstoque; partes: ParteDoAssunto[]; rotulos: Rotulos };

function MovimentacaoDoMes({ secao, partes, rotulos }: MovimentacaoProps) {
  return (
    <QuadroAnalitico titulo={`Movimentação de ${rotulos.mes}`}>
      <TabelaDoEstoque linhas={secao.mes} />
      {mostra(partes, "notas") && (
        <p className="nota">
          Desmame e mudança de categoria tiram de uma categoria e põem em outra: não mudam o total. O ajuste é a
          diferença entre o saldo informado pela fonte e os movimentos lançados.
        </p>
      )}
    </QuadroAnalitico>
  );
}

function AcumuladoDoPeriodo({ secao, rotulos }: { secao: SecaoEstoque; rotulos: Rotulos }) {
  const acumulado = secao.acumulado;
  return (
    <QuadroAnalitico titulo="Acumulado do período">
      <div className="cartoes-analiticos">
        <CartaoAnalitico rotulo={`Estoque inicial (${rotulos.inicio})`} valor={numero(acumulado.estoque_inicial)}
          forte />
        <CartaoAnalitico rotulo="Nascimentos" valor={numero(acumulado.nascimentos)} />
        <CartaoAnalitico rotulo="Compras" valor={numero(acumulado.compras)} />
        <CartaoAnalitico rotulo="Transferências (entrada)" valor={numero(acumulado.transferencia_entrada)} />
        <CartaoAnalitico rotulo="Vendas e abates" valor={numero(acumulado.vendas)} />
        <CartaoAnalitico rotulo="Mortes" valor={numero(acumulado.mortes)} />
        <CartaoAnalitico rotulo="Consumo e doação" valor={numero(acumulado.consumo_doacao)} />
        <CartaoAnalitico rotulo="Transferências (saída)" valor={numero(acumulado.transferencia_saida)} />
        <CartaoAnalitico rotulo="Ajuste de inventário" valor={numero(acumulado.ajuste)} />
        <CartaoAnalitico rotulo={`Estoque final (${rotulos.mes})`} valor={numero(acumulado.estoque_final)} forte />
      </div>
    </QuadroAnalitico>
  );
}

function DistribuicaoFinal({ secao }: { secao: SecaoEstoque }) {
  return (
    <QuadroAnalitico titulo="Distribuição do rebanho final">
      <table className="tabela-analitica tabela-distribuicao">
        <thead>
          <tr>
            <th scope="col">Categoria</th>
            <th scope="col">Cabeças</th>
            <th scope="col">%</th>
            <th scope="col" aria-label="Participação" />
          </tr>
        </thead>
        <tbody>
          {secao.distribuicao_final.map((fatia) => (
            <tr key={fatia.categoria}>
              <th scope="row">{fatia.categoria}</th>
              <td>{numero(fatia.cabecas)}</td>
              <td>{percentual(fatia.participacao ?? null)}</td>
              <td className="barra-da-participacao">
                <span style={{ width: `${(fatia.participacao ?? 0) * 100}%` }} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </QuadroAnalitico>
  );
}

function TabelaDoEstoque({ linhas }: { linhas: LinhaDoEstoque[] }) {
  return (
    <table className="tabela-analitica tabela-estoque">
      <thead>
        <tr>
          <th rowSpan={2} scope="col">Categoria</th>
          <th rowSpan={2} scope="col">Estoque inicial</th>
          <th colSpan={5} scope="colgroup" className="inicio-do-bloco">Entradas</th>
          <th colSpan={6} scope="colgroup" className="inicio-do-bloco">Saídas</th>
          <th rowSpan={2} scope="col" className="inicio-do-bloco">Ajuste</th>
          <th rowSpan={2} scope="col">Estoque final</th>
        </tr>
        <tr>
          <th scope="col" className="inicio-do-bloco">Nasc.</th>
          <th scope="col">Compra</th>
          <th scope="col">Desm.</th>
          <th scope="col">Transf.</th>
          <th scope="col">Categ.</th>
          <th scope="col" className="inicio-do-bloco">Morte</th>
          <th scope="col">Venda</th>
          <th scope="col">Desm.</th>
          <th scope="col">Transf.</th>
          <th scope="col">Cons./Doaç.</th>
          <th scope="col">Categ.</th>
        </tr>
      </thead>
      <tbody>
        {linhas.map((linha) => (
          <tr key={linha.categoria} className={linha.categoria === "TOTAL" ? "linha-total" : undefined}>
            <th scope="row">{linha.categoria}</th>
            <td>{numero(linha.estoque_inicial)}</td>
            <Celula valor={linha.nascimentos} inicio />
            <Celula valor={linha.compras} />
            <Celula valor={linha.desmame_entrada} />
            <Celula valor={linha.transferencia_entrada} />
            <Celula valor={linha.mudanca_entrada} />
            <Celula valor={linha.mortes} inicio />
            <Celula valor={linha.vendas} />
            <Celula valor={linha.desmame_saida} />
            <Celula valor={linha.transferencia_saida} />
            <Celula valor={linha.consumo_doacao} />
            <Celula valor={linha.mudanca_saida} />
            <Celula valor={linha.ajuste} inicio />
            <td className="destaque">{numero(linha.estoque_final)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// Zero fica em branco, como no relatório de inventário: os movimentos do mês saltam aos olhos.
function Celula({ valor, inicio = false }: { valor: number; inicio?: boolean }) {
  return <td className={inicio ? "inicio-do-bloco" : undefined}>{valor === 0 ? "" : numero(valor)}</td>;
}
