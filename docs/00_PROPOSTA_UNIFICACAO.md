# Projeto Terra — Proposta de unificação (Planilhas + Metryx) numa plataforma web única

> Data: 14/10/2026 · Base: análise dos 2 PBIX, dos 2 jobs Pentaho (31 transformações), do Swagger oficial da API Metryx,
> da planilha-modelo (e varredura dos 230 `.xlsm` do Drive) e dos repositórios `locks_agtech_frontend`/`locks_agtech_backend`.
> Relatórios detalhados (fonte de tudo o que está aqui): [`analises/`](analises/)
> **Como as duas estruturas viram um banco igual (campo a campo):** [`01_CONFORMACAO_DAS_FONTES.md`](01_CONFORMACAO_DAS_FONTES.md)
>
> | # | Relatório | Conteúdo |
> |---|---|---|
> | 01 | [BI Ciclo Completo](analises/01_bi_ciclo_completo.md) | 237 medidas, colunas calculadas, M/SQL, RLS, 14 páginas, glossário, bugs |
> | 02 | [BI Metryx](analises/02_bi_metryx.md) | 220 medidas, SQL de saldo/DRE, o que está inacabado/quebrado |
> | 03 | [Pipeline Planilhas](analises/03_pipeline_planilhas.md) | anatomia das 32 abas, 9 KTRs, DDL `stg_*`, spec do adapter de planilhas |
> | 04 | [Pipeline Metryx](analises/04_pipeline_metryx_api.md) | 25 endpoints/24 DTOs campo a campo, 22 KTRs, DDL, spec do adapter Metryx |
> | 05 | [Referência AgTechLab](analises/05_referencia_agtechlab.md) | estrutura back/front, RLS, jobs, o que copiar e o que não copiar |

---

## 0. Resumo executivo

1. **Os dois BIs já são o mesmo modelo semântico.** O BI Metryx foi clonado do Ciclo Completo (14 medidas e 4 colunas do
   Metryx ainda apontam para tabelas que só existem no de planilhas, e vice-versa há colunas residuais com nomes da API
   Metryx no de planilhas). Mesmas páginas, mesmas medidas, mesmos conceitos. **Unificar é viável e barato no nível de
   negócio** — o trabalho está em padronizar a *camada de dados*.
2. **A planilha já fala "Metryx" no financeiro**: a aba `BASEPLANODECONTAS` traduz os centros de custo locais para o
   plano de contas do Metryx. O ponto de convergência do DRE já existe.
3. **A diferença real está em 4 pontos**: (a) identidade da fazenda (`PROP_FAZ` textual × `idcustomer+idfarm`);
   (b) categorias animais (15 categorias BI fixas na planilha × categorias livres por cliente no Metryx);
   (c) estoque (soma de movimentações na planilha × snapshot de balanço com forward-fill no Metryx);
   (d) UA/área (digitado na planilha × não modelado no Metryx, embora a API traga `weight` e `utilizacao-pasto`).
4. **Proposta**: plataforma com **modelo canônico único** no PostgreSQL, alimentado por **2 adapters** (Planilha e Metryx)
   que produzem exatamente as mesmas linhas canônicas; uma **camada de KPIs** em Python/SQL que substitui as ~450 medidas
   DAX por ~70 KPIs com fórmula única e corrigida; **API FastAPI** + **front React/TS/Vite**; **RLS por usuário/fazenda**
   no banco (de verdade — não como no AgTechLab, onde o app roda como superusuário e o RLS não protege nada).
5. **"Sistema produtivo" vira filtro**, não arquivo: CRIA / RECRIA E ENGORDA / CICLO COMPLETO no mesmo painel
   (o PBIX atual trava `CICLO COMPLETO` num filtro de relatório).
6. **Fontes híbridas por fazenda × domínio**: há clientes Metryx com planejamento/financeiro em planilha (`fDre.ktr` e
   `fPlanejamento.ktr` leem `G:\Meu Drive\Financeiro` e `\Planejamento`). O modelo terá uma matriz
   `fazenda × domínio → fonte` em vez de "cliente é Metryx ou planilha".
7. **Ganhos concretos além da unificação**: fim dos TRUNCATE+INSERT (hoje o job de planilhas teve só **39–62% de
   execuções com sucesso** em ago–out/26 e 1 célula derrubou tudo por 7 dias); fim de dados duplicados (5 fazendas com
   arquivo em dobro), de linhas descartadas em silêncio, de tokens/senhas expostos; carga incremental (só arquivos/payloads
   que mudaram); auditoria de qualidade visível no próprio painel.
8. **Segurança — ação imediata, independente do projeto**: tokens Metryx de todos os clientes estão **em texto puro** em
   `"DATABASE".stg_customers.token` (legível pelo DSN ODBC do Power BI); token mestre hardcoded em `get_customer.ktr`;
   senha do superusuário `postgres` e do SMTP Gmail em ofuscação reversível nos `.ktr/.kjb`. **Rotacionar.**

---

## 1. Diagnóstico

### 1.1 Equivalência entre os dois BIs

| Conceito | BI Ciclo Completo (planilha) | BI Metryx (API) | Situação no Metryx |
|---|---|---|---|
| Fazenda (dimensão) | `fUnidades` ← `stg_unidades`, chave `PROP_FAZ = unaccent(proprietário‖fazenda)` | `fUnidades` ← `stg_customers`, chave `idpropfaz = idcustomer‖idfarm` | ok (mas fatos juntam por **nome** da fazenda) |
| Calendário | `dCalendar` 2024-07-01→hoje, safra jul–jun | idem (clonado) | ok |
| Estoque | `fMovGado` (aba `fMovRebanho`): Σ movimentações assinadas | `fSaldoGado`: snapshot `balanco-pecuario` + forward-fill | **lógicas diferentes** |
| Balanço entradas/saídas | medidas `Buy/Sell/Birth/Death/Weaning/Change Category` | quebradas (apontam p/ `fMovGado`) | **inexistente** |
| Rebanho médio | `fRebanhoMedio` por grupo (Bezerros/Jovens/Adultos), cab e UA digitados | `stg_rebanho_medio` por categoria; UA fixa em 0 | **UA ausente** |
| Área / lotação | `fArea` mensal (pasto, ILP, total) | áreas fixas **500 ha / 2911 ha** | **ausente** (API tem `utilizacao-pasto`) |
| Nascimentos | `pecuarioNascimento` | `stg_nascimentos` **sem relação de data** | filtro de período ignorado |
| Mortes | por `grupo_categoria` | por `namegroup` + lista fixa de 19 categorias | frágil |
| Compras | `VALOR TOTAL` | `Total Paid` soma **R$/cab** | **bug** |
| Vendas abate / em pé | 2 abas | 1 endpoint, separado por `deadarrobaavg IS NULL` | ok |
| Transferências | `fTransferencias` | não consumido | **ausente** |
| Desmame | só dentro de `fMovGado` | `pecuarioDesmame` carregada e não usada | **ausente** |
| DRE realizado | `fDre` (data pagamento) | `lancamento-financeiro` (ligado por **vencimento**, fazenda **fiscal**) | inconsistente |
| DRE planejado | abas `*PLANEJADO` | `previsao-financeiro` | `Revenues Forecast` sempre vazio |
| Planejado pecuário | 10 abas `*PLANEJADO` | 6 endpoints `*-mensal-planejamento` | **soma todas as versões do plano**; rebanho previsto = realizado |
| RLS | `RLS[e-mail] = USERNAME()` via planilha de acessos | **nenhum** | **ausente** |

