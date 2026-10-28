# Projeto Terra: como duas estruturas diferentes viram um banco igual

> Complementa a [proposta](00_PROPOSTA_UNIFICACAO.md). Responde à pergunta: *"as estruturas são diferentes e os KPIs são
> calculados de forma diferente, embora entreguem o mesmo número; como garantir que o front seja transparente, que todo o
> tratamento fique no backend e que o banco seja o mais igual possível?"*
> Os campos da API foram conferidos no OpenAPI oficial e as colunas da planilha no template.

---

## 1. A ideia em uma frase

**A diferença entre as fontes morre no adapter.** Daí para frente existe uma só estrutura de tabelas, uma só fórmula por
KPI e um só contrato de API. Nenhum KPI, view, endpoint ou tela pode ter `if fonte == 'metryx'`. Se aparecer a necessidade
de um `if`, o que está faltando é uma coluna ou uma regra no modelo canônico, e é lá que se corrige, nunca na fórmula.

Hoje os dois BIs chegam ao mesmo número por **dois caminhos diferentes**. Por exemplo, no estoque o Ciclo soma as
movimentações desde sempre, enquanto o Metryx pega o último saldo do mês e repete esse saldo nos meses seguintes. Os dois
caminhos só concordam quando o dado concorda. Na plataforma existe **um caminho só**, e o que garante a igualdade é a
própria construção: a fórmula é a mesma e a entrada é a mesma grandeza física.

---

## 2. As camadas e onde fica cada tratamento

```
 FONTE            CAMADA 1: BRUTO         CAMADA 2: ADAPTER (Python)              CAMADA 3: CANÔNICO (Postgres)      CAMADA 4: KPI       FRONT
                  (fiel à origem)         normalize()                              IDÊNTICO p/ as 2 fontes           (1 fórmula)
 .xlsm  ──────►  ingest.file_version  ─►  tipos, datas, números pt-BR,         ─►  core.fazenda / dim.*          ─►  registry de   ─►  só formata
                  (hash, bytes no S3)      unidades → grandezas físicas TOTAIS,     fato.mov_animal                    KPIs + semântica
 API Metryx ──►  raw.metryx_payload   ─►  identidade (fazenda, categoria,          fato.inventario                    de tempo (SQL)
                  (jsonb + sha256)         centro de custo), natureza C/D,          fato.rebanho_medio_mensal
                                           tipo de evento, explode transferência    fato.area_mensal
                                           e desmame, valida → issues/quarentena    fato.lancamento_financeiro
                                                                                    fato.orcamento_financeiro
                                                                                    └► derivados em SQL: fato.estoque_mensal, mart.*
```

| Camada | Responsabilidade | Pode saber a fonte? |
|---|---|---|
| Bruto | guardar exatamente o que veio (replay sem reler o Drive ou chamar a API) | sim |
| Adapter | **toda** a conformação: parse, unidade, identidade, classificação de evento, validação | sim (é o único lugar) |
| Canônico | tabelas iguais, constraints, RLS, derivados (estoque, marts) em SQL | não (coluna `fonte` só para auditoria) |
| KPI | fórmula única + tempo (civil/safra, acumulado, nº de meses) + planejado×realizado | **não** |
| API / Front | contrato JSON / visual | **não** (usa "capacidades", §6) |

As camadas 1 e 3 vivem no **banco**. As camadas 2 e 4 vivem no **backend**. O front não calcula nada.

---

## 3. As 7 regras de conformação

1. **O banco guarda grandezas físicas e totais**: cabeças, kg vivo total, kg de carcaça total, R$ total, hectares e datas.
   Médias, preços, arrobas, percentuais e UA são sempre calculados na camada de KPI.
   *Por quê:* total soma e média não soma. E é aqui que nascem as divergências de hoje: a planilha guarda `PESO_VIVO` por
   cabeça e `PESOVIVO_TOTAL`, o Metryx guarda `liveWeightAVG` e `weightTotal`. Também é por isso que existem 3 convenções
   de arroba no BI Metryx (carcaça÷15, vivo÷30, vivo÷15). No canônico não existe coluna "arroba": a arroba é calculada a
   partir dos kg.
2. **Classificação vem da dimensão, nunca da fonte.** Grupo, era e sexo da categoria vêm de `dim.categoria_bi`.
   DCM, CCM, CF/CV e classificação do DRE vêm de `dim.centro_custo`. A planilha traz `DESEMBOLSO`, `CUSTEIO` e
   `GRUPO_CATEGORIA` já calculados por VLOOKUP, e o Metryx traz `nameGroup` e `groupCategory`. Esses valores **não** são
   usados como verdade: servem só para conferência (gerar issue quando divergem). Isso elimina as 3 codificações
   diferentes do DRE que existem hoje.
