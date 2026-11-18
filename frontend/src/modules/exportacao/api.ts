import { useQuery } from "@tanstack/react-query";
import { chamarApi } from "../../core/api/cliente";
import type { BoletimAnalitico } from "../../core/api/tipos";
import { anexarEscolhasDoFinanceiro, type Consulta, type Visao } from "../../logic/filtro";

// GET /dashboards/analitico?fazendas=..&mes_referencia=AAAA-MM&visao=safra|civil[&versao=..][&situacao=..]
// [&atividade=..][&classificacao=..][&conta=..]: tudo o que as folhas do Boletim Resumido e do Personalizado mostram,
// numa chamada só; as metas nas versões do plano escolhidas e o financeiro no status, no tipo de atividade, na
// classificação e na conta bancária escolhidos.
export function useBoletimAnalitico(consulta: Consulta, mesReferencia: string, visao: Visao) {
  const parametros = new URLSearchParams({ mes_referencia: mesReferencia, visao });
  for (const fazenda of consulta.fazendas) {
    parametros.append("fazendas", fazenda);
  }
  for (const versao of consulta.versoes) {
    parametros.append("versao", versao);
  }
  for (const fazenda of consulta.semPlano) {
    parametros.append("sem_plano", fazenda);
  }
  for (const situacao of consulta.situacoes) {
    parametros.append("situacao", situacao);
  }
  anexarEscolhasDoFinanceiro(parametros, consulta);
  return useQuery({
    queryKey: ["analitico", consulta.fazendas, mesReferencia, visao, consulta.versoes, consulta.semPlano,
      consulta.situacoes, consulta.atividades, consulta.classificacoes, consulta.contas],
    queryFn: () => chamarApi<BoletimAnalitico>(`/dashboards/analitico?${parametros.toString()}`),
  });
}