### 1.2 Problemas que hoje distorcem números (não replicar)

| # | Problema | Onde | Correção na plataforma |
|---|---|---|---|
| P1 | Total do Previsto×Realizado subtrai `"E - OUTROS DÉBITOS"`, mas o SQL gera `"F - OUTROS DÉBITOS"` → dividendos/financiamentos fora do total | ambos | 1 tabela de classificação; total explícito (ver §11 decisão D1) |
| P2 | `Count of Selected Month` conta mês-do-ano (1–12) → médias infladas em seleções > 12 meses | ambos | nº de meses = `count(distinct ano-mês)` |
| P3 | "Acumulados" com janelas diferentes (ALL × ALLSELECTED × ano civil) → `% Mortality` divide janelas distintas | ambos | um único conceito: acumulado começa no início do período selecionado |
| P4 | 3 codificações diferentes da classificação DRE (`classificacao`, `Classificacao2`, `Classificacao`) e 2 de-paras de centro de custo divergentes (investimentos ora custeio, ora investimento) | ambos | `dim.centro_custo` única |
| P5 | Metas somam todas as versões de plano (`plVersionCode` não gravado em vendas/compras) | Metryx | `cenario` + `versao_plano` com versão oficial |
| P6 | `Total Paid` (compras) soma R$/cab | Metryx | `Σ valor_total` |
| P7 | `% Amount Saled` invertido; `Revenues Forecast` sempre vazio (literais sem espaço) | Metryx | fórmula única |
| P8 | Join de metas em vendas sem `retiro` pode **duplicar vendas** | planilha | metas não são mais "coladas" no fato |
| P9 | `planejadoXRealizado` pode multiplicar o realizado quando há metas de mesmo valor no mês | ambos | agregar meta e realizado **antes** do join (FULL OUTER) |
| P10 | Forecasts falsos (realizado × 1,1 / × 1,8), áreas fixas 2911/500 ha, "FAZENDA EXEMPLO" | ambos | removidos; constantes em tabela de parâmetros |
| P11 | Arroba com 3 convenções (carcaça/15, vivo/30, vivo/15) | Metryx | 2 convenções documentadas: carcaça÷15 (abate); vivo÷30 (em pé/compra/transf.) |
| P12 | Financeiro por vencimento × pagamento e fazenda fiscal × destino | Metryx | decisão D2 |
| P13 | `fMetasCompras` com `PROP_FAZ` não normalizado (metas podem não casar) | planilha | identidade por `fazenda_id` |
| P14 | Valores ≥ 1e9 escondidos por filtro no BI ("erro de escala na origem") — provável parsing de número com locale no Pentaho | Metryx | `Decimal` direto do JSON + flag de outlier |
| P15 | Calendário começa fixo em 2024-07-01 e termina "hoje" (metas futuras e histórico somem) | ambos | `dim.calendario` 2015–2035 |
| P16 | Bezerros mamando: cada mês vale o maior saldo do lote daquele mês em diante (lote que zera e volta aparece antes da hora) | Metryx | último saldo do lote no mês, como o inventário do Metryx (20/10/2026, validação §20) |
| P17 | Só "Consumo Abate" é consumo; "Consumo Acidente" e "Doação" contam como morte | Metryx | causas de consumo e doação como no Consolidado Pecuário do Metryx (20/10/2026, validação §20) |

### 1.3 Problemas operacionais e de segurança dos pipelines

| Pipeline | Problema | Evidência |
|---|---|---|
| Planilhas | Full reload de 230 arquivos (13,2 mi linhas Excel lidas p/ gravar 227 mil) 4×/dia | logs Pentaho |
| Planilhas | 1 célula ruim derruba o job inteiro; sucesso 62% (ago), 61% (set), 39% (out) | logs 05–12/10 |
| Planilhas | Leitura **posicional**; 16 variações de cabeçalho nos 230 arquivos; dado digitado na linha 1 é perdido | varredura |
| Planilhas | 5 fazendas com arquivo duplicado → fatos em dobro; 9 nomes em Unicode NFD | varredura |
| Planilhas | Trocar o PERÍODO (`CADASTROINICIAL!B8`) re-data área/rebanho médio e o reload **apaga o histórico** (78 arquivos já em SAFRA 26/27) | template |
| Metryx | Erros HTTP descartados (Dummy); 401/500 de um cliente **apaga os dados dele sem alerta**; se `/customers` falhar, tudo fica vazio | 20 de 22 KTRs |
| Metryx | TRUNCATE + commit a cada 1000 linhas → o BI pode ler tabela vazia/parcial | todos |
| Metryx | Tokens de cliente em texto puro em `stg_customers`; token mestre e 21 tokens em `.ktr`; endpoint `/customers` **fora do Swagger** | get_customer |
| Metryx | `get_transferencias` (órfã) trunca `stg_balanco_pecuario`; `get_vendas` grava JSON de todos os clientes em `Documents\teste.txt` | KTRs |
| Ambos | Senha do superusuário `postgres` e SMTP Gmail nos arquivos ("Encrypted" do Kettle é reversível) | KTRs/KJB |

### 1.4 Fatos importantes sobre a API Metryx (condicionam o adapter)

- **Nenhum endpoint aceita parâmetros** (sem período, fazenda ou paginação): cada chamada devolve o **histórico completo do
  cliente dono do token**. Incremental só do nosso lado (hash do payload + diff).
- Autenticação: header `x-auth-token` com JWT **sem expiração** e **sem endpoint de login/refresh**. Um token por cliente.
- Endpoints de valor ainda não usados: `transferencia-animal-pecuario`, `saldo-inical-pecuario` (grafia da API),
  `retiro`, `previsao-fluxo-caixa-planejamento`, `confina-tech`. Já extraídos mas ignorados pelo BI: `utilizacao-pasto`,
  `desmames-pecuario`, `desmame-mensal-planejamento`, `estoque-medio-mensal-planejamento`.