3. **Cada fato canônico usa o grão mínimo comum**: o grão que *todas* as fontes conseguem entregar.
   - Rebanho médio fica por **grupo × mês**. A planilha só tem grupo; o Metryx tem categoria e é agregado para grupo.
   - O planejado pecuário fica por **mês**. A planilha tem dia; o Metryx tem `MM/YY`.
   - O orçamento fica por **centro × mês**.
   O detalhe extra de uma fonte vai para `extra jsonb` ou para uma tabela de detalhe que nenhum KPI comum usa.
4. **Identidade por id, nunca por nome.** Toda linha canônica tem `fazenda_id` e `categoria_bi_id`, resolvidos pelos
   de-paras `core.fonte_vinculo` e `dim.categoria_map`.
5. **Estoque = checkpoints + fluxos.** A estrutura é a mesma para as duas fontes; só muda a quantidade de checkpoints (§5.1).
6. **O que só uma fonte tem vira "capacidade", não "fonte".** O front pergunta "esta fazenda tem área?" e nunca "esta
   fazenda é Metryx?" (§6).
7. **A equivalência é testada em CI, não presumida.** A mesma fazenda sintética é escrita como `.xlsm` e como JSON do
   Metryx. Os dois adapters precisam gerar o mesmo canônico e os mesmos KPIs (§7).

---

## 4. Matriz de conformação: planilha → canônico ← Metryx

Legenda: `→` regra de conversão aplicada no adapter. Colunas que são **fórmula** na planilha (valor em cache) não entram
no canônico. Elas servem só para checagem cruzada (issue `CACHE_MISMATCH`).

### 4.1 `fato.mov_animal` (realizado e planejado; 1 linha por lançamento)

Colunas canônicas: `fazenda_id, retiro_id, cenario, versao_plano_id, tipo, data, competencia, categoria_bi_id,
categoria_destino_bi_id, qtd, peso_vivo_total_kg, peso_carcaca_total_kg, valor_total, contraparte, causa, local, documento,
fonte, origem_ref, origem_linha, extra`.

| Tipo canônico | Planilha (aba → colunas de entrada) | Metryx (endpoint → campos) |
|---|---|---|
| `COMPRA` | `fCompras`: QTD→qtd · TOTAL_PESO→peso_vivo_total_kg · VALOR TOTAL→valor_total · ORIGEM→contraparte. *Planejado* (`fComprasPLANEJADO`): PESO_VIVO e VALOR_CAB são entrada → `peso_vivo_total = PESO_VIVO×QTD`, `valor_total = VALOR_CAB×QTD` se o total estiver vazio | `compra-pecuario`: amount→qtd · weightTotal→peso_vivo_total_kg (⚠ validar se é total ou por cabeça; o BI atual usa dos dois jeitos. Regra: se `weightTotal/amount` estiver entre 100 e 900, é total; senão issue) · totalFaturamento→valor_total (validar `additions`/`discounts`) · provider→contraparte |
| `ABATE` | `fAbate`: QTD · `PESO_VIVO×QTD`→peso_vivo_total · `PESO_ARROBA×15×QTD`→peso_carcaca_total (a @ de carcaça é *definida* como 15 kg) · FATURAMENTO→valor_total · CLIENTE→contraparte. RENDIMENTO digitado só confere com carcaça÷vivo | `venda-pecuario` **com** `deadArrobaAvg` preenchido: amount · weightTotal (ou liveWeightAVG×amount) → peso_vivo_total · `deadWeightAvg×amount` → peso_carcaca_total · totalFaturamento · client |
| `VENDA_EM_PE` | `fVendaemPe`: QTD · PESOVIVO_TOTAL (é entrada nesta aba) · FATURAMENTO · CLIENTE · DOCUMENTO | `venda-pecuario` **sem** `deadArrobaAvg`: amount · weightTotal · totalFaturamento · client |
| `NASCIMENTO` | `fNascimento`: QTD · `PESO_NASC×QTD`→peso_vivo_total · SAFRA→extra | `nascimento-pecuario`: amount (sem peso → nulo, ver capacidades) |
| `MORTE` | `fMortes`: QTD · `PESO_VIVO×QTD` · CAUSA · LOCAL · CARIMBO_BEZ→extra | `morte-pecuario`: amount · totalWeight · cause · locale · notes→extra |
| `CONSUMO_DOACAO` | `fconsumodoacao`: QTD · PESO_VIVO×QTD · VALOR_CAB×QTD · DESTINO→contraparte | `morte-pecuario` com `cause = 'Consumo Abate'` (hoje o BI Metryx trata assim) → **reclassificado no adapter** como `CONSUMO_DOACAO` |
| `TRANSF_ENTRADA` / `TRANSF_SAIDA` | `ftranfentrada` / `ftranssaida`: QTD · TOTAL_PESO · VALOR TOTAL | `transferencia-animal-pecuario`: **1 registro vira 2 linhas**, SAÍDA em `idFarmOrigin` e ENTRADA em `idFarmDestiny`. Entre retiros da mesma fazenda, as linhas se anulam no estoque da fazenda e ficam visíveis por retiro |
| `DESMAME` | `fdesmame`: CATEGORIA_FAZENDA_SAÍDA→categoria_bi · _ENTRADA→categoria_destino_bi · QTD · PESO_VIVO×QTD | `desmames-pecuario`: oldCategoryId→categoria · newCategoryId→destino · amount · weight×amount (validar se `weight` é médio) |
| `MUDANCA_CATEGORIA` | `fmudcategoria`: SAÍDA/ENTRADA · QTD · TOTAL_PESO | `mudanca-categoria-pecuario`: uuidCategoryOrigin→categoria · uuidCategoryDestiny→destino · amount |
| *(planejado, qualquer tipo)* | abas `*PLANEJADO` com as mesmas colunas e data diária; `versao_plano` = "PLANILHA" (oficial) | `*-mensal-planejamento`: date `MM/YY`→1º dia do mês · plVersionCode→versao_plano · `type` define ABATE×EM PÉ · venda: `weight×amount`→peso_vivo_total, `weight×yield/100×amount`→peso_carcaca_total, totalValue→valor_total |

