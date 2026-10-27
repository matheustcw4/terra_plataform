import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { Navigate, Outlet, useOutletContext, useSearchParams } from "react-router";
import { chamarApi } from "../api/cliente";
import type { Escopo } from "../api/tipos";
import { filtroLembrado, lembrarFiltro } from "../escopo/lembrarFiltro";
import { Aviso } from "../ui/Aviso";
import { consultaDoFiltro, filtroDaUrl, filtroParaUrl, type Consulta, type Filtro } from "../../logic/filtro";
import { BotaoSair } from "./BotaoSair";
import { lerToken } from "./token";

// O que toda página da área logada recebe (via useArea): as fazendas que o usuário vê, o filtro escolhido no MENU,
// a consulta que esse filtro gera para a API e a função que troca o filtro (usada pelo MENU).
export type ContextoDaArea = {
  escopo: Escopo;
  filtro: Filtro;
  consulta: Consulta;
  trocarFiltro: (novo: Filtro) => void;
};

export function useArea(): ContextoDaArea {
  return useOutletContext<ContextoDaArea>();
}

// Rota "mãe" de todas as páginas com login. Em três passos, um componente por passo:
// 1. sem token -> tela de login;  2. carrega o escopo (/escopo);  3. monta o filtro e mostra a página da vez.
export function AreaAutenticada() {
  if (lerToken() === null) {
    return <Navigate to="/login" replace />;
  }
  return <CarregarEscopo />;
}

function CarregarEscopo() {
  const escopo = useQuery({ queryKey: ["escopo"], queryFn: () => chamarApi<Escopo>("/escopo") });
  if (escopo.isPending) {
    return <Aviso>Carregando suas fazendas…</Aviso>;
  }
  if (escopo.isError) {
    return <Aviso tipo="erro">Não foi possível carregar suas fazendas: {escopo.error.message}</Aviso>;
  }
  return <Area escopo={escopo.data} />;
}

function Area({ escopo }: { escopo: Escopo }) {
  const [parametros, setParametros] = useSearchParams();
  // Link com filtro manda; sem filtro na URL, abre o último que a pessoa usou neste navegador.
  const urlTemFiltro = parametros.has("cliente");
  const filtro = filtroDaUrl(urlTemFiltro ? parametros : filtroLembrado(), escopo.fazendas);

  // Na primeira visita a URL ainda está vazia: grava nela o filtro em uso, para o link poder ser compartilhado.
  useEffect(() => {
    if (filtro !== null && !urlTemFiltro) {
      setParametros(filtroParaUrl(filtro), { replace: true });
    }
  }, [filtro, urlTemFiltro, setParametros]);

  function trocarFiltro(novo: Filtro) {
    const url = filtroParaUrl(novo);
    lembrarFiltro(url);
    setParametros(url);
  }

  if (filtro === null) {
    return (
      <div className="sem-acesso">
        <Aviso>Seu usuário ainda não tem acesso a nenhuma fazenda. Fale com o administrador.</Aviso>
        <BotaoSair />
      </div>
    );
  }
  const contexto: ContextoDaArea = {
    escopo,
    filtro,
    consulta: consultaDoFiltro(filtro, escopo.fazendas),
    trocarFiltro,
  };
  return <Outlet context={contexto} />;
}