- `POST /control-birth` **escreve** no Metryx — fica fora da allow-list do adapter.

---

## 2. Arquitetura alvo

```
                        ┌──────────────────────── Fontes ────────────────────────┐
  Google Drive (.xlsm)  │  Relatórios/  Planejamento/  Financeiro/   + upload web │      API Metryx (token por cliente)
                        └───────────────┬────────────────────────────────────────┘                 │
                                        ▼                                                          ▼
                     ┌──────────────────────────────┐                        ┌──────────────────────────────┐
                     │  PlanilhaAdapter (openpyxl/   │                        │  MetryxAdapter (httpx+retry, │
                     │  calamine, aliases, template  │                        │  allow-list GET, landing raw │
                     │  fingerprint, hash/mtime)     │                        │  jsonb + sha256)             │
                     └───────────────┬──────────────┘                        └───────────────┬──────────────┘
                                     │  CanonicalBatch (mesmos modelos pydantic)               │
                                     └───────────────┬─────────────────────────────────────────┘
                                                     ▼
                      ┌───────────────────────────────────────────────────────────────┐
                      │ Pipeline comum: mapping (fazenda/categoria/centro de custo) → │
                      │ validação (issues/quarentena) → loader transacional (replace  │
                      │ por partição ou upsert) → recálculo de estoque/marts          │
                      └───────────────────────────────┬───────────────────────────────┘
                                                      ▼
   PostgreSQL 16:  core.* (cliente, fazenda, usuário, acesso)  dim.* (categoria, centro de custo, calendário)
                   fato.* (mov_animal, rebanho_medio, area, lançamento, orçamento)  mart.* (agregados mensais)
                   ingest.* / raw.* (jobs, arquivos, payloads, issues)   compat.* (views stg_* p/ o PBIX na transição)
                   RLS em todas as tabelas de negócio (app_user NOSUPERUSER NOBYPASSRLS)
                                                      ▼
                      ┌───────────────────────────────────────────────────────────────┐
                      │ FastAPI  /api/v1 — auth JWT, contexto RLS por transação,      │
                      │ camada de KPIs (registro único de métricas), dashboards,      │
                      │ ETL (jobs/wizard de upload), admin, exportação xlsx/pdf       │
                      └───────────────────────────────┬───────────────────────────────┘
                                                      ▼
                      React 19 + TS + Vite — Hub, filtros globais (cliente/fazendas/sistema/civil-safra/período),
                      páginas do boletim, importações & qualidade de dados, cadastros, admin
   Celery worker + beat (Redis) · MinIO (uploads) · tudo em docker-compose (api, worker, beat, db, redis, minio, nginx)
```

Princípio central: **o painel não sabe de onde o dado veio**. Toda diferença de fonte é resolvida no adapter + mapping;
a coluna `fonte` existe só para auditoria/qualidade.

---

## 3. Modelo de dados canônico

### 3.1 Schemas

| Schema | Conteúdo |
|---|---|
| `core` | `tenant` (organização — mantém o padrão AgTechLab e permite vender a outras consultorias), `cliente`, `fazenda`, `retiro`, `usuario`, `usuario_fazenda`, `fonte_vinculo` (de-para id externo → id interno), `fazenda_fonte` (fonte por domínio) |
| `dim` | `categoria_bi` (15), `categoria_map` (origem → BI), `centro_custo`, `subcentro`, `plano_contas_map`, `calendario`, `versao_plano`, `parametro` |
| `fato` | `mov_animal`, `rebanho_medio_mensal`, `area_mensal`, `lancamento_financeiro`, `orcamento_financeiro`, `estoque_mensal` (derivado), `balanco_snapshot` (Metryx, p/ reconciliação) |
| `mart` | agregados mensais por fazenda (tabelas com RLS, recalculadas pelo pipeline) para os dashboards |
| `ingest` / `raw` | `job`, `source_file`, `file_version`, `template_version`, `issue`, `quarantine_row`, `raw.metryx_payload`, `sync_run(_item)` |
| `integracao` | `metryx_credencial` (token cifrado, write-only), `metryx_entitlement` |
| `compat` | views com os nomes/colunas atuais `stg_*` para o PBIX continuar funcionando durante a transição |
| `app` | funções de contexto do RLS (`app.usuario_id()`, `app.tenant_id()`, `app.eh_admin()`, `app.fazendas_visiveis()`) |

### 3.2 Identidade (o ponto mais importante)

- **`core.fazenda`** é a unidade de análise (equivale a `PROP_FAZ`/`idpropfaz`): `id uuid`, `cliente_id`, `nome`,
  `proprietario` (atributo, **nunca chave**), `sistema_produtivo` (CRIA | RECRIA E ENGORDA | CICLO COMPLETO),
  `tipo_ano` (CIVIL | SAFRA), `ativo`.
- **`core.fonte_vinculo(fonte, entidade, id_externo, entidade_id)`** resolve a identidade por fonte:
  - planilha: `id_externo = codigo_cliente|fazenda_norm|retiro_norm` (código lido de `fUnidade!D2` e conferido com o nome do arquivo);
  - Metryx: `id_externo = idCustomer|idFarm` (e `idRetiro`, `idCategory`).
  Nada é casado por nome cru (hoje o BI Metryx junta vendas/compras/financeiro por `farmname`).
- **`core.fazenda_fonte(fazenda_id, dominio, fonte)`** com `dominio ∈ {pecuario_realizado, pecuario_planejado,
  financeiro_realizado, financeiro_planejado, area, rebanho_medio}` — resolve os clientes híbridos e impede dupla contagem
  (o loader rejeita linhas de uma fonte que não é a fonte ativa daquele domínio para aquela fazenda).
- `prop_faz_legacy` exposto apenas nas views `compat.*`.

### 3.3 Categorias animais (o 2º ponto mais importante)

- `dim.categoria_bi`: as 15 categorias da aba `dCategorias` (idêntica nos 230 arquivos) com `sexo`, `grupo`
  (BEZERROS/JOVENS/ADULTOS), `era` (00-08, 08-12, 13-24, 25-36, +36) e `peso_ref_kg` (para UA estimada, ver D5).
- `dim.categoria_map(fazenda_id|cliente_id, fonte, categoria_origem, categoria_bi_id, confirmado_por, confirmado_em)`:
  - planilha: carregado de `CADASTROINICIAL!A11:B74` (o próprio consultor já faz esse de-para hoje);
  - Metryx: sugestão automática a partir de `categoria` (`gender` + `agecategory` + `categorygroup`), **confirmada pelo
    consultor numa tela de mapeamento**. Categoria sem mapeamento → linha em quarentena + alerta (substitui a lista fixa de
    19 nomes de bezerro do BI Metryx).

