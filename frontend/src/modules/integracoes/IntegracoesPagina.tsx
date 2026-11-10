import { useParams } from "react-router";
import { useArea } from "../../core/auth/AreaAutenticada";
import { BotaoSair } from "../../core/auth/BotaoSair";
import { Aviso } from "../../core/ui/Aviso";
import { Casca } from "../../core/ui/Casca";
import { gruposDoBoletim, INTEGRACOES } from "../../core/ui/paginasDoBoletim";
import { PlanilhasEnviadas } from "../importacao/PlanilhasEnviadas";
import { AbasDasIntegracoes } from "./AbasDasIntegracoes";
import { useIntegracoes } from "./api";
import { CargasDaApi } from "./CargasDaApi";

// Integrações (pedido do usuário, 10/11/2026; antes, "Importar planilhas"): a aba Planilhas, de todos, com o envio e
// o resultado de cada arquivo, e uma aba por API (só o admin), com o histórico das cargas e os erros de cada cliente.
// O endereço diz a aba: /integracoes é a das planilhas; /integracoes/metryx, a do Metryx.
export function IntegracoesPagina() {
  const { escopo } = useArea();
  const { fonte } = useParams();
  const ehAdmin = escopo.usuario.eh_admin;
  const apis = useIntegracoes(ehAdmin);

  const controles = (
    <>
      <span className="topo-usuario">{escopo.usuario.nome}</span>
      <BotaoSair />
    </>
  );
  return (
    <Casca secao="Dados" grupos={gruposDoBoletim(ehAdmin)} titulo={INTEGRACOES.rotulo} icone={INTEGRACOES.icone}
      subtitulo="As planilhas e as APIs que alimentam o painel" controles={controles}>
      <div className="pagina">
        <AbasDasIntegracoes apis={apis.data ?? []} />
        {fonte === undefined && <PlanilhasEnviadas ehAdmin={ehAdmin} />}
        {fonte !== undefined && <AbaDaApi fonte={fonte} ehAdmin={ehAdmin} apis={apis} />}
      </div>
    </Casca>
  );
}

type PropsDaAba = { fonte: string; ehAdmin: boolean; apis: ReturnType<typeof useIntegracoes> };

function AbaDaApi({ fonte, ehAdmin, apis }: PropsDaAba) {
  if (!ehAdmin) {
    return <Aviso>O histórico das cargas das APIs é só do administrador.</Aviso>;
  }
  if (apis.isPending) {
    return <Aviso>Carregando…</Aviso>;
  }
  if (apis.isError) {
    return <Aviso tipo="erro">Não foi possível carregar as integrações: {apis.error.message}</Aviso>;
  }
  const integracao = apis.data.find((api) => api.fonte === fonte);
  if (integracao === undefined) {
    return <Aviso tipo="erro">Integração desconhecida: {fonte}</Aviso>;
  }
  return <CargasDaApi integracao={integracao} />;
}
