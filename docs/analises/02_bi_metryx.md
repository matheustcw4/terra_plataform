# 02 — BI "Projeto Terra – Versão Metryx": catálogo do modelo semântico

> Escopo: catálogo técnico do modelo semântico do BI alimentado pela API Metryx (via Pentaho → PostgreSQL → Power BI), para reimplementar os KPIs em SQL/Python e compará-los com o BI de planilhas ("Ciclo Completo").
> Arquivo analisado: `C:\Users\TerraDev\Downloads\última versão dos projetos\Projeto Terra - Versão Metryx 12072026 (1).pbix` (há outras cópias com o mesmo nome base em `Downloads\` que não foram comparadas).
> Fontes da análise: dump do modelo (`pbix_metryx/MODEL.md` + CSVs), `Report/Layout` lido diretamente do .pbix (prototypeQuery, filtros de visual, formatação condicional, bookmarks, navegação), OpenAPI da Metryx (só contexto).
> Nenhuma credencial aparece no M (conexão por DSN ODBC); nada sensível foi copiado.

---

## 0. Sumário executivo

| Item | Valor |
|---|---|
| Tabelas no modelo | 29 (20 importadas via ODBC/M, 1 enter-data, 1 M gerada (`dCalendar`), 1 tabela de medidas, 1 field parameter, 5 tabelas automáticas de data `LocalDateTable_*`/`DateTableTemplate_*`) |
| Medidas | 220 (214 em `Analytics Measures`, 4 em `fSaldoGado`, 1 em `fMetasCompras`, 1 em `pecuarioVendaEmPe`) |
| Colunas calculadas | 62 (30 delas são das tabelas automáticas de data; 32 "de negócio") |
| Relacionamentos | 40 (39 ativos, 1 inativo; 1 bidirecional) |
| RLS | **Nenhuma** role/filtro |
| Páginas | 9 (`MENU 01`, `Financeiro`, `Movimentação do Gado`, `Venda Abate`, `Venda em Pé`, `Compras`, `Nascimento`, `Mortes`, `Planejado x Realizado`) |
| Publicado | Sim — `Connections` aponta para DatasetId/ReportId remotos no Power BI Service |
| Auto date/time | Ligado (`__PBI_TimeIntelligenceEnabled = 1`) |

Principais conclusões (detalhes nas seções 8 e 9):

1. **O modelo é um clone do BI de planilhas "Ciclo Completo"** com as tabelas trocadas por `stg_*` da Metryx. Várias medidas/colunas ainda apontam para objetos que só existem no modelo de planilhas (`fMovGado`, `fArea`, `qtd_cab`, `qtd_ua`, `peso_nasc`, `planejadoXRealizado[centro_de_custo_bi]`, `[Credito/Debito]`, `valueWeight`/`weightAvg`) → **14 medidas quebradas (11 com referência inválida + 3 que dependem delas) e 4 colunas calculadas quebradas**.
2. **Balanço/movimentação do rebanho não existe** nesta versão: `Stock`, entradas/saídas, desmame, mudança de categoria e transferências estão quebrados ou ausentes. `pecuarioDesmame`, `Compras`, `Categorias` e `Tabela` são carregadas mas não alimentam nenhum visual.
3. **UA e área não existem**: `Mean Month - UA` está fixa em `0` ("Não tem por UA na API" — porém a API `rebanho-medio-pecuario` devolve `weight`, e `utilizacao-pasto` devolve `areaTotal/areaProdutiva`), lotação usa áreas fixas `2911 ha` e `500 ha`.
4. **Nascimentos realizados não têm relacionamento de data** com `dCalendar` → todos os visuais de nascimento ignoram ano/mês.
5. **"Planejado" de rebanho médio = realizado**: `fMetasRebanhoMedio` lê a mesma `stg_rebanho_medio` de `pecuarioRebanhoMedioMensal` (a API tem `estoque-medio-mensal-planejamento`, não usada).
6. Bugs de fórmula relevantes: `Total Paid` (compras) soma valor **por cabeça** em vez de valor total; `Revenues Forecast` sempre vazio (filtro com literais que não existem); `% Amount Saled` invertido (previsto/realizado); `AVG Price @ (Em Pe + Abate) - Forecast` mistura @ com kg; peso médio previsto (`Σweight/Σamount`) inconsistente com `pesovivo_total = weight*amount`; totais do Planejado x Realizado não subtraem "Outros Débitos" (literal `E - …` vs `F - …` do SQL).
7. Visuais quebrados: 1 card com medida inexistente (`% mORTALITY ( MEAN MONTH)`), 9 cards com filtro de visual em coluna inexistente (`grupo_categoria` em `pecuarioRebanhoMedioMensal`/`fMetasMortes`, `sexo` em `fMetasCompras`), botões de bookmark e de navegação do MENU apontando para bookmark/página inexistentes.

---

## 1. Fontes de dados (Power Query M)

### 1.1 Conexão

* Todas as tabelas de dados usam `Odbc.Query("dsn=DATALAKE_METRYX", "<SQL>")` — DSN ODBC para o PostgreSQL do datalake. As consultas usam o schema literal **`"DATABASE"`** (ex.: `FROM "DATABASE".stg_vendas`) e tabelas de staging **`stg_*`** gravadas pelo job Pentaho que consome a API Metryx.
* Não há parâmetros M (`m_parameters` vazio). Não há credenciais no M.
* Ordem de carga (`PBI_QueryOrder`): pecuarioNascimento, pecuarioRebanhoMedioMensal, pecuarioVendaAbate, pecuarioVendaEmPe, pecuarioCompras, pecuarioDesmame, pecuarioMortes, financeiroDre, dCalendar, Categorias, Tabela, Compras, fUnidades, fMetasCompras, fMetasAbate, fMetasNascimentos, fMetasMortes, fMetasDre, fMetasRebanhoMedio, fSaldoGado, fMetasEmPe, fPlanejadoxRealizado.
* Convenção de chave fazenda: **`idpropfaz = CONCAT(idcustomer, idfarm)`** (sem separador), calculada no SQL de quase todas as tabelas — comentário no SQL de `fPlanejadoxRealizado`: "equivale ao PROP_FAZ da planilha".
* Vários SQL fazem `LEFT JOIN "DATABASE".stg_farm t1 ON t1.idcustomer = t.idcustomer AND t1.farmname = t.farmname` + `WHERE t1.idfarm IS NOT NULL` → **na prática um INNER JOIN por nome de fazenda** (texto). Linhas cuja `farmname` não bate com `stg_farm` são descartadas; nomes duplicados em `stg_farm` duplicariam linhas.

### 1.2 Mapa tabela do modelo → staging → endpoint Metryx

| Tabela do modelo | Tipo | Origem SQL | Endpoint Metryx (inferido) | Filtros / transformações principais |
|---|---|---|---|---|
| `pecuarioNascimento` | fato realizado | `stg_nascimentos` | `GET /nascimento-pecuario` | `date`→`DATA` (remove texto " 00:00:00.000", tipa date); `WHERE idfarm IS NOT NULL` (M) ; idpropfaz |
| `pecuarioRebanhoMedioMensal` | fato realizado (snapshot mensal) | `stg_rebanho_medio` | `GET /rebanho-medio-pecuario` | `month`→date→`DATA`; `idfarm IS NOT NULL`. **Não seleciona `weight` nem `groupCategory`** que a API devolve |
| `fMetasRebanhoMedio` | "planejado" | **`stg_rebanho_medio` (mesma do realizado!)** | deveria ser `GET /estoque-medio-mensal-planejamento` | idêntica a `pecuarioRebanhoMedioMensal` (mesmas cardinalidades em todas as colunas) |
| `pecuarioVendaAbate` | fato realizado | `stg_vendas` ⨝ `stg_farm` | `GET /venda-pecuario` | `WHERE deadarrobaavg IS NOT NULL`; colunas derivadas no SQL (ver 1.3) |
| `pecuarioVendaEmPe` | fato realizado | `stg_vendas` ⨝ `stg_farm` | `GET /venda-pecuario` | `WHERE deadarrobaavg IS NULL`; `peso_arroba = liveweightavg/15` |
| `pecuarioCompras` | fato realizado | `stg_compras` ⨝ `stg_farm` | `GET /compra-pecuario` | colunas derivadas (ver 1.3) |
| `Compras` | fato realizado (duplicada) | `stg_compras` ⨝ `stg_farm` | `GET /compra-pecuario` | mesmas linhas de `pecuarioCompras`, nomes originais da API; **não usada em visual** |
| `pecuarioDesmame` | fato realizado | `stg_desmames` | `GET /desmames-pecuario` | `date`→`DATA`; `idfarm IS NOT NULL`; **não usada em nenhuma medida/visual** |
| `pecuarioMortes` | fato realizado | `stg_mortes` | `GET /morte-pecuario` | renomeações (`cause`→`causa`, `locale`→`pasto`, `namegroup`→`grupo_categoria`, `totalweight`→`peso_vivo` e `peso_total`, `anosafra`→`safra`), `null as carimbo_bez` |
| `financeiroDre` | fato realizado (lançamentos/pagamentos) | `stg_dre` ⨝ `stg_farm` (INNER, por `farmname = farmfiscal`) + CTE `mapa` | `GET /lancamento-financeiro` | limpeza de caracteres invisíveis (`translate(... chr(8203)…chr(65279) …)`), classificação por centro de custo (tabela 1.4); M tipa `datepayment`, `duedate` |
| `fMetasDre` | planejado | `stg_dreprevisto` + CTE `mapa` | `GET /previsao-financeiro` | idem limpeza; `idfarm IS NOT NULL` |
| `fMetasCompras` | planejado | `stg_comprasprevisto` | `GET /compra-mensal-planejamento` | `to_date(date,'MM/YY')` no SQL |
| `fMetasAbate` | planejado | `stg_vendasasprevisto` | `GET /venda-mensal-planejamento` | `tipo ILIKE '%abate%'`; M converte `date` "MM/YY" → 1º dia do mês |
| `fMetasEmPe` | planejado | `stg_vendasasprevisto` | `GET /venda-mensal-planejamento` | `tipo ILIKE '%em%'` (frágil: qualquer tipo com "em"); M converte "MM/YY" |
| `fMetasNascimentos` | planejado | `stg_nascimentosprevisto` | `GET /nascimento-mensal-planejamento` | M converte "MM/YY"; traz `plversioncode/plversionname` (não filtrados!) |
| `fMetasMortes` | planejado | `stg_mortesprevisto` | `GET /morte-mensal-planejamento` | M converte "MM/YY"; traz `plversioncode/plversionname` (não filtrados!) |
| `fSaldoGado` | snapshot de estoque (fim de mês) | `stg_balanco_pecuario` ⨝ `stg_category` (SQL grande, ver 1.5) | `GET /balanco-pecuario` (+ `/categoria`) | renomeia `ultimodiames`→`date` |
| `fPlanejadoxRealizado` | fato agregado previsto × realizado | `stg_dre` + `stg_dreprevisto` (SQL grande, ver 1.6) | `/lancamento-financeiro` + `/previsao-financeiro` | sem passos M |
| `fUnidades` | dimensão fazenda/cliente | `stg_customers` | `GET /fazenda` | `idfarm IS NOT NULL`; `idpropfaz` |
| `Categorias` | dimensão categoria | `stg_category` | `GET /categoria` | `idcategory <> null` (M) |
| `dCalendar` | dimensão data | gerada em M | — | ver 2.3 |
| `Tabela` | dimensão "tipo de venda" | Enter Data (JSON comprimido) | — | 2 linhas: `"Abate"`, `"Em Pe"` |
| `Analytics Measures` | tabela de medidas | DAX `Row("Column", BLANK())` | — | — |
| `Parâmetro - Data` | field parameter | DAX | — | `("CÍVIL", NAMEOF(dCalendar[Nome do Mês]), 0)`, `("SAFRA", NAMEOF(dCalendar[mesano]), 1)` |
| `LocalDateTable_*` (4) / `DateTableTemplate_*` | auto date/time | DAX `CALENDAR` | — | para `dCalendar[Data]`, `pecuarioNascimento[DATA]`, `financeiroDre[datepayment]`, `fSaldoGado[data_saldo]` |

**Endpoints da API Metryx que este BI NÃO consome** (relevantes para o app unificado): `transferencia-animal-pecuario`, `mudanca-categoria-pecuario`, `saldo-inical-pecuario`, `utilizacao-pasto` (áreas: `areaTotal`, `areaProdutiva`, `areaCalculada`), `estoque-medio-mensal-planejamento`, `desmame-mensal-planejamento`, `previsao-fluxo-caixa-planejamento`, `confina-tech`, `retiro`, `control-birth`.

### 1.3 Colunas derivadas dentro do SQL (regras que precisam ser replicadas)

**`pecuarioVendaAbate`** (`stg_vendas t`, `deadarrobaavg IS NOT NULL`):

| Coluna modelo | Expressão SQL | Significado |
|---|---|---|
| `cliente` | `t.client` | comprador |
| `categ_fazenda`, `categoria_bi` | `t.category` | categoria (duas cópias) |
| `DATA` | `t.date` | data da venda |
| `qtd` | `t.amount` | cabeças |
| `peso_vivo` | `t.liveweightavg` | peso vivo médio (kg/cab) |
| `peso_arroba` | `t.deadarrobaavg` | @ de carcaça média por cabeça |
| `valor_arroba` | `t.valuearroba` | R$/@ |
| `faturamento` | `t.totalfaturamento` | R$ total |
| `sexo` | `t.gender` | |
| `peso_morto` | `t.deadweightavg` | peso de carcaça médio (kg/cab) |
| `pesovivo_total` | `t.weighttotal` | peso vivo total (kg) |
| `pesomorto_total` | `t.amount * t.deadweightavg` | peso de carcaça total (kg) |
| `valor_kg` | `t.valueweight` | R$/kg |
| `valor_cab` | `t.totalfaturamento / t.amount` | R$/cab |
| `proprietArio` | `t.customer` (**cliente, não owner**) | |
| `fazenda`, `retiro` | `t.farmname`, `t.retironame` | |
| `idpropfaz` | `CONCAT(t.idcustomer, t1.idfarm)` | |

**`pecuarioVendaEmPe`** (`deadarrobaavg IS NULL`): igual, exceto `peso_arroba = t.liveweightavg / 15` (@ **vivas** por cabeça, 15 kg), sem `peso_morto`/`pesomorto_total` (comentados), `proprietÁrio = t.customer`.

**`pecuarioCompras`** (`stg_compras t`):

| Coluna | Expressão | Observação |
|---|---|---|
| `DATA` | `t.date` | |
| `qtd` | `t.amount` | |
| `total_peso` | `t.weighttotal` | API: `weightTotal` (na venda é o **peso total**) |
| `valor_cab` | `t.totalfaturamento / t.amount` | |
| `VALOR TOTAL` | `t.totalfaturamento` | |
| `valo_kg` (sic) | `t.totalfaturamento / (t.amount * t.weighttotal)` | só correto se `weighttotal` for peso **por cabeça** |
| `valor_arroba` | `t.valuearroba` | |
| `peso_arroba` | `t.weighttotal / 15` | @ vivas (15 kg) — total ou por cabeça conforme semântica de `weighttotal` |
| `proprietArio` | `t.owner` (**owner**, ≠ venda que usa customer) | |
| demais | `categoryid, idcustomer, customer, farmname, idretiro, retironame, anosafra, provider, averagevalue, valueweight` | |

**`pecuarioMortes`** (`stg_mortes`): `date→DATA`, `category→categ_fazenda/categoria_bi`, `amount→qtd`, `cause→causa`, `locale→pasto`, `totalweight→peso_vivo` **e** `peso_total` (mesma coluna), `anosafra→safra`, `namegroup→grupo_categoria` (valores usados: `BEZERROS`, `JOVENS`, `ADULTOS`, `Bezerros Mamando`, `Bezerras Mamando`…; 8 valores distintos), `enumgroup`, `era`, `gender→sexo`, `owner→proprietArio`.

**`financeiroDre`** (`stg_dre t JOIN stg_farm t1 ON t1.idcustomer=t.idcustomer AND t1.farmname=t.farmfiscal LEFT JOIN mapa m ON m.costcenter=t.costcenter`): colunas de texto limpas com `translate(..., chr(8203)||chr(8204)||chr(8205)||chr(65279), '')`; `idpropfaz = CONCAT(t.idcustomer, t1.idfarm)` → **atribui o lançamento à fazenda FISCAL** (`farmfiscal`), enquanto `fPlanejadoxRealizado` atribui à fazenda **DESTINO** (`idfarmdestination`); `custeio_cat/tipo_custeio_cat/desembolso_cat = COALESCE(m.*, 'VERIFICAR')`.

**`fMetasDre`** (`stg_dreprevisto t LEFT JOIN mapa m`): `idpropfaz = CONCAT(t.idcustomer, t.idfarm)`, mesmas colunas de classificação; `valorrealizado` vem sempre vazio (cardinalidade 1).

### 1.4 Tabela de-para de centro de custo (CTE `mapa`, usada em `financeiroDre` e `fMetasDre`)

`custeio_cat` = entra no "Custeio" (`CCM`); `tipo_custeio_cat` = CF/CV/Receita…; `desembolso_cat` = entra no "Desembolso" (`DCM`). `'0,0'` = não entra.

| costcenter | custeio_cat | tipo_custeio_cat | desembolso_cat |
|---|---|---|---|
| Almoxarifado | 0,0 | 0,0 | 0,0 |
| Arrendamento | Receita outras | Receita outras | Receita outras |
| Cultura - Receita | Receita Agr | Receita Agr | Receita Agr |
| Culturas - Despesa | CCM | CV | DCM |
| Dividendos | 0,0 | 0,0 | 0,0 |
| Empréstimos sócios débito | 0,0 | 0,0 | 0,0 |
| Financiamentos créditos | Financiamentos | Financiamentos | Financiamentos |
| Financiamentos débitos | 0,0 | 0,0 | **DCM** |
| Forrageiras e Culturas Anuais | CCM | CV | DCM |
| Insumos do rebanho | CCM | CV | DCM |
| Investimentos em RH | 0,0 | 0,0 | DCM |
| Investimentos em infraestrutura | **CCM** | CF | DCM |
| Investimentos em outros animais | **CCM** | CF | DCM |
| Manutenção da fazenda (`-- revisar`) | CCM | CF | DCM |
| Milheto | 0,0 | 0,0 | 0,0 |
| Milho Safrinha | CCM | CV | DCM |
| Mão de Obra Geral | CCM | CF | DCM |
| Mão de Obra Permanente Administração | CCM | CF | DCM |
| Mão de Obra Permanente Cultura | CCM | CF | DCM |
| Mão de Obra Permanente Manutenção da Fazenda | CCM | CF | DCM |
| Mão de Obra Permanente Parque de Máquinas | CCM | CF | DCM |
| Mão de Obra Permanente Rebanho | CCM | CF | DCM |
| Outros animais | CCM | CF | DCM |
| Pastagens | CCM | CV | DCM |
| Rebanho | Receita Pec | Receita Pec | Receita Pec |
| Rebanho Investimento | **CCM** | CV | DCM |
| Receitas Parque de máquinas | Receita outras | Receita outras | Receita outras |
| Receitas financeiras | Financiamentos | Financiamentos | Financiamentos |
| Receitas outros | Receita outras | Receita outras | Receita outras |
| Silagem de Capim / de Milheto / de Milho | CCM | CV | DCM |
| Silagem | CCM | CV (**em `fMetasDre`: `CCM` → F/V = "VERIFICAR"**) | DCM |
| Soja | CCM | CV | DCM |
| Sorgo Grão | CCM | CV | DCM |
| Suporte à Produção Administração | CCM | CF | DCM |
| Suporte à Produção Parque de máquinas | CCM | CF | DCM |
| Taxas e impostos (`-- revisar`) | CCM | CF | DCM |
| Vendas outros animais | Receita outras | Receita outras | Receita outras |
| *(qualquer outro)* | VERIFICAR | VERIFICAR | VERIFICAR |

Centros de custo que aparecem no CASE de `fPlanejadoxRealizado` mas **não** no `mapa` (caem em `VERIFICAR` no financeiro): Algodão, Aveia, Feno, Milho Verão, Silagem de Capiaçu, Silagem de Sorgo, Empréstimos sócios crédito, Outros Débitos, Aporte de capital, Prejuízo Administração, Venda de Imóveis. Inversamente, `Culturas - Despesa`, `Milheto`, `Silagem` estão no `mapa` mas não no CASE.

### 1.5 `fSaldoGado` — lógica do SQL (estoque de fim de mês)

Fonte: `stg_balanco_pecuario` (registros de saldo por data × proprietário × fazenda × retiro × categoria × birth × harvest) `LEFT JOIN stg_category ON idcategory = uuidcategory`.

1. `dCalendarioMensal`: último dia de cada mês de **2010-01-01 até CURRENT_DATE** (inclui o fim do mês corrente, data futura).
2. CTE `saldo` = UNION ALL de três origens:
   * **`OUTRAS CAT`** (categorygroup NÃO contém "Bezerros Mamando"/"Bezerras Mamando"): por (owner, farmname, anosafra, category, mês, retironame) pega o **último registro do mês** (`row_number … ORDER BY date DESC = 1`); `amount` = saldo desse registro.
   * **`BEZERR CHAVE DIFERENTE`** (bezerros mamando, quando a chave owner/farm/retiro/category/birth/harvest tem 1 só mês — `validador = 1`): último registro do mês e `amountacc = SUM(amount) OVER (PARTITION BY owner, farmname, retironame, category ORDER BY date)` (soma corrente entre diferentes birth/harvest).
   * **`BEZERR MESMA CHAVE`** (bezerros mamando, `validador <> 1`): `amountacc = MAX(amount) OVER (PARTITION BY owner, farmname, retironame, category, birth, harvest ORDER BY date DESC)`.
3. Para cada fim de mês, `DISTINCT ON (mês, owner, farmname, retironame, category[, birth, harvest])` com `s.date <= UltimoDiaMes ORDER BY s.date DESC` → **carrega para frente o último saldo conhecido** (forward-fill). `saldo_por_mes4` (outras cat.), `saldo_por_mes3` (bezerro chave diferente), `saldo_por_mes2` (bezerro mesma chave, por birth/harvest). `saldo_por_mes` é definido e não usado.
4. `UNION` (distinct) das três; colunas finais: `date` (= último dia do mês), `owner`, `farmname`, `retironame`, `category`, `birth`, `harvest`, `idpropfaz`, `amountacc` (saldo em cabeças), `data_saldo` (data do registro de origem).

Grão: **mês (fim) × owner × fazenda × retiro × categoria** (× birth × harvest para bezerros "mesma chave"). Não há `idcustomer`/`idfarm`/`gender` na saída. Consequências: um saldo nunca "zera" se a origem não emitir um registro zero (forward-fill eterno); o mês corrente fica com data futura (fora de `dCalendar`).

SQL equivalente simplificado para o app (outras categorias):
```sql
WITH meses AS (SELECT (date_trunc('month', gs) + interval '1 month - 1 day')::date AS fim_mes
               FROM generate_series(date '2010-01-01', current_date, interval '1 month') gs),
ult_mes AS (  -- último registro de cada mês por chave
  SELECT DISTINCT ON (owner, farmname, retironame, category, date_trunc('month', date))
         owner, farmname, retironame, category, idcustomer, idfarm, date, amount
  FROM stg_balanco_pecuario
  ORDER BY owner, farmname, retironame, category, date_trunc('month', date), date DESC)
SELECT DISTINCT ON (m.fim_mes, u.owner, u.farmname, u.retironame, u.category)
       m.fim_mes AS date, u.owner, u.farmname, u.retironame, u.category,
       CONCAT(u.idcustomer, u.idfarm) AS idpropfaz, u.amount AS amountacc, u.date AS data_saldo
FROM meses m JOIN ult_mes u ON u.date <= m.fim_mes
ORDER BY m.fim_mes, u.owner, u.farmname, u.retironame, u.category, u.date DESC;
```

### 1.6 `fPlanejadoxRealizado` — lógica do SQL (DRE previsto × realizado)

Comentário no próprio SQL: realizado = `stg_dre` (`amountpaid`, `datepayment`, `costcenter`, `idcustomer`, `idfarmdestination`); previsto = `stg_dreprevisto` (`valorprevisto`, `date`, `costcenter`, `idcustomer`, `idfarm`). **Filtro temporário**: ignora lançamentos com `|amountpaid| >= 1e9` ("erro de escala na origem, ex.: Receitas financeiras ~5e16") — esse filtro **não** existe em `financeiroDre`.

1. `prop`: lista de fazendas (`CONCAT(idcustomer, idfarmdestination)` do realizado ∪ `CONCAT(idcustomer, idfarm)` do previsto), com `proprietario` (owner/customer) e `fazenda`.
2. `c_custo`: todos os centros de custo (das duas fontes) × todas as fazendas (CROSS JOIN).
3. `datas`: meses distintos (`date_trunc('month', datepayment)` ∪ `date_trunc('month', date)`).
4. `base`: grade fazenda × centro de custo × mês.
5. `previsto`: `SUM(valorprevisto)` por idpropfaz × mês × costcenter → `meta`.
6. `realizado`: `SUM(amountpaid)` por idpropfaz × mês × costcenter × **type** (Crédito/Débito) → somado depois sem sinal (**créditos e débitos do mesmo centro se somam em vez de se compensarem**).
7. `classificacao` (CASE por costcenter): `A - RECEITAS` (Arrendamento, Cultura - Receita, Rebanho, Receitas financeiras, Receitas outros, Receitas Parque de máquinas, Vendas outros animais); `C - INVESTIMENTOS` (Investimentos em infraestrutura, em outros animais, em RH, Rebanho Investimento); `D - CUSTEIO` (Algodão, Aveia, Feno, Forrageiras e Culturas Anuais, Insumos do rebanho, Manutenção da fazenda, Mão de Obra * (6), Milho Safrinha, Milho Verão, Outros animais, Pastagens, Silagens (5), Soja, Sorgo Grão, Suporte à Produção * (2), Taxas e impostos); `E - OUTROS CRÉDITOS` (Empréstimos sócios crédito, Financiamentos créditos); `F - OUTROS DÉBITOS` (Dividendos, Empréstimos sócios débito, Financiamentos débitos, Outros Débitos); `''` (Almoxarifado, Aporte de capital, Prejuízo Administração, Venda de Imóveis); demais → NULL.
8. `meta = ABS(p.meta)`, `realizado = ABS(ROUND(SUM(r.valor),2))` (sinais descartados).
9. Saída = linhas por centro de custo **UNION ALL** linha sintética `costcenter='DESEMBOLSO'`, `classificacao='B - DESEMBOLSO'` (= cópia das linhas C + D).

Grão: **idpropfaz × costcenter × mês (1º dia)**; colunas `meta`, `realizado`, `classificacao`, `proprietario`, `fazenda`.

### 1.7 `dCalendar` (M)

`List.Dates` de **2024-07-01** até `DateTime.LocalNow()` (data de refresh). Colunas: `Data`, `Ano`, `Mês` (nº), `Nome do Mês` (`Date.MonthName`), `mesano` (`"MMM-yy"`, ex. `jul-24`), `anosafra` (`"jul-24/25"`), `OrdemSafra` (jul=1 … jun=12), `safra` (`"Safra 2024/25"`), `OrdemAnoSafra` (`ano_inicio*100 + ordem`), + DAX `Classificador Mês-Ano = 100*Ano + Mês`. **Fatos anteriores a jul/2024 nunca aparecem em visuais filtrados por data**, e o mês corrente termina "hoje" (afeta `fSaldoGado`, cuja data é o fim do mês).

---

## 2. Modelo estrela

### 2.1 Dimensões

| Dimensão | Chave(s) usadas em relacionamentos | Atributos usados no relatório | Observações |
|---|---|---|---|
| `dCalendar` | `Data` (date) | `Ano`, `mesano`, `Nome do Mês`, `safra` (slicer oculto) | Único calendário "de negócio". 2024-07-01 → hoje. Não há evidência de "Mark as date table"; auto date/time ligado. |
| `fUnidades` (apesar do prefixo *f*, é dimensão) | `idfarm` **e** `idpropfaz` (duas colunas-chave diferentes recebendo relacionamentos) | `customer` (slicer "PROPRIETÁRIO"), `farmname` (slicer "FAZENDA") | 70 fazendas, 10 clientes. Fonte `stg_customers`. |
| `Categorias` | `idcategory` | — (nenhum visual) | 260 ids, 162 nomes, 8 `categorygroup`, 5 `agecategory`, `gender`. Só filtra nascimentos e rebanho médio. |
| `Tabela` | `TipoVenda` (`Abate`, `Em Pe`) | — (nenhum visual) | Liga-se às colunas constantes `tipovenda` das duas tabelas de venda. Inútil na prática. |
| `Parâmetro - Data` | — (field parameter) | slicer de modo "CÍVIL/SAFRA" e slicer "Mês" dinâmico (`Parâmetro - Data Campos`) | CÍVIL → `Nome do Mês`; SAFRA → `mesano`. Os gráficos usam `dCalendar[mesano]` fixo, não o parâmetro. |
| `LocalDateTable_*` ×4, `DateTableTemplate_*` | auto | — | Gerados pelo auto date/time; `LocalDateTable_96757441` é de `pecuarioNascimento[DATA]` (confirma que essa coluna não está ligada a `dCalendar`). |

### 2.2 Fatos (grão e chaves)

| Fato | Grão (1 linha =) | FK → dCalendar | FK → fUnidades | FK → outros | Métricas-base |
|---|---|---|---|---|---|
| `pecuarioNascimento` | evento/lote de nascimento: data × cliente × fazenda × retiro × owner × categoria × sexo | **nenhuma** | `idfarm` | `idcategory → Categorias` | `amount` (cabeças) |
| `pecuarioRebanhoMedioMensal` | mês × cliente × fazenda × retiro × owner × categoria × sexo | `DATA` | `idfarm` | `idcategory → Categorias` | `amount` (cabeças médias no mês) |
| `fMetasRebanhoMedio` | idem (cópia do realizado) | `DATA` | `idfarm` | `idcategory → Categorias` | `amount` |
| `pecuarioVendaAbate` | linha de venda para abate (data × cliente comprador × categoria × sexo × fazenda × retiro) | `DATA` | `idpropfaz` | `tipovenda → Tabela` | `qtd`, `faturamento`, `pesovivo_total`, `pesomorto_total`, `peso_arroba` |
| `pecuarioVendaEmPe` | linha de venda em pé | `DATA` | `idpropfaz` | `tipovenda → Tabela` | `qtd`, `faturamento`, `pesovivo_total` |
| `pecuarioCompras` | linha de compra (data × fornecedor × categoria × sexo × fazenda × retiro) | `DATA` | `idpropfaz` | — | `qtd`, `VALOR TOTAL`, `total_peso` |
| `Compras` | idem (duplicada) | `date` (**inativo**) | `idpropfaz` | — | `amount`, `totalfaturamento`, `weighttotal` |
| `pecuarioDesmame` | evento de desmame (data × categoria antiga → nova × nascimento) | `DATA` | `idfarm` | — | `amount`, `weight` |
| `pecuarioMortes` | evento de morte (data × categoria × causa × pasto × grupo) | `DATA` | `idfarm` | — | `qtd`, `peso_total` |
| `financeiroDre` | parcela/pagamento de lançamento financeiro (`idfinancialentrie` × `idpayment`) | `duedate` (**vencimento**, não pagamento) | `idpropfaz` (fazenda fiscal) | — | `amountpaid`, `amountpayable` |
| `fMetasDre` | valor previsto por mês × fazenda × centro/classe/subcentro | `date` | `idfarm` | — | `valorprevisto` |
| `fMetasCompras` | previsão mensal de compra (fazenda × retiro × categoria × grupo animal × sexo) | `date` | `idfarm` | — | `amount`, `weight`, `totalvalue` |
| `fMetasAbate` | previsão mensal de venda abate | `date` | `idpropfaz` | — | `amount`, `weight`, `yield`, `arrobaweight`, `totalvalue` |
| `fMetasEmPe` | previsão mensal de venda em pé | `date` | `idpropfaz` | — | `amount`, `weight`, `totalvalue` |
| `fMetasNascimentos` | previsão mensal de nascimentos (por versão de plano!) | `date` | `idfarm` | — | `amount` |
| `fMetasMortes` | previsão mensal de mortes (por versão de plano!) | `date` | `idfarm` | — | `amount` |
| `fSaldoGado` | fim de mês × owner × fazenda × retiro × categoria (× birth × harvest) | `date` (**bidirecional**) | `idpropfaz` | — | `amountacc` (saldo em cabeças) |
| `fPlanejadoxRealizado` | mês × idpropfaz × costcenter | `data` | `idpropfaz` | — | `meta`, `realizado` |

### 2.3 Relacionamentos (todos)

Todos M:1, cross-filter Single, exceto onde indicado.

| # | De (N) | Para (1) | Ativo | Obs. |
|---|---|---|---|---|
| 0 | pecuarioDesmame[DATA] | dCalendar[Data] | ✔ | |
| 1 | pecuarioVendaAbate[tipovenda] | Tabela[TipoVenda] | ✔ | coluna constante "Abate" |
| 2 | pecuarioVendaEmPe[tipovenda] | Tabela[TipoVenda] | ✔ | constante "Em Pe" |
| 3 | pecuarioVendaAbate[DATA] | dCalendar[Data] | ✔ | |
| 4 | pecuarioVendaEmPe[DATA] | dCalendar[Data] | ✔ | |
| 5 | pecuarioMortes[DATA] | dCalendar[Data] | ✔ | |
| 6 | pecuarioCompras[DATA] | dCalendar[Data] | ✔ | |
| 7 | pecuarioNascimento[idfarm] | fUnidades[idfarm] | ✔ | |
| 8 | pecuarioRebanhoMedioMensal[idfarm] | fUnidades[idfarm] | ✔ | |
| 9 | pecuarioDesmame[idfarm] | fUnidades[idfarm] | ✔ | |
| 10 | pecuarioMortes[idfarm] | fUnidades[idfarm] | ✔ | |
| 11 | fMetasCompras[idfarm] | fUnidades[idfarm] | ✔ | |
| 12 | fMetasNascimentos[idfarm] | fUnidades[idfarm] | ✔ | |
| 13 | fMetasMortes[idfarm] | fUnidades[idfarm] | ✔ | |
| 14 | fMetasDre[idfarm] | fUnidades[idfarm] | ✔ | |
| 15 | fMetasRebanhoMedio[idfarm] | fUnidades[idfarm] | ✔ | |
| 16 | pecuarioNascimento[idcategory] | Categorias[idcategory] | ✔ | |
| 17 | pecuarioRebanhoMedioMensal[idcategory] | Categorias[idcategory] | ✔ | |
| 18 | fMetasRebanhoMedio[idcategory] | Categorias[idcategory] | ✔ | |
| 19 | pecuarioRebanhoMedioMensal[DATA] | dCalendar[Data] | ✔ | |
| 20 | fMetasRebanhoMedio[DATA] | dCalendar[Data] | ✔ | |
| 21 | pecuarioVendaAbate[idpropfaz] | fUnidades[idpropfaz] | ✔ | |
| 22 | pecuarioVendaEmPe[idpropfaz] | fUnidades[idpropfaz] | ✔ | |
| 23 | pecuarioCompras[idpropfaz] | fUnidades[idpropfaz] | ✔ | |
| 24 | financeiroDre[idpropfaz] | fUnidades[idpropfaz] | ✔ | |
| 25 | Compras[idpropfaz] | fUnidades[idpropfaz] | ✔ | |
| 26 | fSaldoGado[idpropfaz] | fUnidades[idpropfaz] | ✔ | |
| 27 | fMetasDre[date] | dCalendar[Data] | ✔ | |
| 28 | fMetasMortes[date] | dCalendar[Data] | ✔ | |
| 29 | fMetasNascimentos[date] | dCalendar[Data] | ✔ | |
| 30 | fMetasAbate[date] | dCalendar[Data] | ✔ | |
| 31 | Compras[date] | dCalendar[Data] | **✘ inativo** | nenhuma medida ativa via USERELATIONSHIP |
| 32 | fMetasCompras[date] | dCalendar[Data] | ✔ | |
| 33 | financeiroDre[duedate] | dCalendar[Data] | ✔ | data de **vencimento** |
| 34 | fSaldoGado[date] | dCalendar[Data] | ✔ | **Both** (bidirecional) |
| 35 | fPlanejadoxRealizado[idpropfaz] | fUnidades[idpropfaz] | ✔ | |
| 36 | fPlanejadoxRealizado[data] | dCalendar[Data] | ✔ | |
| 37 | fMetasAbate[idpropfaz] | fUnidades[idpropfaz] | ✔ | |
| 38 | fMetasEmPe[idpropfaz] | fUnidades[idpropfaz] | ✔ | |
| 39 | fMetasEmPe[date] | dCalendar[Data] | ✔ | |

Lacunas relevantes: **`pecuarioNascimento` sem data**; nenhuma tabela de vendas/compras/mortes/metas ligada a `Categorias`; `financeiroDre[datepayment]` sem relacionamento (só auto-date); `fSaldoGado` sem relacionamento com `Categorias`. Muitas medidas usam `USERELATIONSHIP(dCalendar[Data], fMetas…[date])` ou `USERELATIONSHIP(fMetas…[idfarm], fUnidades[idfarm])` sobre relacionamentos **que já são ativos** (redundante, sem efeito).

Diagrama lógico:
```
                         Categorias ◄── pecuarioNascimento (sem data!)
                             ▲    ▲
                             │    └── pecuarioRebanhoMedioMensal ─┐
                             └─────── fMetasRebanhoMedio ──────────┤
                                                                   ▼
 Tabela ◄─ pecuarioVendaAbate / pecuarioVendaEmPe ─────────► dCalendar ◄─ pecuarioMortes, pecuarioCompras, pecuarioDesmame,
                │                                              ▲  ▲  ▲     fMetas{Abate,EmPe,Compras,Mortes,Nascimentos,Dre},
                ▼                                              │  │  │     financeiroDre(duedate), fPlanejadoxRealizado,
            fUnidades (idpropfaz | idfarm) ◄───────────────────┘  │  └──── fSaldoGado (Both)
```

### 2.4 Calendário e "safra"

* Ano civil: `Ano`, `Mês`, `Nome do Mês`, `mesano`.
* Ano-safra pecuário: **julho a junho** (`OrdemSafra` jul=1), rótulos `safra` = "Safra 2024/25", `anosafra` = "jul-24/25".
* Todas as medidas "acumuladas" usam `YEAR(dCalendar[Data])` (ano **civil**) para o YTD — não respeitam o modo SAFRA.
* Os fatos trazem seu próprio `anosafra`/`harvest` vindos da Metryx (formatos não verificados), mas nenhuma medida os usa.

---

## 3. RLS

**Não existe RLS** (`rls.csv` vazio; nenhuma role). O isolamento por cliente hoje depende apenas de slicers (`fUnidades[customer]`, `fUnidades[farmname]`) — qualquer usuário com acesso ao relatório vê todos os 10 clientes/70 fazendas. Para o app unificado, a chave natural de RLS é `idcustomer` (cliente/conta Metryx) e, em granularidade fina, `idpropfaz` (`CONCAT(idcustomer, idfarm)`); **todas** as tabelas de fato desta versão carregam `idpropfaz` ou `idcustomer`+`idfarm`, exceto `fSaldoGado` (só `idpropfaz`).

---

## 4. Colunas calculadas (DAX) — todas

Status: ✅ OK · ⚠️ funciona mas com problema · ❌ quebrada (referência inexistente → erro/blank) · 💤 não usada em medida nem visual.

### 4.1 `financeiroDre`

| Coluna | DAX (resumo) | Regra de negócio | SQL sugerido | Status |
|---|---|---|---|---|
| `Desembolso` | `IF([desembolso_cat]="DCM", [amountpaid]*-1, 0)` | Valor pago que conta como desembolso, com sinal negativo; **independe de `type`** (crédito em centro DCM também conta) | `CASE WHEN desembolso_cat='DCM' THEN -amountpaid ELSE 0 END` | ⚠️ |
| `Custeio` | `IF([custeio_cat]="CCM", [amountpaid], 0)` | Valor pago que conta como custeio (positivo); inclui centros de investimento marcados CCM | `CASE WHEN custeio_cat='CCM' THEN amountpaid ELSE 0 END` | ⚠️ |
| `F/V` | `IF(tipo_custeio_cat IN {"Receita Pec","Receita outras","Receita Agr"},"A - RECEITAS", IF(="CF","B - CUSTO FIXO", IF(="CV","C - CUSTO VARIAVEL", IF(="Financiamentos","D - FINANCIAMENTOS","VERIFICAR"))))` | Agrupador DRE fixo/variável | `CASE WHEN tipo_custeio_cat IN ('Receita Pec','Receita outras','Receita Agr') THEN 'A - RECEITAS' WHEN tipo_custeio_cat='CF' THEN 'B - CUSTO FIXO' WHEN tipo_custeio_cat='CV' THEN 'C - CUSTO VARIAVEL' WHEN tipo_custeio_cat='Financiamentos' THEN 'D - FINANCIAMENTOS' ELSE 'VERIFICAR' END` | ✅ (só usado num filtro vazio) |
| `Class subcenter` | IF aninhado com listas de `subcenter` → `INVESTIMENTOS` / `MAO DE OBRA PERMANENTE` / `DESPESAS COM ATIVIDADES PRODUTIVAS` / `DEMAIS DESPESAS` | Agrupamento por subcentro. **As listas 2 e 3 têm espaço à esquerda** (`" Aluguéis e Condomínios"`), só casam se o dado vier com espaço; a lista 1 mistura com/sem espaço. Lista "MAO DE OBRA PERMANENTE" contém despesas administrativas/manutenção (rótulo enganoso) | `CASE WHEN subcenter IN (...) THEN 'INVESTIMENTOS' WHEN subcenter IN (...) THEN 'MAO DE OBRA PERMANENTE' WHEN subcenter IN (...) THEN 'DESPESAS COM ATIVIDADES PRODUTIVAS' ELSE 'DEMAIS DESPESAS' END` (normalizar com `trim`) | ⚠️💤 |
| `Type Operation` | `financeiroDre[Credito/Debito]` | resto do modelo de planilhas | — (usar `type`) | ❌💤 |

Listas completas de `Class subcenter` (para a tabela de-para do app):
* **INVESTIMENTOS**: Compra equipamentos informática, telefonia e comunicação; Novas instalações pecuárias; Novas instalações residenciais; Novas construções, barracões e outros; Novos móveis e eletrodomésticos; Nova rede elétrica; Projetos, medições e outros; Reflorestamento; Solo, contenções, destoca e recuperação; Compra veículos, tratores e implementos; Formação de pasto; Imóveis rurais e urbanos; Investimento em segurança; Nova rede hidráulica; Novas cercas; Novas estradas e pontes; Novas ferramentas e equipamentos; ␣Cursos e treinamentos; ␣Eventos e presentes; ␣Benefícios à funcionarios; ␣Uniformes e EPI; ␣Compra de aves; ␣Compra suínos; ␣Compra tropa de serviço; ␣Compra tropa reprodução; ␣Compra de ovinos.
* **MAO DE OBRA PERMANENTE** (todos com ␣ inicial): Aluguéis e Condomínios; Comunicação e energia da fazenda; Contabilidade, jurídico, consultorias e sistemas; Deslocamento, alimentação e hospedagem; Despesa financeira; Despesas casa sede; Outras despesas administrativas; Horta, pomar e jardins; Manutenção rede elétrica; Manutenção rede hidráulica; Manutenção de cercas; Manutenção, construções, barracões e outros; Manutenção em segurança; Manutenção estradas e pontes; Manutenção ferramentas e equipamentos; Manutenção informática; Manutenção instalações pecuárias; Manutenção instalações residenciais; Manutenção móveis e eletrodomésticos; Combustíveis; Manutenção e conserto de máquinas e implementos; Seguros, impostos, multas e outros; Custeio de aves; Custeio tropa reprodução; Ovinos; Suínos; Taxas e impostos; Taxas e impostos. S/Venda; Taxas e impostos S/Lucro; Taxas, Impostos Sobre Propriedade, ITR, IPTU.
* **DESPESAS COM ATIVIDADES PRODUTIVAS**: (com ␣) Colheita e transporte; Corretivos, fertilizantes e adubos; Defensivos; Despesas comerciais e outras; Parceria agrícola; Sementes/Mudas, tratamentos e serviços; Energia para irrigação agrícola; Aluguel de Máquinas Terceirizadas; Preparo de Solo␣ — e (sem ␣) os mesmos + Arrendamento de pastagem; Manutenção de pastagem; Despesas comercias, fretes e comissões; Identificação animal e rastreamento; Nutrição; Reprodução; Sanidade; Melhoramento genético; Energia para irrigação pecuária.
* senão **DEMAIS DESPESAS**.

### 4.2 `fMetasDre`

| Coluna | DAX | Regra | SQL | Status |
|---|---|---|---|---|
| `Desembolso` | `IF([desembolso_cat]="DCM", [valorprevisto]*-1, 0)` | desembolso previsto (negativo) | `CASE WHEN desembolso_cat='DCM' THEN -valorprevisto ELSE 0 END` | ✅ |
| `Custeio` | `IF([custeio_cat]="CCM", [valorprevisto], 0)` | custeio previsto | `CASE WHEN custeio_cat='CCM' THEN valorprevisto ELSE 0 END` | ✅ |
| `F/V` | idem `financeiroDre[F/V]` | | idem | ✅💤 |

### 4.3 `fPlanejadoxRealizado`

| Coluna | Regra | Status |
|---|---|---|
| `Classificacao2` | `SWITCH(costcenter, …)` → `A - RECEITAS` (Arrendamento, Cultura - Receita, Rebanho, Receitas financeiras, Receitas outros, Receitas Parque de máquinas, Vendas outros animais), `B - INVESTIMENTOS` (Investimentos em infraestrutura / outros animais / RH, Rebanho Investimento), `C - CUSTEIO` (mesma lista do `D - CUSTEIO` do SQL), `D - OUTROS CRÉDITOS` (Empréstimos sócios crédito, Financiamentos créditos), `E - OUTROS DÉBITOS` (Dividendos, Empréstimos sócios débito, Financiamentos débitos, Outros Débitos), `""` (Almoxarifado, Aporte de capital, Prejuízo Administração, Venda de Imóveis); `DESEMBOLSO` → BLANK. **Esquema de letras diferente do `classificacao` do SQL** (B/C/D/E vs C/D/E/F). Usada só por `Icon Acc`. SQL: `CASE costcenter WHEN … END`. | ⚠️ |

### 4.4 Vendas

| Tabela[Coluna] | DAX | Regra | SQL | Status |
|---|---|---|---|---|
| `pecuarioVendaAbate[Total de @]` | `[peso_arroba] * [qtd]` | @ de carcaça vendidas (`deadarrobaavg × amount`) | `deadarrobaavg * amount` | ✅ |
| `pecuarioVendaAbate[Peso Morto Total]` | `[pesomorto_total]` | cópia | `amount * deadweightavg` | ✅ (duplicada) |
| `pecuarioVendaAbate[tipovenda]` | `"Abate"` | constante | `'Abate'` | ✅ |
| `pecuarioVendaAbate[Total Value]` | `[valueWeight] * [weightAvg]` | resto do modelo de planilhas | — | ❌💤 |
| `pecuarioVendaAbate[teste]` | `[valueWeight] / 15` | teste | — | ❌💤 |
| `pecuarioVendaEmPe[Total de @]` | `[pesovivo_total] / 30` | @ **de carcaça equivalentes** a partir do peso vivo (rendimento implícito 50%: 30 kg vivo = 1 @) | `weighttotal / 30.0` | ✅ |
| `pecuarioVendaEmPe[Peso Morto]` | `[pesovivo_total] / 30` | idêntica a `Total de @` (nome errado: é @, não kg) | `weighttotal / 30.0` | ⚠️ |
| `pecuarioVendaEmPe[Peso Total]` | `[pesovivo_total]` | cópia | `weighttotal` | ✅ |
| `pecuarioVendaEmPe[tipovenda]` | `"Em Pe"` | constante | `'Em Pe'` | ✅ |

### 4.5 Compras

| Coluna | DAX | Regra | SQL | Status |
|---|---|---|---|---|
| `pecuarioCompras[Paid]` | `[valo_kg] * [total_peso]` | Pretende "valor pago"; algebricamente = `totalfaturamento/(amount*weighttotal) * weighttotal` = **`totalfaturamento/amount` (R$ por cabeça)** | correto seria `totalfaturamento` | ❌ (lógico) |
| `pecuarioCompras[Total de @]` | `[peso_arroba] * [qtd]` | `weighttotal/15 × amount` — @ vivas totais **se** `weighttotal` for por cabeça; se for total (como em vendas), multiplica duas vezes | `(weighttotal/15.0) * amount` ou `weighttotal/15.0` (validar) | ⚠️ |
| `Analytics Measures[Purchased Quantity MALE]` | `CALCULATE([Purchased Quantity], pecuarioCompras[sexo]="MACHO")` | coluna (não medida!) na tabela de medidas: total geral de machos comprados, congelado no refresh | `SUM(amount) FILTER (WHERE gender='MACHO')` | ⚠️💤 |

### 4.6 Metas de venda

| Coluna | DAX | Regra | SQL | Status |
|---|---|---|---|---|
| `fMetasAbate[pesovivo_total]` | `[weight] * [amount]` | peso vivo total previsto (assume `weight` por cabeça) | `weight*amount` | ✅ |
| `fMetasAbate[pesomorto_total]` | `([weight] * ([yield]/100)) * [amount]` | carcaça prevista (kg) com rendimento em % | `weight*(yield/100.0)*amount` | ✅ |
| `fMetasAbate[Total de @]` | `[arrobaweight] * [amount]` | @ de carcaça previstas | `arrobaweight*amount` | ✅ |
| `fMetasEmPe[pesovivo_total]` | `[weight] * [amount]` | | `weight*amount` | ✅ |
| `fMetasEmPe[Total de @]` | `([weight] * [amount]) / 30` | @ equivalentes (50%) | `weight*amount/30.0` | ✅ |
| `fMetasEmPe[pesomorto_total]` | `([weight] * [amount]) * [yield]` | **sem /100 e `yield` vazio** (cardinalidade 1) → sempre blank | — | ❌ (lógico) |

### 4.7 Rebanho / mortes / estoque

| Coluna | DAX | Regra | Status |
|---|---|---|---|
| `pecuarioRebanhoMedioMensal[farm]` | `"FAZENDA EXEMPLO"` | placeholder do template | 💤 |
| `pecuarioRebanhoMedioMensal[Forecast]` | `([qtd_cab]*0.1) + [qtd_cab]` | "meta" fake +10%; coluna `qtd_cab` não existe | ❌💤 |
| `pecuarioMortes[forecast]` | `INT(qtd*0.8 + qtd)` | "meta" fake +80% | ⚠️💤 |
| `fSaldoGado[UltimaDataMovimentacao]` | para a chave (owner, farmname, category, retironame): soma de `amountacc` na **maior** `date` da chave em toda a tabela | apesar do nome, é o **último saldo** da chave (número), constante por chave. SQL: `SUM(amountacc) OVER (PARTITION BY owner,farmname,category,retironame) FILTER date = MAX(date) OVER (…)` | ⚠️ (só usada em `Saldo 32322`, não usada) |

### 4.8 Calendário e auto-date

* `dCalendar[Classificador Mês-Ano] = 100*[Ano] + [Mês]` (chave de ordenação AAAAMM) — SQL `EXTRACT(YEAR)*100+EXTRACT(MONTH)`.
* `LocalDateTable_*`/`DateTableTemplate_*`: `Ano=YEAR`, `MonthNo=MONTH`, `Mês=FORMAT(,"MMMM")`, `QuarterNo=INT((MonthNo+2)/3)`, `Trimestre="Qtr "&QuarterNo`, `Dia=DAY` — gerados automaticamente, sem valor de negócio (30 colunas).

---

## 5. Medidas (todas as 220)

### 5.0 Convenções usadas nas fórmulas

Aliases de tabela: `N`=pecuarioNascimento, `RM`=pecuarioRebanhoMedioMensal, `MRM`=fMetasRebanhoMedio, `VA`=pecuarioVendaAbate, `VE`=pecuarioVendaEmPe, `C`=pecuarioCompras, `CO`=Compras, `M`=pecuarioMortes, `FD`=financeiroDre, `MD`=fMetasDre, `MC`=fMetasCompras, `MA`=fMetasAbate, `ME`=fMetasEmPe, `MN`=fMetasNascimentos, `MM`=fMetasMortes, `SG`=fSaldoGado, `PR`=fPlanejadoxRealizado.

`F` = filtros correntes (cliente/fazenda via `fUnidades`, período via `dCalendar`, e filtros de visual como sexo/grupo). `:max` = `MAX(dCalendar[Data])` no contexto; `:sel_ini`/`:sel_fim` = limites da seleção do usuário (`ALLSELECTED`).

Padrões de inteligência de tempo encontrados (referenciados nas tabelas):

| Código | DAX | Equivalente SQL |
|---|---|---|
| **ACC-ALL** | `CALCULATE(x, FILTER(ALL(dCalendar), Data <= MAX(Data)))` | `WHERE data <= :max` (ignora o início da seleção; começa em 2024-07-01, início do calendário) |
| **ACC-SEL** | `CALCULATE(x, FILTER(ALLSELECTED(dCalendar), Data <= MAX(Data)))` | `WHERE data BETWEEN :sel_ini AND :max` |
| **ACC-SEL-EOM** | idem com `Data <= EOMONTH(MAX(Data),0)` | `WHERE data BETWEEN :sel_ini AND fim_do_mes(:max)` |
| **YTD/ALL** | `IF([Count of Selected Years]=1, x em FILTER(ALL(dCalendar), Data<=MAX && YEAR(Data)=YEAR(MAX)), x em ACC-ALL)` | 1 ano civil selecionado → `data BETWEEN date_trunc('year', :max) AND :max`; senão ACC-ALL |
| **YTD/SEL** | idem com `ALLSELECTED` | 1 ano → `data BETWEEN greatest(:sel_ini, date_trunc('year', :max)) AND :max`; senão ACC-SEL |
| **ANO** | `CALCULATE(x, ALLEXCEPT(dCalendar, dCalendar[Ano]))` | ano civil inteiro do contexto: `WHERE extract(year from data) = :ano` |
| **ULT-MÊS** | `FILTER(ALL(dCalendar), Data >= EOMONTH(MAX(ALLSELECTED),-1)+1 && Data <= MAX(ALLSELECTED))` | último mês da seleção: `data BETWEEN date_trunc('month', :sel_fim) AND :sel_fim` |
| **+0** | `… + 0` | `COALESCE(x, 0)` (força zero em vez de vazio) |

Helper central — **`Count of Selected Month`** (usado como "nº de meses" em quase todos os KPIs por cabeça/mês):
```
VAR MesesComDados = FILTER(VALUES(dCalendar[Mês]), CALCULATE(SUM(RM[amount])) > 0)
RETURN COUNTROWS(MesesComDados)
```
= quantidade de **números de mês (1–12)** no contexto em que há rebanho médio > 0. SQL: `SELECT COUNT(DISTINCT extract(month from RM.data)) FROM RM WHERE F GROUP BY … HAVING SUM(amount) > 0`. ⚠️ Em seleção de vários anos, jan/2025 e jan/2026 contam como 1 mês (subconta → infla KPIs por mês); depende da existência de rebanho médio, não do calendário.

Status: ✅ OK · ⚠️ funciona com ressalva/bug lógico · ❌ quebrada · 💤 não usada em visual (direta ou indiretamente). "Uso" = página(s) onde aparece.

---

### 5.1 Rebanho médio, contagens e estoque (saldo)

| Medida | Significado | Fórmula (pseudo-SQL) | Tempo / filtros | Uso / status |
|---|---|---|---|---|
| `Mean Month` | **Rebanho médio mensal** (cab.) | `SUM(RM.amount) / [Count of Selected Month]` | contexto F | Movimentação (card "Rebanho Médio Cab") ✅; base de desembolso/cab |
| `Count of Selected Month` | nº de meses com rebanho | ver 5.0 | contexto F | indireto ⚠️ |
| `Count of Selected Years` | nº de anos civis na seleção | `COUNT(DISTINCT extract(year from data))` sobre `ALLSELECTED(dCalendar)` | seleção | indireto ✅ |
| `Mean Month Accumulated` | rebanho médio acumulado | `IF(anos=1, Mean Month em YTD/SEL, Mean Month em ACC-SEL) / [Count of Selected Month]` | YTD/SEL | 💤 ⚠️ divide duas vezes por nº de meses |
| `Mean Month Accumulated - Aux (Desembolso)` | **rebanho médio do período acumulado** (denominador do desembolso/custeio por cabeça) | `IF(anos=1, [Mean Month] em YTD/SEL, [Mean Month] em ACC-SEL)` — dentro do período, `Mean Month` = Σ amount / nº meses do período | YTD/SEL | indireto ✅ |
| `Mean Month Accumulated - Aux (Desembolso) - Forecast` | "rebanho médio previsto acumulado" | **idêntica** à anterior (usa `[Mean Month]` realizado) | YTD/SEL | indireto ⚠️ previsto = realizado |
| `Mean Month - forecast` | rebanho médio "previsto" | `SUM(MRM.amount) / [Count of Selected Month]` (+ USERELATIONSHIP redundantes) | F | indireto ⚠️ `MRM` é cópia do realizado |
| `Mean Month Accumulated - Forecast` | soma acumulada do rebanho "previsto" | `SUM(MRM.amount) WHERE amount IS NOT NULL` em ACC-SEL (não divide por meses) | ACC-SEL | 💤 |
| `Count Mean Month` | nº de **linhas** de rebanho médio no período | `COUNT(*) FROM RM` em YTD/ALL | YTD/ALL | 💤 (nome sugere meses, conta linhas) |
| `Count Mean Month Accumulated` | nº de meses de calendário na seleção até `:max` | `COUNT(DISTINCT mesano) FROM dCalendar WHERE data BETWEEN :sel_ini AND :max` | ACC-SEL | indireto ✅ (código YTD comentado) |
| `Rebanho Median Month` | (pretendia) rebanho médio/meses | `DIVIDE([], [Count Mean Month Accumulated])` | — | ❌ erro de sintaxe (`[]`) 💤 |
| `Saldo Acumulado` (em `fSaldoGado`) | **Estoque (saldo) de cabeças na data final do contexto** | `SELECT SUM(amountacc) FROM SG WHERE SG.date = :max AND F(cliente/fazenda/categoria/retiro)` (remove filtro de calendário; mantém owner/farm/category/retiro e fUnidades.customer/farmname) | data exata = `:max` | Movimentação (gráfico "ESTOQUE POR CATEGORIA" + card) ⚠️ **retorna vazio quando `:max` não é fim de mês** (ex.: mês/ano corrente terminam "hoje") |
| `Saldo UltimaDataMovimentacao` (em `fSaldoGado`) | maior `SG.date` até `:max` | `SELECT MAX(date) FROM SG WHERE date <= :max` (filtros de chave comentados) | ACC-ALL | 💤 |
| `Saldo 32322` (em `fSaldoGado`) | soma da coluna `UltimaDataMovimentacao` | `SUM(SG.UltimaDataMovimentacao)` | F | 💤 nome de teste |
| `SaldoCategoria_Final` (em `fSaldoGado`) | estoque final por retiro×categoria na última data ≤ `:max` | para cada (retironame, category) visível: `MAX(amountacc)` na `MAX(date) <= :max`; soma | até `:max` | 💤 (versão mais robusta que `Saldo Acumulado`, ignora owner/farm na chave) |

Visual que **não usa medida**: "ESTOQUE FINAL MENSAL" = `SUM(SG.amountacc)` por `dCalendar[mesano]` (fim de mês via relacionamento). Card `SUM(RM.amount)` (Movimentação) = soma (não média) do rebanho médio no período.

### 5.2 Balanço / movimentação de estoque (entradas e saídas) — **não implementado**

| Medida | Pretendia | Fórmula | Status |
|---|---|---|---|
| `Stock` | quantidade com sinal das movimentações | `SUM(fMovGado[QTD C])` | ❌ tabela `fMovGado` não existe (resto do Ciclo Completo) 💤 |
| `Stock Accumulated Inicial` | estoque inicial do período | `[Stock]` com `Data < EOMONTH(MIN(Data),-1)+1` (antes do 1º dia do mês inicial), ALL(dCalendar) | ❌ 💤 |
| `Stock Accumulated Final` | estoque final | `[Stock]` em ACC-ALL | ❌ 💤 |
| `Change Category entry` | entradas por mudança de categoria | `[Stock] WHERE OPERAÇÃO='Mud. de Categoria' AND Type Operation='Entrada'` | ❌ 💤 |
| `Change Category exit` | saídas por mudança de categoria | idem `'Saída'` | ❌ 💤 |
| `Weaning Entry` | entradas por desmame | `[Stock] WHERE OPERAÇÃO='Desmame' AND 'Entrada'` | ❌ 💤 |
| `Weaning Exit` | saídas por desmame | `[Stock] WHERE OPERAÇÃO='DESMAME' AND 'Saída'` | ❌ 💤 |
| `Buy` | compras (cab.) | `SUM(CO.amount)` | ⚠️ 💤 `Compras.date` inativo → não filtra por período |
| `Sell` | vendas (cab.) | `SUM(VA.qtd)` (só abate) | ⚠️ 💤 ignora venda em pé |
| `Birth` | nascimentos | `SUM(N.amount)` | ⚠️ 💤 sem relação de data |
| `Death` | mortes | `SUM(M.qtd)` | ✅ 💤 (duplicata de `Dead Quantity` sem +0) |
| `comsuption / donation` | consumo/doação | `SUM(M.qtd) WHERE causa = 'Consumo Abate'` | ✅ 💤 (consumo é tratado como causa de morte) |

Não existem medidas para transferências (entrada/saída), saldo inicial, nem uso de `pecuarioDesmame`. A API oferece `transferencia-animal-pecuario`, `mudanca-categoria-pecuario`, `saldo-inical-pecuario` e `desmames-pecuario` — insumos para o balanço no app.

### 5.3 Área, lotação e UA

| Medida | Significado | Fórmula | Status / uso |
|---|---|---|---|
| `Mean Month - UA` | rebanho médio em UA | **`0`** (comentário: "Não tem por UA na API"; original `SUM(RM[qtd_ua])`) | ⚠️ placeholder |
| `Mean Month Accumulated - UA` | UA média acumulada | padrão YTD/SEL sobre `[Mean Month - UA]` / nº meses | sempre 0 |
| `UA Median Month` | UA média no período (card "Rebanho Médio UA") | `DIVIDE([Mean Month Accumulated - UA], [Count Mean Month Accumulated])` | Movimentação; sempre 0 ⚠️ ("Median" = média) |
| `UA Median Ha` | lotação UA/ha (card "Lotação UA") | `[UA Median Month] / (SUM(fArea[Área_total]) / [Count of Selected Month])` | ❌ `fArea` não existe; Movimentação (visual também com filtro inválido) |
| `Mean Month Ha` | lotação cab/ha (card "Lotação Cab") | `[Mean Month] / (500 / [Count of Selected Month])` = `SUM(RM.amount) / 500` | ⚠️ área **fixa 500 ha**; algebricamente é soma (não média) ÷ área; Movimentação (filtro de visual inválido) |
| `Lotation` | lotação UA/ha | `[Mean Month Accumulated - UA] / 2911 + 0` | ⚠️ área **fixa 2911 ha** (herdada do Ciclo Completo), numerador 0 💤 |
| `Lotation - Forecast` | lotação "prevista" | `[Lotation] * 1.1` | ⚠️ meta fake +10% 💤 |
| `Lotation - Forecast - MAX` | máximo do gauge | `[Lotation - Forecast] * 1.4` | 💤 |

> Para o app: UA = Σ(cab × peso médio kg)/450 seria calculável — a API `rebanho-medio-pecuario` devolve `weight` (não selecionado pelo SQL) — e a área pode vir de `utilizacao-pasto` (`areaTotal`, `areaProdutiva`). Nenhuma constante 450 kg existe neste modelo.

### 5.4 Nascimentos

⚠️ Geral: `pecuarioNascimento` **não tem relacionamento de data** → todas as medidas de nascimento realizado ignoram filtros de Ano/Mês/mesano (mostram o total histórico do cliente/fazenda em todo mês). As previstas (`MN`) filtram normalmente.

| Medida | Significado | Fórmula | Tempo | Uso / status |
|---|---|---|---|---|
| `Birth Quantity` | nascimentos (cab.) | `COALESCE(SUM(N.amount),0)` | (sem data) | Movimentação, Nascimento ⚠️ |
| `Birth Quantity - Forecast` | nascimentos previstos | `SUM(MN.amount)` (USERELATIONSHIP redundante) | F | Nascimento ⚠️ soma **todas as versões de plano** (`plversioncode`) |
| `% Birth x Forecast` | % realizado/meta | `[Birth Quantity] / [Birth Quantity - Forecast]` | F | Movimentação, Nascimento ⚠️ |
| `Birth Quantity Accumulated` | nascimentos acumulados | `[Birth Quantity]` em YTD/ALL | YTD/ALL | Nascimento ⚠️ (constante, sem data) |
| `Birth Quantity Accumulated - Forecast` | previstos acumulados | `[Birth Quantity - Forecast]` em YTD/ALL | YTD/ALL | Nascimento ✅ |
| `Birth Quantity - Forecast - Const` | meta do ano inteiro | `[Birth Quantity - Forecast]` em ANO | ANO | 💤 |
| `% Birth x Forecast (Year)` | realizado / meta anual | `[Birth Quantity] / [Birth Quantity - Forecast - Const]` | | 💤 |
| `IN - % Female Birth` | % de fêmeas nos nascimentos | `SUM(N.amount WHERE gender='FÊMEA') / SUM(N.amount)` | | Nascimento ✅ |
| `IN - % Male Birth` | % de machos | `SUM(N.amount WHERE gender='MACHO') / SUM(N.amount)` | | Nascimento ✅ |
| `Average Birth Weight` | peso médio ao nascer | `SUM(N[peso_nasc]) / SUM(N[qtd])` | | ❌ colunas não existem (API não fornece peso ao nascer) 💤 |

Visuais também usam `SUM(N.amount)` e `SUM(MN.amount)` direto, com filtro de visual por `gender` ('Fêmea'/'Macho').

### 5.5 Mortes

| Medida | Significado | Fórmula | Tempo | Uso / status |
|---|---|---|---|---|
| `Dead Quantity` | mortes (cab.) | `COALESCE(SUM(M.qtd),0)` | F | Movimentação, Mortes (cards por grupo via filtro de visual `grupo_categoria` = BEZERROS/JOVENS/ADULTOS; gráfico por `causa`) ✅ |
| `Dead Quantity forecast` | mortes previstas | `SUM(MM.amount)` | F | Mortes (gráfico mensal) ⚠️ soma todas as versões de plano |
| `Dead Quantity - Forecast` | idem (duplicata exata) | `SUM(MM.amount)` | F | Mortes (cards) ⚠️ cards por grupo **não filtram o grupo** (filtro aplicado em `pecuarioVendaAbate[sexo]`, sem efeito) → mostram o total em cada grupo |
| `% Death x Death Forecast` | % realizado/meta | `[Dead Quantity] / [Dead Quantity forecast]` | F | Movimentação ✅ |
| `Dead Quantity Accumulated` | mortes acumuladas | `[Dead Quantity]` em **ACC-ALL** | desde jul/2024 | Mortes ⚠️ (não respeita início da seleção) |
| `Dead Quantity Accumulated - Forecast` | previstas acumuladas | `[Dead Quantity forecast]` em **ACC-SEL** | seleção | Mortes ⚠️ comparado com realizado em base diferente (ACC-ALL × ACC-SEL) |
| `Accumulated Death` | mortes YTD | `[Dead Quantity]` em YTD/ALL | YTD/ALL | 💤 |
| `Const Death` | mortes do ano inteiro | `[Dead Quantity]` em ANO | ANO | 💤 |
| `% Death Accumulated` | YTD / ano | `[Accumulated Death] / [Const Death]` | | 💤 |
| `% Mortality ( AVG Month)` | **Índice de mortalidade sobre rebanho médio** | `[Dead Quantity] / [Mean Month]` = mortes ÷ rebanho médio mensal do período | F | Mortes (cards "% Sobre Rebanho Médio") ⚠️ ver nota |
| `% Mortality` | **Mortalidade sobre nascimentos** | `[Dead Quantity Accumulated] / [Birth Quantity Accumulated]` | ACC-ALL / YTD-ALL (nascimentos sem data) | Mortes (card BEZERROS "% Sobre Nascimento") ⚠️ |
| `% Realized Indicator` | mortes / Σ rebanho médio | `[Dead Quantity] / SUM(RM.amount)` | F | 💤 (Σ, não média) |
| `% Forecast Indicator` | mortes previstas / Σ rebanho "previsto" | `[Dead Quantity forecast] / SUM(MRM.amount)` | F | 💤 |
| `% Realized Indicator Accumulated` | mortes acumuladas / rebanho médio acumulado | `DIVIDE([Dead Quantity Accumulated], [Mean Month Accumulated]/[Count Mean Month Accumulated], 0)` | mistos | 💤 |
| `% Forecast Indicator Accumulated` | previsto | `DIVIDE([Dead Quantity Accumulated - Forecast], [Mean Month Accumulated - Forecast]/[Count Mean Month Accumulated], 0)` | ACC-SEL | 💤 |
| `Dead KG Amount` | peso morto (kg) | `SUM(M.peso_total)` | F | 💤 |
| `Dead Quantity (Teens)` | mortes JOVENS | `SUM(M.qtd) WHERE grupo_categoria='JOVENS'` | F | 💤 (visual usa filtro) |
| `Dead Quantity (Adults)` | mortes ADULTOS | `… = 'ADULTOS'` | F | 💤 |
| `Dead Quantity (Calves)` | mortes BEZERROS | `… = 'BEZERROS'` | F | 💤 |

Nota sobre os cards da página Mortes: (a) BEZERROS — `Dead Quantity` filtra `grupo_categoria='BEZERROS'`, mas `% Mortality ( AVG Month)` filtra `grupo_categoria IN ('Bezerras Mamando','Bezerros Mamando')` **e** o rebanho médio por uma lista fixa de 19 nomes de categoria de bezerros de clientes específicos (`'04) Bezerro M'`, `'05) Bezerras F'`, `'BEZERRA'`, `'Bezerra 0 a 8 Meses'`, `'Bezerra 8 a 12 Meses'`, `'BEZERRA DESMAMA'`, `'BEZERRA FEMEA'`, `'Bezerra Mamando'`, `'BEZERRAS'`, `'BEZERRO'`, `'Bezerro 0 a 8 Meses'`, `'Bezerro 08 a 12 Meses'`, `'Bezerro 8 a 12 Meses'`, `'BEZERRO DESMAMA'`, `'BEZERRO MACHO'`, `'Bezerro Mamando'`, `'BEZERROS'`, `'BO - Bezerro 00 a 08 Meses'`, `'BA - Bezerra 00 a 08 Meses'`); (b) JOVENS — `% Mortality ( AVG Month)` sem filtro de grupo (= mortalidade do rebanho todo); (c) ADULTOS — filtra mortes ADULTOS mas o rebanho médio é o total; (d) GERAL — total/total.

### 5.6 Compras

| Medida | Significado | Fórmula | Tempo | Uso / status |
|---|---|---|---|---|
| `Purchased Quantity` | cabeças compradas | `COALESCE(SUM(C.qtd),0)` | F | Compras (gráfico) ✅ |
| `Purchase Quantity` | nº de lotes/linhas de compra | `COUNT(*) FROM C` | F | 💤 |
| `Purchased Quantity FEMALE` | cab. fêmeas compradas | `SUM(C.qtd) WHERE sexo='FÊMEA'` | F | 💤 |
| `Purchased Quantity - Forecast` | compra prevista (cab.) | `SUM(MC.amount)` | F | Compras ✅ |
| `% Purchased Quantity` | % realizado/meta | `[Purchased Quantity]/[Purchased Quantity - Forecast]` | F | Movimentação (filtro de visual sem valor) ✅ |
| `Purchase Quantity Accumulated` | cab. compradas acumuladas | `COALESCE(SUM(C.qtd),0)` em ACC-SEL | ACC-SEL | Compras (linha) ✅ |
| `Total Paid` | "investimento realizado" em compra (R$) | `SUM(C.Paid)` = **Σ (totalfaturamento/amount)** = soma de R$/cabeça | F | Compras (gráfico "RELAÇÃO DESEMBOLSO DE COMPRAS", cards "Inv. Realizado") ❌ lógico — correto: `SUM(C."VALOR TOTAL")` |
| `Total Paid - Forecast` | investimento previsto | `COALESCE(SUM(MC.totalvalue),0)` | F | Compras ✅ |
| `@ AVG Price Purchase` | preço médio da @ comprada | `SUM(C."VALOR TOTAL") / SUM(C."Total de @")` com `Total de @ = weighttotal/15 × qtd` | F | Compras ⚠️ depende da semântica de `weighttotal` (ver 4.5) |
| `AVG Purchase Price KG` | R$/kg comprado | `COALESCE(SUM("VALOR TOTAL")/SUM(total_peso),0)` | F | Compras ✅ (se `weighttotal` = peso total) |
| `AVG Purchase Price KG (Forecast)` | R$/kg previsto | `COALESCE(SUM(MC.totalvalue)/SUM(MC.weight),0)` | F | Compras ⚠️ se `weight` for por cabeça deveria ser `Σ weight×amount` |
| `IN AVG - Peso Médio de Compra` | peso médio comprado (kg/cab) | `SUM(C.total_peso)/SUM(C.qtd)` | F | Compras ✅ (se total) |
| `IN AVG - Peso Médio de Compra (Forecast)` | peso médio previsto | `SUM(MC.weight)/SUM(MC.amount)` | F | Compras ⚠️ inconsistente com `pesovivo_total = weight*amount` usado nas metas de venda |
| `Ágio` | ágio da reposição | `([@ AVG Price Purchase] − [AVG Price @ (Em Pe + Abate)]) / [AVG Price @ (Em Pe + Abate)]` (preço da @ comprada vs. @ vendida) | F | Compras ⚠️ (herda dúvidas de @ da compra) |
| `VALORCALC` (em `fMetasCompras`) | ? | `CALCULATE(SUM(fMetasCompras[VALOR TOTAL]), USERELATIONSHIP(fUnidades[PROPRIETARIO], pecuarioCompras[proprietÁrio]))` | | ❌ colunas/relacionamento inexistentes 💤 |

### 5.7 Vendas — abate (frigorífico)

| Medida | Significado | Fórmula | Tempo | Uso / status |
|---|---|---|---|---|
| `Amount Saled (Abate)` | cabeças vendidas p/ abate | `SUM(VA.qtd)` | F | Venda Abate (gráfico), Movimentação (card "Vendas") ✅ |
| `Invoicing Abate` | faturamento abate (R$) | `SUM(VA.faturamento)` | F | Venda Abate ✅ |
| `AVG Price @ Dead Sale` | preço médio da @ (carcaça) | `SUM(VA.faturamento) / SUM(VA.deadarrobaavg × VA.qtd)` | F | Venda Abate ✅ |
| `AVG Ticket Dead Sale` | ticket médio (R$/cab) | `SUM(faturamento)/SUM(qtd)` | F | 💤 |
| `Rendimento Carcaça` | rendimento de carcaça | `SUM(VA.pesomorto_total)/SUM(VA.pesovivo_total)` = Σ(amount×deadweightavg)/Σweighttotal | F | Venda Abate ✅ |
| `Peso em @ Abate` | @ de carcaça por cabeça | `(SUM(pesomorto_total)/15) / SUM(qtd)` | F | 💤 |
| `IN - AVG Live Weight` | peso vivo médio (kg/cab) | `SUM(pesovivo_total)/SUM(qtd)` | F | Venda Abate ✅ |
| `Invoicing Accumulated (Abate)` | **cabeças** vendidas acumuladas (nome errado) | `COALESCE(SUM(VA.qtd),0)` em ACC-SEL | ACC-SEL | Venda Abate (linha) ⚠️ nome |
| `Amount Head Saled Accumulated` | cab. acumuladas | `[Amount Saled (Abate)]` em ACC-ALL | ACC-ALL | 💤 |
| `Amount Saled - Forecast (Abate)` | cab. previstas abate | `SUM(MA.amount)` | F | Venda Abate ✅ |
| `Incoicing - Forecast` (sic) | faturamento previsto abate | `SUM(MA.totalvalue)` | F | Venda Abate ✅ |
| `IN - Invoicing - Forecast (Abate)` | idem + 0 | `COALESCE(SUM(MA.totalvalue),0)` | F | 💤 duplicata |
| `AVG Price @ Dead Sale - Forecast` | preço @ previsto | `SUM(MA.totalvalue)/SUM(MA.arrobaweight × MA.amount)` | F | Venda Abate ✅ |
| `IN - Rendimento Carcaça (Forecast)` | rendimento previsto | `SUM(MA.weight×yield/100×amount)/SUM(MA.weight×amount)` | F | Venda Abate ✅ |
| `IN - AVG Live Weight (Forecast)` | peso vivo médio previsto | `SUM(MA.weight)/SUM(MA.amount)` | F | Venda Abate ⚠️ deveria ser `Σ pesovivo_total/Σ amount` |
| `Amount Head Saled - Forecast Accumulated` | previstas acumuladas | `[Amount Saled - Forecast (Abate)]` ACC-ALL | ACC-ALL | 💤 |
| `% Amount Saled` | "% da meta de vendas" | `[Amount Saled - Forecast (Abate)] / [Amount Saled (Abate)]` | F | Movimentação (card "% Meta" de Vendas) ⚠️ **invertida** (previsto/realizado) e só abate |
| `Total de @` | @ vendidas | `[Arroba Value] × [Amount Saled (Abate)]` | | ❌ depende de `Arroba Value` 💤 |
| `Arroba Value` | @ média | `SUM(VA[ArrobaAVG]) + SUM(VE[arrobaAvg])` | | ❌ colunas não existem 💤 |

### 5.8 Vendas — em pé (boi magro/reposição/gado vivo)

| Medida | Significado | Fórmula | Tempo | Uso / status |
|---|---|---|---|---|
| `Amount Saled (Em pe)` | cab. vendidas em pé | `SUM(VE.qtd)` | F | Venda em Pé ✅ |
| `Invoicing (Em Pe )` | faturamento em pé | `COALESCE(SUM(VE.faturamento),0)` | F | Venda em Pé ✅ |
| `AVG Price @ Sale Venda em Pe` | preço médio da @ (equivalente carcaça, 50%) | `SUM(VE.faturamento) / SUM(VE.weighttotal/30)` | F | Venda em Pé ✅ |
| `AVG Price KG Sale Venda em Pe` | R$/kg vivo | `SUM(faturamento)/SUM(weighttotal)` | F | Venda em Pé ✅ |
| `AVG Ticket Sale` | R$/cab | `SUM(faturamento)/SUM(qtd)` | F | 💤 |
| `Peso em @ Em Pe` | @ equivalentes/cab | `(SUM(weighttotal)/30)/SUM(qtd)` | F | 💤 |
| `IN - AVG Live Weight (Em Pe)` | peso vivo médio | `COALESCE(SUM(weighttotal)/SUM(qtd),0)` | F | Venda em Pé ✅ |
| `Amount Saled Accumulated (Em Pe)` | cab. acumuladas | `COALESCE(SUM(VE.qtd),0)` ACC-SEL | ACC-SEL | Venda em Pé ✅ (queryRef antigo "Invoicing Accumulated (Em Pe)") |
| `Amount Saled - Forecast (Em Pe)` | cab. previstas | `SUM(ME.amount)` | F | Venda em Pé ✅ |
| `Incoicing - Forecast (Em Pe)` | faturamento previsto | `SUM(ME.totalvalue)` | F | Venda em Pé ⚠️ cards Fêmea/Macho filtram `fMetasAbate[gender]` (tabela errada) → mostram total |
| `AVG Price @ Sale Venda em Pe - Forecast` | preço @ previsto | `COALESCE(SUM(ME.totalvalue)/SUM(ME.weight×amount/30),0)` | F | Venda em Pé ⚠️ idem filtro |
| `AVG Price KG Sale Venda em Pe - Forecast` | R$/kg previsto | `COALESCE(SUM(ME.totalvalue)/SUM(ME.weight×amount),0)` | F | Venda em Pé ⚠️ idem |
| `IN - AVG Live Weight (Forecast - Em Pe)` | peso vivo previsto | `SUM(ME.weight×amount)/SUM(ME.amount)` | F | Venda em Pé ⚠️ idem |
| `Medida` (em `pecuarioVendaEmPe`) | — | expressão vazia | | ❌ 💤 |

### 5.9 Vendas consolidadas (abate + em pé)

| Medida | Significado | Fórmula | Uso / status |
|---|---|---|---|
| `IN - Invoicing` | faturamento total de gado | `SUM(VE.faturamento)+SUM(VA.faturamento)` | 💤 |
| `Invoicing Accumulated` | faturamento acumulado | `[IN - Invoicing]` ACC-ALL | 💤 |
| `Forecast Accumulated` | faturamento previsto acumulado | `[Incoicing - Forecast]` (só abate) ACC-ALL | 💤 |
| `% Atingido Faturamento` | % meta faturamento | `COALESCE([IN - Invoicing]/[Incoicing - Forecast],0)` | 💤 ⚠️ realizado (abate+em pé) ÷ previsto (só abate) |
| `AVG Price @ (Em Pe + Abate)` | **preço médio da @ vendida (geral)** | `(SUM(VA.faturamento)+SUM(VE.faturamento)) / (SUM(VA.pesomorto_total)/15 + SUM(VE.weighttotal/30))` | Financeiro (gauge "Valor de Venda @") ✅ |
| `AVG Price @ (Em Pe + Abate) - Forecast` | preço @ previsto geral | `(SUM(MA.totalvalue)+SUM(ME.totalvalue)) / (SUM(MA.pesomorto_total)/15 + SUM(ME.pesomorto_total))` | Financeiro ❌ lógico: parte em pé em kg×yield (vazio) → denominador só do abate, numerador inclui em pé |
| `MAX AVG Price @ Forecast` | máximo do gauge | `forecast × 1.15` | Financeiro (UI) |
| `AVG Price @` | — | `[AVG Price @ Dead Sale] + [AVG Price @ Sale Venda em Pe]` (soma de dois preços médios) | ❌ lógico 💤 |
| `Peso em @` | @ por cabeça vendida (geral) | `(SUM(VA.pesomorto_total)/15 + SUM(VE.weighttotal)/30) / (SUM(VA.qtd)+SUM(VE.qtd))` | 💤 |

### 5.10 Transferências, desmame, mudança de categoria

* **Transferências**: nenhuma tabela nem medida (só o rótulo `IN - TRANSFERÊNCIAS`, não usado).
* **Desmame**: `pecuarioDesmame` carregada (com `oldcategory → newcategory`, `amount`, `weight`, `valueweight`) e ligada a `dCalendar`/`fUnidades`, mas **nenhuma medida/visual**. `Weaning Entry/Exit` apontam para `fMovGado` (quebradas).
* **Mudança de categoria**: `Change Category entry/exit` quebradas (fMovGado). Sem tabela Metryx carregada.

### 5.11 Financeiro (fluxo de caixa, desembolso, custeio, por cabeça)

Base: `FD` = pagamentos (`amountpaid`) filtrados no tempo pela **data de vencimento** (`duedate`). `type` ∈ {`Crédito`, `Débito`}.

| Medida | Significado | Fórmula | Tempo | Uso / status |
|---|---|---|---|---|
| `Revenues` | **Receitas** pecuária + agricultura | `SUM(FD.amountpaid) WHERE type='Crédito' AND tipo_custeio_cat IN ('Receita Pec','Receita Agr')` | F (duedate) | Financeiro (card, fluxo de caixa, realizado×planejado) ✅ (exclui "Receita outras" e financeiras) |
| `All Revenues` | receitas incl. outras | idem `IN ('Receita Pec','Receita Agr','Receita outras')` | F | 💤 |
| `Expenses` | despesas (negativo) | `-SUM(FD.amountpaid) WHERE type='Débito'` | F | indireto ✅ (todas as saídas: inclui financiamentos, dividendos, investimentos) |
| `Expenses Graph` | despesas (positivo) | `SUM(FD.amountpaid) WHERE type='Débito'` | F | Financeiro (gráficos) ✅ |
| `Balance` | **saldo de caixa** | `[Revenues] + [Expenses]` = receitas − débitos | F | Financeiro (linha do fluxo de caixa) ✅ |
| `% Resultado` | margem sobre despesas | `[Balance] / (−[Expenses])` | F | 💤 |
| `Finance Indicator` | sinal do resultado | `1 / −1 / 0` conforme `% Resultado` | F | 💤 |
| `Outlay` | **Desembolso** (negativo) | `COALESCE(SUM(FD.Desembolso),0)` = `−SUM(amountpaid) WHERE desembolso_cat='DCM'` | F | Financeiro (card "DESEMBOLSO") ⚠️ independe de `type` |
| `Outlay Forecast` | desembolso previsto (negativo) | `SUM(MD.Desembolso)` = `−SUM(valorprevisto) WHERE desembolso_cat='DCM'` | F | indireto ✅ |
| `% Atingido Outlay` | % desembolso realizado/previsto | `[Outlay]/[Outlay Forecast]` | F | 💤 |
| `Expenses Forecast` | despesas previstas | `SUM(MD.valorprevisto) WHERE type='Débito'` | F | Financeiro ✅ |
| `Revenues Forecast` | receitas previstas | `SUM(MD.valorprevisto) WHERE type='Crédito' AND tipo_custeio_cat IN ('ReceitasPec','ReceitasAgr','ReceitaPec','ReceitaAgr')` | F | Financeiro ❌ **sempre vazio**: os valores reais são `'Receita Pec'`/`'Receita Agr'` (com espaço) |
| `Costing` | **Custeio** realizado | `SUM(FD.Custeio)` = `SUM(amountpaid) WHERE custeio_cat='CCM'` | F | indireto ⚠️ inclui centros de investimento marcados CCM |
| `Costing Forecast` | custeio previsto | `SUM(MD.Custeio)` | F | indireto |
| `Expenses Accumulated` | desembolso acumulado | `[Outlay]` em ACC-SEL-EOM | ACC-SEL-EOM | indireto |
| `Expenses Accumulated - Forecast` | desembolso previsto acumulado | `[Outlay Forecast]` em ACC-SEL | ACC-SEL | indireto |
| `Costing Accumulated` | custeio acumulado | `[Costing]` em ACC-SEL-EOM | ACC-SEL-EOM | indireto |
| `Costing Accumulated - Forecast` | custeio previsto acumulado | `[Costing Forecast]` em ACC-SEL | ACC-SEL | indireto |
| `head outlay mOm` | **Desembolso/cab/mês** (mensal) | `(−[Outlay] / [Mean Month]) / [Count of Selected Month]` → por mês: `desembolso_mês / rebanho_médio_mês` | por mês | Financeiro (gráfico, filtro visual `> 0`) ✅ |
| `head outlay mOm (forecast)` | desembolso/cab/mês previsto | `(−[Outlay Forecast] / [Mean Month - forecast]) / [Count of Selected Month]` | por mês | Financeiro ⚠️ rebanho "previsto" = realizado |
| `head outlay accumulated` | **Desembolso/cab/mês acumulado** | `COALESCE((−[Expenses Accumulated] / [Mean Month Accumulated - Aux (Desembolso)]) / [Count of Selected Month], 0)` = desembolso acumulado ÷ rebanho médio do período ÷ nº meses | ACC-SEL-EOM / YTD-SEL | Financeiro (gauge) ✅ |
| `head outlat accumulated - forecast` (sic) | meta do gauge | `COALESCE((−[Expenses Accumulated - Forecast] / [Mean Month Accumulated - Aux (Desembolso) - Forecast]) / [Count of Selected Month], 0)` | idem | Financeiro ⚠️ usa rebanho realizado |
| `Costing head Accumulated` | **Custeio/cab/mês acumulado** | `COALESCE(([Costing Accumulated] / [Mean Month Accumulated - Aux (Desembolso)]) / [Count of Selected Month], 0)` | idem | Financeiro (gauge) ✅ |
| `Costing Head accumulated - forecast` | meta do gauge | `COALESCE(([Costing Accumulated - Forecast] / [Mean Month Accumulated - Aux (Desembolso) - Forecast]) / [Count of Selected Month], 0)` | idem | Financeiro ⚠️ |

Pseudo-SQL de referência do KPI principal (desembolso/cab/mês acumulado, período `[ini, fim]`, fazenda `f`):
```sql
WITH desemb AS (            -- Outlay em módulo (o DAX guarda negativo e multiplica por -1)
  SELECT SUM(amountpaid) AS v FROM financeiro_dre
  WHERE idpropfaz = :f AND desembolso_cat = 'DCM'
    AND duedate BETWEEN :ini AND (date_trunc('month', :fim) + interval '1 month - 1 day')::date),
reb_mes AS (                -- rebanho médio por nº de mês (réplica de Count of Selected Month)
  SELECT extract(month FROM data) AS m, SUM(amount) AS s
  FROM rebanho_medio WHERE idpropfaz = :f AND data BETWEEN :ini AND :fim
  GROUP BY 1 HAVING SUM(amount) > 0),
reb AS (SELECT SUM(s) AS soma, COUNT(*) AS n_meses FROM reb_mes)
SELECT (SELECT v FROM desemb) / (reb.soma / NULLIF(reb.n_meses,0)) / NULLIF(reb.n_meses,0) AS desembolso_cab_mes
FROM reb;
-- = desembolso_total / rebanho_medio_do_periodo / n_meses
```

### 5.12 Planejado × Realizado (DRE por centro de custo — `fPlanejadoxRealizado`)

| Medida | Significado | Fórmula | Uso / status |
|---|---|---|---|
| `Valor Último Mês Selecionado` | realizado do último mês da seleção | se `classificacao` em escopo: `SUM(PR.realizado)` em ULT-MÊS; no total: `Receitas − Despesas` onde Receitas = `classificacao='A - RECEITAS'` e Despesas = `classificacao IN ('C - INVESTIMENTOS','D - CUSTEIO','E - OUTROS DÉBITOS')` | Planejado x Realizado ⚠️ |
| `Meta Último Mês Selecionado` | previsto do último mês | idem com `PR.meta` | idem ⚠️ |
| `% Variação` | desvio mensal | `([Valor Último Mês Selecionado] − [Meta Último Mês Selecionado]) / [Meta …]` | indireto |
| `% Variação Graph` | wrapper | `= [% Variação]` (variável de ícone calculada e não usada) | Planejado x Realizado |
| `Value Accumulated` | realizado acumulado | escopo: `SUM(PR.realizado)` em ACC-SEL; total: Receitas acum − (C+D+"E - OUTROS DÉBITOS") acum | Planejado x Realizado ⚠️ |
| `Meta Accumulated` | previsto acumulado | idem com `meta` | idem ⚠️ |
| `%% Variação Acc` | desvio acumulado | `([Value Accumulated] − [Meta Accumulated]) / [Meta Accumulated]` | indireto |
| `% Variação Acc Graph` | wrapper | `= [%% Variação Acc]` | Planejado x Realizado |
| `Icon` | semáforo mensal (formatação condicional) | `_var=[% Variação]`, `_class = SELECTEDVALUE(PR.classificacao)`: RECEITAS → `>+3%` VERDE, `<−3%` VERMELHO, senão AMARELO; despesas → `−100% ≤ var ≤ 0` VERDE, `> 3%` VERMELHO, `0 < var ≤ 3%` AMARELO | ícones no pivot |
| `Icon Acc` | semáforo acumulado | idem com `[%% Variação Acc]` e `SELECTEDVALUE(PR.Classificacao2)` | ícones no pivot |

⚠️ No total geral: o literal `"E - OUTROS DÉBITOS"` não existe na coluna `classificacao` (o SQL gera `"F - OUTROS DÉBITOS"`; `"E - …"` só existe em `Classificacao2`) → **Outros Débitos nunca são subtraídos**; a linha sintética `B - DESEMBOLSO` (duplicata de C+D) aparece como linha do pivot mas é corretamente ignorada no total. `ISINSCOPE` é verdadeiro também no nível `costcenter`, então o subtotal por classificação é a soma simples. Como `meta` e `realizado` são `ABS()`, despesas e receitas são positivas e o sinal vem só da regra do total.

### 5.13 Indicadores zootécnicos — o que existe e o que não existe

| Indicador | Existe? | Como (neste modelo) |
|---|---|---|
| Rebanho médio (cab.) | Sim | `Mean Month` (média mensal de `stg_rebanho_medio`) |
| Rebanho médio (UA) | Não (fixo 0) | — |
| Estoque final (saldo) | Sim | `Saldo Acumulado` / `SUM(fSaldoGado.amountacc)` por fim de mês |
| Lotação cab/ha | Parcial | `Mean Month Ha` (área fixa 500) |
| Lotação UA/ha | Não | `UA Median Ha` quebrada; `Lotation` = 0/2911 |
| Natalidade (taxa) | **Não** | só nº de nascimentos, % fêmea/macho e % vs meta; não há divisão por matrizes/vacas expostas |
| Mortalidade | Sim | `% Mortality ( AVG Month)` (mortes/rebanho médio) e `% Mortality` (mortes/nascimentos, bezerros) |
| Desfrute | **Não** | — |
| GMD / ganho de peso | **Não** | — (API não traz pesagens; só pesos médios de compra/venda/desmame) |
| Desmama (taxa, peso) | **Não** | `pecuarioDesmame` não usada |
| Rendimento de carcaça | Sim | `Rendimento Carcaça` (realizado) / `IN - Rendimento Carcaça (Forecast)` |
| Peso médio de venda / compra | Sim | `IN - AVG Live Weight*`, `IN AVG - Peso Médio de Compra*` |
| Preço da @ (venda/compra) e ágio | Sim | `AVG Price @ *`, `@ AVG Price Purchase`, `Ágio` |
| Desembolso / custeio por cabeça/mês | Sim | `head outlay *`, `Costing head *` |

### 5.14 Medidas de UI (títulos, cores, ícones, flags) — resumo

* **Cores** (formatação condicional do preenchimento dos gauges no Financeiro): `Color Desemb Cab Mês` = `IF([head outlay accumulated] > [head outlat accumulated - forecast], "#870000", "#007D08")`; `Color Costing Cab Mês` = idem com custeio; `Color @ Venda Geral` = verde se `[AVG Price @ (Em Pe + Abate)] > forecast`, senão vermelho.
* **Flags ±1 (não usadas)**: `IN Venda Geral` (`IN - Invoicing > Incoicing - Forecast`), `IN Costing Cab Mês`, `IN Desembolso Cab Mês` (invertido: acima da meta = −1), `IN Mean Month` (`Mean Month > Mean Month - forecast`).
* **Ícones**: `Icon`, `Icon Acc` (ver 5.12).
* **Texto dinâmico**: `Selected Farm` = `"GRUPO"` se nenhuma fazenda única selecionada, senão o nome (não usada); `IN - Periodo Capa` = `FORMAT(MAX(dCalendar[Data]), "MMMM \d\e yyyy")` (não usada); `IN - Periodo Envio` = `"Cuiabá, " & FORMAT(TODAY(),"MMMM") & " de " & YEAR(TODAY()) & "."` (cidade fixa; não usada); `RL Acumulado` = `"ACUMULADO"`, `RL Mensal` = `"MENSAL"` (não usadas).
* **Rótulos estáticos (pasta `IN - Data Labels`, 53 constantes de texto)**: `IN - % Meta` ("% Em Relação a Meta"), `IN - Adultos`, `IN - Ágio`, `IN - Bezerro`, `IN - Cabeças` ("Cb"), `IN - Cbs Compradas`, `IN - Cbs Vendidas` ("Cabeças Vendidas"), `IN - Compra`, `IN - COMPRA X VENDA`, `IN - Compras (Label 2 )`, `IN - Compras (Label)`, `IN - Data Análise`, `IN - Entrada`, `IN - Faturamento` ("Fat. Realizado"), `IN - Faturamento Planejado`, `IN - Fêmea`, `IN - Geral`, `IN - Indice de Mortalidade`, `IN - Inv Planejado`, `IN - Inv Realizado`, `IN - Jovens`, `IN - Lotação Cab`, `IN - Lotação UA`, `IN - Macho`, `IN - Meta` ("Planejado"), `IN - Meta Valor KG`, `IN - Mortalidade sobre Nascimento`, `IN - Mortalidade sobre Rebanho Médio`, `IN - Mortes`, `IN - Mortes (2)`, `IN - Nascimentos` ("% Sobre Sobre o Total" — typo), `IN - Nascimentos (Label - 2)`, `IN - Nascimentos (Label)`, `IN - Peso Médio Vivo`, `IN - Planejado`, `IN - Preço do KG`, `IN - Quantidade`, `IN - Realizado`, `IN - Rebanho Médio`, `IN - Rebanho Médio Cab`, `IN - Rebanho Médio UA`, `IN - Relação a Meta`, `IN - Rendimento de Carcaça`, `IN - Saida`, `IN - Separador de`, `IN - Site Terra` ("terradesenvolvimento.com.br"), `IN - TRANSFERÊNCIAS`, `IN - Valor da @` ("Preço de Venda da @"), `IN - Valor da @ Compra`, `IN - Vendas (Geral)`, `IN - Vendas (Label)`, `IN Peso Médio` ("PESO MÉDIO"), `IN Valor@` ("VALOR @"). Usados como "cards-rótulo" (padrão de layout do template: um card por texto). Não usados: `IN - Compra`, `IN - Compras (Label)`, `IN - Data Análise`, `IN - Entrada`, `IN - Faturamento Planejado`, `IN - Meta Valor KG`, `IN - Quantidade`, `IN - Relação a Meta`, `IN - Saida`, `IN - Separador de`, `IN - Site Terra`, `IN - TRANSFERÊNCIAS`, `IN - Vendas (Geral)`, `IN Peso Médio`, `IN Valor@`.

---

## 6. Glossário (definições como ESTE modelo as implementa)

| Termo | Definição no modelo Metryx |
|---|---|
| **Cliente / customer** | Conta do cliente na Metryx (`idcustomer`, `customer`). Slicer rotulado "PROPRIETÁRIO" usa `fUnidades[customer]`. |
| **Proprietário / owner** | Dono dos animais (`owner`) — pode diferir do cliente. Inconsistente: `pecuarioVendaAbate/EmPe[proprietArio] = customer`, `pecuarioCompras/Mortes[proprietArio] = owner`; `fSaldoGado` particiona por `owner`. |
| **Fazenda / farm** | `idfarm`, `farmname` (`fUnidades`). Financeiro: fazenda **fiscal** (`farmfiscal`) em `financeiroDre`; fazenda **destino** em `fPlanejadoxRealizado`. |
| **Retiro** | Subdivisão da fazenda (`idretiro`, `retironame`). |
| **idpropfaz** | `CONCAT(idcustomer, idfarm)` — chave proprietário-fazenda ("PROP_FAZ" da planilha). |
| **Categoria** | Categoria animal do cliente (`category`, `idcategory`), livre por cliente (ex.: "Bezerro 0 a 8 Meses", "BO - Bezerro 00 a 08 Meses"). `Categorias.categorygroup` (8 grupos, ex. "Bezerros Mamando"), `agecategory`, `gender`. |
| **Grupo de categoria (mortes)** | `pecuarioMortes[grupo_categoria]` = `namegroup` da API: `BEZERROS`, `JOVENS`, `ADULTOS` (+ "Bezerros/Bezerras Mamando" etc.). Não existe em rebanho médio/metas no modelo (a API de rebanho médio tem `groupCategory`). |
| **Era** | `pecuarioMortes[era]` (faixa etária da API, 5 valores) — carregada, não usada. |
| **Sexo** | `gender`/`sexo`: "MACHO"/"FÊMEA" (realizado, maiúsculas) e "Macho"/"Fêmea" (metas e venda em pé). DAX compara sem diferenciar maiúsculas. |
| **Safra / ano-safra** | Julho→junho. `dCalendar[safra]` = "Safra 2024/25"; `anosafra` = "jul-24/25". Acumulados usam ano **civil**. |
| **Rebanho médio** | Média de cabeças no mês por categoria (pré-calculada pela Metryx, `stg_rebanho_medio.amount`). KPI `Mean Month` = Σ amount ÷ nº de meses com dados. |
| **Estoque / saldo** | Cabeças no último dia do mês (`fSaldoGado.amountacc`), derivado de `stg_balanco_pecuario` com forward-fill do último saldo. |
| **UA (unidade animal)** | **Não implementada** (`Mean Month - UA = 0`). Não há constante de 450 kg. |
| **Lotação** | `Mean Month Ha` = Σ rebanho médio ÷ 500 ha (fixo) ("Lotação Cab"); `Lotation` = UA ÷ 2911 ha (fixo) — inoperante. |
| **Arroba (@)** | 15 kg. Três convenções: (1) **abate**: @ de carcaça = `deadarrobaavg × qtd` (da API) ou `pesomorto_total/15`; (2) **venda em pé e metas em pé**: @ equivalentes = peso vivo ÷ 30 (rendimento implícito 50%); (3) **compras** e `pecuarioVendaEmPe[peso_arroba]`: @ "vivas" = peso vivo ÷ 15. |
| **Peso vivo / peso morto (carcaça)** | `pesovivo_total = weighttotal` (kg totais); `pesomorto_total = amount × deadweightavg`. |
| **Rendimento de carcaça** | Σ peso morto ÷ Σ peso vivo (realizado); previsto = Σ(weight×yield/100×amount) ÷ Σ(weight×amount). |
| **Venda abate × venda em pé** | Mesma tabela `stg_vendas`: abate se `deadarrobaavg IS NOT NULL`, em pé se nulo. Metas: `stg_vendasasprevisto.tipo ILIKE '%abate%'` / `'%em%'`. |
| **Faturamento** | `totalfaturamento` (R$) da venda. |
| **Ticket médio** | Faturamento ÷ cabeças (`AVG Ticket *`, não usadas). |
| **Preço da @** | Faturamento ÷ @ (abate: carcaça; em pé: vivo/30; geral: soma das duas bases). |
| **Ágio** | (preço @ compra − preço @ venda) ÷ preço @ venda. |
| **Natalidade** | Não há taxa; apenas nº de nascimentos (`Birth Quantity`), % fêmeas/machos e % vs planejado. |
| **Mortalidade** | (a) sobre rebanho médio: mortes ÷ `Mean Month`; (b) sobre nascimentos: mortes acumuladas ÷ nascimentos acumulados (cards de bezerros). |
| **Consumo/doação** | Morte com `causa = 'Consumo Abate'`. |
| **Desfrute, GMD, taxa de desmama** | Não existem neste modelo. |
| **Desembolso (Outlay)** | Σ `amountpaid` dos lançamentos cujo centro de custo tem `desembolso_cat = 'DCM'` (custeio + investimentos + RH + pagamento de financiamentos), com sinal negativo. |
| **Custeio (Costing)** | Σ `amountpaid` dos centros com `custeio_cat = 'CCM'` (inclui centros de investimento marcados CCM). |
| **Receitas (Revenues)** | Σ `amountpaid` com `type='Crédito'` e `tipo_custeio_cat ∈ {Receita Pec, Receita Agr}`. |
| **Despesas (Expenses)** | Σ `amountpaid` com `type='Débito'` (todas as saídas). |
| **Saldo / Balance (fluxo de caixa)** | Receitas − Despesas por mês de **vencimento**. |
| **Desembolso/cab/mês** | Desembolso do período ÷ rebanho médio do período ÷ nº de meses. |
| **Custeio/cab/mês** | Custeio do período ÷ rebanho médio do período ÷ nº de meses. |
| **F/V** | Agrupador DRE: A-RECEITAS, B-CUSTO FIXO (CF), C-CUSTO VARIÁVEL (CV), D-FINANCIAMENTOS, VERIFICAR. |
| **Classificação DRE (Planejado x Realizado)** | `A - RECEITAS`, `B - DESEMBOLSO` (sintético = C+D), `C - INVESTIMENTOS`, `D - CUSTEIO`, `E - OUTROS CRÉDITOS`, `F - OUTROS DÉBITOS`, `''`. (Coluna `Classificacao2` usa outra numeração.) |
| **Forecast / Meta / Planejado** | Valores do módulo de planejamento Metryx (`stg_*previsto`). "Forecast" no nome da medida = planejado. Planejado de rebanho médio = cópia do realizado. |
| **Accumulated / Acumulado** | Ver padrões ACC-ALL, ACC-SEL, YTD/ALL, YTD/SEL em 5.0 — não há um único conceito de acumulado. |
| **Median** (nas medidas) | Significa "médio" (média), não mediana. |

---

## 7. Páginas do relatório

Padrão de layout: páginas de 1920×1080 (MENU 1280×720) com "cards-rótulo" (medidas `IN - …`) + cards de valor, divididos em blocos **FÊMEA / MACHO / GERAL** (ou BEZERROS / JOVENS / ADULTOS / GERAL) via **filtros de nível de visual** (não por medidas). Não há grupos de sincronização de slicers no layout: cada página tem seus próprios slicers (Ano, Mês, Proprietário = `fUnidades[customer]`, Fazenda = `fUnidades[farmname]`). O slicer "Mês" das páginas de detalhe é o field parameter (`Parâmetro - Data Campos`), cujo conteúdo muda entre "Nome do Mês" (CÍVIL) e `mesano` (SAFRA); os gráficos usam sempre `dCalendar[mesano]` no eixo.

### 7.1 MENU 01 (capa/navegação)
* Logo Terra; texto "SELECIONE A FORMA DE VISUALIZAÇÃO:"; slicers Proprietário, Fazenda, Ano, Safra (oculto), Mês (`mesano`), seletor CÍVIL/SAFRA (field parameter).
* Botões "Safra/Cívil Habilitado/Desabilitado" → bookmarks `2ebe1df6…` e `b135b8c2…` que **não existem** (os bookmarks existentes são "MENU -SAFRA" e "MENU - CIVÍL" com outros ids). Botão de navegação → página `a788b7f2…` **inexistente**.
* Sem medidas.

### 7.2 Financeiro
* Propósito: fluxo de caixa, desembolso e custeio por cabeça, preço da @.
* Visuais: card "DESEMBOLSO" (`Outlay`, `Revenues`); gauges "DESEMBOLSO CABEÇA MÊS" (`head outlay accumulated` × alvo `head outlat accumulated - forecast`, cor `Color Desemb Cab Mês`), "CUSTEIO CABEÇA MÊS" (`Costing head Accumulated` × `Costing Head accumulated - forecast`, cor `Color Costing Cab Mês`), "Valor de Venda @" (`AVG Price @ (Em Pe + Abate)` × `… - Forecast`, máx. `MAX AVG Price @ Forecast`, cor `Color @ Venda Geral`); colunas "RELAÇÃO DESEMBOLSO TOTAL" (`Expenses Graph` por `financeiroDre[costcenter]`); tabela "RELAÇÃO DESEMBOLSO TOTAL" (costcenter, Σ amountpaid ×2, status, subcenter, parcel, doctype, duedate, code — sobreposta ao gráfico); colunas "Realizado x Planejado - Desembolso/cab/mês" (`head outlay mOm` × `head outlay mOm (forecast)` por `mesano`, filtro `head outlay mOm > 0`); "REALIZADO X PLANEJADO - DESEMBOLSO" (`Expenses Graph` × `Expenses Forecast` — compara **todos os débitos**, não o desembolso DCM); "REALIZADO X PLANEJADO - RECEITAS" (`Revenues` × `Revenues Forecast` — previsto sempre vazio); combo "FLUXO DE CAIXA MENSAL" (`Revenues`, `Expenses Graph` + linha `Balance`).
* Slicers (Proprietário, Fazenda, Ano, Mês, CÍVIL/SAFRA) dentro do grupo **"Filtros" oculto** → usuário não consegue filtrar nesta página. Sem botão de voltar ao menu.

### 7.3 Movimentação do Gado
* Propósito: visão geral do rebanho (estoque, nascimentos, mortes, rebanho médio/lotação, compras×vendas).
* Visuais: colunas "ESTOQUE FINAL MENSAL" (`SUM(fSaldoGado.amountacc)` por `mesano`); colunas "ESTOQUE POR CATEGORIA" (`Saldo Acumulado` por `fSaldoGado[category]`); card `Saldo Acumulado`; bloco Nascimentos (`Birth Quantity`, `% Birth x Forecast`); bloco Mortes (`Dead Quantity`, `% Death x Death Forecast`); "Índice de Mortalidade" (`% mORTALITY ( MEAN MONTH)` — **medida inexistente**); bloco Rebanho Médio ("Rebanho Médio Cab" `Mean Month`, "Rebanho Médio UA" `UA Median Month` = 0, "Lotação Cab" `Mean Month Ha`, "Lotação UA" `UA Median Ha` ❌); bloco Compras|Vendas (`SUM(pecuarioCompras.qtd)`, `% Purchased Quantity`, `Amount Saled (Abate)`, `% Amount Saled`); card `SUM(pecuarioRebanhoMedioMensal.amount)`.
* Slicers: Proprietário, Fazenda, Ano, `Nome do Mês` (não usa o field parameter). 6 cards com filtro de visual em coluna inexistente (ver 8). Sem botão de voltar.
* Não há entradas/saídas, transferências, desmame, mudança de categoria (apesar do nome da página).

### 7.4 Venda Abate
* Combos "RELAÇÃO MENSAL - VENDA EM CABEÇAS" (`Amount Saled (Abate)` × `Amount Saled - Forecast (Abate)` + linha `Invoicing Accumulated (Abate)` = cab. acumuladas) e "RELAÇÃO MENSAL - FATURAMENTO" (`Invoicing Abate` × `Incoicing - Forecast`).
* Blocos FÊMEA/MACHO/GERAL (filtros `pecuarioVendaAbate[sexo]` e `fMetasAbate[gender]`): faturamento realizado × planejado; cabeças vendidas (`SUM(VA.qtd)` × `SUM(MA.amount)`); preço @ (`AVG Price @ Dead Sale` × `… - Forecast`); rendimento de carcaça (`Rendimento Carcaça` × `IN - Rendimento Carcaça (Forecast)`); peso médio vivo (`IN - AVG Live Weight` × `IN - AVG Live Weight (Forecast)`).

### 7.5 Venda em Pé
* Combos "RELAÇÃO MENSAL - FATURAMENTO" (`Invoicing (Em Pe )` × `Incoicing - Forecast (Em Pe)`) e "RELAÇÃO MENSAL - VENDA EM CABEÇAS" (`Amount Saled (Em pe)` × `Amount Saled - Forecast (Em Pe)` + linha `Amount Saled Accumulated (Em Pe)`).
* Blocos FÊMEA/MACHO/GERAL: faturamento; cabeças (`SUM(VE.qtd)` × `SUM(ME.amount)`); preço @ (`AVG Price @ Sale Venda em Pe` × forecast); preço kg (`AVG Price KG Sale Venda em Pe` × forecast); peso médio vivo (`IN - AVG Live Weight (Em Pe)` × `IN - AVG Live Weight (Forecast - Em Pe)`). **Os cards de planejado por sexo filtram `fMetasAbate[gender]`** (tabela errada) → exibem o total.

### 7.6 Compras
* Combos "RELAÇÃO DESEMBOLSO DE COMPRAS" (`Total Paid` × `Total Paid - Forecast` + linha `@ AVG Price Purchase`) e "RELAÇÃO CABEÇAS COMPRADAS" (`Purchased Quantity` × `Purchased Quantity - Forecast` + linha `Purchase Quantity Accumulated`).
* Blocos FÊMEA/MACHO/GERAL: cabeças (`SUM(C.qtd)` × `SUM(MC.amount)`), preço kg (`AVG Purchase Price KG` × forecast), peso médio (`IN AVG - Peso Médio de Compra` × forecast), investimento (`Total Paid` × `Total Paid - Forecast`); card "Preço de @ de Compra" (`@ AVG Price Purchase`) e `Ágio`. Botão volta ao MENU. 3 cards GERAL com filtro em `fMetasCompras[sexo]` inexistente.

### 7.7 Nascimento
* Combos "NASCIMENTOS - REALIZADO X PLANEJADO - MENSAL" (`Birth Quantity` × `Birth Quantity - Forecast`) e "… - ACUMULADO" (`Birth Quantity Accumulated` × `Birth Quantity Accumulated - Forecast`).
* Blocos FÊMEA/MACHO/GERAL: `SUM(N.amount)` × `SUM(MN.amount)`, `IN - % Female Birth` / `IN - % Male Birth`, `% Birth x Forecast`. Botão volta ao MENU. Realizado não responde ao período (sem relacionamento de data).

### 7.8 Mortes
* Combos "REALIZADO X PLANEJADO - ACUMULADO GERAL" (`Dead Quantity Accumulated` × `Dead Quantity Accumulated - Forecast`) e "MORTES - REALIZADO X PLANEJADO - MENSAL" (`Dead Quantity`, `Dead Quantity forecast` + linha `Dead Quantity Accumulated`); barras "Causa Morte" (`Dead Quantity` por `pecuarioMortes[causa]`, filtro > 0).
* Blocos BEZERROS/JOVENS/ADULTOS/GERAL: `Dead Quantity` (filtro `grupo_categoria`), `Dead Quantity - Forecast` (sem filtro de grupo → total), `% Mortality ( AVG Month)` ("% Sobre Rebanho Médio"); BEZERROS também `% Mortality` ("% Sobre Nascimento"). Botão volta ao MENU.

### 7.9 Planejado x Realizado
* Tabela com `classificacao` (lista/seletor) e matriz linhas `classificacao` → `costcenter`, valores `Valor Último Mês Selecionado`, `Meta Último Mês Selecionado`, `% Variação Graph` (ícone `Icon`), `Value Accumulated`, `Meta Accumulated`, `% Variação Acc Graph` (ícone `Icon Acc`). Filtro de visual em `financeiroDre[F/V]` (modo invertido, vazio → sem efeito; e `financeiroDre` não filtra `fPlanejadoxRealizado`). Botão volta ao MENU.

---

## 8. O que está inacabado, quebrado ou não usado

### 8.1 Objetos quebrados (referência inexistente / erro)
| Objeto | Problema |
|---|---|
| Medidas `Stock`, `Stock Accumulated Inicial`, `Stock Accumulated Final`, `Change Category entry/exit`, `Weaning Entry/Exit` | tabela `fMovGado` não existe (vem do Ciclo Completo) |
| `Arroba Value` → `Total de @` (medida) | colunas `ArrobaAVG`/`arrobaAvg` não existem |
| `Average Birth Weight` | `peso_nasc`, `qtd` não existem em `pecuarioNascimento` |
| `UA Median Ha` (usada em card!) | tabela `fArea` não existe |
| `Rebanho Median Month` | `DIVIDE([], …)` — sintaxe inválida |
| `VALORCALC` (fMetasCompras) | `VALOR TOTAL`, `fUnidades[PROPRIETARIO]`, relacionamento inexistentes |
| `Medida` (pecuarioVendaEmPe) | expressão vazia |
| Colunas `pecuarioVendaAbate[Total Value]`, `[teste]`, `financeiroDre[Type Operation]`, `pecuarioRebanhoMedioMensal[Forecast]` | colunas de origem inexistentes (tipo `object`, cardinalidade 1 = erro/vazio) |
| Card "Índice de Mortalidade" (Movimentação) | medida `% mORTALITY ( MEAN MONTH)` não existe |
| Cards Movimentação: `Mean Month`, `Sum(pecuarioCompras.qtd)` | filtro de visual em `pecuarioRebanhoMedioMensal[grupo_categoria]` (coluna inexistente) |
| Cards Movimentação: `UA Median Ha`, `Mean Month Ha`, `% Amount Saled`, `Amount Saled (Abate)` | filtro em `fMetasMortes[grupo_categoria] = 'BEZERROS'` (coluna inexistente) |
| Cards Compras (GERAL): `AVG Purchase Price KG (Forecast)`, `IN AVG - Peso Médio de Compra (Forecast)`, `Total Paid - Forecast` | filtro em `fMetasCompras[sexo]` (coluna inexistente; a coluna é `gender`) |
| MENU: botões de bookmark Safra/Cívil e botão de navegação | apontam para bookmarks/página que não existem |
| `Revenues Forecast` | literais `ReceitasPec/ReceitaAgr…` não batem com `Receita Pec/Receita Agr` → sempre vazio |

### 8.2 Funcionalidades ausentes / placeholders
* **Balanço de rebanho** (estoque inicial + nascimentos + compras + transferências de entrada + mudança de categoria entrada − mortes − vendas − consumo − transferências de saída − mudança saída = estoque final): inexistente. Endpoints Metryx existem (`saldo-inical`, `transferencia`, `mudanca-categoria`, `balanco-pecuario`).
* **UA**: `Mean Month - UA = 0` ("Não tem por UA na API"), embora `rebanho-medio-pecuario` retorne `weight` e `groupCategory` (não selecionados no SQL).
* **Área/pasto**: inexistente (área fixa 500/2911 ha); `utilizacao-pasto` não consumido.
* **Desmame**: `pecuarioDesmame` carregada e não usada.
* **Planejado de rebanho médio**: `fMetasRebanhoMedio` = realizado; `estoque-medio-mensal-planejamento` não consumido.
* **Planejado de desmame** (`desmame-mensal-planejamento`) e **fluxo de caixa previsto** (`previsao-fluxo-caixa-planejamento`) não consumidos.
* **Transferências**: só um rótulo de texto.
* "Forecast" fake em colunas: `pecuarioMortes[forecast]` (+80%), `pecuarioRebanhoMedioMensal[Forecast]` (+10%, quebrada), `Lotation - Forecast` (+10%), `farm = "FAZENDA EXEMPLO"`.
* Página Financeiro com slicers ocultos; Movimentação sem filtros CÍVIL/SAFRA; MENU sem navegação funcional.

### 8.3 Tabelas/colunas carregadas e não usadas por medida ou visual
`Compras` (duplicata de `pecuarioCompras`, data inativa), `pecuarioDesmame`, `Categorias` (só relacionamentos), `Tabela` (só relacionamentos), `fMetasDre[F/V]`, `financeiroDre[Class subcenter]`, `pecuarioMortes[era]`, `[pasto]`, `[enumgroup]`, `[carimbo_bez]` (sempre null), colunas de versão de plano (`plversioncode/plversionname`), `idplherdtype/plherdtypename`, `idanimalgroup/animalgroupname`, `age`, `currency*`, as 5 tabelas auto-date. 83 das 220 medidas não são usadas direta nem indiretamente por nenhum visual — 88 sem prototypeQuery, das quais 5 (`Color Desemb Cab Mês`, `Color Costing Cab Mês`, `Color @ Venda Geral`, `Icon`, `Icon Acc`) são usadas em formatação condicional (lista: seção 5, marcadas 💤; inclui os 15 rótulos `IN - …` não usados).

---

## 9. Problemas e peculiaridades (para não replicar no app)

### 9.1 Erros de lógica de negócio
1. **`Total Paid`** = Σ `Paid` = Σ (`totalfaturamento/amount`) → soma de **R$/cabeça**; deveria ser Σ `totalfaturamento`. Afeta gráfico e cards "Inv. Realizado" de Compras.
2. **Semântica de `weighttotal` em compras** usada de dois jeitos: como peso **total** (`AVG Purchase Price KG`, `IN AVG - Peso Médio de Compra`) e como peso **por cabeça** (`valo_kg`, `peso_arroba × qtd`, logo `@ AVG Price Purchase` e `Ágio`). Em vendas, `weighttotal` é total (a API de venda tem `liveWeightAVG` separado). Validar no dado (`weighttotal/amount` deve dar ~200–550 kg se for total).
3. **Nascimentos sem relacionamento de data** → filtros de período ignorados; `% Mortality` (mortes/nascimentos) e `% Birth x Forecast` comparam bases temporais diferentes.
4. **`% Amount Saled` invertida** (previsto ÷ realizado) e só abate, exibida como "% Meta" de vendas.
5. **`Revenues Forecast` sempre vazia** (literais errados).
6. **Totais do Planejado x Realizado** subtraem `"E - OUTROS DÉBITOS"`, que não existe em `classificacao` (SQL usa `F - OUTROS DÉBITOS`) → outros débitos ignorados; `Icon` usa `classificacao`, `Icon Acc` usa `Classificacao2` (numerações diferentes).
7. **`AVG Price @ (Em Pe + Abate) - Forecast`**: denominador soma @ (abate) com `fMetasEmPe[pesomorto_total]` (kg × yield sem /100, e yield vazio) → preço previsto inflado quando há venda em pé planejada. O realizado usa @ = peso vivo/30 para em pé — a meta deveria usar `fMetasEmPe[Total de @]`.
8. **Pesos médios previstos** `Σ weight / Σ amount` (abate e compras) inconsistentes com `pesovivo_total = weight × amount`; idem `AVG Purchase Price KG (Forecast)` = Σ totalvalue/Σ weight.
9. **Rebanho "previsto" = realizado** (`fMetasRebanhoMedio` lê `stg_rebanho_medio`; `… - Aux (Desembolso) - Forecast` usa `[Mean Month]`).
10. **Metas somam todas as versões de plano** (`fMetasNascimentos`/`fMetasMortes` têm 5 `plversioncode`, 20+ `plversionname`; `stg_vendasasprevisto`/`stg_comprasprevisto` também não filtram versão) → risco de dupla contagem do planejado.
11. **Acumulados inconsistentes**: realizado `Dead Quantity Accumulated` (ACC-ALL desde jul/2024) vs previsto (ACC-SEL); YTD só em ano civil; `Mean Month Accumulated` divide duas vezes por nº de meses.
12. **`Count of Selected Month` conta números de mês (1–12)**, não mês-ano → KPIs por mês errados em seleções multi-ano; e depende de haver rebanho médio.
13. **Financeiro por vencimento**: `financeiroDre` liga ao calendário por `duedate`, mas as medidas somam `amountpaid` (valor pago) — fluxo de caixa "pago" posicionado na data de vencimento; `fPlanejadoxRealizado` usa `datepayment`. As duas páginas não batem.
14. **Fazenda fiscal × destino**: `financeiroDre` atribui à fazenda fiscal (`farmfiscal`, via join por nome), `fPlanejadoxRealizado` à fazenda destino.
15. **Desembolso/Custeio ignoram `type`**: créditos (estornos/reembolsos) em centros DCM/CCM somam como desembolso/custeio. No `fPlanejadoxRealizado`, créditos e débitos do mesmo centro são somados em módulo (`ABS`), não compensados.
16. **Definições de custeio divergentes**: no `mapa`, "Investimentos em infraestrutura/outros animais" e "Rebanho Investimento" são **custeio (CCM)**; no `fPlanejadoxRealizado` são **INVESTIMENTOS**. `Silagem` tem `tipo_custeio_cat` diferente entre realizado (CV) e previsto (CCM).
17. **Filtro de valores absurdos** (|valor| ≥ 1e9) só existe no SQL de `fPlanejadoxRealizado`; `financeiroDre` pode carregar os mesmos valores (ex.: Receitas financeiras ~5e16), afetando `Expenses`/`Balance` se forem débitos.
18. **`Saldo Acumulado` vazio quando a data máxima não é fim de mês** (mês/ano corrente, pois `dCalendar` termina hoje e `fSaldoGado.date` é o último dia do mês).
19. **Estoque com forward-fill eterno** em `fSaldoGado` (categoria que some da origem mantém o último saldo para sempre), e regras especiais para "Bezerros Mamando" (soma corrente entre chaves de nascimento) difíceis de auditar.
20. **Cards por sexo/grupo com filtro na tabela errada** (Venda em Pé → `fMetasAbate[gender]`; Mortes → `Dead Quantity - Forecast` filtrado por `pecuarioVendaAbate[sexo]`) → mostram totais.
21. Cards de mortalidade de bezerros usam grupos diferentes no numerador (`BEZERROS` vs `Bezerros/Bezerras Mamando`) e **lista fixa de 19 nomes de categoria** de clientes específicos para o rebanho de bezerros (não escala para novos clientes; deveria usar `Categorias[categorygroup]`).

### 9.2 Valores fixos (hardcoded)
* Áreas: **2911 ha** (`Lotation`), **500 ha** (`Mean Month Ha`).
* Fatores: `/15` (kg por @), `/30` (kg vivo por @ de carcaça, rendimento 50%), `×1.15` (máx. gauge preço @), `×1.1` e `×1.4` (lotação prevista/máx.), `×1.8` (`pecuarioMortes[forecast]`), `×1.1` (`Forecast` rebanho), `±3%` (semáforo), `-1` (sinal desembolso).
* Textos: "Cuiabá" (`IN - Periodo Envio`), "FAZENDA EXEMPLO", "terradesenvolvimento.com.br", "GRUPO".
* Datas: calendário a partir de **2024-07-01**; `fSaldoGado` a partir de 2010-01-01.
* Listas: categorias de bezerro (19 nomes), centros de custo (`mapa`, CASE do SQL, `Classificacao2`), subcentros (`Class subcenter`), causa `'Consumo Abate'`, valores `'Débito'/'Crédito'`, `'MACHO'/'FÊMEA'`, `'DCM'/'CCM'`.
* Filtro temporário `ABS(amountpaid) < 1e9`.

### 9.3 Lógica duplicada
* `pecuarioCompras` × `Compras` (mesma origem); `Dead Quantity forecast` × `Dead Quantity - Forecast`; `Death` × `Dead Quantity`; `Birth` × `Birth Quantity`; `Sell` × `Amount Saled (Abate)`; `Incoicing - Forecast` × `IN - Invoicing - Forecast (Abate)`; `Mean Month Accumulated - Aux (Desembolso)` × `… - Forecast` (idênticas); `pecuarioVendaAbate[Peso Morto Total]` × `pesomorto_total`; `pecuarioVendaEmPe[Peso Morto]` × `[Total de @]`; `% Variação Graph` / `% Variação Acc Graph` (wrappers com variável de ícone morta); CTE `mapa` copiada em dois SQL (com divergência em `Silagem`); três esquemas de classificação DRE (`F/V`, `classificacao` SQL, `Classificacao2`).
* `USERELATIONSHIP` redundantes sobre relacionamentos já ativos (`Mean Month - forecast`, `Outlay Forecast`, `Costing Forecast`, `Birth/Dead/Purchased … - Forecast`, `Expenses/Revenues Forecast`, `Total Paid - Forecast`).

### 9.4 Nomenclatura
* Mistura inglês/português e erros: `Incoicing`, `Saled`, `outlat`, `comsuption`, `Lotation`, `valo_kg`, `proprietArio`/`proprietÁrio`, `Rendimento Carcaça` vs `IN - Rendimento Carcaça (Forecast)`, "Median" = média, `Saldo 32322`, `teste`, `Medida`, `Invoicing Accumulated (Abate)` que conta cabeças, `Peso Morto` que é @, `UltimaDataMovimentacao` que é saldo.
* Pastas de exibição incoerentes: `UA Median Month`/`UA Median Ha` em "Purchase Measures"; `Count of Selected Month` em "Dead Measures"; medidas soltas em tabelas de fato (`fSaldoGado`, `fMetasCompras`, `pecuarioVendaEmPe`).
* Prefixo `f` em dimensão (`fUnidades`); `Tabela` sem nome significativo; `Parâmetro - Data` com valores "CÍVIL"/"SAFRA".
* Coluna calculada dentro da tabela de medidas (`Analytics Measures[Purchased Quantity MALE]`).
* Visuais com `queryRef` antigo (renomeações): `Amount Saled` → `Amount Saled (Abate)`, `IN - Cabeças Vendidas` → `IN - Cbs Vendidas`, `IN - Peso Médio` → `IN - Peso Médio Vivo`, `Invoicing Accumulated (Em Pe)` → `Amount Saled Accumulated (Em Pe)`.

### 9.5 Riscos de dados/ETL
* Joins por **nome** de fazenda (`farmname`/`farmfiscal` ↔ `stg_farm.farmname`) em vendas, compras e financeiro — renomeações na Metryx descartam ou duplicam linhas silenciosamente.
* `idpropfaz` sem separador (`CONCAT(idcustomer, idfarm)`) — colisão teórica.
* `tipo ILIKE '%em%'` para metas em pé.
* Datas de metas como texto `MM/YY` (`+2000` fixo no M; `to_date(date,'MM/YY')` no SQL de compras).
* Caracteres invisíveis (U+200B…U+FEFF) nos textos da Metryx tratados só em `financeiroDre`/`fMetasDre`/`fPlanejadoxRealizado` — nas demais tabelas não.
* `fMetasDre[valorrealizado]` sempre vazio.

---

## 10. Notas para a reimplementação (app unificado) e comparação com o BI de planilhas

1. Reimplementar a partir das tabelas `stg_*` (ou direto da API) com os **mesmos nomes de conceito** da seção 6, mas corrigindo os itens 9.1. Sugestão de camada canônica: `fato_nascimento`, `fato_morte`, `fato_compra`, `fato_venda (tipo ∈ abate/em pé)`, `fato_desmame`, `fato_transferencia`, `fato_mudanca_categoria`, `fato_rebanho_medio (cab, peso→UA)`, `fato_saldo_mensal`, `fato_lancamento_financeiro`, `fato_previsto_*` (com versão de plano), `dim_fazenda (idpropfaz)`, `dim_categoria`, `dim_centro_custo (de-para único CCM/DCM/CF/CV/classificação DRE)`, `dim_calendario (civil + safra jul–jun)`.
2. Fixar **uma** definição de acumulado (sugestão: dentro do período selecionado; YTD por safra ou civil conforme o modo) e de "nº de meses" (mês-ano distintos do período).
3. RLS: filtrar por `idcustomer` (e opcionalmente lista de `idpropfaz` por usuário) em todas as fatos.
4. Os objetos quebrados (`fMovGado`, `fArea`, `qtd_ua`, `qtd_cab`, `peso_nasc`, `planejadoXRealizado`) **existem no modelo "Ciclo Completo"** — usar as definições de lá como especificação de: balanço de rebanho (`fMovGado`: Inicial, Nascimento, Morte, Vendas, Mudança de Categoria Entrada/Saída, Transferências), área (`fArea`: `Área_pasto`, `Área_ilp`, `Área_total`), UA (`qtd_ua`). Na Metryx, as fontes equivalentes são `saldo-inical-pecuario`, `mudanca-categoria-pecuario`, `transferencia-animal-pecuario`, `utilizacao-pasto` e `rebanho-medio-pecuario.weight`.
5. Pontos a validar com dados antes de comparar KPIs entre as duas fontes: semântica de `weighttotal` (compras), sinal de `amountpaid`, duplicidade por versão de plano, se `stg_balanco_pecuario` emite saldo zero, formato de `anosafra`/`harvest` da Metryx.