### 3.4 Fatos

| Fato | Grão | Planilha (aba) | Metryx (endpoint) | Observações |
|---|---|---|---|---|
| `fato.mov_animal` | lançamento | `fCompras`, `fAbate`, `fVendaemPe`, `fMortes`, `fNascimento`, `ftranfentrada`, `ftranssaida`, `fconsumodoacao`, `fmudcategoria`, `fdesmame`, `CADASTROINICIAL!F` (saldo inicial) + todas as `*PLANEJADO` | `compra-`, `venda-`, `morte-`, `nascimento-`, `desmames-`, `mudanca-categoria-`, `transferencia-animal-`, `saldo-inical-pecuario` + `*-mensal-planejamento` | `tipo` ∈ {SALDO_INICIAL, COMPRA, NASCIMENTO, TRANSF_ENTRADA, ABATE, VENDA_EM_PE, MORTE, CONSUMO_DOACAO, TRANSF_SAIDA, DESMAME, MUDANCA_CATEGORIA}; `cenario` ∈ {realizado, planejado}; `versao_plano_id`; `categoria_bi_id` + `categoria_destino_bi_id` (desmame/mudança) |
| `fato.estoque_mensal` | fazenda × categoria × mês × cenário | (derivado) | (derivado) | saldo inicial + Σ movimentos assinados; entradas/saídas por tipo → **balanço de rebanho** para as duas fontes. Substitui `fMovRebanho` (100% fórmula) e `fSaldoGado` |
| `fato.balanco_snapshot` | fazenda × categoria × data | — | `balanco-pecuario` | só para reconciliação com `estoque_mensal` (check de qualidade) |
| `fato.rebanho_medio_mensal` | fazenda × grupo (× categoria) × mês × cenário | `fRebanhoMedio(+PLANEJADO)` (cab, UA) | `rebanho-medio-pecuario` (cab, `weight`→UA) e `estoque-medio-mensal-planejamento` | `ua_fonte` ∈ {informada, calculada_peso, estimada_categoria} |
| `fato.area_mensal` | fazenda × mês × cenário | `fArea(+PLANEJADO)` | `utilizacao-pasto` | pasto, ILP, total, produtiva |
| `fato.lancamento_financeiro` | lançamento/pagamento | `fDre` | `lancamento-financeiro` | `data_pagamento`, `data_vencimento`, `operacao` C/D, `valor` (> 0), `centro_custo_id`, `subcentro_id`, `fazenda_id` (+ `fazenda_fiscal_id` Metryx) |
| `fato.orcamento_financeiro` | competência × centro × versão | `fDrePLANEJADO` | `previsao-financeiro` (+ `previsao-fluxo-caixa-planejamento`) | por versão de plano |

Colunas técnicas em **todos** os fatos: `tenant_id`, `fazenda_id`, `fonte`, `origem_ref` (file_version_id ou payload_id),
`origem_linha`/`row_hash`, `ingest_job_id`, `carregado_em`, `extra jsonb` (campos da origem não mapeados — nada se perde).

### 3.5 DDL essencial (trecho)

```sql
CREATE TABLE fato.mov_animal (
  id                     bigserial PRIMARY KEY,
  tenant_id              uuid NOT NULL REFERENCES core.tenant(id),
  fazenda_id             uuid NOT NULL REFERENCES core.fazenda(id),
  retiro_id              uuid REFERENCES core.retiro(id),
  cenario                text NOT NULL CHECK (cenario IN ('realizado','planejado')),
  versao_plano_id        uuid REFERENCES dim.versao_plano(id),           -- NULL no realizado
  tipo                   text NOT NULL CHECK (tipo IN ('SALDO_INICIAL','COMPRA','NASCIMENTO','TRANSF_ENTRADA',
                           'ABATE','VENDA_EM_PE','MORTE','CONSUMO_DOACAO','TRANSF_SAIDA','DESMAME','MUDANCA_CATEGORIA')),
  data                   date NOT NULL,
  competencia            date GENERATED ALWAYS AS (date_trunc('month', data::timestamp)::date) STORED,  -- cast p/ timestamp: mantém a expressão IMMUTABLE
  categoria_origem       text,                                           -- texto original (CATEG_FAZENDA / category)
  categoria_bi_id        smallint NOT NULL REFERENCES dim.categoria_bi(id),
  categoria_destino_bi_id smallint REFERENCES dim.categoria_bi(id),      -- desmame / mudança de categoria
  qtd                    numeric(12,2) NOT NULL CHECK (qtd >= 0),
  peso_vivo_medio_kg     numeric(10,2),
  peso_total_kg          numeric(14,2),
  rendimento_carcaca     numeric(6,4),                                   -- fração 0–1
  arroba_carcaca_cab     numeric(10,4),                                  -- abate
  valor_total            numeric(16,2),
  contraparte            text,                                           -- frigorífico/comprador/fornecedor/destino
  documento text, causa text, local text, era text, safra text,
  fonte                  text NOT NULL CHECK (fonte IN ('planilha','metryx','manual')),
  origem_ref             bigint NOT NULL, origem_linha text NOT NULL,    -- file_version/payload + linha/row_hash
  extra                  jsonb, ingest_job_id uuid, carregado_em timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON fato.mov_animal (fazenda_id, cenario, tipo, data);

-- sinal no estoque (uma regra, numa função; espelha CADASTROINICIAL!L22 e fMovGado[QTD C])
CREATE FUNCTION dim.sinal_estoque(tipo text) RETURNS smallint IMMUTABLE LANGUAGE sql AS $$
  SELECT CASE WHEN tipo IN ('SALDO_INICIAL','COMPRA','NASCIMENTO','TRANSF_ENTRADA') THEN 1
              WHEN tipo IN ('ABATE','VENDA_EM_PE','MORTE','CONSUMO_DOACAO','TRANSF_SAIDA') THEN -1
              ELSE 0 END $$;   -- DESMAME/MUDANCA: -qtd na origem, +qtd no destino (tratado na view de estoque)

CREATE TABLE dim.centro_custo (
  id smallserial PRIMARY KEY,
  nome text UNIQUE NOT NULL,                       -- taxonomia Metryx (já usada pelas planilhas)
  classificacao text NOT NULL,                     -- A-RECEITAS | C-INVESTIMENTOS | D-CUSTEIO | E-OUTROS CRÉDITOS | F-OUTROS DÉBITOS | NEUTRO
  entra_desembolso boolean NOT NULL,               -- DCM
  entra_custeio    boolean NOT NULL,               -- CCM
  tipo_custeio text,                               -- CF | CV | RECEITA_PEC | RECEITA_AGR | RECEITA_OUTRAS | FINANCIAMENTO | APORTE
  eh_reposicao boolean NOT NULL DEFAULT false      -- REP.
);
```

