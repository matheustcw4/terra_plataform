import type { IntegracaoPorApi } from "../../core/api/tipos";
import { Aviso } from "../../core/ui/Aviso";
import { algumaRodando } from "../../logic/integracoes";
import { useCargasDaApi } from "./api";
import { CargaDaApi } from "./CargaDaApi";

// A aba de uma API (hoje, o Metryx): se está ligada e quando roda, e as cargas mais recentes, a mais nova aberta.
export function CargasDaApi({ integracao }: { integracao: IntegracaoPorApi }) {
  const cargas = useCargasDaApi(integracao.fonte);
  return (
    <>
      <section className="painel-grafico">
        <h2>
          {integracao.rotulo.toUpperCase()}
          {integracao.ligada && <span className="selo selo-ok">ligado</span>}
          {!integracao.ligada && <span className="selo selo-aviso">desligado</span>}
        </h2>
        <SituacaoDaApi integracao={integracao} />
      </section>
      <section className="painel-grafico">
        <h2>
          CARGAS RECENTES
          {cargas.data && algumaRodando(cargas.data) && <span className="selo selo-andamento">rodando</span>}
        </h2>
        {cargas.isPending && <Aviso>Carregando…</Aviso>}
        {cargas.isError && <Aviso tipo="erro">Não foi possível carregar as cargas: {cargas.error.message}</Aviso>}
        {cargas.data && cargas.data.length === 0 && <p className="explicacao">Nenhuma carga ainda.</p>}
        {cargas.data && (
          <div className="cargas-da-api">
            {cargas.data.map((carga, posicao) => (
              <CargaDaApi key={carga.id} carga={carga} aberta={posicao === 0} />
            ))}
          </div>
        )}
      </section>
    </>
  );
}

function SituacaoDaApi({ integracao }: { integracao: IntegracaoPorApi }) {
  if (!integracao.ligada) {
    return (
      <p className="explicacao">
        Desligado: nenhuma carga roda sozinha e o botão "Atualizar agora" não aparece. Para ligar, preencha a agenda
        ({integracao.variavel_da_agenda}) na configuração do servidor; a agenda é também a autorização para chamar a
        API real.
      </p>
    );
  }
  return (
    <p className="explicacao">
      A carga roda {integracao.quando}, cliente por cliente; o botão "Atualizar agora", no topo, pede uma fora da
      agenda. Uma carga com erro não apaga nada: os números ficam os da carga anterior. Os avisos das fazendas (valor
      fora do padrão, conta a classificar) também aparecem em Pendências.
    </p>
  );
}
