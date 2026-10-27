import { useState } from "react";
import type { FazendaDoAcesso } from "../../core/api/tipos";
import { Aviso } from "../../core/ui/Aviso";
import { agruparPor, contemTexto, marcarVarios, type Grupo } from "../../logic/agrupar";
import { useFazendasDoUsuario, useTrocarAcesso } from "./api";
import { ROTULO_DA_FONTE } from "./fontes";

// As fazendas que o usuário vê: lista por cliente, com "marcar todas" por cliente, busca e um botão para gravar.
// Nada muda até gravar; gravar troca a lista inteira (o que ficou desmarcado perde o acesso).
export function AcessoAsFazendas({ usuarioId }: { usuarioId: string }) {
  const fazendas = useFazendasDoUsuario(usuarioId);
  const gravar = useTrocarAcesso();
  if (fazendas.isPending) {
    return <Aviso>Carregando as fazendas…</Aviso>;
  }
  if (fazendas.isError) {
    return <Aviso tipo="erro">Não foi possível carregar as fazendas: {fazendas.error.message}</Aviso>;
  }
  return (
    <>
      {gravar.isError && <Aviso tipo="erro">Não foi possível gravar: {gravar.error.message}</Aviso>}
      {gravar.isSuccess && <Aviso>Acesso gravado.</Aviso>}
      {/* a chave recomeça a seleção quando chega a lista gravada */}
      <Selecao key={fazendas.dataUpdatedAt} fazendas={fazendas.data} gravando={gravar.isPending}
        gravar={(marcadas) => gravar.mutate({ id: usuarioId, fazendas: marcadas })} />
    </>
  );
}

type SelecaoProps = {
  fazendas: FazendaDoAcesso[];
  gravando: boolean;
  gravar: (marcadas: string[]) => void;
};

function Selecao({ fazendas, gravando, gravar }: SelecaoProps) {
  const [marcadas, trocarMarcadas] = useState(() => idsComAcesso(fazendas));
  const [busca, trocarBusca] = useState("");
  const visiveis = fazendas.filter((fazenda) => contemTexto(`${fazenda.cliente} ${fazenda.nome}`, busca));
  return (
    <div className="acesso-as-fazendas">
      <div className="acesso-barra">
        <input type="search" value={busca} onChange={(evento) => trocarBusca(evento.target.value)}
          placeholder="fazenda ou cliente" aria-label="Buscar fazenda ou cliente" />
        <span>{marcadas.length} de {fazendas.length} fazendas marcadas</span>
        <button type="button" className="botao" disabled={gravando} onClick={() => gravar(marcadas)}>
          Gravar acesso
        </button>
      </div>
      {agruparPor(visiveis, (fazenda) => fazenda.cliente).map((grupo) => (
        <GrupoDoCliente key={grupo.chave} grupo={grupo} marcadas={marcadas}
          marcar={(ids, marcar) => trocarMarcadas(marcarVarios(marcadas, ids, marcar))} />
      ))}
    </div>
  );
}

function idsComAcesso(fazendas: FazendaDoAcesso[]): string[] {
  return fazendas.filter((fazenda) => fazenda.tem_acesso).map((fazenda) => fazenda.id);
}

type GrupoProps = {
  grupo: Grupo<FazendaDoAcesso>;
  marcadas: string[];
  marcar: (ids: string[], marcar: boolean) => void;
};

// Um cliente: a caixa do título marca ou desmarca todas as fazendas dele.
function GrupoDoCliente({ grupo, marcadas, marcar }: GrupoProps) {
  const ids = grupo.itens.map((fazenda) => fazenda.id);
  const todasMarcadas = ids.every((id) => marcadas.includes(id));
  return (
    <fieldset className="acesso-cliente">
      <legend>
        <label>
          <input type="checkbox" checked={todasMarcadas} onChange={(evento) => marcar(ids, evento.target.checked)} />
          {grupo.chave}
        </label>
      </legend>
      {grupo.itens.map((fazenda) => (
        <label key={fazenda.id} className="acesso-fazenda">
          <input type="checkbox" checked={marcadas.includes(fazenda.id)}
            onChange={(evento) => marcar([fazenda.id], evento.target.checked)} />
          {fazenda.nome}
          {fazenda.origem !== null && <span className="sugestao">{ROTULO_DA_FONTE[fazenda.origem] ?? fazenda.origem}</span>}
        </label>
      ))}
    </fieldset>
  );
}