---

## 4. Adapters

### 4.1 Contrato comum

```python
class SourceAdapter(Protocol):
    fonte: Literal["planilha", "metryx"]
    def discover(self, ctx: JobContext) -> list[SourceUnit]: ...          # arquivos alterados / (tenant × endpoint)
    def extract(self, unit: SourceUnit) -> RawBatch: ...                  # bytes/JSON + hash; nunca escreve na origem
    def normalize(self, raw: RawBatch, maps: Mappings) -> CanonicalBatch: ...  # linhas canônicas + issues
```

`CanonicalBatch` contém listas de modelos pydantic (`MovAnimal`, `RebanhoMedio`, `AreaMensal`, `Lancamento`,
`Orcamento`, `Fazenda`, `CategoriaOrigem`, …) + `issues` + a **chave de partição** a substituir. O mesmo `loader`,
as mesmas validações e o mesmo recálculo de estoque servem às duas fontes.

### 4.2 Adapter de planilhas (spec completa no relatório 03 §8)

- **Descoberta**: pasta do Drive (preferir **Google Drive API** com service account → dispensa rclone e permite rodar fora
  do servidor Windows) **e** upload pela web (wizard em 4 passos do AgTechLab: upload → pré-visualização → confirmação →
  job). Normalização NFC do nome; regex `^RELAT[ÓO]RIOS?\s*[-_]\s*(\d+)\s*[-_]\s*(.+?)\s*\.xlsm$`.
- **Incremental**: (size, mtime) → SHA-256 → só processa arquivo alterado (hoje > 50% dos arquivos não mudam entre execuções).
- **Leitura por nome de cabeçalho com aliases** (padrão `_ALIASES` do decoder do AgTechLab), fingerprint de template,
  fallback posicional com aviso. Abrir o arquivo uma vez só (hoje são 23 aberturas por arquivo).
- **Recalcular derivados** (peso médio, R$/kg, R$/@, peso carcaça) em Python e comparar com o cache das fórmulas;
  `fMovRebanho` deixa de ser lida — o estoque é recalculado a partir dos lançamentos + saldo inicial.
- **Validação com quarentena**: ~15 códigos (`CATEGORY_UNMAPPED`, `ACCOUNT_UNMAPPED`, `DATE_FROM_TEXT`, `HEADER_ROW_HAS_DATA`,
  `DUPLICATE_UNIT_FILE`, `PERIOD_CHANGED`…). Erro de linha → quarentena; erro de arquivo → mantém a versão anterior.
  **Um arquivo nunca derruba o lote.**
- **Gravação**: lançamentos = substituição atômica por (fazenda, cenário, tipo) da versão do arquivo; mensais (área,
  rebanho médio) = upsert por (fazenda, cenário, grupo, competência) — **trocar o PERÍODO não apaga mais o histórico**.
- Também incorpora as abas que hoje só entram agregadas (`fconsumodoacao`, `fmudcategoria`, `fdesmame`) como lançamentos.

### 4.3 Adapter Metryx (spec completa no relatório 04 §8)

- `httpx` + `tenacity` (retry em 429/5xx/timeout; sem retry em 401/403/404), semáforo + rate limit, allow-list de GETs.
- **Landing bruto**: `raw.metryx_payload (jsonb + sha256)` antes de normalizar → *replay* sem chamar a API.
- **Snapshot + diff**: payload com mesmo hash = nada a fazer; senão substituição atômica por (tenant, endpoint[, versão]).
- **Guarda de volume**: snapshot vazio ou queda > 50% → `held` + alerta, não apaga dados bons (hoje um 401 zera o cliente).
- **Credenciais**: token por cliente **cifrado** (`integracao.metryx_credencial`), cadastrado pela UI em campo write-only,
  validação diária via `GET /fazenda`, conferência `idCustomer` do payload × credencial.
- `Decimal` direto do JSON (resolve os valores 1e16 escondidos no BI); `farm_id` sempre por `idFarm`; `plVersionCode` sempre gravado.
- Prioridade de endpoints novos: `transferencia-animal-pecuario`, `saldo-inical-pecuario`, `retiro`,
  `utilizacao-pasto` (modelar), `previsao-fluxo-caixa-planejamento`.

### 4.4 Pipeline, jobs e agendamento

- Tabela `ingest.job` no padrão AgTechLab (status `pendente → processando → concluido | concluido_com_avisos | erro`,
  `detalhe jsonb` com alertas estruturados), endpoint `POST` cria o job, `GET /status/{id}`.
- `pg_advisory_xact_lock` por (fonte, fazenda/tenant) — duas cargas da mesma fazenda nunca se atropelam.
- Celery beat: planilhas a cada 30 min (só arquivos alterados); Metryx 2×/dia + botão "sincronizar agora".
- Após cada carga: recálculo de `fato.estoque_mensal` e `mart.*` **só das fazendas afetadas**.
- Notificação consolidada por execução (e-mail de serviço/Teams), não 11 e-mails por job com conta pessoal.
- Tela **"Saúde dos dados"**: última carga por fazenda, issues, quarentena, divergências de reconciliação.

---

## 5. RLS por usuário (corrigindo o padrão AgTechLab)

O AgTechLab tem a *forma* certa (GUC + `current_setting(...,true)` + migração `rls_*` + ENABLE/FORCE), mas não protege
nada: o app conecta como **superusuário** (ignora RLS), o `SET` é de sessão (vaza pelo pool), as políticas cobrem só
SELECT/INSERT e o vínculo usuário→fazenda existe só no front. Proposta:

```sql
CREATE ROLE app_owner NOLOGIN;                         -- dono das tabelas (Alembic)
CREATE ROLE app_user  LOGIN NOSUPERUSER NOBYPASSRLS;   -- API
CREATE ROLE app_etl   LOGIN NOSUPERUSER NOBYPASSRLS;   -- workers (contexto de serviço por tenant)

CREATE TABLE core.usuario_fazenda (
  usuario_id uuid REFERENCES core.usuario(id) ON DELETE CASCADE,
  fazenda_id uuid REFERENCES core.fazenda(id) ON DELETE CASCADE,
  papel      text NOT NULL CHECK (papel IN ('cliente','tecnico','gerente','regional')),
  PRIMARY KEY (usuario_id, fazenda_id));
-- (opcional) core.usuario_cliente para conceder todas as fazendas de um cliente, inclusive as futuras

CREATE FUNCTION app.fazendas_visiveis() RETURNS uuid[] STABLE SECURITY DEFINER LANGUAGE sql AS $$
  SELECT CASE WHEN app.eh_admin() THEN NULL
         ELSE array(SELECT fazenda_id FROM core.usuario_fazenda WHERE usuario_id = app.usuario_id()) END $$;

ALTER TABLE fato.mov_animal ENABLE ROW LEVEL SECURITY;
ALTER TABLE fato.mov_animal FORCE  ROW LEVEL SECURITY;
CREATE POLICY acesso ON fato.mov_animal FOR ALL TO app_user
  USING      (tenant_id = app.tenant_id() AND (app.eh_admin() OR fazenda_id = ANY(app.fazendas_visiveis())))
  WITH CHECK (tenant_id = app.tenant_id() AND app.eh_admin());          -- usuário comum não grava fato
CREATE POLICY etl ON fato.mov_animal FOR ALL TO app_etl
  USING (tenant_id = app.tenant_id()) WITH CHECK (tenant_id = app.tenant_id());
```

