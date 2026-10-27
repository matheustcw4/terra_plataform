import { useState } from "react";
import { useLocation, useNavigate } from "react-router";
import { mesDeReferencia, rotuloDoMesDeReferencia } from "../../logic/analitico";
import { paginasNaOrdem } from "../../logic/exportacao";
import { alternarItem } from "../../logic/listas";
import { PARTES, type ParteDoAssunto, TODAS_AS_PARTES } from "../../logic/personalizado";
import { useArea } from "../auth/AreaAutenticada";
import { CAPA, ordemDoModo, rotuloDaFolha, type ModoDoPdf, type PedidoDePdf } from "./paginasDoBoletim";

type Props = { aoFechar: () => void };

const MODOS: { modo: ModoDoPdf; rotulo: string }[] = [
  { modo: "padrao", rotulo: "Padrão" },
  { modo: "analitico", rotulo: "Analítico" },
  { modo: "personalizado", rotulo: "Personalizado" },
];

// cabe numa folha A4 com folga (o texto mais longo faz a folha crescer, sem cortar)
const TAMANHO_DA_NOTA = 4000;

const LEGENDA_DA_LISTA: Record<ModoDoPdf, string> = {
  padrao: "Páginas",
  analitico: "Folhas",
  personalizado: "Assuntos",
};

// Escolha do modo (padrão: as páginas do painel; analítico: folhas A4 com o mês de referência, o acumulado e a meta,
// explicados; personalizado: os assuntos e as partes de cada um que a pessoa marcar), das páginas ou assuntos (todos
// marcados de início), da cidade da capa e das notas técnicas do começo e do fim do PDF. A cidade e as notas só valem
// para este arquivo: vão na navegação para a página que gera o PDF e não são gravadas em lugar nenhum.
export function DialogoDeExportacao({ aoFechar }: Props) {
  const { escopo, filtro } = useArea();
  const [modo, trocarModo] = useState<ModoDoPdf>("padrao");
  const [marcadas, setMarcadas] = useState<string[]>(ordemDoModo("padrao"));
  const [partes, trocarPartes] = useState<ParteDoAssunto[]>(TODAS_AS_PARTES);
  const [cidade, setCidade] = useState("Cuiabá");
  const [notaInicial, trocarNotaInicial] = useState("");
  const [notaFinal, trocarNotaFinal] = useState("");
  const navegar = useNavigate();
  const { pathname, search } = useLocation();
  const ordem = ordemDoModo(modo);
  const referencia = rotuloDoMesDeReferencia(mesDeReferencia(filtro, escopo.fazendas));
  const semPartes = modo === "personalizado" && partes.length === 0;

  function escolherModo(novo: ModoDoPdf) {
    trocarModo(novo);
    setMarcadas(ordemDoModo(novo));
  }

  function gerar() {
    const pedido: PedidoDePdf = {
      modo,
      paginas: paginasNaOrdem(marcadas, ordem),
      partes,
      cidade,
      notaInicial,
      notaFinal,
      voltar: pathname,
    };
    navegar({ pathname: "/exportar", search }, { state: pedido });
  }

  return (
    <div className="dialogo-fundo" onKeyDown={(evento) => evento.key === "Escape" && aoFechar()}>
      <div className="dialogo" role="dialog" aria-modal="true" aria-labelledby="titulo-exportacao">
        <h2 id="titulo-exportacao">Exportar PDF</h2>
        <div className="abas dialogo-modo" role="group" aria-label="Modo do PDF">
          {MODOS.map((opcao) => (
            <button key={opcao.modo} type="button" className={modo === opcao.modo ? "active" : undefined}
              aria-pressed={modo === opcao.modo} onClick={() => escolherModo(opcao.modo)}>
              {opcao.rotulo}
            </button>
          ))}
        </div>
        <DescricaoDoModo modo={modo} referencia={referencia} />
        <div className="dialogo-atalhos">
          <button type="button" onClick={() => setMarcadas(ordem)}>Marcar todas</button>
          <button type="button" onClick={() => setMarcadas([])}>Desmarcar todas</button>
        </div>
        <fieldset className="dialogo-paginas">
          <legend>{LEGENDA_DA_LISTA[modo]}</legend>
          {ordem.map((chave) => (
            <label key={chave}>
              <input type="checkbox" checked={marcadas.includes(chave)}
                onChange={() => setMarcadas(alternarItem(marcadas, chave))} />
              {rotuloDaFolha(modo, chave)}
            </label>
          ))}
        </fieldset>
        {modo === "personalizado" && (
          <fieldset className="dialogo-paginas dialogo-partes">
            <legend>O que mostrar em cada assunto</legend>
            {PARTES.map((parte) => (
              <label key={parte.chave}>
                <input type="checkbox" checked={partes.includes(parte.chave)}
                  onChange={() => trocarPartes(alternarItem(partes, parte.chave))} />
                <span>
                  <strong>{parte.rotulo}</strong>
                  <small>{parte.descricao}</small>
                </span>
              </label>
            ))}
          </fieldset>
        )}
        <label className="dialogo-campo">
          <span>Nota técnica no início do PDF (opcional)</span>
          <textarea rows={3} maxLength={TAMANHO_DA_NOTA} value={notaInicial}
            placeholder="Abre o PDF, logo depois da capa. Linha em branco separa os parágrafos."
            onChange={(evento) => trocarNotaInicial(evento.target.value)} />
        </label>
        <label className="dialogo-campo">
          <span>Nota técnica no fim do PDF (opcional)</span>
          <textarea rows={3} maxLength={TAMANHO_DA_NOTA} value={notaFinal}
            placeholder="Fecha o PDF, depois de todo o resto."
            onChange={(evento) => trocarNotaFinal(evento.target.value)} />
        </label>
        <label className="dialogo-campo">
          <span>Cidade (na capa)</span>
          <input type="text" value={cidade} maxLength={40} disabled={!marcadas.includes(CAPA)}
            onChange={(evento) => setCidade(evento.target.value)} />
        </label>
        <div className="dialogo-botoes">
          <button type="button" onClick={aoFechar}>Cancelar</button>
          <button type="button" className="primario" disabled={marcadas.length === 0 || semPartes} onClick={gerar}>
            Gerar PDF
          </button>
        </div>
      </div>
    </div>
  );
}

function DescricaoDoModo({ modo, referencia }: { modo: ModoDoPdf; referencia: string }) {
  if (modo === "analitico") {
    return (
      <p>
        Uma folha A4 por assunto, com o mês de referência (<strong>{referencia}</strong>, o último mês do filtro), o
        acumulado do período, a meta e uma leitura explicada dos números.
      </p>
    );
  }
  if (modo === "personalizado") {
    return (
      <p>
        Escolha os assuntos e o que mostrar em cada um. O mês de referência é <strong>{referencia}</strong>; os assuntos
        vão um depois do outro, ocupando as folhas A4 sem deixar espaço vazio.
      </p>
    );
  }
  return <p>As páginas do painel, como estão na tela. O filtro é o do MENU.</p>;
}