> Detalhe que pega quem não olha o Swagger: o **planejamento** do Metryx usa `idCategory` **inteiro** (com `animalGroupName`,
> `age` e `gender`), enquanto o **realizado** usa `categoryId` como **texto/uuid**. São dois de-paras de categoria
> diferentes (`metryx_realizado` e `metryx_plano`) para as 15 categorias BI.

### 4.2 `fato.inventario` (checkpoints de estoque)

| Planilha | Metryx |
|---|---|
| `CADASTROINICIAL!F11:F74` (saldo inicial por categoria da fazenda). A data é o mês anterior ao PERÍODO (`O22:T22`). Cada troca de período gera um **novo** checkpoint | `saldo-inical-pecuario` (date, uuidCategory, amount) **e** `balanco-pecuario` (saldo por data × categoria; cada registro é um checkpoint) |

### 4.3 `fato.rebanho_medio_mensal` (grupo × mês)

| Coluna canônica | Planilha `fRebanhoMedio` | Metryx `rebanho-medio-pecuario` |
|---|---|---|
| grupo (BEZERROS/JOVENS/ADULTOS) | GRUPO_CATEGORIA (Bezerros/Jovens/Adultos → caixa normalizada) | **soma** das categorias por `dim.categoria_bi.grupo` (o `groupCategory` da API só confere) |
| qtd_cab | QTD_CAB | Σ amount |
| peso_vivo_total_kg | — (nulo) | Σ (amount × weight) (validar se `weight` é médio) |
| qtd_ua_informada | QTD_UA (frequentemente vazia) | — (nulo) |

UA na camada de KPI, sempre pela mesma regra: `COALESCE(qtd_ua_informada, peso_vivo_total_kg / kg_por_ua,
Σ(cab × peso_ref_categoria) / kg_por_ua)`, devolvendo junto a **origem da UA** (informada, peso, estimada).

### 4.4 `fato.area_mensal` (mês)

| Planilha `fArea` | Metryx `utilizacao-pasto` |
|---|---|
| ÁREA_PASTO, ÁREA_ILP por mês (ÁREA_TOTAL é fórmula; `SILAGEM` no cabeçalho é campo à parte) | 1 linha por pasto e período de uso com `areaTotal`, `areaProdutiva`, `statusPecuaria`, `dataInicio`, `dataFim` → **expandido por mês** (16/10/2026): no último dia do mês vale o período mais recente de cada pastagem; área total = Σ `areaTotal` das de uso Pecuária (vai para `area_pasto_ha` e `area_total_ha`), Σ `areaProdutiva` em `area_produtiva_ha`; do primeiro período até o último mês do rebanho médio (`adapters/metryx/pasto.py`) |