```python
# db/session.py — contexto POR TRANSAÇÃO, aplicado num único lugar (nunca SET de sessão)
@event.listens_for(SessionLocal, "after_begin")
def _contexto_rls(session, transaction, connection):
    ctx = session.info.get("rls")
    if ctx:
        connection.execute(text("SELECT set_config('app.tenant_id', :t, true), set_config('app.usuario_id', :u, true),"
                                " set_config('app.eh_admin', :a, true)"),
                           {"t": str(ctx.tenant_id), "u": str(ctx.usuario_id), "a": "true" if ctx.eh_admin else "false"})
```

Pontos de atenção:
- **Views materializadas não respeitam RLS** → `mart.*` são **tabelas** (com política) recalculadas pelo pipeline;
  views comuns com `security_invoker = true`.
- Login via função `SECURITY DEFINER` (`app.autenticar(email)`), nunca "rodar como superusuário".
- Papéis checados no servidor (`exige_papel('admin')`); rotas de criação de usuário só para admin.
- Seed dos acessos a partir de `Levantamento Clientes para Power BI.xlsx` (297 linhas; e-mails de técnico/gerente/regional,
  com trim — 54 têm espaço sobrando) + e-mails de cliente.
- **Teste automatizado obrigatório**: conectar como `app_user`, setar usuário A e provar que linhas da fazenda de B são
  invisíveis e não-graváveis.

---

## 6. Camada de KPIs (substitui as ~450 medidas DAX)

### 6.1 Semântica única de tempo e filtros

Todo KPI recebe o mesmo contexto: `fazendas[]` (já ∩ RLS), `sistema_produtivo?`, `modo` (civil | safra jul–jun),
`inicio`, `fim` (meses), `granularidade` (`periodo` | `mes`), filtros de recorte (`sexo`, `grupo`, `categoria`, `tipo_venda`)
e `cenario` (realizado | planejado | ambos → devolve realizado, planejado, % atingido, variação).

- **Acumulado** = sempre a partir de `inicio` (no modo safra, desde jul do ano-safra inicial). Um único conceito (corrige P3).
- **Nº de meses** = `count(distinct ano-mês)` do período (corrige P2); para médias de estoque/área, meses com dado > 0.
- **Planejado** = versão oficial (`dim.versao_plano.oficial`) por fazenda (corrige P5).

### 6.2 Parâmetros (tabela `dim.parametro`, editáveis pelo admin)

`kg_carcaca_por_arroba = 15` · `kg_vivo_por_arroba = 30` · `kg_por_ua = 450` · `semaforo_limiar = 0,03` ·
`multiplicador_gauge_preco = 1,15` · `multiplicador_gauge_desembolso = 1,2` · cidade do boletim ("Cuiabá").

### 6.3 Catálogo unificado (fórmula corrigida → medidas DAX de origem)

Implementado como **registro declarativo** (`app/kpis/registry.py`): cada KPI = id, rótulo, unidade, SQL sobre as views
canônicas, dependências, formatação, regra de semáforo. O mesmo registro alimenta cards, séries mensais e exportações.

| Domínio | KPI | Fórmula canônica | Substitui (DAX) |
|---|---|---|---|
| Rebanho | Estoque final (cab) | Σ estoque_mensal até `fim` (por categoria) | `Stock Accumulated Final`, `Saldo Acumulado` |
| | Estoque inicial | Σ até antes de `inicio` | `Stock Accumulated Inicial` |
| | Balanço (entradas/saídas por tipo) | Σ qtd por `tipo` no período (desmame/mudança se anulam no total) | `Buy/Sell/Birth/Death/Weaning*/Change Category*` |
| | Rebanho médio (cab) | Σ qtd_cab mensal ÷ nº meses | `Mean Month` |
| | Rebanho médio (UA) | Σ qtd_ua mensal ÷ nº meses | `UA Median Month` (Metryx: fixo 0) |
| | Área média (ha) | Σ area_total ÷ nº meses com área | (implícito) |
| | Lotação cab/ha · UA/ha | rebanho médio ÷ área média | `Mean Month Ha`, `UA Median Ha` (sem 500/2911 fixos) |
| Nascimentos | Nascimentos · % machos · % fêmeas | Σ qtd; Σ por sexo ÷ total | `Birth Quantity`, `IN - % Male/Female Birth` |
| | Peso médio ao nascer | Σ(qtd × peso) ÷ Σ qtd | `Average Birth Weight` (corrigido) |
| Mortes | Mortes (total/grupo/causa) | Σ qtd | `Dead Quantity*` |
| | Mortalidade s/ rebanho médio | mortes ÷ rebanho médio (mesmo grupo, mesma janela) | `% mORTALITY ( MEAN MONTH)` |
| | Mortalidade de bezerros s/ nascimentos | mortes BEZERROS ÷ nascimentos (mesma janela) | `% Mortality` (corrigido P3) |
| Compras | Cabeças · valor total | Σ qtd; Σ valor_total | `Purchased Quantity`, `Total Paid` (corrige P6) |
| | Preço da @ compra · R$/kg · peso médio | Σ valor ÷ (Σ kg vivo ÷ 30); Σ valor ÷ Σ kg; Σ kg ÷ Σ cab | `@ AVG Price Purchase`, `AVG Purchase Price KG`, `IN AVG - Peso Médio de Compra` |
| | Ágio | (preço @ compra − preço @ venda) ÷ preço @ venda | `Ágio` |
| Venda abate | Cabeças · faturamento | Σ qtd; Σ valor_total | `Amount Saled (Abate)`, `Invoicing (Abate)` |
| | Preço @ carcaça · rendimento · peso vivo médio | Σ fat ÷ Σ(@ carcaça); Σ kg carcaça ÷ Σ kg vivo; Σ kg vivo ÷ Σ cab | `AVG Price @ Dead Sale`, `Rendimento Carcaça`, `IN - AVG Live Weight` |
| Venda em pé | Cabeças · faturamento · preço @ (vivo÷30) · R$/kg · peso médio | idem com @ = kg vivo ÷ 30 | `* Em Pe *` |
| Vendas total | Cabeças · faturamento · preço @ ponderado · @/cab | (fat_ab + fat_ep) ÷ (kg carc_ab/15 + kg vivo_ep/30) | `Amount Saled`, `Invoicing`, `AVG Price @ (Em Pe + Abate)`, `Peso em @` |
| Transferências | Entrada/saída cab · peso médio · R$/@ | Σ por tipo; Σ kg ÷ Σ cab; Σ valor ÷ (Σ kg ÷ 30) | `IN - Incoming/Outgoing Transfer`, `IN QTD Transfer`, `IN - AVG *Transfer*` |
| Financeiro | Receitas operacionais · receitas totais | Σ C com tipo RECEITA_PEC/AGR; + RECEITA_OUTRAS | `Revenues`, `All Revenues` |
| | Despesas · saldo de caixa | Σ D; receitas totais − despesas (barras e linha com a **mesma** base) | `Expenses Graph`, `Balance` |
| | Desembolso (DCM) · custeio (CCM) | Σ por flag de `dim.centro_custo` (respeitando C/D) | `Outlay`, `Costing` |
| | Desembolso/cab/mês · custeio/cab/mês | valor do período ÷ Σ rebanhos mensais | `head outlay *`, `Costing head *` |
| DRE P×R | Realizado, planejado, var% e semáforo por classificação/centro (mês e acumulado) | FULL OUTER JOIN de agregados mensais; total = decisão D1 | `Valor/Meta Último Mês Selecionado`, `Value/Meta Accumulated`, `Icon*` |
| Todos | % atingido · variação | realizado ÷ planejado; (realizado − planejado) ÷ planejado | `% … x Forecast`, `% Variação*` |

