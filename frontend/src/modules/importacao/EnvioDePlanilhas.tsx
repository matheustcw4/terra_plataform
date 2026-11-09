import { useState, type ChangeEvent, type DragEvent } from "react";
import { Icone } from "../../core/ui/Icone";
import { motivoDaRecusa, PADRAO_EXPLICADO, tamanhoLegivel } from "../../logic/importacao";
import { useEnviarPlanilha } from "./api";

type SituacaoDoEnvio = "enviando" | "enviada" | "recusado";
type Envio = { chave: string; nome: string; tamanho: number; situacao: SituacaoDoEnvio; mensagem: string | null };

const ROTULO_DO_ENVIO: Record<SituacaoDoEnvio, string> = {
  enviando: "Enviando…",
  enviada: "Enviada: o resultado sai na lista abaixo",
  recusado: "Recusado",
};

// Onde a pessoa solta (ou escolhe) as planilhas. Os arquivos vão um de cada vez, na ordem: o worker carrega na ordem
// de chegada. O que a API recusa na hora (nome fora do padrão, não é Excel) aparece aqui; o resultado da carga, na
// lista de importações.
export function EnvioDePlanilhas() {
  const enviar = useEnviarPlanilha();
  const [envios, trocarEnvios] = useState<Envio[]>([]);
  const [arrastando, trocarArrastando] = useState(false);

  function anotar(chave: string, situacao: SituacaoDoEnvio, mensagem: string | null) {
    trocarEnvios((atuais) => atuais.map((envio) => (envio.chave === chave ? { ...envio, situacao, mensagem } : envio)));
  }

  async function enviarArquivos(arquivos: File[]) {
    for (const arquivo of arquivos) {
      const motivo = motivoDaRecusa(arquivo.name, arquivo.size);
      let situacao: SituacaoDoEnvio = "enviando";
      if (motivo !== null) {
        situacao = "recusado";
      }
      const envio: Envio = { chave: crypto.randomUUID(), nome: arquivo.name, tamanho: arquivo.size, situacao,
        mensagem: motivo };
      trocarEnvios((atuais) => [envio, ...atuais]);
      if (motivo !== null) {
        continue;
      }
      try {
        await enviar.mutateAsync(arquivo);
        anotar(envio.chave, "enviada", null);
      } catch (erro) {
        anotar(envio.chave, "recusado", erro instanceof Error ? erro.message : "não foi possível enviar");
      }
    }
  }

  function aoEscolher(evento: ChangeEvent<HTMLInputElement>) {
    const arquivos = Array.from(evento.target.files ?? []);
    evento.target.value = ""; // deixa escolher o mesmo arquivo de novo
    void enviarArquivos(arquivos);
  }

  function aoArrastar(evento: DragEvent<HTMLLabelElement>) {
    evento.preventDefault();
    trocarArrastando(true);
  }

  function aoSoltar(evento: DragEvent<HTMLLabelElement>) {
    evento.preventDefault();
    trocarArrastando(false);
    void enviarArquivos(Array.from(evento.dataTransfer.files));
  }

  return (
    <div className="envio-de-planilhas">
      <label className={arrastando ? "area-de-envio arrastando" : "area-de-envio"} onDragOver={aoArrastar}
        onDragLeave={() => trocarArrastando(false)} onDrop={aoSoltar}>
        <Icone nome="enviar" tamanho={28} />
        <strong>Arraste as planilhas para cá</strong>
        <span>
          ou <span className="link">escolha os arquivos</span> (.xlsm ou .xlsx, com o nome {PADRAO_EXPLICADO})
        </span>
        <input type="file" accept=".xlsm,.xlsx" multiple onChange={aoEscolher} />
      </label>
      {envios.length > 0 && (
        <ul className="envios">
          {envios.map((envio) => (
            <li key={envio.chave} className={`envio envio-${envio.situacao}`}>
              <span className="envio-nome">{envio.nome}</span>
              <span className="envio-tamanho">{tamanhoLegivel(envio.tamanho)}</span>
              <span className="envio-situacao">{ROTULO_DO_ENVIO[envio.situacao]}</span>
              {envio.mensagem && <span className="envio-mensagem">{envio.mensagem}</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
