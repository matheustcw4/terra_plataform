import type { ReactNode } from "react";
import { ComprasPagina } from "../compras/ComprasPagina";
import { FinanceiroPagina } from "../financeiro/FinanceiroPagina";
import { MortesPagina } from "../mortes/MortesPagina";
import { NascimentosPagina } from "../nascimentos/NascimentosPagina";
import { PrevistoPagina } from "../previsto/PrevistoPagina";
import { MovimentacaoPagina } from "../rebanho/MovimentacaoPagina";
import { TransferenciasPagina } from "../transferencias/TransferenciasPagina";
import { VendasPagina } from "../vendas/VendasPagina";

// A página do boletim que cada chave do seletor do PDF desenha (as mesmas das abas, em core/ui/paginasDoBoletim).
export const PAGINA_DO_PDF: Record<string, ReactNode> = {
  "/previsto_realizado": <PrevistoPagina />,
  "/financeiro": <FinanceiroPagina />,
  "/rebanho/movimentacao": <MovimentacaoPagina />,
  "/vendas/abate": <VendasPagina tipo="abate" />,
  "/vendas/em_pe": <VendasPagina tipo="em_pe" />,
  "/compras": <ComprasPagina />,
  "/nascimentos": <NascimentosPagina />,
  "/mortes": <MortesPagina />,
  "/transferencias": <TransferenciasPagina />,
};