### 6.4 KPIs novos (não existem em nenhum dos BIs — padrão de consultoria pecuária)

| KPI | Fórmula proposta (validar — D4) | Dados |
|---|---|---|
| Taxa de natalidade | nascimentos da estação ÷ matrizes expostas (média de MATRIZES [+ NOVILHAS 25-36]) | já existem |
| Taxa de desmame | desmamados ÷ nascidos (mesma safra) · peso médio à desmama | `fdesmame` / `desmames-pecuario` |
| Taxa de desfrute | (abate + venda em pé + consumo − compras) ÷ rebanho médio | já existem |
| Idade/peso médio ao abate | ponderado por cabeças (`era`, `peso_vivo`) | já existem |
| Reconciliação de estoque | estoque calculado × balanço Metryx × saldo informado | qualidade |
| GMD | só com pesagens (não há na API nem na planilha hoje) | futuro |

---

## 7. API (FastAPI, `/api/v1`)

| Grupo | Rotas |
|---|---|
| Auth | `POST /auth/login` → `{token, usuario}` · `GET /auth/me` · (refresh/expiração curta) |
| Escopo | `GET /escopo` → clientes, fazendas visíveis (já filtradas por RLS), sistemas, períodos disponíveis |
| Dashboards | `GET /dashboards/{pagina}?fazendas=&sistema=&modo=&inicio=&fim=&sexo=` — 1 chamada devolve todos os cards + séries da página (backend agrega; o front só formata — padrão do Painel do Fly) |
| KPIs | `GET /kpis?ids=…&<contexto>` e `GET /kpis/{id}/serie?granularidade=mes` (genérico, p/ montar telas novas) |
| ETL | `POST /etl/planilhas/upload` → `GET /etl/jobs/{id}/preview` → `POST /etl/jobs/{id}/confirmar` · `POST /etl/sync {fonte, fazendas?}` · `GET /etl/jobs[/{id}]` · `GET /qualidade/issues` |
| Cadastros/Admin | `/clientes`, `/fazendas`, `/usuarios`, `/acessos`, `/mapeamentos/categorias`, `/mapeamentos/centros-custo`, `/parametros`, `/integracoes/metryx/credenciais` (token write-only) |
| Exportação | `GET /export/{pagina}.xlsx` · `GET /boletim.pdf` (capa + páginas — substitui o "Boletim Mensal" do PBIX) |

Tipos do front gerados do OpenAPI (`openapi-typescript`) para não repetir o desalinhamento front×back do AgTechLab.

---

## 8. Frontend (React 19 + TS strict + Vite)

Telas (as páginas dos PBIX viram rotas; os cards GERAL/MACHO/FÊMEA e BEZERROS/JOVENS/ADULTOS viram componentes
parametrizados por recorte, em vez de dezenas de "cards-rótulo"):

| Módulo | Telas |
|---|---|
| `boletim` | Visão geral (Movimentação do Gado + balanço) · Venda Abate · Venda em Pé · Compras · Nascimentos · Mortes · Transferências · **Desmame** (novo) · Financeiro · Previsto × Realizado (matriz hierárquica com semáforo) · Capa/Exportar |
| `dados` | Importações (wizard de upload, histórico de jobs) · Saúde dos dados (última carga por fazenda, quarentena, reconciliação) |
| `cadastros` | Clientes, fazendas, retiros (`EntityCrudPage` por configuração, como no AgTechLab) |
| `admin` | Usuários e acessos · Mapeamento de categorias (Metryx → 15 categorias BI) · Centros de custo · Parâmetros · Credenciais Metryx |

Filtros globais (provider de escopo no padrão `EscopoUnidadeProvider`, mas incluindo período — o AgTechLab deixa
safra/período local por página): **cliente → fazendas[]**, **sistema produtivo**, **modo civil/safra**, **ano/safra + meses**;
persistidos em `localStorage` **e na URL** (link compartilhável de um boletim). Cascata explícita de estados
vazio/erro/parcial (`AvisoDadosParciais`). Gráficos Recharts com tokens CSS; gauges como componente próprio.

---

## 9. Estrutura de pastas (espelhando o AgTechLab, já corrigida)

