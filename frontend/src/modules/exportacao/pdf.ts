import type { QueryClient } from "@tanstack/react-query";
import type { jsPDF } from "jspdf";

// Cada folha (a capa ou uma página do boletim, já desenhada na tela) vira uma imagem e uma página do PDF. A largura
// da página é fixa e a altura acompanha a folha: página comprida não é cortada nem espremida.
const LARGURA_DA_PAGINA_PT = 1200;

function esperar(milissegundos: number): Promise<void> {
  return new Promise((resolver) => setTimeout(resolver, milissegundos));
}

// As páginas buscam os dados quando aparecem: espera a API responder e os gráficos (Recharts) terminarem a animação
// de entrada, que leva 1,5 s.
export async function esperarAsPaginas(cliente: QueryClient): Promise<void> {
  await esperar(500);
  while (cliente.isFetching() > 0) {
    await esperar(300);
  }
  await esperar(1800);
}

export async function gerarPdf(folhas: HTMLElement[], nomeDoArquivo: string,
  aoAvancar: (prontas: number) => void): Promise<void> {
  // as duas bibliotecas são pesadas e só servem aqui: carregam na hora de exportar, fora do pacote principal
  const { toJpeg } = await import("html-to-image");
  const { jsPDF: Documento } = await import("jspdf");
  let documento: jsPDF | null = null;
  for (const [posicao, folha] of folhas.entries()) {
    const imagem = await toJpeg(folha, { quality: 0.92, pixelRatio: 2, backgroundColor: "#f2f2f2" });
    const altura = (LARGURA_DA_PAGINA_PT * folha.offsetHeight) / folha.offsetWidth;
    const orientacao = altura > LARGURA_DA_PAGINA_PT ? "portrait" : "landscape";
    if (documento === null) {
      documento = new Documento({ orientation: orientacao, unit: "pt", format: [LARGURA_DA_PAGINA_PT, altura],
        compress: true });
    } else {
      documento.addPage([LARGURA_DA_PAGINA_PT, altura], orientacao);
    }
    documento.addImage(imagem, "JPEG", 0, 0, LARGURA_DA_PAGINA_PT, altura);
    aoAvancar(posicao + 1);
  }
  documento?.save(nomeDoArquivo);
}
