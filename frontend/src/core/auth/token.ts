// O token do login fica no localStorage: continua valendo depois de um F5 e some no "Sair".
// Se o navegador bloquear o localStorage (aba anônima com bloqueio), o usuário só precisa entrar de novo.
const CHAVE = "terra.token";

export function lerToken(): string | null {
  try {
    return localStorage.getItem(CHAVE);
  } catch {
    return null;
  }
}

export function guardarToken(token: string): void {
  try {
    localStorage.setItem(CHAVE, token);
  } catch {
    // sem localStorage: o login vale só até a página recarregar
  }
}

export function apagarToken(): void {
  try {
    localStorage.removeItem(CHAVE);
  } catch {
    // nada para apagar
  }
}