```
projeto-terra/
├── docker-compose.yml            # db (postgres 16), redis, minio, api, worker, beat, web (nginx)
├── backend/
│   ├── pyproject.toml            # TODAS as deps pinadas
│   ├── alembic.ini · alembic/versions/   # create_<tabela> seguido de rls_<tabela>; seeds (categorias, centros, calendário)
│   ├── tests/                    # unit (adapters, kpis) + integração com Postgres real (RLS, paridade)
│   └── app/
│       ├── main.py               # FastAPI, /api/v1, /health, CORS, handlers, logging
│       ├── api/v1/router.py · api/v1/endpoints/{auth,escopo,dashboards,kpis,etl,qualidade,cadastros,admin,export}.py
│       ├── api/deps.py           # get_db_autenticado (JWT → contexto RLS), exige_papel()
│       ├── core/{config,security,logging}.py
│       ├── db/{session,base}.py  # listener after_begin com set_config(..., true); mixins Tenant/Timestamp
│       ├── models/  schemas/  repositories/  services/
│       ├── kpis/                 # registry.py (catálogo), contexto.py (tempo/filtros), sql/*.sql, semaforo.py
│       ├── etl/
│       │   ├── adapters/base.py              # SourceAdapter (Protocol)
│       │   ├── adapters/planilha/            # discovery.py (Drive API/upload), reader.py, aliases.py, template_v1.yaml, normalize/
│       │   ├── adapters/metryx/              # client.py, credentials.py, endpoints.py, dto.py, normalize/
│       │   ├── canonical.py · mapping.py · quality.py · loaders.py · pipeline.py · estoque.py
│       │   └── compat_views.sql              # views stg_* para o PBIX na transição
│       ├── tasks/{celery_app,etl_tasks}.py
│       └── storage.py            # MinIO
└── frontend/
    ├── vite.config.ts · tsconfig.json ("strict": true) · oxlint
    └── src/
        ├── main.tsx · App.tsx · index.css (tokens)
        ├── pages/{LoginPage,HubPage}.tsx
        ├── core/{moduleRegistry.ts, api/{sessao,http,tipos.gerados}.ts, auth/, escopo/, ui/, relatorio/}
        └── modules/{boletim,dados,cadastros,admin}/{XxxModule,XxxShell,XxxContexto}.tsx + api.ts, hooks/, logic/, pages/, componentes/
```

---

## 10. Plano de execução

| Fase | Entregável | Critério de pronto |
|---|---|---|
| **0. Contenção (já)** | Rotacionar token mestre e tokens de cliente Metryx, senha `postgres`, SMTP; revogar `SELECT` em `stg_customers.token` para o usuário do BI; apagar `Documents\teste.txt` e remover o passo que o gera | nenhum segredo válido em arquivo/tabela legível |
| **1. Fundação** | Repos back/front, docker-compose, Alembic com `core/dim/fato/ingest`, papéis + RLS + testes de RLS, auth (`login`, `me`, papéis), seeds (15 categorias, centros de custo unificados, calendário, parâmetros) | teste "usuário A não vê fazenda B" passando |
| **2. Adapter de planilhas** | Ingestão incremental dos 230 arquivos, quarentena, tela de jobs; views `compat.stg_*` | **teste golden**: mesmas somas do Pentaho por (fazenda, mês, operação) — diferenças só nas documentadas (duplicatas, linha 1, histórico preservado) |
| **3. Adapter Metryx** | Credenciais cifradas, landing bruto, sync por tenant×endpoint, mapeamento de categorias (tela), endpoints novos | paridade diária com `stg_*` por 2–4 semanas em paralelo |
| **4. Camada de KPIs** | Registro de KPIs + `/dashboards/*` + `/kpis` | valores batem com os cards do PBIX nos casos sem bug; divergências = bugs P1–P15, documentadas |
| **5. Frontend** | Shell + filtros globais + páginas na ordem: Movimentação → Vendas → Compras → Nascimentos/Mortes → Transferências/Desmame → Financeiro → P×R → Capa/PDF | homologação com 2–3 consultores |
| **6. Corte** | Desligar os 2 jobs Pentaho e os 2 PBIX; KPIs novos (natalidade, desmame, desfrute) | 1 ciclo de boletim mensal emitido só pela plataforma |

As fases 2 e 3 podem andar em paralelo depois da 1. As views `compat.stg_*` permitem desligar o Pentaho **antes** do
front novo existir, sem mexer nos PBIX.

---

## 11. Decisões que dependem de você

| # | Decisão | Opções / minha recomendação |
|---|---|---|
| D1 | Total do Previsto×Realizado | Recomendo **Resultado = Receitas + Outros créditos − (Investimentos + Custeio + Outros débitos)**, exibindo "Desembolso" (= Investimentos + Custeio) como subtotal. Hoje outros débitos/créditos ficam fora por bug |
| D2 | Financeiro Metryx: data e fazenda | Recomendo **data de pagamento** (fluxo de caixa, igual à planilha) e **fazenda destino** (rateio gerencial), com fazenda fiscal disponível como filtro |
| D3 | Investimentos entram no custeio? | O de-para do BI Metryx diz que sim (CCM) para infraestrutura/outros animais/rebanho investimento; o P×R diz que são investimento. Recomendo **não** (custeio = CCM operacional) |
| D4 | Fórmulas de natalidade, desfrute e taxa de desmame | Validar as propostas do §6.4 com a equipe técnica |
| D5 | UA quando a planilha não informa | Recomendo calcular `Σ(cab × peso_ref_categoria) ÷ 450` marcado como "estimada", com peso de referência editável por categoria |
| D6 | Mapeamento de categorias Metryx → 15 categorias BI | Quem confirma (consultor responsável pela fazenda?) e se vale por cliente ou por fazenda |
| D7 | Versão oficial do planejamento Metryx | Consultor marca a versão oficial por fazenda/safra, ou usamos a mais recente |
| D8 | Onde roda e como lê o Drive | Recomendo servidor/VPS com Docker + **Google Drive API** (service account) em vez de rclone na máquina Windows |
| D9 | Duplicatas de arquivo (MARANGUAPE/MARANGUAPE1, ATTO SEMENTES./.., BHR/BHR - OK, MATER/MATER (1), GUARÁ 1×AZS) | Regra: vale o mais recente + override manual na tela de importações |
| D10 | Escopo de usuários | Clientes finais também acessam (cada um vê só as suas fazendas) ou só a equipe interna? Afeta login (convite por e-mail, SSO Google/Microsoft) |

---

## 12. Perguntas abertas para a Metryx

1. `GET /api-metryx/customers` (fora do Swagger) é suportado? Um cliente pode ter vários tokens?
2. Há parâmetros não documentados (período, `idFarm`, `updatedSince`, paginação) e rate limit?
3. Tokens expiram/podem ser revogados? Lista de permissões por endpoint (ex.: `UTILIZACAO_PASTO`)?
4. Formato oficial das datas (`date`, `month`, `birth`, `harvest`, `anoSafra`) e se os valores monetários `int64` são arredondados.
5. IDs estáveis para eventos pecuários (venda, compra, morte, nascimento, desmame, balanço)?
6. `balanco-pecuario` já inclui transferências e saldo inicial? Convenção de sinal de `amount`?
7. Como identificar a versão oficial/ativa do planejamento (`plVersionCode`)?
