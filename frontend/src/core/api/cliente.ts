import { apagarToken, lerToken } from "../auth/token";

// Em desenvolvimento o Vite repassa /api para a API (vite.config.ts); em produção front e API ficam no mesmo endereço.
const BASE = "/api/v1";

export class ErroDaApi extends Error {
  status: number;

  constructor(status: number, mensagem: string) {
    super(mensagem);
    this.status = status;
  }
}

// Toda chamada à API passa por aqui: põe o token, transforma erro HTTP em ErroDaApi e lê o JSON da resposta.
export async function chamarApi<T>(caminho: string, opcoes: RequestInit = {}): Promise<T> {
  const cabecalhos = new Headers(opcoes.headers);
  cabecalhos.set("Content-Type", "application/json");
  const token = lerToken();
  if (token !== null) {
    cabecalhos.set("Authorization", `Bearer ${token}`);
  }

  const resposta = await fetch(BASE + caminho, { ...opcoes, headers: cabecalhos });

  if (resposta.status === 401 && token !== null) {
    // O login venceu (ou o usuário foi desativado): volta para a tela de login, com a página zerada.
    apagarToken();
    window.location.assign("/login");
  }
  if (!resposta.ok) {
    throw new ErroDaApi(resposta.status, await mensagemDeErro(resposta));
  }
  if (resposta.status === 204) {
    // gravou e não tem corpo (ex.: classificar um de-para)
    return undefined as T;
  }
  return (await resposta.json()) as T;
}

// O FastAPI responde {"detail": "texto"} nos erros das rotas (e uma lista quando o erro é de validação).
async function mensagemDeErro(resposta: Response): Promise<string> {
  try {
    const corpo = await resposta.json();
    if (typeof corpo.detail === "string") {
      return corpo.detail;
    }
  } catch {
    // corpo vazio ou não é JSON
  }
  return `erro ${resposta.status} na API`;
}
