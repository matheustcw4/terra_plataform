import type { ReactNode } from "react";

// Ícones de linha do painel (o mesmo traço dos ícones do AgTechLab): SVG em linha, na cor do texto em volta.
const DESENHOS: Record<string, ReactNode> = {
  alvo: (
    <>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1" />
    </>
  ),
  moeda: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M14.8 9.4c-.5-1-1.6-1.6-2.8-1.6-1.6 0-2.6.9-2.6 2 0 2.6 5.4 1.4 5.4 4.2 0 1.2-1.1 2.1-2.8 2.1-1.3 0-2.4-.6-2.9-1.7" />
      <path d="M12 6v1.8M12 16.2V18" />
    </>
  ),
  fluxo: <path d="M3 12h4l3-8 4 16 3-8h4" />,
  etiqueta: (
    <>
      <path d="M20.6 13.4l-7.2 7.2a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z" />
      <circle cx="7.5" cy="7.5" r="1.5" />
    </>
  ),
  caminhao: (
    <>
      <path d="M2 6h12v10H2zM14 9h4l3 3v4h-7" />
      <circle cx="6" cy="17.5" r="1.8" />
      <circle cx="17" cy="17.5" r="1.8" />
    </>
  ),
  carrinho: (
    <>
      <path d="M2 3h3l2.6 12.2a1 1 0 0 0 1 .8h9.6a1 1 0 0 0 1-.8L21 7H6" />
      <circle cx="9.5" cy="20" r="1.3" />
      <circle cx="17" cy="20" r="1.3" />
    </>
  ),
  broto: (
    <>
      <path d="M12 21v-9" />
      <path d="M12 12c0-4.4 3-7 8-7 0 4.4-3 7-8 7z" />
      <path d="M12 14c0-3.4-2.4-5.6-6.5-5.6 0 3.4 2.4 5.6 6.5 5.6z" />
    </>
  ),
  cruz: <path d="M12 3v18M7 8h10" />,
  setas: (
    <>
      <path d="M4 8h15l-4-4" />
      <path d="M20 16H5l4 4" />
    </>
  ),
  alerta: (
    <>
      <path d="M10.3 3.9L2.4 18a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
      <path d="M12 9.5v4M12 17h.01" />
    </>
  ),
  ajustes: (
    <>
      <path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1" />
      <circle cx="15" cy="6" r="2" />
      <circle cx="9" cy="12" r="2" />
      <circle cx="17" cy="18" r="2" />
    </>
  ),
  etiquetas: (
    <>
      <path d="M3 5v6l8.5 8.5a1.5 1.5 0 0 0 2.1 0l5.3-5.3a1.5 1.5 0 0 0 0-2.1L10.5 3.6H5" />
      <circle cx="7" cy="8" r="1.2" />
      <path d="M14 3.6l7 7" />
    </>
  ),
  livro: (
    <>
      <path d="M4 4.5A1.5 1.5 0 0 1 5.5 3H20v15H5.5A1.5 1.5 0 0 0 4 19.5z" />
      <path d="M4 19.5A1.5 1.5 0 0 0 5.5 21H20M8 7h8M8 11h6" />
    </>
  ),
  pessoas: (
    <>
      <circle cx="9" cy="8" r="3.5" />
      <path d="M2.5 20c.6-3.6 3.2-5.5 6.5-5.5s5.9 1.9 6.5 5.5" />
      <path d="M16 4.6a3.5 3.5 0 0 1 0 6.8M18 14.8c2 .7 3.2 2.4 3.5 5.2" />
    </>
  ),
  cracha: (
    <>
      <rect x="4" y="3" width="16" height="18" rx="2" />
      <circle cx="12" cy="10" r="2.6" />
      <path d="M8 17c.7-2 2.2-3 4-3s3.3 1 4 3" />
    </>
  ),
  filtro: <path d="M3 5h18l-7 8.5V19l-4 2v-7.5z" />,
  menu: <path d="M4 6h16M4 12h16M4 18h16" />,
  recolher: <path d="M4 6h16M4 12h16M4 18h10" />,
  sair: (
    <>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <path d="M16 17l5-5-5-5M21 12H9" />
    </>
  ),
  baixar: (
    <>
      <path d="M12 3v12M7 10l5 5 5-5" />
      <path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
    </>
  ),
  voltar: <path d="M15 6l-6 6 6 6" />,
  atualizar: (
    <>
      <path d="M20 12a8 8 0 1 1-2.3-5.7" />
      <path d="M20 4v4.5h-4.5" />
    </>
  ),
  grade: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </>
  ),
};

type Props = {
  nome: string;
  tamanho?: number;
};

export function Icone({ nome, tamanho = 18 }: Props) {
  return (
    <svg className="icone" width={tamanho} height={tamanho} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {DESENHOS[nome] ?? DESENHOS.grade}
    </svg>
  );
}
