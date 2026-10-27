import { type Cabecalho, paragrafosDaNota } from "../../../logic/analitico";
import { FolhaAnalitica } from "./FolhaAnalitica";

export const TITULO_DA_NOTA = "Nota técnica";

// A nota técnica digitada na exportação, numa folha A4 própria com o cabeçalho das folhas analíticas (fazenda, mês e
// período). Nos modos Padrão e Analítico ela abre (logo depois da capa) e fecha o PDF; nota vazia não gera folha.
export function FolhaDaNota({ texto, cabecalho }: { texto: string; cabecalho: Cabecalho }) {
  const paragrafos = paragrafosDaNota(texto);
  if (paragrafos.length === 0) {
    return null;
  }
  return (
    <div className="folha-pdf folha-a4">
      <FolhaAnalitica titulo={TITULO_DA_NOTA} cabecalho={cabecalho} leitura={[]}>
        <section className="nota-tecnica">
          {paragrafos.map((paragrafo, posicao) => (
            <p key={posicao} className="nota-tecnica-paragrafo">
              {paragrafo}
            </p>
          ))}
        </section>
      </FolhaAnalitica>
    </div>
  );
}