### 4.5 Financeiro

| Canônico | Planilha `fDre` / `fDrePLANEJADO` | Metryx `lancamento-financeiro` / `previsao-financeiro` |
|---|---|---|
| centro_custo_id, subcentro_id | CENTRO_DE_CUSTO + SUB_CENTRO **locais** → `BASEPLANODECONTAS` (já na taxonomia Metryx) → `dim.centro_custo` | costCenter + subCenter (já na taxonomia; limpar U+200B…U+FEFF) → `dim.centro_custo` |
| natureza (C/D) | via `ConsultaPlanoContas` (a coluna OPERAÇÃO é fórmula; aqui é recalculada) | `type` (Crédito/Débito) |
| valor (> 0) | VALOR | amountPaid (realizado) / valorPrevisto (previsto) |
| data_pagamento / data_vencimento | DATA_PAG / — | datePayment / dueDate |
| fazenda_id | a fazenda do arquivo | idfarmDestination (ou idFarmFiscal, decisão D2) |
| chave idempotente | (versão do arquivo, linha) | (idFinancialEntrie, idPayment, parcel) |
| DCM, CCM, CF/CV, classificação DRE | **não** carrega as colunas DESEMBOLSO/CUSTEIO/TIPO_CUSTEIO da planilha | **não** usa o `mapa` duplicado do SQL atual |
| orçamento (grão centro × mês × versão) | `fDrePLANEJADO` **agregado** por competência | `previsao-financeiro` por date; `previsao-fluxo-caixa-planejamento` por plVersionCode |

---

## 5. Os casos difíceis, um por um

### 5.1 Estoque: o caso que mais diverge hoje

| | Hoje: planilha | Hoje: Metryx | Plataforma |
|---|---|---|---|
| Fonte do número | Σ de todas as movimentações assinadas desde o "Saldo Anterior" (`fMovRebanho`, 100% fórmula) | último registro de `balanco-pecuario` no mês, repetido nos meses seguintes, com regra especial para "bezerros mamando" | **checkpoints** (`fato.inventario`) + **fluxos** (`fato.mov_animal`), com a mesma regra para as duas fontes |

Regra única, implementada como função SQL no banco que gera `fato.estoque_mensal`:

```
saldo_final(f, cat, mês) = último checkpoint ≤ fim do mês
                         + Σ fluxos assinados entre a data desse checkpoint e o fim do mês

ajuste(f, cat, mês)      = checkpoint do mês − (saldo_final do mês anterior + Σ fluxos do mês)
                           (só existe quando há checkpoint dentro do mês)
```

- **Planilha**: só há checkpoint no início de cada PERÍODO. O saldo vem dos fluxos e o ajuste é zero na prática. Isso
  também resolve o problema de hoje em que trocar o PERÍODO **apaga** o histórico ou **duplica** o saldo anterior: cada
  período vira um checkpoint datado e o anterior continua lá.
- **Metryx**: há checkpoint todo mês (balanço). O saldo final **é** o número oficial do Metryx, e os fluxos (nascimento,
  morte, compra, venda, desmame, mudança, transferência) explicam a variação. O que não fecha aparece como linha
  **"Ajuste de inventário"** no balanço de rebanho e na tela de qualidade, em vez de ficar escondido.
- **Início do estoque:** o estoque da fazenda começa no primeiro checkpoint dela. Os fluxos até essa data já estão
  nesse retrato e ficam de fora. Uma categoria (ou retiro) que não aparece nele começa em zero: o movimento que a
  abre conta como movimento, e o primeiro checkpoint dela corrige o que não fechar. Fazenda sem checkpoint nenhum
  soma os fluxos desde o início. (Migração 0015, achado A28 do relatório de validação.)
- KPI "Estoque final" = `Σ saldo_final`. KPI "Balanço" = saldo inicial + entradas − saídas ± ajuste, lido das mesmas colunas.

Exemplo (categoria BEZERRO, julho):

| | Planilha | Metryx |
|---|---|---|
| checkpoint 30/06 | 1.000 (Saldo Anterior) | 1.000 (balanço) |
| fluxos de julho | +120 nascimentos, −5 mortes, −300 desmame | iguais |
| checkpoint 31/07 | — | 812 (balanço) |
| `estoque_mensal` jul | saldo_final 815, ajuste 0 | saldo_final 812, **ajuste −3** |

