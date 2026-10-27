type Props = {
  rotulo: string;
  valor: string; // já formatado
  unidade?: string;
  forte?: boolean; // o começo e o fim de uma conta (estoque inicial e final), em destaque
};

// Um número em destaque no alto de uma folha do boletim analítico.
export function CartaoAnalitico({ rotulo, valor, unidade, forte = false }: Props) {
  return (
    <div className={forte ? "cartao-analitico forte" : "cartao-analitico"}>
      <span>{rotulo}</span>
      <strong>{valor}</strong>
      {unidade && <small>{unidade}</small>}
    </div>
  );
}
