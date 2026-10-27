// O último filtro usado fica no navegador, para o painel abrir onde a pessoa parou.
// Guarda só ids e meses (nada sensível). Sem localStorage, apenas não lembra.
const CHAVE = "terra.filtro";

export function filtroLembrado(): URLSearchParams {
  try {
    return new URLSearchParams(localStorage.getItem(CHAVE) ?? "");
  } catch {
    return new URLSearchParams();
  }
}

export function lembrarFiltro(parametros: URLSearchParams): void {
  try {
    localStorage.setItem(CHAVE, parametros.toString());
  } catch {
    // segue sem lembrar
  }
}
