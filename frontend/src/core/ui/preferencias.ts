// Preferências de tela de quem usa este navegador (o menu lateral recolhido). Sem localStorage, só não lembra.
const CHAVE_RAIL = "terra.rail-recolhido";

export function railRecolhidoLembrado(): boolean {
  try {
    return localStorage.getItem(CHAVE_RAIL) === "1";
  } catch {
    return false;
  }
}

export function lembrarRailRecolhido(recolhido: boolean): void {
  try {
    localStorage.setItem(CHAVE_RAIL, recolhido ? "1" : "0");
  } catch {
    // segue sem lembrar
  }
}