A tela é a mesma. A diferença de 3 cabeças passa a ser um dado visível e rastreável, não uma divergência entre dois BIs.

### 5.2 Rebanho médio e UA

A planilha digita o rebanho por grupo e a UA quando o consultor preenche. O Metryx calcula por categoria e tem peso, mas
não tem UA. O canônico fica no grão grupo × mês (regra 3) e a UA é calculada sempre pela mesma regra (§4.3), com a origem
devolvida pela API. Assim o front mostra um selo "UA estimada" sem saber de que fonte o dado veio.

No Metryx, o rebanho médio do mês é a média do saldo de cada dia do balanço, por categoria, como o relatório do próprio
Metryx (`adapters/metryx/rebanho.py`, 27/10/2026). O endpoint `rebanho-medio-pecuario`, que o BI usa, conta animais a
mais e fica só no bruto (relatório de validação §21, defeito P18).

### 5.3 Planejado: lançamento × agregado mensal, com versões

A planilha planeja lançamento a lançamento; o Metryx planeja por mês e por versão (`plVersionCode`). Como nenhum KPI
planejado usa grão menor que o mês, os dois entram em `fato.mov_animal` com `cenario='planejado'` e são sempre agregados
por `competencia`. A versão é obrigatória: na planilha é uma única versão "PLANILHA" marcada como oficial; no Metryx, a
versão oficial é escolhida pelo consultor (decisão D7). Isso acaba com a soma de todas as versões que existe hoje.
Até a D7, entra a versão mais recente de cada fazenda e safra (27/10/2026). O número da versão só é único dentro da
fazenda (cada fazenda tem a sua versão 1), então o código canônico é fazenda + número. O `previsao-financeiro` não tem
versão e entra numa versão própria; o rebanho médio previsto sai da evolução do rebanho
(`estoque-medio-mensal-planejamento`), regras em `app/etl/adapters/metryx/planejamento.py`.

### 5.4 Consumo, transferência e desmame

Os três têm formas diferentes nas duas fontes e o mesmo significado de negócio:
- **Consumo**: aba própria na planilha; no Metryx vem como morte com causa "Consumo Abate".
- **Transferência**: na planilha são 2 abas; no Metryx é 1 registro com origem e destino.
- **Desmame**: categoria de saída e de entrada nas duas fontes, com nomes de campo diferentes.

O adapter converte cada um para o mesmo `tipo` canônico (§4.1). Daí em diante o estoque e os KPIs não conseguem mais
distinguir a origem.

### 5.5 Financeiro

A planilha classifica cada lançamento por VLOOKUP na própria pasta. O Metryx traz o centro de custo já com o nome padrão.
No canônico, os dois carregam só `centro_custo_id`, natureza, valor e datas. Desembolso, custeio, CF/CV e a classificação
do DRE são **atributos de `dim.centro_custo`**: existe um único de-para, editável na tela de admin. Com isso deixam de
existir as 3 codificações e os 2 mapas divergentes que existem hoje.

---

## 6. Front transparente sem esconder a realidade: "capacidades"

Algumas informações existem só numa fonte:
- peso ao nascer: só na planilha;
- fazenda fiscal, versões de plano e área por pasto: só no Metryx;
- UA informada: só na planilha, quando o consultor preenche.

Para o front continuar sem saber a fonte, o `GET /escopo` devolve, por fazenda, **capacidades** e não a fonte:

```json
{ "fazenda_id": "…", "nome": "Bela Vista", "sistema_produtivo": "CICLO COMPLETO",
  "capacidades": { "area": true, "ua": "estimada", "peso_nascimento": false, "versoes_plano": false,
                   "estoque_reconciliado": true },
  "atualizado_em": "2026-10-14T07:02:00-04:00" }
```

As respostas de KPI trazem o mesmo tipo de informação quando ela importa, por exemplo
`{"valor": 0.92, "unidade": "UA/ha", "qualidade": "estimada"}`. O front decide sobre **o dado** (mostrar o selo, esconder um
card sem base, avisar "dado parcial"), nunca sobre a **fonte**. Se amanhã a planilha ganhar peso ao nascer, nada muda no front.

---

## 7. Como garantir que o número é o mesmo

