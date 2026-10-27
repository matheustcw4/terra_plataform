const DESCRICAO: Record<string, string> = {
  verde: "no rumo da meta",
  amarelo: "um pouco fora da meta",
  vermelho: "fora da meta",
};

// O status de um indicador contra o previsto: bolinha verde, amarela ou vermelha (vazio quando não há lado certo).
export function Status({ status }: { status: string | null | undefined }) {
  if (status === null || status === undefined) {
    return null;
  }
  return <span className={`status-bolinha status-${status}`} title={DESCRICAO[status]} aria-label={DESCRICAO[status]} />;
}
