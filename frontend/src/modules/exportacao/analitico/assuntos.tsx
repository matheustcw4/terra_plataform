import type { BoletimAnalitico, SecaoDeLotes } from "../../../core/api/tipos";
import type { ParteDoAssunto } from "../../../logic/personalizado";
import { ConteudoCaixa } from "./ConteudoCaixa";
import { ConteudoDeLotes } from "./ConteudoDeLotes";
import { ConteudoEstoque } from "./ConteudoEstoque";
import { ConteudoFinanceiro } from "./ConteudoFinanceiro";
import { ConteudoLotacao } from "./ConteudoLotacao";
import { ConteudoMortes } from "./ConteudoMortes";
import { ConteudoPlacar } from "./ConteudoPlacar";
import { ConteudoTransferencias } from "./ConteudoTransferencias";
import type { Rotulos } from "./FolhaAnalitica";

// Os assuntos do boletim analítico e do personalizado: o título e a leitura de cada um, e os quadros (só as partes
// escolhidas). A chave é a de FOLHAS_ANALITICAS e ASSUNTOS_PERSONALIZADOS.

type TextosDoAssunto = { titulo: string; leitura: string[] };

export function textosDoAssunto(chave: string, boletim: BoletimAnalitico): TextosDoAssunto | null {
  switch (chave) {
    case "estoque":
      return { titulo: "Movimentação do estoque", leitura: boletim.estoque.leitura };
    case "lotacao":
      return { titulo: "Lotação", leitura: boletim.lotacao.leitura };
    case "placar_zootecnico":
      return { titulo: "Placar zootécnico", leitura: boletim.placar_zootecnico.leitura };
    case "nascimentos":
      return { titulo: "Nascimentos", leitura: boletim.nascimentos.leitura };
    case "compras":
      return { titulo: "Compras", leitura: boletim.compras.leitura };
    case "vendas_abate":
    case "vendas_em_pe":
      return textosDaVenda(chave, boletim);
    case "transferencias":
      return { titulo: "Transferências", leitura: boletim.transferencias.leitura };
    case "mortes":
      return { titulo: "Mortes", leitura: boletim.mortes.leitura };
    case "placar_financeiro":
      return { titulo: "Financeiro", leitura: boletim.financeiro.leitura };
    case "caixa":
      return { titulo: "Fluxo de caixa: previsto × realizado", leitura: boletim.caixa.leitura };
    default:
      return null;
  }
}

function textosDaVenda(chave: string, boletim: BoletimAnalitico): TextosDoAssunto | null {
  const secao = vendaDaChave(chave, boletim);
  if (secao === undefined) {
    return null;
  }
  return { titulo: secao.titulo, leitura: secao.leitura };
}

function vendaDaChave(chave: string, boletim: BoletimAnalitico): SecaoDeLotes | undefined {
  const tipo = chave === "vendas_abate" ? "abate" : "em_pe";
  return boletim.vendas.find((venda) => venda.tipo === tipo);
}

type Props = {
  chave: string;
  boletim: BoletimAnalitico;
  partes: ParteDoAssunto[];
  rotulos: Rotulos;
  faixa?: [number, number]; // as peças (quadros) do assunto a mostrar; sem ela, todas
};

export function ConteudoDoAssunto({ chave, boletim, partes, rotulos, faixa }: Props) {
  switch (chave) {
    case "estoque":
      return <ConteudoEstoque secao={boletim.estoque} partes={partes} faixa={faixa} rotulos={rotulos} />;
    case "lotacao":
      return <ConteudoLotacao secao={boletim.lotacao} partes={partes} faixa={faixa} />;
    case "placar_zootecnico":
      return <ConteudoPlacar linhas={boletim.placar_zootecnico.linhas} partes={partes} faixa={faixa}
        rotulos={rotulos} />;
    case "nascimentos":
      return <ConteudoDeLotes secao={boletim.nascimentos} partes={partes} faixa={faixa} rotulos={rotulos}
        tituloDosLancamentos={`Nascimentos de ${rotulos.mes}`} />;
    case "compras":
      return <ConteudoDeLotes secao={boletim.compras} partes={partes} faixa={faixa} rotulos={rotulos}
        tituloDosLancamentos={`Lotes de ${rotulos.mes}`} />;
    case "vendas_abate":
    case "vendas_em_pe":
      return <ConteudoDaVenda chave={chave} boletim={boletim} partes={partes} faixa={faixa} rotulos={rotulos} />;
    case "transferencias":
      return <ConteudoTransferencias secao={boletim.transferencias} partes={partes} faixa={faixa}
        rotulos={rotulos} />;
    case "mortes":
      return <ConteudoMortes secao={boletim.mortes} partes={partes} faixa={faixa} rotulos={rotulos} />;
    case "placar_financeiro":
      return <ConteudoFinanceiro secao={boletim.financeiro} partes={partes} faixa={faixa} rotulos={rotulos} />;
    case "caixa":
      return <ConteudoCaixa secao={boletim.caixa} partes={partes} faixa={faixa} rotulos={rotulos} />;
    default:
      return null;
  }
}

function ConteudoDaVenda({ chave, boletim, partes, rotulos, faixa }: Props) {
  const secao = vendaDaChave(chave, boletim);
  if (secao === undefined) {
    return null;
  }
  return <ConteudoDeLotes secao={secao} partes={partes} faixa={faixa} rotulos={rotulos}
    tituloDosLancamentos={`Lotes de ${rotulos.mes}`} />;
}
