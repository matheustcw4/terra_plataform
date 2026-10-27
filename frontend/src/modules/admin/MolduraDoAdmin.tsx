import type { ReactNode } from "react";
import { useLocation } from "react-router";
import { useArea } from "../../core/auth/AreaAutenticada";
import { BotaoSair } from "../../core/auth/BotaoSair";
import { Aviso } from "../../core/ui/Aviso";
import { Casca, type GrupoDoMenu } from "../../core/ui/Casca";
import { paginaDoCaminho } from "../../core/ui/paginasDoBoletim";

const SECOES = [
  { caminho: "/admin/categorias", rotulo: "De-para de categorias", icone: "etiquetas" },
  { caminho: "/admin/contas", rotulo: "De-para de contas", icone: "livro" },
  { caminho: "/admin/usuarios", rotulo: "Usuários e acesso", icone: "pessoas" },
  { caminho: "/admin/funcoes", rotulo: "Funções", icone: "cracha" },
];

const GRUPOS: GrupoDoMenu[] = [
  { titulo: "Administração", itens: SECOES },
  { titulo: "Geral", itens: [{ caminho: "/menu", rotulo: "Voltar ao boletim", icone: "voltar" }] },
];

type Props = {
  titulo: string; // o título de reserva (o do menu vale quando a seção está nele)
  children: ReactNode;
};

// A moldura das telas de administração: a mesma casca do boletim, com as seções do admin no menu. Quem não é admin
// vê só o aviso (a API também recusa: as rotas /admin exigem admin).
export function MolduraDoAdmin({ titulo, children }: Props) {
  const { escopo } = useArea();
  const { pathname } = useLocation();
  const secao = paginaDoCaminho(pathname, SECOES);
  const controles = (
    <>
      <span className="topo-usuario">{escopo.usuario.nome}</span>
      <BotaoSair />
    </>
  );
  return (
    <Casca secao="Administração" grupos={GRUPOS} titulo={secao?.rotulo ?? titulo} icone={secao?.icone}
      subtitulo="De-paras, usuários, funções e acesso às fazendas" controles={controles}>
      {escopo.usuario.eh_admin && children}
      {!escopo.usuario.eh_admin && <Aviso tipo="erro">Só o administrador acessa esta área.</Aviso>}
    </Casca>
  );
}