| Garantia | Como | Quando |
|---|---|---|
| **Teste de equivalência entre adapters** | Uma fazenda sintética (1 ano: saldo inicial, compras, abates, vendas em pé, nascimentos, mortes, desmame, transferência, DRE e planejado) escrita **como .xlsm no template** e **como payloads JSON do Metryx**. Os dois adapters precisam gerar o **mesmo** canônico (comparação linha a linha, ignorando `fonte`/`origem_*`) e o **mesmo** resultado em todos os KPIs do registro | CI, a cada commit |
| **Invariantes no banco** | `CHECK`s e job de qualidade: qtd ≥ 0; peso médio implícito entre 20 e 900 kg/cab; rendimento entre 0,40 e 0,65; toda linha com `categoria_bi_id`; natureza ∈ {C,D}; identidade do balanço (`saldo_final = inicial + fluxos + ajuste`) | a cada carga |
| **Paridade com o legado** | Para cada fonte, KPI novo × card do PBIX atual em um snapshot. Diferenças só nos bugs catalogados (P1–P15 da proposta) | antes do corte |
| **Reconciliação contínua** | estoque calculado × balanço Metryx × cache do `fMovRebanho` da planilha → `ajuste` e issues na tela "Saúde dos dados" | a cada carga |
| **KPI único por construção** | O registro de KPIs só enxerga `fato.*`, `dim.*` e `mart.*`. Um teste de arquitetura falha se algum SQL ou módulo de KPI referenciar `raw.*`, `ingest.*` ou a coluna `fonte` | CI |

### Exemplo completo: preço da @ no abate

Mesmo lote (50 cabeças, 540 kg vivo, rendimento 54%, R$ 320/@) nas duas fontes:

| Planilha `fAbate` | Metryx `venda-pecuario` |
|---|---|
| QTD 50 · PESO_VIVO 540 · RENDIMENTO 0,54 · PESO_ARROBA 19,44 · VALOR_ARROBA 320 · FATURAMENTO 311.040 | amount 50 · liveWeightAVG 540 · weightTotal 27.000 · deadArrobaAvg 19,44 · deadWeightAvg 291,6 · valueArroba 320 · totalFaturamento 311.040 |

Os dois adapters gravam **a mesma linha**:

| tipo | qtd | peso_vivo_total_kg | peso_carcaca_total_kg | valor_total |
|---|---|---|---|---|
| ABATE | 50 | 27.000 | 14.580 | 311.040 |

Fórmula única no registro de KPIs:

```sql
-- app/kpis/sql/venda_abate.sql (não existe "versão planilha" nem "versão Metryx")
SELECT SUM(m.qtd)                                                                   AS cabecas,
       SUM(m.valor_total)                                                           AS faturamento,
       SUM(m.valor_total) / NULLIF(SUM(m.peso_carcaca_total_kg) / :kg_carcaca_por_arroba, 0) AS preco_arroba,
       SUM(m.peso_carcaca_total_kg) / NULLIF(SUM(m.peso_vivo_total_kg), 0)          AS rendimento_carcaca,
       SUM(m.peso_vivo_total_kg)    / NULLIF(SUM(m.qtd), 0)                         AS peso_vivo_medio
FROM fato.mov_animal m
JOIN dim.categoria_bi c ON c.id = m.categoria_bi_id
WHERE m.tipo = 'ABATE' AND m.cenario = :cenario
  AND m.fazenda_id = ANY(:fazendas)                     -- já ∩ RLS
  AND m.competencia BETWEEN :inicio AND :fim
  AND (CAST(:sexo AS text) IS NULL OR c.sexo = :sexo);
```

Resultado para as duas fontes: preço da @ = 311.040 ÷ (14.580 ÷ 15) = **R$ 320,00**, rendimento = **54%**, peso médio =
**540 kg**. O resultado é igual porque a entrada é igual, e não porque duas fórmulas diferentes coincidiram.

---

## 8. O que isso muda no plano

- A **Fase 1** ganha os artefatos que tornam a conformação verificável desde o primeiro dia:
  - modelos pydantic do canônico (`app/etl/canonical.py`);
  - a função SQL de estoque (checkpoints + fluxos);
  - as dimensões com os de-paras;
  - a **fazenda sintética de equivalência** em `.xlsm` e em JSON.
- As **Fases 2 e 3** (adapters) passam a ter um critério objetivo de pronto: o teste de equivalência passa e a paridade
  com o legado só diverge nos bugs catalogados.
- Antes de fixar 4 regras, é preciso validar com um **payload real** do Metryx:
  - `weightTotal` de compra: total ou por cabeça;
  - `weight` de desmame e de rebanho médio: médio ou total;
  - semântica de `utilizacao-pasto` ao longo do tempo;
  - se `balanco-pecuario` já inclui transferências e o saldo inicial.
