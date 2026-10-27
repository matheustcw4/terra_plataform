# BI "CICLO COMPLETO - BOLETIM MENSAL" — Catálogo do modelo semântico

> Fonte analisada: `CICLO COMPLETO - BOLETIM MENSAL (6).pbix` (pasta "última versão dos projetos"), formato PBIR.
> Insumos: dump do modelo (pbixray), definição PBIR das páginas/visuais/filtros/bookmarks (lida direto do .pbix), planilha de exemplo `.xlsm` (para entender colunas de origem) e os dumps dos jobs Pentaho (apenas para confirmar tabelas `stg_*` e limpezas de texto).
> Objetivo: permitir reimplementar todos os KPIs em SQL/Python no app unificado. Credenciais **não** foram copiadas.

---

## 0. Visão geral (resumo executivo)

* **Fonte única**: tudo vem de um PostgreSQL via ODBC (DSN `DATALAKE_PLANILHA`, banco `DATALAKE_PLAN`, schema `"DATABASE"`), exceto `dCalendar` (gerada em M), `Tabela` (tabela digitada) e tabelas DAX calculadas. As tabelas `stg_*` são carregadas pelo Pentaho a partir das planilhas `.xlsm` (uma planilha por fazenda).
* **Chave universal de fazenda**: `PROP_FAZ = unaccent(replace(concat(proprietário, fazenda), ' ', ''))`, calculada em SQL em praticamente todas as consultas. É a FK de todos os fatos para a dimensão `fUnidades`.
* **Modelo**: 1 dimensão de fazenda (`fUnidades`), 1 calendário diário (`dCalendar`, 2024-07-01 → hoje, com colunas de **safra jul–jun**), 1 dimensão de categoria animal (`Categorias`), 1 dimensão de tipo de venda (`Tabela`), 1 tabela de segurança (`RLS`), **10 fatos "realizado"** e **8 fatos "planejado/metas"** (`fMetas*`) + 1 fato pré-cruzado `planejadoXRealizado` (DRE previsto x realizado por centro de custo).
* **RLS**: papel único `Regra RLS` com `RLS[e-mail] = USERNAME()`; a tabela `RLS` (e-mails de cliente/técnico por fazenda, despivotados) filtra `fUnidades` por relação **bidirecional** em `prop_faz`, e daí todos os fatos.
* **Filtro global do relatório** (travado): `fUnidades[SISTEMA PRODUTIVO] = 'CICLO COMPLETO'`. Ou seja, este .pbix é uma "visão" de um modelo multi-sistema (existem também `CRIA` e `RECRIA E ENGORDA`).
* **237 medidas** (232 na tabela `Analytics Measures`): **172 usadas** (151 diretamente em visuais — campo, filtro ou formatação condicional — e 21 só via outras medidas) e **65 sem uso**; **56 são rótulos de texto** (`IN - Data Labels`) e ~15 são cores/ícones/indicadores de UI. ~48 medidas de negócio estão mortas e várias estão quebradas/fakes (ver §8).
* **Conceitos-chave na DAX**: arroba de carcaça = 15 kg (abate), arroba "viva" = 30 kg (em pé, compras e transferências); estoque = soma acumulada de movimentações assinadas desde o "Saldo Anterior"; rebanho médio = média mensal de `qtd_cab` (planilha já traz o rebanho médio pronto por grupo Bezerros/Jovens/Adultos e `qtd_ua` pronta — **a conversão UA não está na DAX**); lotação = rebanho médio / área média (cab/ha e UA/ha); desembolso e custeio por cabeça/mês = valor acumulado / rebanho médio / nº de meses.
* **14 páginas: 11 visíveis + 3 ocultas** (`Duplicata de PG1`, `PG3`, `Duplicata de PG2`): Menu, Capa, Previsto x Realizado (DRE), Financeiro, Movimentação do Gado, Venda Abate, Venda em Pé, Compras, Nascimentos, Mortes, Transferências.

---

## 1. Fontes de dados (Power Query / SQL)

### 1.1 Conexão

| Item | Valor |
|---|---|
| Conector | `Odbc.Query("dsn=DATALAKE_PLANILHA", <SQL nativo>)` — todas as tabelas de dados usam SQL nativo (sem query folding de passos M) |
| Banco | PostgreSQL `DATALAKE_PLAN` (o Pentaho grava nele; host local do servidor Pentaho) |
| Schema | `"DATABASE"` (com aspas, maiúsculo) |
| Funções PG usadas | `unaccent()` (extensão `unaccent` precisa estar instalada), `regexp_replace`, `to_date`, `date_trunc`, window `COUNT() OVER` |
| Parâmetros M | nenhum (`m_parameters` vazio). Ordem de queries em `PBI_QueryOrder`. |
| Time intelligence automática | **ligada** (`__PBI_TimeIntelligenceEnabled = 1`) → existem `LocalDateTable_*` e `DateTableTemplate_*` (lixo, ver §8) |

Observações gerais do SQL:

* Colunas com acento vêm entre aspas com grafia "estranha" (`"proprietÁrio"`, `"operaÇÃo"`, `"tÉcnico"`, `"cÓdigo_cliente"`) — é o nome real da coluna na `stg_*` (o Pentaho grava o cabeçalho da planilha em maiúsculas e o PG preserva).
* Aliases sem aspas viram minúsculos no PG (`PROP_FAZ` → `prop_faz`, `MES` → `mes`), por isso no modelo aparecem como `prop_faz`, `mes`, `ano`.
* Datas chegam como **texto** em várias `stg_*` (`'YYYY/MM/DD 00:00:00.000'`, `'YYYY-MM-DD'` ou `DD/MM/YYYY`). O padrão é `SUBSTRING("DATA" FROM 1 FOR 10)` + `Table.ReplaceValue(" 00:00:00.000","")` + `type date` no M. As tabelas de metas (`fMetasAbate`, `fMetasEmPe`, `fMetasDre`) têm um parser robusto via regex (aceita `YYYYMMDD` e `DDMMYYYY`).

### 1.2 Tabela a tabela

| Tabela do modelo | Origem (`"DATABASE".…`) | SQL / transformações M | Grão resultante |
|---|---|---|---|
| **pecuarioNascimento** | `stg_fnascimento` | Seleciona `operaÇÃo, categ_fazenda, qtd, safra, peso_nasc, data_abrev, categoria_bi, sexo, proprietÁrio, fazenda, retiro`; `DATA = SUBSTRING(DATA,1,10)`; `PROP_FAZ`. M: remove `" 00:00:00.000"`, `DATA` → date | 1 linha por lançamento de nascimento (data, categoria, sexo) |
| **pecuarioRebanhoMedioMensal** | `stg_frebanhomedio` | `SELECT *` + `PROP_FAZ`. M: `DATA` → date | mês × fazenda(retiro) × `grupo_categoria` (Bezerros/Jovens/Adultos), com `qtd_cab` e `qtd_ua` |
| **pecuarioVendaAbate** | `stg_fvendaabate` (T0) LEFT JOIN agregado de `stg_fmetasabates` (T1) | T1 = `SUM(qtd)`, `SUM(faturamento) AS META` por `operaÇÃo, proprietÁrio, fazenda, retiro, MES, ANO` (MES/ANO = substrings de `DATA`). Join T0↔T1 por `proprietÁrio, fazenda, ANO, MES` (**não** por retiro). `DILUICAO_META = COUNT(QTD_META_MENSAL) OVER (PARTITION BY proprietÁrio, fazenda, ANO, MES)`; `QTD_META_DILUIDA = QTD_META_MENSAL / DILUICAO_META`; `META_DILUIDA = META_MENSAL / DILUICAO_META` (0 se diluição = 0). `DATA` substring; `PROP_FAZ`. M: limpa hora, date | 1 linha por lote de abate (cliente, data, categoria) — **pode duplicar** se a meta tiver >1 retiro por fazenda/mês (§8) |
| **pecuarioVendaEmPe** | `stg_fvendaempe` LEFT JOIN agregado de `stg_fmetasempe` | Idêntico ao abate (sem `era`, `rendimento`, `peso_arroba`, `peso_morto`) | 1 linha por lote de venda em pé |
| **pecuarioCompras** | `stg_fcompras` | `SELECT *` + `PROP_FAZ`. M: `DATA` → date | 1 linha por lote de compra |
| **pecuarioMortes** | `stg_fmortes` | `SELECT *` + `PROP_FAZ` + `SUBSTRING("DATA",1,10) AS data` (alias minúsculo). M: aplica o `ReplaceValue(" 00:00:00.000")` na coluna `DATA` original (que será descartada), tipa `data` como date, **remove** `DATA` original e renomeia `data` → `DATA` | 1 linha por lançamento de morte (data, categoria, causa, local) |
| **financeiroDre** | `stg_fdre` | `GROUP BY centro_de_custo, sub_centro, data_pag, operaÇÃo, centro_de_custo_bi, sub_centro_bi, proprietÁrio, fazenda, desembolso, custeio, tipo_custeio` com `SUM(valor)`; `data_pag` substring; `MES`, `ANO` substrings; `PROP_FAZ`. M: limpa hora, date; renomeia `desembolso→desembolso-CAT`, `custeio→custeio-CAT`, `tipo_custeio→tipo_custeio-CAT` | dia × sub-centro × fazenda × classificações |
| **fMovGado** | `stg_fmovgado` | `SELECT *` + `PROP_FAZ`. M: limpa hora, date; renomeia `operaÇÃo→OPERAÇÃO`, `qtd→QTD` | mês (1º dia) × `OPERAÇÃO` × `categoria_bi` × fazenda (vem pré-agregado da aba `fMovRebanho` da planilha) |
| **dCalendar** | gerada em M | Datas diárias de `#date(2024,7,1)` até `DateTime.LocalNow()` (data do refresh). Colunas: `Data, Ano, Mês, Nome do Mês, mesano ("MMM-yy"), anosafra ("jul-24/25"), OrdemSafra (jul=1…jun=12), safra ("Safra 2024/25"), OrdemAnoSafra (ano_inicio*100+ordem)` | dia |
| **Categorias** | `stg_fmovgado` | `SELECT DISTINCT categoria_bi, sexo`; renomeia `sexo→gender` | categoria_bi (15 valores) |
| **Tabela** | literal embutido | `[["Abate"],["Em Pe"]]` → coluna `TipoVenda` | tipo de venda |
| **fUnidades** | `STG_UNIDADES` | `WHERE projeto IS NOT NULL` + `PROP_FAZ`; renomeia `prop_faz→PROP_FAZ` | fazenda (224 linhas = 224 `filename`) |
| **fMetasCompras** | `stg_fmetascompras` | `SELECT *` + `PROP_FAZ` (SQL, normalizado). M: `DATA`→date; duplica `proprietÁrio` e `fazenda` e as **concatena sem normalização** numa nova coluna `PROP_FAZ` → conflito de nome com a do SQL; o modelo ficou com `PROP_FAZ` **e** `prop_faz 2` (§8) | lote de meta de compra |
| **fMetasAbate** | `stg_fmetasabates` | `DATA_2` = parser regex (`YYYYMMDD` se ano 1800–2100 e mês 1–12 nos 4+2 primeiros dígitos; senão `DDMMYYYY` com `lpad` 8; senão NULL); `SELECT DATA_2, *` + `PROP_FAZ`. M: `DATA→DATA_OLD`, `DATA_2→DATA`; `ReplaceText("ABATE","Abate")` em `operaÇÃo` (para casar com `Tabela`) | lote de meta de abate |
| **fMetasEmPe** | `stg_fmetasempe` | Mesmo parser; `ReplaceText("EMPÉ","Em Pe")` em `operaÇÃo` | lote de meta de venda em pé |
| **fMetasNascimentos** | `stg_fmetasnascimento` | `SELECT *` + `PROP_FAZ`; `DATA`→date | meta de nascimento (data, categoria) |
| **fMetasMortes** | `stg_fmetasmorte` | `SELECT *` + `PROP_FAZ`; `DATA`→date | meta de morte (data, categoria, grupo) |
| **fMetasDre** | `stg_fmetasdre` | `data_pag_corrigida` = parser regex; `SELECT data_pag_corrigida, *` + `PROP_FAZ`. M: limpa hora em `data_pag`; renomeia `data_pag→data_pag_old`, `data_pag_corrigida→data_pag`, `desembolso/custeio/tipo_custeio → *-CAT`. **Atenção**: o Pentaho remove TODOS os espaços de `CUSTEIO/DESEMBOLSO/TIPO_CUSTEIO` nas metas (ex.: `ReceitaPec`) | lançamento de meta financeira |
| **fMetasRebanhoMedio** | `stg_fmetasrebanhomedio` | `SELECT *` + `PROP_FAZ`; `DATA`→date | mês × grupo_categoria (meta) |
| **RLS** | `stg_rls` | `SELECT *` + `PROP_FAZ = unaccent(replace(concat(proprietÁrio, "NOME DO PROJETO (FAZENDA)"),' ',''))`. M: **Unpivot** de todas as colunas exceto `base, CÓDIGO DO CLIENTE, proprietÁrio, cliente, NOME DO PROJETO (FAZENDA), tÉcnico, prop_faz` → (`tipo-email`, `e-mail`); `Table.Distinct` | (fazenda × e-mail); 3 tipos de e-mail, 36 e-mails, 296 prop_faz |
| **fArea** | `STG_AREA` | `WHERE projeto IS NOT NULL` + `PROP_FAZ`; renomeia; `DATA`→date | mês × fazenda/retiro (`Área_pasto`, `Área_ilp`, `Área_total`) |
| **planejadoXRealizado** | `stg_unidades`, `STG_FDRE`, `STG_FMETASDRE` | SQL com CTEs (detalhado em 1.3) | mês × fazenda × centro_de_custo_bi (+ linhas sintéticas "DESEMBOLSO") |
| **fTransferencias** | `stg_ftransfentrada` UNION ALL `stg_ftransfsaida` | Colunas explícitas + `PROP_FAZ`; `DATA`→date | lote de transferência (entrada ou saída) |
| **fMetasTransferencias** | `stg_fmetastransfentrada` UNION ALL `stg_fmetatransfsaida` (sic, sem "s") | idem | meta de transferência |

Tabelas `stg_*` carregadas pelo Pentaho mas **não usadas** neste BI: `STG_FMETASAREA` (meta de área), `STG_DRE_PLN` e as `STG_*PREVISTO_PLN` (fluxo "MP"/planejamento alternativo). As abas `fconsumodoacao`, `fdesmame` e `fmudcategoria` da planilha só chegam ao BI **agregadas** dentro de `fMovGado` (aba `fMovRebanho`).

Mapeamento provável aba da planilha → stg → modelo (útil para o adapter de planilhas):

| Aba `.xlsm` | stg | Tabela do modelo |
|---|---|---|
| `fUnidade` | `stg_unidades` | `fUnidades` |
| `fArea` | `stg_area` | `fArea` |
| `fMovRebanho` (agregação por fórmulas SUMIFS das abas de eventos + saldo inicial do `CADASTROINICIAL`) | `stg_fmovgado` | `fMovGado`, `Categorias` |
| `fRebanhoMedio` | `stg_frebanhomedio` | `pecuarioRebanhoMedioMensal` |
| `fNascimento` / `fMortes` / `fCompras` / `fAbate` / `fVendaemPe` | `stg_fnascimento` / `stg_fmortes` / `stg_fcompras` / `stg_fvendaabate` / `stg_fvendaempe` | `pecuarioNascimento` / `pecuarioMortes` / `pecuarioCompras` / `pecuarioVendaAbate` / `pecuarioVendaEmPe` |
| `ftranfentrada` / `ftranssaida` | `stg_ftransfentrada` / `stg_ftransfsaida` | `fTransferencias` |
| `fDre` | `stg_fdre` | `financeiroDre`, `planejadoXRealizado` |
| `*PLANEJADO` | `stg_fmetas*` | `fMetas*`, `planejadoXRealizado` |
| (planilha/fonte separada de RLS) | `stg_rls` | `RLS` |

### 1.3 SQL do `planejadoXRealizado` (lógica)

```sql
WITH prop AS (            -- todas as fazendas cadastradas
  SELECT proprietário, fazenda, PROP_FAZ FROM stg_unidades WHERE proprietário IS NOT NULL),
c_custo AS (              -- todos os centros BI que existem no DRE realizado, × todas as fazendas (CROSS JOIN)
  SELECT DISTINCT f.centro_de_custo_bi, p.* FROM stg_fdre f CROSS JOIN prop p WHERE centro_de_custo_bi IS NOT NULL),
datas AS (                -- 1º dia de todos os meses presentes em stg_fdre ∪ stg_fmetasdre
  SELECT DISTINCT date_trunc('month', to_date(data_pag, 'YYYY/MM/DD' | 'DD/MM/YYYY')) ...),
base AS (SELECT * FROM c_custo CROSS JOIN datas),
previsto AS (             -- meta por centro e DIA (data_pag original), truncada p/ mês
  SELECT centro_de_custo_bi, proprietário, fazenda, PROP_FAZ, date_trunc('month', data_pag) data_pag, SUM(valor) META
  FROM stg_fmetasdre GROUP BY proprietário, fazenda, centro_de_custo_bi, data_pag),
realizado AS (            -- realizado por centro e DIA (agrupado também por valor e centro_de_custo)
  SELECT operação, centro_de_custo_bi, ..., date_trunc('month', data_pag), SUM(valor) valor
  FROM stg_fdre GROUP BY centro_de_custo, data_pag, operação, centro_de_custo_bi, proprietário, fazenda, valor),
dados AS (
  SELECT b.PROP_FAZ, b.proprietário, b.fazenda, b.centro_de_custo_bi,
         CASE centro_de_custo_bi  -- classificação (ver tabela abaixo)
         END AS Classificacao,
         b.primeiro_dia_do_mes AS data, p.meta, CAST(SUM(r.valor) AS numeric(10,2)) AS realizado
  FROM base b
  LEFT JOIN previsto  p ON p.PROP_FAZ=b.PROP_FAZ AND ano/mês iguais AND p.centro_de_custo_bi=b.centro_de_custo_bi
  LEFT JOIN realizado r ON r.PROP_FAZ=b.PROP_FAZ AND ano/mês iguais AND r.centro_de_custo_bi=b.centro_de_custo_bi
  WHERE p.meta IS NOT NULL OR r.valor IS NOT NULL
  GROUP BY b.PROP_FAZ, b.proprietário, b.fazenda, b.centro_de_custo_bi, b.primeiro_dia_do_mes, p.meta)
SELECT PROP_FAZ, proprietário, fazenda, centro_de_custo_bi, classificacao, data, SUM(meta) meta, realizado
FROM ( SELECT * FROM dados
       UNION ALL   -- linha sintética de DESEMBOLSO = investimentos + custeio
       SELECT PROP_FAZ, proprietário, fazenda, 'DESEMBOLSO', 'B - DESEMBOLSO', data, meta, ROUND(realizado,2)
       FROM dados WHERE classificacao IN ('C - INVESTIMENTOS','D - CUSTEIO') ) t
GROUP BY PROP_FAZ, proprietário, fazenda, centro_de_custo_bi, classificacao, data, realizado;
```

Classificação gerada no SQL (coluna `classificacao`):

| centro_de_custo_bi | classificacao (SQL) |
|---|---|
| Arrendamento, Cultura - Receita, Rebanho, Receitas financeiras, Receitas outros, Receitas Parque de máquinas, Vendas outros animais | `A - RECEITAS` |
| (sintético) DESEMBOLSO | `B - DESEMBOLSO` |
| Investimentos em infraestrutura, Investimentos em outros animais, Investimentos em RH, Rebanho Investimento | `C - INVESTIMENTOS` |
| Algodão, Aveia, Feno, Forrageiras e Culturas Anuais, Insumos do rebanho, Manutenção da fazenda, Mão de Obra Geral, Mão de Obra Permanente (Administração/Cultura/Manutenção da Fazenda/Parque de Máquinas/Rebanho), Milho Safrinha, Milho Verão, Outros animais, Pastagens, Silagem (Capiaçu/Capim/Milheto/Milho/Sorgo), Soja, Sorgo Grão, Suporte à Produção (Administração/Parque de máquinas), Taxas e impostos | `D - CUSTEIO` |
| Empréstimos sócios crédito, Financiamentos créditos | `E - OUTROS CRÉDITOS` |
| Dividendos, Empréstimos sócios débito, Financiamentos débitos, Outros Débitos | `F - OUTROS DÉBITOS` |
| Almoxarifado, Aporte de capital, Prejuízo Administração, Venda de Imóveis | `''` (vazio) |
| demais | NULL |

> Importante para a unificação: os nomes de `centro_de_custo_bi`/`sub_centro_bi` da planilha são mapeados na própria planilha (aba `BASEPLANODECONTAS`: "CENTRO DE CUSTO - INTTEGRA" → "CENTRO DE CUSTO - METRYX") para o **plano de contas do Metryx**. Ou seja, o DRE das planilhas já está na taxonomia Metryx — o adapter pode convergir os dois mundos por `centro_de_custo_bi`.

---

## 2. Esquema estrela

### 2.1 Dimensões

| Dimensão | Chave | Atributos relevantes | Observações |
|---|---|---|---|
| **fUnidades** (fazenda) | `PROP_FAZ` (único) | `proprietÁrio` (92), `fazenda` (196), `projeto`, `SISTEMA PRODUTIVO` (CRIA / RECRIA E ENGORDA / CICLO COMPLETO), `CÓDIGO PROJETO`, `ano` (2 valores: CÍVIL/SAFRA = tipo de ano da planilha), `filename` | É o "hub" de filtros; slicers Proprietário/Fazenda saem daqui. 1 linha por planilha (224). `ano` não é usado em nenhuma medida. |
| **dCalendar** | `Data` (diária) | `Ano`, `Mês` (1–12), `Nome do Mês`, `mesano` ("jul-24"), `anosafra`, `OrdemSafra`, `safra` ("Safra 2024/25"), `OrdemAnoSafra`, calc: `Classificador Mês-Ano` (=100*Ano+Mês, provável sort de `mesano`), `Safra Abreviada` ("24/25") | Range fixo 2024-07-01 → data do refresh. **Não** marcada explicitamente como date table no dump (as medidas usam FILTER/ALL manualmente). Todo eixo de gráfico usa `dCalendar[mesano]`. |
| **Categorias** | `categoria_bi` | `gender` (MACHO/FÊMEA) | Só usada no gráfico "Relação por sexo" (página oculta). Na planilha existe `dCategorias` com `GRUPO CATEGORIA` e `ERA` que **não** foram trazidos para a dimensão (ficam denormalizados nos fatos). |
| **Tabela** | `TipoVenda` | "Abate", "Em Pe" | Permite gráfico de faturamento por tipo de venda. |
| **RLS** | (`prop_faz`, `e-mail`) | `base`, `CÓDIGO DO CLIENTE`, `proprietÁrio`, `cliente`, `NOME DO PROJETO (FAZENDA)`, `tÉcnico`, `tipo-email` | Tabela de segurança/ponte. |
| **Parâmetro - Data** | — | Field parameter `{("CÍVIL", 'dCalendar'[Nome do Mês]), ("SAFRA", 'dCalendar'[mesano])}` | Slicer oculto em todas as páginas; **nenhum visual usa o parâmetro como eixo** → sem efeito. |
| **Analytics Measures** | — | `Row("Column", BLANK())` | Só container de medidas. |
| `LocalDateTable_f7150c8f…`, `DateTableTemplate_921fb57a…` | — | Auto date/time | Lixo do auto time-intelligence; descartar. |

### 2.2 Fatos (realizado)

| Fato | Grão | Medidas-base (colunas) | FKs |
|---|---|---|---|
| **fMovGado** | mês × operação × categoria_bi × fazenda/retiro | `QTD` (positivo na origem, exceto saídas de desmame/mudança de categoria que já vêm negativas), calc `QTD C` (assinado) | `DATA`→dCalendar, `categoria_bi`→Categorias, `prop_faz`→fUnidades |
| **pecuarioRebanhoMedioMensal** | mês × grupo_categoria × fazenda/retiro | `qtd_cab`, `qtd_ua` | `DATA`→dCalendar, `prop_faz`→fUnidades |
| **pecuarioNascimento** | lançamento | `qtd`, `peso_nasc` (kg/cab), `sexo`, `safra`, `categoria_bi` | `DATA`, `categoria_bi`, `prop_faz` |
| **pecuarioMortes** | lançamento | `qtd`, `peso_total`, `peso_vivo` (texto!), `causa`, `LOCAL`, `grupo_categoria` (BEZERROS/JOVENS/ADULTOS), `era`, `carimbo_bez` | `DATA`, `categoria_bi`, `prop_faz` |
| **pecuarioCompras** | lote | `qtd`, `peso_vivo` (kg/cab), `total_peso` (kg), `valor_cab`, `VALOR TOTAL`, `valo_kg`, `valor_arroba`, `peso_arroba` (=peso_vivo/30), `origem`, calc `Total de @` | `DATA`, `categoria_bi`, `prop_faz` |
| **pecuarioVendaAbate** | lote | `qtd`, `peso_vivo` (kg/cab), `rendimento`, `peso_arroba` (@ carcaça/cab), `valor_arroba`, `faturamento`, `peso_morto` (=peso_arroba*15), `pesovivo_total`, `pesomorto_total`, `valor_kg` (=faturamento/pesovivo_total), `valor_cab`, `cliente`, `era`; colunas de meta diluída (não usadas); calc `Total de @`, `Peso Morto Total`, `tipovenda` | `DATA`, `categoria_bi`, `prop_faz`, `tipovenda`→Tabela |
| **pecuarioVendaEmPe** | lote | `qtd`, `peso_vivo`, `pesovivo_total`, `valor_arroba`, `valor_cab`, `faturamento`, `valor_kg`, `cliente`; calc `Total de @`, `Peso Total`, `Peso Morto`, `tipovenda` | idem |
| **fTransferencias** | lote | `operaÇÃo` (Transf. Entrada / Transf. Saida), `qtd`, `peso_vivo`, `total_peso`, `VALOR TOTAL`, `peso_arroba`, `valor_cab`, `valo_kg`, `valor_arroba`; calc `Peso Total @` | `DATA`, `categoria_bi`, `prop_faz` |
| **financeiroDre** | dia × sub-centro × fazenda | `valor` (positivo), `operaÇÃo` (C/D), `centro_de_custo_bi`, `sub_centro_bi`, `desembolso-CAT` (DCM / REP. / Receita… / 0), `custeio-CAT` (CCM / …), `tipo_custeio-CAT` (CV / CF / Receita Pec / Receita Agr / Receita outras / Financiamentos / Aporte); calcs `Desembolso`, `Custeio`, `F/V`, `Classificacao`, `Valor C` | `data_pag`→dCalendar, `prop_faz`→fUnidades |
| **fArea** | mês × fazenda/retiro | `Área_pasto`, `Área_ilp`, `Área_total` (ha) | `DATA`, `PROP_FAZ` |

### 2.3 Fatos (planejado / metas)

| Fato | Espelha | Relação com dCalendar | Observação |
|---|---|---|---|
| fMetasCompras | pecuarioCompras | `DATA` **ativa** | FK de fazenda pela coluna `PROP_FAZ` gerada no M (suspeita, §8) |
| fMetasAbate | pecuarioVendaAbate | `DATA` ativa | `operaÇÃo`→Tabela (ativa) |
| fMetasEmPe | pecuarioVendaEmPe | `DATA` ativa | `operaÇÃo`→Tabela (ativa) |
| fMetasNascimentos | pecuarioNascimento | `DATA` ativa | |
| fMetasMortes | pecuarioMortes | `DATA` **inativa** → medidas usam `USERELATIONSHIP` | sem relação com Categorias |
| fMetasRebanhoMedio | pecuarioRebanhoMedioMensal | `DATA` **inativa** → `USERELATIONSHIP` | |
| fMetasDre | financeiroDre | `data_pag` **inativa** → `USERELATIONSHIP` | valores de classificação sem espaços (`ReceitaPec`) |
| fMetasTransferencias | fTransferencias | `DATA` ativa | |
| planejadoXRealizado | (DRE meta + realizado já cruzados) | `data` ativa | colunas `meta`, `realizado`, calcs `Meta C`, `Valor C`, `Classificacao2` |

### 2.4 Relacionamentos (todos M:1, todos com integridade referencial "não confiável")

| De (N) | Para (1) | Ativa | Filtro |
|---|---|---|---|
| pecuarioVendaAbate[tipovenda] | Tabela[TipoVenda] | sim | single |
| pecuarioVendaEmPe[tipovenda] | Tabela[TipoVenda] | sim | single |
| fMetasAbate[operaÇÃo] | Tabela[TipoVenda] | sim | single |
| fMetasEmPe[operaÇÃo] | Tabela[TipoVenda] | sim | single |
| fMovGado[DATA], pecuarioVendaAbate[DATA], pecuarioVendaEmPe[DATA], pecuarioRebanhoMedioMensal[DATA], pecuarioNascimento[DATA], pecuarioCompras[DATA], pecuarioMortes[DATA], financeiroDre[data_pag], fArea[DATA], planejadoXRealizado[data], fTransferencias[DATA] | dCalendar[Data] | sim | single |
| fMetasCompras[DATA], fMetasNascimentos[DATA], fMetasEmPe[DATA], fMetasAbate[DATA], fMetasTransferencias[DATA] | dCalendar[Data] | sim | single |
| **fMetasMortes[DATA]**, **fMetasRebanhoMedio[DATA]**, **fMetasDre[data_pag]** | dCalendar[Data] | **não** | single |
| pecuarioNascimento, pecuarioVendaAbate, pecuarioVendaEmPe, pecuarioCompras, pecuarioMortes, fMovGado, fMetasAbate, fMetasEmPe, fTransferencias, fMetasTransferencias `[categoria_bi]` | Categorias[categoria_bi] | sim | single |
| todos os 19 fatos `[prop_faz]` (fMetasCompras e fArea via `[PROP_FAZ]`) | fUnidades[PROP_FAZ] | sim | single |
| **RLS[prop_faz]** | fUnidades[PROP_FAZ] | sim | **Both** (bidirecional) |

Não há relação de `pecuarioRebanhoMedioMensal`, `fArea`, `financeiroDre`, `planejadoXRealizado`, `fMetasMortes`, `fMetasNascimentos`, `fMetasCompras`, `fMetasDre`, `fMetasRebanhoMedio` com `Categorias` — os filtros por grupo/sexo nesses fatos são sempre por coluna própria.

Diagrama (simplificado):

```
                      RLS (e-mail, prop_faz)
                         │ (bidirecional)
   Categorias ──┐        ▼
   Tabela ──────┼──▶ [ FATOS realizados / metas ] ◀── fUnidades (PROP_FAZ, sistema produtivo)
   dCalendar ───┘          (prop_faz, DATA, categoria_bi, tipovenda)
```

### 2.5 Tabela de datas e conceito de safra

* `dCalendar` é **diária**; os fatos mensais (`fMovGado`, `pecuarioRebanhoMedioMensal`, `fArea`, `fMetasRebanhoMedio`, `planejadoXRealizado`) são datados no **dia 1** do mês.
* **Ano civil**: `Ano`, `Mês`, `Nome do Mês`.
* **Ano safra (pecuário) = julho→junho**: `safra = "Safra " & ano_inicio & "/" & right(ano_inicio+1,2)` onde `ano_inicio = ano se mês ≥ 7, senão ano−1`; `OrdemSafra = mês−6 se mês≥7, senão mês+6`; `anosafra = "jul-24/25"`; `Safra Abreviada = MID(safra, 9, 5)` → `"24/25"`.
* O menu alterna (via bookmarks "MENU - SAFRA"/"MENU - CIVIL") entre slicer de **Safra** e de **Ano**; o slicer de **Mês** (`mesano`) é sempre visível. Todos os slicers são sincronizados (ocultos) em todas as páginas.
* O fim do calendário é a data do refresh: **metas futuras (meses após hoje) e qualquer fato com data fora de [2024-07-01, hoje] são invisíveis**.

---

## 3. RLS (segurança por linha)

| Item | Valor |
|---|---|
| Papel | `Regra RLS` (único) |
| Tabela filtrada | `RLS` |
| Expressão | `RLS[e-mail] = USERNAME()` (no serviço Power BI, `USERNAME()` retorna o UPN/e-mail do usuário, equivalente a `USERPRINCIPALNAME()`) |
| Propagação | `RLS[prop_faz]` →(M:1, **Both**)→ `fUnidades[PROP_FAZ]` → (single) → todos os fatos. Requer "aplicar filtro de segurança em ambas as direções" na relação (o dump só mostra `CrossFilteringBehavior = Both`; o comportamento de segurança não foi extraído, mas o relatório funciona em produção, então presume-se habilitado). |
| Tabela fonte | `stg_rls` (planilha de controle de acesso separada; job Pentaho `d_rls`) |
| Estrutura | Colunas fixas `base` (11 valores), `CÓDIGO DO CLIENTE`, `proprietÁrio`, `cliente`, `NOME DO PROJETO (FAZENDA)`, `tÉcnico` + N colunas de e-mail que são **despivotadas** em (`tipo-email`, `e-mail`). Há 3 tipos de e-mail (ex.: e-mail do cliente, do técnico, de outro responsável). |
| Chave | `prop_faz = unaccent(replace(concat(proprietário, "NOME DO PROJETO (FAZENDA)"), ' ', ''))` — **mesma regra** do `PROP_FAZ` dos fatos, mas usando o nome do projeto/fazenda da planilha de RLS: se o nome digitado divergir do `fazenda` da planilha de dados, o usuário não vê a fazenda. |
| Semântica | Um usuário vê **todas** as fazendas em que o seu e-mail aparece em qualquer coluna de e-mail (cliente ou técnico). Usuário sem linha → não vê nada. Não há papel "admin" — os consultores precisam constar na tabela. |

Equivalente Postgres (sugestão para o app):

```sql
-- tabela de acesso normalizada
CREATE TABLE acesso_fazenda (email text, prop_faz text, tipo_email text, PRIMARY KEY (email, prop_faz));
-- política RLS em cada fato
ALTER TABLE fato_x ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_fazenda ON fato_x USING (
  prop_faz IN (SELECT prop_faz FROM acesso_fazenda WHERE email = current_setting('app.user_email')));
```


---

## 4. Colunas calculadas (DAX)

Legenda: **[OK]** regra de negócio válida; **[QUEBRADA]** referencia coluna/tabela inexistente (resíduo do modelo Metryx: `amount`, `origin`, `originEnum`, `subCenter`, `kgValue`, `totalWeight`, `valueWeight`, `weightAvg`, `Credito/Debito`, `meta`, tabela `pecuarioDMG`) → retorna erro/BLANK (cardinalidade 1 nas estatísticas); **[FAKE]** valor inventado para demo; **[LIXO]** sem uso.

### 4.1 fMovGado (movimentação do rebanho)

| Coluna | DAX | Regra | SQL sugerido |
|---|---|---|---|
| `Type Operation` [OK] | `IF(QTD<0,"Saída", IF(OPERAÇÃO IN {"ABATE","Consumo/Doação","MORTE","EMPÉ","Transf. Saida"},"Saída","Entrada"))` | Classifica o lançamento em Entrada/Saída: negativos (saída de desmame / mudança de categoria) ou operações de baixa são **Saída**; o resto (Saldo Anterior, COMPRA, NASCIMENTO, Transf. Entrada, entrada de DESMAME/Mud. de Categoria) é **Entrada** | `CASE WHEN qtd<0 OR operacao IN ('ABATE','Consumo/Doação','MORTE','EMPÉ','Transf. Saida') THEN 'Saída' ELSE 'Entrada' END` |
| `QTD C` [OK] — **base do estoque** | `IF(QTD<0, QTD, IF([Type Operation]="Entrada", QTD, -QTD))` | Quantidade **assinada**: entradas positivas, saídas negativas | `CASE WHEN qtd<0 THEN qtd WHEN tipo='Entrada' THEN qtd ELSE -qtd END AS qtd_assinada` (coluna gerada ou view) |
| `Inicial` [OK, não usada] | `IF(OPERAÇÃO="Saldo Anterior", QTD C, 0)` | Saldo inicial | `CASE WHEN operacao='Saldo Anterior' THEN qtd_assinada ELSE 0 END` |
| `Vendas` [LIXO] | `IF(OPERAÇÃO="Venda", QTD C, 0)` | Operação "Venda" não existe (são ABATE/EMPÉ) → sempre 0 | descartar |
| `Nascimento`, `Morte`, `Mudança de Categoria (Saída)`, `Mudança de Categoria (Entrada)`, `Origin Ordenated` [QUEBRADA] | referenciam `pecuarioDMG[origin]`, `fMovGado[amount]`, `fMovGado[origin]` | resíduo Metryx | descartar |

Valores de `OPERAÇÃO` (11): `Saldo Anterior`, `COMPRA`, `NASCIMENTO`, `MORTE`, `ABATE`, `EMPÉ`, `Consumo/Doação`, `DESMAME` (linhas de saída negativas na categoria de origem + linhas de entrada positivas na categoria destino), `Mud. de Categoria` (idem), `Transf. Entrada`, `Transf. Saida`.

### 4.2 pecuarioRebanhoMedioMensal

| Coluna | DAX | Regra | SQL |
|---|---|---|---|
| `farm` [FAKE] | `"FAZENDA EXEMPLO"` | constante de demo | descartar |
| `Forecast` [FAKE] | `qtd_cab*0.1 + qtd_cab` | "meta" inventada = realizado +10% (usada em `Mean Month Accumulated - Forecast` e `% Forecast Indicator` → página oculta PG3) | descartar; usar `fMetasRebanhoMedio` |

### 4.3 pecuarioMortes

| Coluna | DAX | Regra | SQL |
|---|---|---|---|
| `forecast` [FAKE] | `INT(qtd*0.8 + qtd)` | meta inventada = realizado × 1,8 | descartar; usar `fMetasMortes` |

### 4.4 pecuarioCompras

| Coluna | DAX | Regra | SQL |
|---|---|---|---|
| `Total de @` [OK] | `peso_arroba * qtd` | Total de arrobas compradas, com `peso_arroba = peso_vivo/30` (arroba "viva" de 30 kg, calculada na planilha) ⇒ `= total_peso/30` | `peso_arroba*qtd` (ou `total_peso/30.0`) |
| `Paid` [QUEBRADA] | `kgValue * totalWeight` | resíduo Metryx | descartar |

### 4.5 pecuarioVendaAbate

| Coluna | DAX | Regra | SQL |
|---|---|---|---|
| `Total de @` [OK] | `peso_arroba * qtd` | arrobas de **carcaça** vendidas (`peso_arroba` = @ carcaça por cabeça, digitada) | `peso_arroba*qtd` |
| `Peso Morto Total` [OK] | `= pesomorto_total` | alias (kg carcaça total = `peso_morto*qtd`, `peso_morto = peso_arroba*15`) | `pesomorto_total` |
| `tipovenda` [OK] | `"Abate"` | chave para `Tabela` | literal `'Abate'` |
| `Total Value`, `teste` [QUEBRADA] | `valueWeight*weightAvg`, `valueWeight/15` | resíduo Metryx | descartar |

### 4.6 pecuarioVendaEmPe

| Coluna | DAX | Regra | SQL |
|---|---|---|---|
| `Total de @` [OK] | `pesovivo_total / 30` | arrobas "vivas" vendidas (30 kg = 1 @ a 50% de rendimento) | `pesovivo_total/30.0` |
| `Peso Total` [OK] | `= pesovivo_total` | kg vivo total | `pesovivo_total` |
| `Peso Morto` [OK, nome enganoso] | `pesovivo_total / 30` | **não é kg de carcaça**, é a mesma coisa que `Total de @` (arrobas) | `pesovivo_total/30.0` |
| `tipovenda` [OK] | `"Em Pe"` | chave para `Tabela` | literal |

### 4.7 fMetasAbate / fMetasEmPe / fMetasTransferencias / fTransferencias

| Tabela.Coluna | DAX | SQL |
|---|---|---|
| fMetasAbate[`Total de @`] | `peso_arroba * qtd` | idem realizado |
| fMetasAbate[`Peso Morto Total`] | `= pesomorto_total` | idem |
| fMetasEmPe[`Total de @`] | `pesovivo_total/30` | idem |
| fMetasEmPe[`Peso Total`] | `= pesovivo_total` | idem |
| fMetasEmPe[`Peso Morto`] | `pesovivo_total/30` (arrobas) | idem |
| fTransferencias[`Peso Total @`] | `peso_arroba * qtd` (`peso_arroba = peso_vivo/30`) | `peso_arroba*qtd` |
| fMetasTransferencias[`Peso Total @`] | `peso_arroba * qtd` | idem |

### 4.8 financeiroDre (DRE realizado)

| Coluna | DAX | Regra de negócio | SQL |
|---|---|---|---|
| `Desembolso` [OK] | `IF([desembolso-CAT]="DCM", valor*-1, 0)` | **Desembolso** = saída de caixa operacional ("DCM" no plano de contas). Fica **negativo**. "REP." (reposição: Rebanho, Fretes e Comissões de compra de gado) **não** entra | `CASE WHEN desembolso_cat='DCM' THEN -valor ELSE 0 END` |
| `Custeio` [OK] | `IF([custeio-CAT]="CCM", valor, 0)` | **Custeio** = custo operacional ("CCM"), positivo | `CASE WHEN custeio_cat='CCM' THEN valor ELSE 0 END` |
| `F/V` [OK] | `tipo_custeio-CAT IN {Receita Pec, Receita outras, Receita Agr}`→`A - RECEITAS`; `CF`→`B - CUSTO FIXO`; `CV`→`C - CUSTO VARIAVEL`; `Financiamentos`→`D - FINANCIAMENTOS`; senão `VERIFICAR` | Classificação fixo/variável | `CASE …` (view) |
| `Classificacao` [OK] | `SWITCH(centro_de_custo_bi, …)` | Mesma lista do SQL do `planejadoXRealizado`, **porém letras diferentes**: `A - RECEITAS`, `B - INVESTIMENTOS`, `C - CUSTEIO`, `D - OUTROS CRÉDITOS`, `E - OUTROS DÉBITOS`, `""` para Almoxarifado/Aporte/Prejuízo Adm./Venda de Imóveis, BLANK para não mapeados | tabela de-para `centro_custo_classificacao` |
| `Valor C` [OK, não usada em medida] | `IF(F/V <> "A - RECEITAS", valor*-1, valor)` | valor com sinal (receita +, despesa −) | `CASE WHEN fv='A - RECEITAS' THEN valor ELSE -valor END` |
| `Meta C` [QUEBRADA] | usa `financeiroDre[meta]` (inexistente) | — | descartar |
| `Type Operation` [QUEBRADA] | `= financeiroDre[Credito/Debito]` | — | descartar (usar `operaÇÃo` C/D) |
| `Class subcenter` [QUEBRADA] | lista enorme sobre `subCenter` (INVESTIMENTOS / "MAO DE OBRA PERMANENTE" / DESPESAS COM ATIVIDADES PRODUTIVAS / DEMAIS DESPESAS) | resíduo Metryx; listas com espaço inicial em metade dos itens | descartar |

### 4.9 fMetasDre

| Coluna | DAX | Observação |
|---|---|---|
| `Desembolso` | `IF([desembolso-CAT]="DCM", valor*-1, 0)` | idem realizado |
| `Custeio` | `IF([custeio-CAT]="CCM", valor, 0)` | idem |
| `F/V` | mesma regra do realizado | **Não funciona para receitas**: nas metas o Pentaho removeu os espaços (`ReceitaPec`), então receitas caem em `VERIFICAR` (coluna não usada em medidas) |

### 4.10 planejadoXRealizado

| Coluna | DAX | Observação |
|---|---|---|
| `Valor C` | `= realizado` (a versão com sinal está comentada) | valores positivos para receita e despesa |
| `Meta C` | `= meta` | idem |
| `Classificacao2` | `SWITCH(centro_de_custo_bi, …)` com letras **B-INVESTIMENTOS, C-CUSTEIO, D-OUTROS CRÉDITOS, E-OUTROS DÉBITOS** | ≠ coluna SQL `classificacao` (C-INVESTIMENTOS, D-CUSTEIO, E-OUTROS CRÉDITOS, F-OUTROS DÉBITOS, B-DESEMBOLSO). Usada só no ícone `Icon Acc` |
| `F/V` | todo comentado → BLANK | descartar |

### 4.11 dCalendar

| Coluna | DAX | SQL |
|---|---|---|
| `Classificador Mês-Ano` | `100*Ano + Mês` | `extract(year)*100+extract(month)` |
| `Safra Abreviada` | `MID(safra, 9, 5)` → `"24/25"` | `substr(safra, 9, 5)` |

### 4.12 Tabelas auto-geradas (descartar)

`DateTableTemplate_*` e `LocalDateTable_*`: `Ano=YEAR`, `MonthNo=MONTH`, `Mês=FORMAT(,"MMMM")`, `QuarterNo=INT((MonthNo+2)/3)`, `Trimestre="Qtr "&QuarterNo`, `Dia=DAY`. São do recurso auto date/time.


---

## 5. Medidas (DAX) por domínio de negócio

### 5.0 Convenções para traduzir o contexto de filtro do Power BI em SQL

Todas as medidas são avaliadas dentro de um **contexto** formado por:

| Símbolo | Significado | Origem no relatório |
|---|---|---|
| `:fazendas` | conjunto de `prop_faz` visíveis | RLS (e-mail) ∩ slicers Proprietário/Fazenda ∩ filtro global `SISTEMA PRODUTIVO = 'CICLO COMPLETO'` |
| `:ini`, `:fim` | primeira e última data **selecionadas** (ALLSELECTED de dCalendar) | slicers Ano **ou** Safra + Mês (`mesano`); `:fim` ≤ data do refresh |
| `ctx` | sub-período do ponto do visual. Em **cards/gauges** `ctx = [:ini, :fim]`. Em **gráficos por `mesano`** `ctx` = o mês do eixo ∩ seleção | eixo do visual |
| `ctx_ini`, `ctx_fim` | `MIN(dCalendar[Data])` / `MAX(dCalendar[Data])` no contexto | — |
| filtros de visual | ex.: `sexo='MACHO'`, `grupo_categoria='BEZERROS'`, `operaÇÃo='Transf. Entrada'` | aplicados como `WHERE` extra na tabela do fato |

Padrões de inteligência de tempo encontrados (vou referenciá-los por código):

| Código | DAX | Tradução SQL |
|---|---|---|
| **T0 – período** | agregação simples | `WHERE data BETWEEN ctx_ini AND ctx_fim` |
| **T1 – acumulado na seleção** | `FILTER(ALLSELECTED(dCalendar), Data <= MAX(Data))` | `WHERE data BETWEEN :ini AND ctx_fim` (running total que começa no início da seleção) |
| **T1e – idem até fim do mês** | `… Data <= EOMONTH(MAX(Data),0)` | `WHERE data BETWEEN :ini AND (date_trunc('month',ctx_fim)+'1 month -1 day')` |
| **T2 – acumulado desde sempre** | `FILTER(ALL(dCalendar), Data <= MAX(Data))` | `WHERE data <= ctx_fim` (ignora `:ini`; começa em 2024-07-01, início do calendário) |
| **T3 – "YTD condicional" (ALL)** | `IF([Count of Selected Years]=1, ALL… Data<=MAX && YEAR=YEAR(MAX), ALL… Data<=MAX)` | se a seleção tem 1 ano civil: `data BETWEEN date_trunc('year',ctx_fim) AND ctx_fim`; senão `data <= ctx_fim` (T2) |
| **T3s – "YTD condicional" (ALLSELECTED)** | idem com `ALLSELECTED` | se 1 ano: `data BETWEEN GREATEST(:ini, date_trunc('year',ctx_fim)) AND ctx_fim`; senão T1 |
| **T4 – ano inteiro** | `ALLEXCEPT(dCalendar, dCalendar[Ano])` | `WHERE extract(year from data) IN (anos do ctx)` (ignora mês/safra) |
| **T5 – último mês selecionado** | `MaxSel = CALCULATE(MAX(Data), ALLSELECTED)`; `Data BETWEEN EOMONTH(MaxSel,-1)+1 AND MaxSel` | `WHERE data BETWEEN date_trunc('month', :fim) AND :fim` |
| **USEREL** | `USERELATIONSHIP(dCalendar[Data], fMetasX[DATA])` | apenas indica que a meta é filtrada pela sua data (relação inativa); em SQL é só `WHERE meta.data …` |

Auxiliar onipresente — **nº de meses com rebanho** (`[Count of Selected Month]`):

```sql
-- N(ctx): número de MESES-DO-ANO (1..12) distintos no ctx que têm rebanho médio > 0
SELECT COUNT(DISTINCT extract(month FROM r.data))
FROM rebanho_medio r
WHERE r.prop_faz = ANY(:fazendas) AND r.data BETWEEN ctx_ini AND ctx_fim
GROUP BY extract(month FROM r.data) HAVING SUM(r.qtd_cab) > 0;   -- (contar os grupos)
```

> Atenção: usa `dCalendar[Mês]` (1–12), não ano-mês. Seleções com mais de 12 meses contam no máximo 12 (§8).

Base SQL sugerida (views) usada nas fórmulas abaixo:

```sql
v_mov(prop_faz, data, operacao, categoria_bi, sexo, qtd, tipo, qtd_assinada)        -- fMovGado + §4.1
v_reb(prop_faz, data, grupo_categoria, qtd_cab, qtd_ua)                              -- pecuarioRebanhoMedioMensal
v_reb_meta(prop_faz, data, grupo_categoria, qtd_cab, qtd_ua)                         -- fMetasRebanhoMedio
v_area(prop_faz, data, area_pasto, area_ilp, area_total)                             -- fArea
v_nasc / v_nasc_meta, v_morte / v_morte_meta, v_compra / v_compra_meta,
v_abate / v_abate_meta, v_empe / v_empe_meta, v_transf / v_transf_meta,
v_dre(prop_faz, data_pag, operacao, centro_bi, sub_centro_bi, desembolso_cat, custeio_cat, tipo_custeio_cat, valor,
      desembolso = CASE WHEN desembolso_cat='DCM' THEN -valor ELSE 0 END,
      custeio    = CASE WHEN custeio_cat='CCM' THEN valor ELSE 0 END)
v_dre_meta(…mesmas colunas…; categorias SEM espaços: 'ReceitaPec','ReceitaAgr','Receitaoutras')
v_pxr(prop_faz, data, centro_bi, classificacao, meta, realizado)                     -- planejadoXRealizado
```

Nas fórmulas, `Σ` = `SUM(...)` restrito a `prop_faz = ANY(:fazendas)` + filtros de visual + janela de tempo indicada.

---

### 5.1 Auxiliares de tempo e contagem

| Medida | O que calcula | Lógica | Pseudo-SQL / Python | Uso |
|---|---|---|---|---|
| `Count of Selected Month` | nº de meses (1–12) com rebanho no contexto | `COUNTROWS(FILTER(VALUES(dCalendar[Mês]), CALCULATE(SUM(pecuarioRebanhoMedioMensal[qtd_cab]))>0))` | `N(ctx)` (acima) | divisor de quase todas as médias mensais |
| `Count of Selected Years` | nº de anos civis distintos na seleção | `CALCULATE(DISTINCTCOUNT(dCalendar[Ano]), ALLSELECTED(dCalendar))` | `SELECT COUNT(DISTINCT extract(year FROM d)) FROM generate_series(:ini,:fim,'1 day') d` | decide T3/T3s |
| `Count Mean Month` | nº de **linhas** de rebanho médio acumuladas (T3) | `CALCULATE(COUNTROWS(pecuarioRebanhoMedioMensal), T3)` | `SELECT COUNT(*) FROM v_reb WHERE … T3` | **não usada** |
| `Count Mean Month Accumulated` | nº de meses-calendário (`mesano`) na janela T1 | `CALCULATE(DISTINCTCOUNT(dCalendar[mesano]), T1)` | `SELECT COUNT(DISTINCT date_trunc('month',d)) FROM generate_series(:ini, ctx_fim, '1 day') d` | divisor nos indicadores acumulados de mortalidade |

### 5.2 Estoque e movimentação do rebanho (`fMovGado`)

Conceito: o estoque é a **soma acumulada desde o início** de todas as movimentações assinadas (o primeiro lançamento de cada planilha é a operação `Saldo Anterior`, datada no mês anterior ao início do ano/safra da planilha).

| Medida | O que calcula | Dependências / tempo | Pseudo-SQL | Uso |
|---|---|---|---|---|
| `Stock` | saldo líquido das movimentações no contexto | `SUM(fMovGado[QTD C])`, T0 | `Σ v_mov.qtd_assinada` (T0) | base |
| **`Stock Accumulated Final`** | **estoque final** (cabeças) no fim do contexto | `[Stock]` com **T2** (`ALL(dCalendar)`, `Data <= MAX`) | `SELECT SUM(qtd_assinada) FROM v_mov WHERE prop_faz=ANY(:fazendas) AND data <= ctx_fim [AND categoria_bi=…]` | cards "Estoque", gráficos "ESTOQUE FINAL MENSAL" (por mês) e "ESTOQUE POR CATEGORIA" (por `fMovGado[categoria_bi]`) |
| `Stock Accumulated Inicial` | estoque inicial do contexto | `[Stock]` com `ALL(dCalendar)`, `Data < EOMONTH(MIN(Data),-1)+1` (antes do 1º dia do 1º mês) | `… WHERE data < date_trunc('month', ctx_ini)` | não usada (mas é o "saldo inicial" de uma tabela de movimentação) |
| `Buy` | entradas por compra | `[Stock]` com `OPERAÇÃO="COMPRA"` | `Σ qtd_assinada WHERE operacao='COMPRA'` | não usada |
| `Sell` | saídas por venda (negativo) | `OPERAÇÃO IN {"EMPÉ","ABATE"}` | `… IN ('EMPÉ','ABATE')` | não usada |
| `Birth` | nascimentos | `OPERAÇÃO="NASCIMENTO"` | | não usada |
| `Death` | mortes (negativo) | `OPERAÇÃO="MORTE"` | | não usada |
| `comsuption / donation` | consumo/doação (negativo) | `OPERAÇÃO="Consumo/Doação"` | | não usada |
| `Weaning Exit` | saída de desmame (negativo, na categoria bezerro) | `OPERAÇÃO="DESMAME"` e `Type Operation="Saída"` | `… operacao='DESMAME' AND tipo='Saída'` | não usada |
| `Weaning Entry` | entrada de desmame (na categoria desmamada) | `OPERAÇÃO="Desmame"` (comparação DAX é case-insensitive) e `Entrada` | `… upper(operacao)='DESMAME' AND tipo='Entrada'` | não usada |
| `Change Category exit` | saída por mudança de categoria | `"Mud. de Categoria"` e `Saída` | | não usada |
| `Change Category entry` | entrada por mudança de categoria | `"Mud. de Categoria"` e `Entrada` | | não usada |

Identidade de conferência (usada na planilha `CADASTROINICIAL`): `Estoque final = Saldo anterior + Compras + Nascimentos + Transf. entrada + Desmame(entrada) + Mud.categ(entrada) − Abate − Em pé − Mortes − Consumo/Doação − Transf. saída − Desmame(saída) − Mud.categ(saída)`. Desmame e mudança de categoria se anulam no total do rebanho (só trocam de categoria).

Python (estoque final por mês e categoria):

```python
mov['qtd_ass'] = np.where(mov.qtd < 0, mov.qtd,
                 np.where(mov.operacao.isin(['ABATE','Consumo/Doação','MORTE','EMPÉ','Transf. Saida']), -mov.qtd, mov.qtd))
estoque_final = (mov[mov.data <= ctx_fim].groupby('categoria_bi').qtd_ass.sum())
```

### 5.3 Rebanho médio, UA e lotação (`pecuarioRebanhoMedioMensal`, `fMetasRebanhoMedio`, `fArea`)

Conceito: a planilha já entrega, por mês e grupo (Bezerros/Jovens/Adultos), o **rebanho médio em cabeças (`qtd_cab`) e em UA (`qtd_ua`)**. O BI só agrega: soma os grupos do mês e faz média entre meses.

| Medida | O que calcula | Lógica | Pseudo-SQL | Uso |
|---|---|---|---|---|
| **`Mean Month`** | **Rebanho médio (cab)** no contexto | `SUM(qtd_cab) / [Count of Selected Month]` (T0) | `Σ v_reb.qtd_cab (ctx) / N(ctx)` | cards "Rebanho Médio Cab" (Movimentação), base de lotação, mortalidade e R$/cab |
| `Mean Month - forecast` | rebanho médio **planejado** (cab) | `CALCULATE(SUM(fMetasRebanhoMedio[qtd_cab]) / [Count of Selected Month], USEREL)` — o divisor N vem do **realizado** | `Σ v_reb_meta.qtd_cab (ctx) / N(ctx)` | base de R$/cab planejado |
| `Mean Month - UA` | soma de UA (sem dividir) | `SUM(qtd_ua)` | `Σ v_reb.qtd_ua` | base |
| `Mean Month Accumulated - UA` | **UA média** | `IF(anos=1, CALCULATE([Mean Month - UA], T3s), CALCULATE(…, T1)) / [Count of Selected Month]` | `Σ qtd_ua (janela T3s/T1) / N(ctx)` — num card = UA média do período | base |
| **`UA Median Month`** | **Rebanho médio em UA** | `= [Mean Month Accumulated - UA]` | idem | card "Rebanho Médio UA" |
| **`Mean Month Ha`** | **Lotação cab/ha** | `[Mean Month] / (SUM(fArea[Área_total]) / [Count of Selected Month])` | `(Σqtd_cab/N) / (Σarea_total/N)` = `Σqtd_cab / Σarea_total` (meses do ctx) | card "Lotação Cab" |
| **`UA Median Ha`** | **Lotação UA/ha** | `[UA Median Month] / (SUM(fArea[Área_total]) / [Count of Selected Month])` | `(Σqtd_ua/N) / (Σarea_total/N)` | card "Lotação UA" |
| `Mean Month Accumulated` | rebanho médio "acumulado" | `IF(anos=1, CALCULATE([Mean Month],T3s), CALCULATE([Mean Month],T1)) / [Count of Selected Month]` | `(Σqtd_cab(jan)/N(jan)) / N(ctx)` — **divide duas vezes por N** num card (§8) | não usada em visual (só em `% Realized Indicator Accumulated`, morta) |
| `Mean Month Accumulated - Aux (Desembolso)` | rebanho médio da janela acumulada | `IF(anos=1, CALCULATE([Mean Month],T3s), CALCULATE([Mean Month],T1))` | `Σqtd_cab(jan) / N(jan)` | denominador de R$/cab realizado |
| `Mean Month Accumulated - Aux (Desembolso) - Forecast` | idem com meta | `… [Mean Month - forecast] …` | `Σmeta.qtd_cab(jan) / N(jan)` | denominador de R$/cab planejado |
| `Mean Month Accumulated - Forecast` | soma acumulada da coluna FAKE `Forecast` (= realizado×1,1) | `CALCULATE(SUM(pecuarioRebanhoMedioMensal[Forecast]), T1, Forecast<>BLANK())` | `Σ qtd_cab*1.1 (T1)` | só PG3 (oculta) via `% Forecast Indicator Accumulated` |
| `Lotation` | lotação UA/ha com área **fixa 2911 ha** | `[Mean Month Accumulated - UA] / 2911 + 0` | — | não usada (hardcode) |
| `Lotation - Forecast` | `Lotation × 1,1` | fake | — | não usada |
| `Lotation - Forecast - MAX` | `Lotation - Forecast × 1,4` | fake | — | não usada |
| `IN Mean Month` | indicador +1/−1 | `IF([Mean Month] > [Mean Month - forecast], 1, -1)` | — | não usada (UI) |
| `Rebanho Median Month` | vazia (comentada) | — | — | lixo |

### 5.4 Nascimentos (`pecuarioNascimento`, `fMetasNascimentos`)

| Medida | O que calcula | Lógica | Pseudo-SQL | Uso |
|---|---|---|---|---|
| **`Birth Quantity`** | nº de nascimentos | `CALCULATE(SUM(pecuarioNascimento[qtd]))+0` (T0) | `COALESCE(Σ v_nasc.qtd,0)` | cards (total, por sexo via filtro de visual), gráfico mensal |
| `Average Birth Weight` | peso médio ao nascer | `SUM(peso_nasc)/SUM(qtd)` | `Σpeso_nasc/Σqtd` (**errado** se `qtd>1`: `peso_nasc` é kg/cab → correto seria `Σ(qtd*peso_nasc)/Σqtd`) | não usada |
| **`Birth Quantity - Forecast`** | nascimentos planejados | `CALCULATE(SUM(fMetasNascimentos[qtd]), USEREL)` (relação já é ativa → redundante) | `Σ v_nasc_meta.qtd` | cards "Planejado", gráfico mensal |
| **`% Birth x Forecast`** | % atingido da meta de nascimentos | `DIVIDE([Birth Quantity], [Birth Quantity - Forecast])` | `realizado / NULLIF(meta,0)` | Movimentação, Nascimentos |
| **`Birth Quantity Accumulated`** | nascimentos acumulados | `[Birth Quantity]` com **T3** (ALL: se 1 ano → desde 1º/jan do ano de `ctx_fim`; senão desde sempre) | ver T3 | gráfico "NASCIMENTOS – REALIZADO X PLANEJADO – ACUMULADO", denominador de `% Mortality` |
| `Birth Quantity Accumulated - Forecast` | meta acumulada | `[Birth Quantity - Forecast]` com T3 | idem com `v_nasc_meta` | mesmo gráfico |
| `Birth Quantity - Forecast - Const` | meta do(s) ano(s) civil(is) inteiro(s) | `CALCULATE([Birth Quantity - Forecast], ALLEXCEPT(dCalendar, dCalendar[Ano]))` (T4) | `Σ meta.qtd WHERE year(data) IN anos(ctx)` | base |
| `% Birth x Forecast (Year)` | % do realizado sobre a meta anual | `DIVIDE([Birth Quantity], [Birth Quantity - Forecast - Const])` | `realizado(ctx)/meta(ano)` | PG3 (oculta) |
| **`IN - % Male Birth`** | % de machos nos nascimentos | `DIVIDE(CALCULATE([Birth Quantity], sexo="MACHO"), [Birth Quantity])` | `Σqtd FILTER(sexo='MACHO') / Σqtd` | Nascimentos |
| **`IN - % Female Birth`** | % de fêmeas | idem `"FÊMEA"` (variável chamada `qtdmale` por copy-paste) | idem | Nascimentos |

### 5.5 Mortes / mortalidade (`pecuarioMortes`, `fMetasMortes`)

| Medida | O que calcula | Lógica | Pseudo-SQL | Uso |
|---|---|---|---|---|
| **`Dead Quantity`** | nº de mortes | `SUM(pecuarioMortes[qtd])` (T0) | `Σ v_morte.qtd` | cards (total e por `grupo_categoria` via filtro), gráfico mensal, gráfico "Causa Morte" (por `causa`, filtro `> 0`) |
| `Dead KG Amount` | kg mortos | `SUM(peso_total)` | `Σ peso_total` | não usada |
| `Dead Quantity (Teens)` / `Dead Quantity (Adults)` / `Dead Quantity (Calves)` | mortes por grupo | `grupo_categoria = "JOVENS" / "ADULTOS" / "BEZERROS"` | `Σqtd WHERE grupo=…` | não usadas (a página usa filtro de visual) |
| **`Dead Quantity forecast`** | mortes planejadas | `CALCULATE(SUM(fMetasMortes[qtd]), USEREL)` (relação inativa → necessário) | `Σ v_morte_meta.qtd` | gráfico mensal Mortes |
| **`Dead Quantity - Forecast`** | **duplicata exata** da anterior | idem | idem | cards "Planejado" por grupo (Mortes) |
| **`% Death x Death Forecast`** | % mortes realizadas / planejadas | `DIVIDE([Dead Quantity], [Dead Quantity forecast])` | `real/meta` | Movimentação ("Índ. Mortalidade % em relação à meta") |
| `Accumulated Death` | mortes acumuladas | `[Dead Quantity]` com **T3** (ALL) | ver T3 | PG3 (oculta) |
| `Const Death` | mortes do(s) ano(s) civil(is) inteiros | `CALCULATE([Dead Quantity], ALLEXCEPT(dCalendar, dCalendar[Ano]))` (T4) | | não usada |
| `% Death Accumulated` | `DIVIDE([Accumulated Death],[Const Death])` | | | não usada |
| **`Dead Quantity Accumulated`** | mortes acumuladas na seleção | `[Dead Quantity]` com **T1** (ALLSELECTED) | `Σqtd WHERE data BETWEEN :ini AND ctx_fim` | gráficos acumulados (Mortes), numerador de `% Mortality` |
| **`Dead Quantity Accumulated - Forecast`** | meta acumulada | `[Dead Quantity forecast]` com T1 | idem meta | gráficos acumulados |
| **`% Mortality`** | **mortalidade sobre nascimentos** | `DIVIDE([Dead Quantity Accumulated], [Birth Quantity Accumulated], 0)` — numerador T1, denominador T3 (janelas diferentes, §8) | `mortes_acum / nascimentos_acum` | card Mortes "% Sobre Nascimento" (filtro `grupo_categoria='BEZERROS'` em pecuarioMortes ⇒ **mortalidade de bezerros / nascimentos**) |
| **`% mORTALITY ( MEAN MONTH)`** | **mortalidade sobre rebanho médio** | `[Dead Quantity] / [Mean Month]` (divisão sem DIVIDE) | `Σmortes(ctx) / (Σqtd_cab(ctx)/N)` | Movimentação (geral); Mortes por grupo com filtros casados `pecuarioMortes[grupo_categoria]='BEZERROS'` + `pecuarioRebanhoMedioMensal[grupo_categoria]='Bezerros'` (idem Jovens/Adultos) |
| `% Realized Indicator` | `DIVIDE([Dead Quantity], SUM(pecuarioRebanhoMedioMensal[qtd_cab]))` | mortes / soma (não média) do rebanho | | não usada |
| `% Forecast Indicator` | `DIVIDE([Dead Quantity forecast], SUM(pecuarioRebanhoMedioMensal[forecast]))` | usa coluna FAKE | | não usada |
| `% Realized Indicator Accumulated` | `DIVIDE([Dead Quantity Accumulated], [Mean Month Accumulated]/[Count Mean Month Accumulated], 0)` | | | não usada |
| `% Forecast Indicator Accumulated` | mortalidade acumulada planejada | `DIVIDE([Dead Quantity Accumulated - Forecast], [Mean Month Accumulated - Forecast]/[Count Mean Month Accumulated], 0)` — denominador = média do rebanho FAKE (realizado ×1,1) | `meta_mortes_acum / (Σ(qtd_cab*1.1)(T1) / nº meses T1)` | PG3 (oculta) |

### 5.6 Compras (`pecuarioCompras`, `fMetasCompras`)

| Medida | O que calcula | Lógica | Pseudo-SQL | Uso |
|---|---|---|---|---|
| **`Purchased Quantity`** | cabeças compradas | `CALCULATE(SUM(pecuarioCompras[qtd]))` | `Σ v_compra.qtd` | Compras (gráfico), PG2 |
| `Purchase Quantity` | nº de lotes de compra | `COUNTROWS(pecuarioCompras)` | `COUNT(*)` | não usada |
| **`Total Paid`** | valor total pago | `CALCULATE(SUM([VALOR TOTAL]))+0` | `COALESCE(Σ valor_total,0)` | Compras ("Inv. Realizado", total e por sexo) |
| **`Purchased Quantity - Forecast`** | cabeças planejadas | `CALCULATE(SUM(fMetasCompras[qtd]), USEREL)` (redundante, relação ativa) | `Σ v_compra_meta.qtd` | Compras (gráfico) |
| `Purchased Quantity - Forecast - TESTE` | idem com `USERELATIONSHIP(fMetasCompras[PROP_FAZ], fUnidades[PROP_FAZ])` (já ativa) | teste | | não usada |
| **`% Purchased Quantity`** | % atingido (cabeças) | `DIVIDE([Purchased Quantity], [Purchased Quantity - Forecast])` | `real/meta` | Movimentação ("Compras % em relação à meta") |
| **`Total Paid - Forecast`** | valor planejado | `CALCULATE(SUM(fMetasCompras[VALOR TOTAL]), USEREL)+0` | `Σ meta.valor_total` | Compras ("Inv. Planejado") |
| `% Purchased Value` | % atingido (R$) | `DIVIDE([Total Paid], [Total Paid - Forecast])` | | não usada |
| `Purchased Quantity FEMALE` / `Purchased Quantity MALE` | cabeças por sexo | `CALCULATE([Purchased Quantity], sexo="FÊMEA"/"MACHO")` | | não usadas |
| **`@ AVG Price Purchase`** | **preço médio da @ de compra** (R$/@ viva, 30 kg) | `SUM(VALOR TOTAL) / SUM(Total de @)` | `Σvalor_total / Σ(peso_arroba*qtd)` = `Σvalor_total / (Σtotal_peso/30)` | Compras (card + linha do gráfico de desembolso de compras) |
| **`AVG Purchase Price KG`** | preço médio por kg vivo | `SUM(VALOR TOTAL)/SUM(total_peso)+0` | `Σvalor_total/Σtotal_peso` | Compras (total e por sexo) |
| **`AVG Purchase Price KG (Forecast)`** | idem meta | sobre `fMetasCompras` | | Compras |
| **`IN AVG - Peso Médio de Compra`** | peso médio (kg/cab) | `DIVIDE(SUM(total_peso), SUM(qtd))` | `Σtotal_peso/Σqtd` | Compras |
| **`IN AVG - Peso Médio de Compra (Forecast)`** | idem meta | sobre `fMetasCompras` | | Compras |
| **`Purchase Quantity Accumulated`** | cabeças compradas acumuladas | `SUM(qtd)+0` com **T1** | `Σqtd WHERE data BETWEEN :ini AND ctx_fim` | linha do gráfico "RELAÇÃO CABEÇAS COMPRADAS" |
| **`Ágio`** | ágio da reposição | `DIVIDE([@ AVG Price Purchase] − [AVG Price @ (Em Pe + Abate)], [AVG Price @ (Em Pe + Abate)])` | `(preço_@_compra − preço_@_venda) / preço_@_venda` (positivo = pagou mais pela @ do que vendeu) | card Compras "Ágio" |
| `VALORCALC` (tabela fMetasCompras) | `CALCULATE(SUM(fMetasCompras[VALOR TOTAL]), USERELATIONSHIP(fUnidades[PROPRIETARIO], pecuarioCompras[proprietÁrio]))` | relação inexistente → **erro** | | lixo |

### 5.7 Vendas — Abate (`pecuarioVendaAbate`, `fMetasAbate`)

Unidades: `qtd` cab; `peso_vivo` kg vivo/cab; `peso_arroba` @ **carcaça**/cab (1 @ = 15 kg de carcaça); `pesomorto_total` kg carcaça; `faturamento` R$.

| Medida | O que calcula | Lógica | Pseudo-SQL | Uso |
|---|---|---|---|---|
| **`Amount Saled (Abate)`** | cabeças abatidas | `SUM(qtd)` | `Σqtd` | gráfico mensal Venda Abate |
| **`Amount Saled - Forecast (Abate)`** | meta de cabeças | `SUM(fMetasAbate[qtd])` (relação de data ativa) | `Σmeta.qtd` | idem |
| **`Invoicing (Abate)`** | faturamento abate | `SUM(faturamento)+0` | `Σfaturamento` | cards (total/sexo), gráfico mensal |
| `Invoicing Abate` | duplicata sem `+0` | | | não usada |
| **`Incoicing - Forecast (Abate)`** (sic) | faturamento planejado | `SUM(fMetasAbate[faturamento])+0` | | cards, gráfico |
| **`AVG Price @ Dead Sale`** | **preço médio da @ (carcaça)** | `SUM(faturamento) / SUM(Total de @)` | `Σfaturamento / Σ(peso_arroba*qtd)` | cards (total/sexo), PG2 |
| **`AVG Price @ Dead Sale - Forecast`** | idem meta | `SUM(fMetasAbate[faturamento]) / SUM(fMetasAbate[Total de @])` | | cards |
| `AVG Ticket Dead Sale` | R$/cab | `SUM(faturamento)/SUM(qtd)` | | não usada |
| **`Rendimento Carcaça`** | **rendimento de carcaça** | `SUM(pesomorto_total)/SUM(pesovivo_total)` | `Σkg_carcaça/Σkg_vivo` | cards (total/sexo), PG2 |
| **`IN - Rendimento Carcaça (Forecast)`** | idem meta | sobre `fMetasAbate` | | cards |
| `Peso em @ Abate` | @ carcaça por cabeça | `(SUM(Peso Morto Total)/15)/SUM(qtd)` | `Σpesomorto_total/15/Σqtd` | não usada |
| **`IN - AVG Live Weight`** | **peso vivo médio** (kg/cab) | `DIVIDE(SUM(pesovivo_total), SUM(qtd))` | `Σpesovivo_total/Σqtd` | cards (total/sexo) |
| **`IN - AVG Live Weight (Forecast)`** | idem meta | sobre `fMetasAbate` | | cards |
| **`Invoicing Accumulated (Abate)`** (nome errado) | **cabeças** abatidas acumuladas | `SUM(qtd)+0` com **T1** | `Σqtd WHERE data BETWEEN :ini AND ctx_fim` | linha Y2 do gráfico "RELAÇÃO MENSAL – VENDA EM CABEÇAS" |

### 5.8 Vendas — Em pé (`pecuarioVendaEmPe`, `fMetasEmPe`)

Unidades: arroba "viva" = 30 kg de peso vivo.

| Medida | O que calcula | Lógica | Pseudo-SQL | Uso |
|---|---|---|---|---|
| **`Amount Saled (Em pe)`** | cabeças vendidas em pé | `SUM(qtd)` | | gráfico |
| **`Amount Saled - Forecast (Em Pe)`** | meta | `SUM(fMetasEmPe[qtd])` | | gráfico |
| **`Invoicing (Em Pe )`** | faturamento em pé | `SUM(faturamento)+0` | | cards, gráfico |
| **`Incoicing - Forecast (Em Pe)`** | faturamento planejado | `SUM(fMetasEmPe[faturamento])+0` | | cards, gráfico |
| **`AVG Price @ Sale Venda em Pe`** | **preço médio da @ (viva)** | `SUM(faturamento)/SUM(Total de @)+0` | `Σfaturamento / (Σpesovivo_total/30)` | cards |
| **`AVG Price @ Sale Venda em Pe - Forecast`** | idem meta | | | cards |
| **`AVG Price KG Sale Venda em Pe`** | **preço médio do kg vivo** | `SUM(faturamento)/SUM(Peso Total)+0` | `Σfaturamento/Σpesovivo_total` | cards, PG2 |
| **`AVG Price KG Sale Venda em Pe - Forecast`** | idem meta | | | cards |
| `AVG Ticket Sale` | R$/cab | `SUM(faturamento)/SUM(qtd)` | | não usada |
| `Peso em @ Em Pe` | @ viva/cab | `(SUM(pesovivo_total)/30)/SUM(qtd)+0` | | não usada |
| **`IN - AVG Live Weight (Em Pe)`** | peso vivo médio | `DIVIDE(SUM(pesovivo_total), SUM(qtd))+0` | | cards |
| **`IN - AVG Live Weight (Em Pe - Forecast)`** | idem meta | | | cards |
| **`Amount Saled Accumulated (Em Pe)`** | cabeças acumuladas | `SUM(qtd)+0` com T1 | | linha Y2 do gráfico de cabeças |

### 5.9 Vendas — consolidado (abate + em pé)

| Medida | O que calcula | Lógica | Pseudo-SQL | Uso |
|---|---|---|---|---|
| **`Amount Saled`** | cabeças vendidas (total) | `SUM(EmPe.qtd)+SUM(Abate.qtd)` | `Σqtd_empe + Σqtd_abate` | Movimentação ("Vendas"), PG2 (incl. por `Categorias[gender]`) |
| **`Amount Saled - Forecast`** | meta | `SUM(fMetasAbate.qtd)+SUM(fMetasEmPe.qtd)` | | PG2 |
| **`% Amount Saled`** | % atingido (cabeças) | `DIVIDE([Amount Saled], [Amount Saled - Forecast])` | | Movimentação, PG2 |
| **`Invoicing`** | faturamento total pecuário | `SUM(EmPe.faturamento)+SUM(Abate.faturamento)` | | PG2 (por `Tabela[TipoVenda]`, filtro "not blank") |
| **`Incoicing - Forecast`** (sic) | meta | `SUM(fMetasAbate.faturamento)+SUM(fMetasEmPe.faturamento)` | | PG2 |
| `% Atingido Faturamento` | `DIVIDE([Invoicing],[Incoicing - Forecast])+0` | | | não usada |
| `Invoicing Accumulated` | faturamento T2 | | | não usada |
| `Forecast Accumulated` | meta faturamento T2 | | | não usada |
| `Amount Head Saled Accumulated` | cabeças T2 | | | não usada |
| `Amount Head Saled - Forecast Accumulated` | meta cabeças T2 | | | não usada |
| **`AVG Price @ (Em Pe + Abate)`** | **preço médio ponderado da @ vendida** | `(fat_abate+fat_empe) / (SUM(Abate[Peso Morto Total])/15 + SUM(EmPe[Peso Morto]))` — mistura @ carcaça (abate) e @ viva/30 (em pé) | `(Σfat_ab+Σfat_ep) / (Σpesomorto_total_ab/15 + Σpesovivo_total_ep/30)` | gauge "Valor de Venda @" (Financeiro), base do Ágio |
| **`AVG Price @ (Em Pe + Abate) - Forecast`** | idem metas | | | alvo do gauge |
| **`MAX AVG Price @ Forecast`** | máximo do gauge | `forecast × 1,15` | | UI (gauge) |
| `AVG Price @` | soma de dois preços médios (errado) | `[AVG Price @ Dead Sale] + [AVG Price @ Sale Venda em Pe]` | | não usada |
| **`Peso em @`** | @ média por cabeça vendida | `(Σpesomorto_total_ab/15 + Σpesovivo_total_ep/30) / (Σqtd_ab+Σqtd_ep)` | | PG2 |
| `Total de @` | `[Arroba Value]*[Amount Saled]` com `Arroba Value` vazia → BLANK | | | lixo |
| `Arroba Value` | vazia (comentada) | | | lixo |
| `IN Venda Geral` | `IF([Invoicing] > [Incoicing - Forecast], 1, -1)` | | | não usada (UI) |
| `Color @ Venda Geral` | `IF(realizado > meta, "#008D7D" (verde), "#870000" (vermelho))` | | | formatação condicional do gauge |

### 5.10 Transferências (`fTransferencias`, `fMetasTransferencias`)

Todas as medidas são agregações simples; a página separa Entrada/Saída e Macho/Fêmea por **filtros de visual** (`operaÇÃo`, `sexo`).

| Medida | O que calcula | Lógica | Uso |
|---|---|---|---|
| **`IN - Incoming Transfer`** | cabeças transferidas para a fazenda | `CALCULATE(SUM(qtd), operaÇÃo="Transf. Entrada")` | gráfico mensal |
| **`IN - Outgoing Transfer`** | cabeças transferidas para fora | `… "Transf. Saida"` | gráfico mensal |
| `IN - Incoming Transfer - Forecast` / `IN - Outgoing Transfer - Forecast` | idem metas | | não usadas |
| **`IN QTD Transfer`** | cabeças (realizado) | `SUM(fTransferencias[qtd])` | cards |
| **`IN QTD Transfer Forecast`** | cabeças (meta) | `SUM(fMetasTransferencias[qtd])` | cards |
| **`IN - AVG Price @ Transfer`** | R$/@ (viva) | `SUM(VALOR TOTAL)/SUM(Peso Total @)` | cards |
| **`IN - AVG Price @ Transfer Forecas`** (sic) | idem meta | | cards |
| **`IN - AVG Weight Transfer`** | peso médio kg/cab | `DIVIDE(SUM(total_peso), SUM(qtd))` | cards |
| **`IN - AVG Weight Transfer Forecast`** | idem meta | | cards |

SQL genérico: `SELECT SUM(qtd), SUM(valor_total)/NULLIF(SUM(peso_arroba*qtd),0), SUM(total_peso)/NULLIF(SUM(qtd),0) FROM v_transf WHERE … AND operacao=:op AND sexo=:sexo`.

### 5.11 Financeiro — receitas, despesas, desembolso, custeio (`financeiroDre`, `fMetasDre`)

Convenções do DRE da planilha: `valor` > 0 sempre; `operaÇÃo` = `C` (crédito/receita) ou `D` (débito/despesa); `desembolso-CAT` ∈ {DCM, REP., Receita…, Financiamentos, Aporte, 0}; `custeio-CAT` ∈ {CCM, …}; `tipo_custeio-CAT` ∈ {CV, CF, Receita Pec, Receita Agr, Receita outras, Financiamentos, Aporte}.

| Medida | O que calcula | Lógica | Pseudo-SQL | Uso |
|---|---|---|---|---|
| **`Revenues`** | receitas operacionais (pecuária + agricultura) | `CALCULATE(SUM(valor), operaÇÃo="C", tipo_custeio-CAT IN {"Receita Pec","Receita Agr"})` | `Σvalor WHERE operacao='C' AND tipo_custeio_cat IN ('Receita Pec','Receita Agr')` | Financeiro (barras "Realizado x Planejado – Receitas", Fluxo de caixa, card) |
| **`All Revenues`** | receitas incluindo "Receita outras" | idem + `"Receita outras"` | | PG1 oculta; usado em `Balance` |
| `Expenses` | despesas (negativo) | `CALCULATE(SUM(valor), operaÇÃo="D") * -1` | `-Σvalor WHERE operacao='D'` | base de `Balance` |
| **`Expenses Graph`** | despesas (positivo) | `CALCULATE(SUM(valor), operaÇÃo="D")` | `Σvalor WHERE operacao='D'` | Fluxo de caixa; "Realizado x Planejado – Desembolso" (filtro de visual `desembolso-CAT='DCM'`); "Relação Desembolso Total" por `centro_de_custo_bi` (filtro `desembolso-CAT IN ('DCM','REP.')`) |
| **`Balance`** | saldo de caixa | `[All Revenues] + [Expenses]` | `Σ(C receitas) − Σ(D)` | linha do "Fluxo de caixa mensal" |
| `% Resultado` | margem sobre despesas | `DIVIDE([Balance], [Expenses]*-1)` | | não usada |
| `Finance Indicator` | sinal de `% Resultado` (1/−1/0) | | | não usada |
| **`Outlay`** | **desembolso** (negativo) | `SUM(financeiroDre[Desembolso])+0` | `-Σvalor WHERE desembolso_cat='DCM'` | card "DESEMBOLSO" |
| `Outlay Forecast` | desembolso planejado (negativo) | `CALCULATE(SUM(fMetasDre[Desembolso]), USEREL)` | `-Σmeta.valor WHERE desembolso_cat='DCM'` | base |
| `% Atingido Outlay` | `([Outlay]-[Outlay Forecast])/[Outlay Forecast]` | divisão sem DIVIDE | | não usada |
| **`Revenues Forecast`** | receita planejada | `CALCULATE(SUM(fMetasDre[valor]), USEREL, operaÇÃo="C", tipo_custeio-CAT IN {"ReceitasPec","ReceitasAgr","ReceitaPec","ReceitaAgr"})` (sem espaço porque o Pentaho remove espaços nas metas) | `Σmeta.valor WHERE operacao='C' AND tipo IN ('ReceitaPec','ReceitaAgr',…)` | barras "Realizado x Planejado – Receitas" |
| **`Expenses Forecast`** | despesa planejada | `CALCULATE(SUM(fMetasDre[valor]), USEREL, operaÇÃo="D")` | | barras "Realizado x Planejado – Desembolso" (filtro `fMetasDre[desembolso-CAT]='DCM'`) |
| `Costing` | custeio realizado (positivo) | `SUM(financeiroDre[Custeio])` | `Σvalor WHERE custeio_cat='CCM'` | base |
| `Costing Forecast` | custeio planejado | `CALCULATE(SUM(fMetasDre[Custeio]), USEREL)` | | base |

### 5.12 Financeiro por cabeça (R$/cab/mês)

Fórmula de negócio: **Desembolso (ou Custeio) por cabeça por mês = valor acumulado no período ÷ rebanho médio do período ÷ nº de meses**. Num card isso simplifica para `valor / Σ(rebanho mensal)` (R$ por cabeça-mês).

| Medida | O que calcula | Lógica | Pseudo-SQL | Uso |
|---|---|---|---|---|
| **`head outlay mOm`** | desembolso/cab/mês (mês a mês) | `(CALCULATE(DIVIDE([Outlay],[Mean Month])) * -1) / [Count of Selected Month]` | `-Σdesembolso(ctx) / (Σqtd_cab(ctx)/N) / N` = `-Σdesembolso / Σqtd_cab` | gráfico "Realizado x Planejado – Desembolso/cab/mês" (filtro `> 0`) |
| **`head outlay mOm (forecast)`** | idem planejado | `(DIVIDE([Outlay Forecast],[Mean Month - forecast]) * -1) / [Count of Selected Month]` | `-Σmeta_desemb / (Σmeta_qtd_cab/N) / N` | idem |
| `Expenses Accumulated` | desembolso acumulado (negativo) | `CALCULATE([Outlay], FILTER(ALLSELECTED(dCalendar), Data <= EOMONTH(MAX(Data),0)))` (**T1e**) | `-Σvalor DCM WHERE data BETWEEN :ini AND eom(ctx_fim)` | base |
| `Expenses Accumulated - Forecast` | idem meta | `[Outlay Forecast]` com **T1** (sem EOMONTH) | | base |
| **`head outlay accumulated`** | **desembolso/cab/mês acumulado** | `(DIVIDE([Expenses Accumulated], [Mean Month Accumulated - Aux (Desembolso)], 0) * -1) / [Count of Selected Month] + 0` | `(-desemb_acum / rebanho_medio_janela) / N(ctx)` | gauge "DESEMBOLSO CABEÇA MÊS" (valor) |
| **`head outlat accumulated - forecast`** (sic) | idem planejado | `(DIVIDE([Expenses Accumulated - Forecast], [Mean Month Accumulated - Aux (Desembolso) - Forecast], 0) * -1) / [Count of Selected Month] + 0` | | gauge (alvo) |
| `head outlat accumulated - forecast graph` | máximo do gauge | `forecast × 1,2` | | UI (gauge) |
| `Costing Accumulated` | custeio acumulado | `[Costing]` com T1e | | base |
| `Costing Accumulated - Forecast` | idem meta | `[Costing Forecast]` com T1 | | base |
| **`Costing head Accumulated`** | **custeio/cab/mês acumulado** | `DIVIDE([Costing Accumulated], [Mean Month Accumulated - Aux (Desembolso)], 0) / [Count of Selected Month] + 0` | `custeio_acum / rebanho_medio_janela / N` | gauge "CUSTEIO CABEÇA MÊS" (valor) |
| **`Costing Head accumulated - forecast`** | idem planejado | com `Costing Accumulated - Forecast` e `… Aux (Desembolso) - Forecast` | | gauge (alvo) |
| `Color Desemb Cab Mês` | cor | `IF(real > meta, "#870000", "#008D7D")` | | formatação do gauge |
| `Color Costing Cab Mês` | cor | idem custeio | | formatação do gauge |
| `IN Desembolso Cab Mês` / `IN Costing Cab Mês` | ±1 | | | não usadas |

Python (card do período, sem as sutilezas de ano):

```python
N = reb.loc[reb.data.between(ini, fim)].groupby(reb.data.dt.month).qtd_cab.sum().gt(0).sum()
reb_medio = reb.loc[reb.data.between(ini, fim), 'qtd_cab'].sum() / N
desemb = -dre.loc[(dre.desembolso_cat == 'DCM') & dre.data_pag.between(ini, eom(fim)), 'valor'].sum()
desemb_cab_mes = (-desemb / reb_medio) / N          # = soma DCM / soma dos rebanhos mensais
custeio_cab_mes = dre.loc[(dre.custeio_cat == 'CCM') & dre.data_pag.between(ini, eom(fim)), 'valor'].sum() / reb_medio / N
```

### 5.13 Planejado x Realizado do DRE por centro de custo (`planejadoXRealizado`)

Página "Previsto x Realizado": matriz com linhas `classificacao` → `centro_de_custo_bi` e as colunas: Realizado (mês), Planejado (mês), % Var (mês) + ícone, Realizado acumulado, Planejado acumulado, % Var acumulado + ícone.

| Medida | O que calcula | Lógica | Pseudo-SQL |
|---|---|---|---|
| **`Valor Último Mês Selecionado`** (tabela planejadoXRealizado) | realizado do **último mês** da seleção | T5. Se `ISINSCOPE(classificacao)` (linhas de classificação/centro): `SUM(Valor C)`; senão (total geral): `COALESCE(Receitas,0) − COALESCE(Despesas,0)` com Receitas = classificação `"A - RECEITAS"` e Despesas = `{"C - INVESTIMENTOS","D - CUSTEIO","E - OUTROS DÉBITOS"}` | `SELECT SUM(realizado) FROM v_pxr WHERE data = date_trunc('month', :fim) …`; total = `Σ(A) − Σ(C,D,E*)` |
| **`Meta Último Mês Selecionado`** | meta do último mês | idem com `Meta C` (sem COALESCE) | idem com `meta` |
| `% Variação` | variação % mensal | `DIVIDE([Valor Último Mês] − [Meta Último Mês], [Meta Último Mês])` | `(real−meta)/meta` |
| **`% Variação Graph`** | wrapper que devolve `[% Variação]` (o ícone calculado é descartado) | | coluna "% Var" |
| **`Value Accumulated`** | realizado acumulado | `MAX(Data)` do contexto; se `ISINSCOPE(classificacao)`: `SUM(Valor C)` com **T1**; senão `ReceitasAcum − DespesasAcum` (mesmas listas) | `Σrealizado WHERE data BETWEEN :ini AND ctx_fim` |
| **`Meta Accumulated`** | meta acumulada | idem com `Meta C` | |
| `%% Variação Acc` | variação % acumulada | `DIVIDE([Value Accumulated] − [Meta Accumulated], [Meta Accumulated])` | |
| **`% Variação Acc Graph`** | wrapper de `%% Variação Acc` | | coluna "% Var acumulado" |
| `Icon` | semáforo mensal (texto VERDE/AMARELO/VERMELHO) | `_class = SELECTEDVALUE(classificacao)`. Receitas: `>+3%` VERDE, `<−3%` VERMELHO, entre ±3% AMARELO. Demais (despesas): `−100% ≤ var ≤ 0` VERDE, `0 < var ≤ 3%` AMARELO, `>3%` VERMELHO | regra de ícone na formatação condicional |
| `Icon Acc` | semáforo acumulado | idem sobre `%% Variação Acc`, mas com `SELECTEDVALUE(Classificacao2)` (outra codificação de letras) | |
| `RL Mensal` / `RL Acumulado` | rótulos "MENSAL"/"ACUMULADO" | | UI |

Regras de semáforo em Python:

```python
def semaforo(var, is_receita):
    if var is None: return None
    if is_receita:
        return 'VERDE' if var > .03 else 'VERMELHO' if var < -.03 else 'AMARELO'
    if -1 <= var <= 0: return 'VERDE'
    if 0 < var <= .03: return 'AMARELO'
    if var > .03: return 'VERMELHO'
    return None
```

### 5.14 Medidas de UI / formatação (resumo)

* **Rótulos de texto (56, pasta `IN - Data Labels`)**: retornam strings fixas para títulos de cards — p.ex. `IN - Realizado`="Realizado", `IN - Planejado`/`IN - Meta`="Planejado", `IN - Fêmea`="FÊMEA", `IN - Macho`="MACHO", `IN - Geral`="GERAL", `IN - Bezerro`/`Jovens`/`Adultos`, `IN - Valor da @`="Preço de Venda da @", `IN - Preço do KG`, `IN - Peso Médio Vivo`, `IN - Rendimento de Carcaça`, `IN - Faturamento`="Fat. Realizado", `IN - Faturamento Planejado`, `IN - Inv Realizado`/`Inv Planejado`, `IN - Cbs Vendidas`/`Cbs Compradas`, `IN - Ágio`, `IN - Valor da @ Compra`, `IN - Rebanho Médio (Cab/UA)`, `IN - Lotação Cab/UA`, `IN - % Meta`, `IN - Indice de Mortalidade`, `IN - Mortalidade sobre Rebanho Médio`/`sobre Nascimento`, `IN - Nascimentos`(="% Sobre Sobre o Total", typo), `IN - Entrada`/`Saida`/`Quantidade`/`TRANSFERÊNCIAS`, `IN Peso Médio`, `IN Valor@`, `IN - COMPRA X VENDA`, `IN - Site Terra`="terradesenvolvimento.com.br", `IN - Data Análise`="Análise :", `IN - Separador de`="de", `IN - Cabeças`="Cb", etc. Dois são dinâmicos:
  * `IN - Periodo Capa` = `FORMAT(MAX(dCalendar[Data]), "MMMM \d\e yyyy")` → "setembro de 2026" (mês final da seleção).
  * `IN - Periodo Envio` = `"Cuiabá, " & FORMAT(TODAY(),"MMMM") & " de " & YEAR(TODAY()) & "."`.
  * Lista completa (56): `IN - Peso Médio Vivo` = "Peso Médio Vivo"; `IN - Valor da @` = "Preço de Venda da @"; `IN - Rendimento de Carcaça` = "Rendimento de Carcaça"; `IN - Fêmea` = "FÊMEA"; `IN - Macho` = "MACHO"; `IN - Cabeças` = "Cb"; `IN - Geral` = "GERAL"; `IN - Faturamento` = "Fat. Realizado"; `IN - Preço do KG` = "Preço do KG"; `IN - Meta Valor KG` = "Meta Valor KG"; `IN - Ágio` = "Ágio"; `IN - Valor da @ Compra` = "Preço de @ de Compra"; `IN - Bezerro` = "BEZERROS"; `IN - Jovens` = "JOVENS"; `IN - Adultos` = "ADULTOS"; `IN - Meta` = "Planejado"; `IN - Mortalidade sobre Rebanho Médio` = "% Sobre Rebanho Médio"; `IN - Mortalidade sobre Nascimento` = "% Sobre Nascimento"; `IN - Nascimentos` = "% Sobre Sobre o Total"; `IN - Relação a Meta` = "% Em relação a Meta"; `IN - Vendas (Geral)` = "VENDAS"; `IN - Compras (Label)` = "COMPRAS"; `IN - Nascimentos (Label)` = "Nascimentos"; `IN - Mortes` = "MORTES"; `IN - Compra` = "Valor Compra"; `IN - Planejado` = "Planejado"; `IN - Realizado` = "Realizado"; `IN - Rebanho Médio` = "REBANHO MÉDIO"; `IN - Rebanho Médio Cab` = "Rebanho Médio Cab"; `IN - Rebanho Médio UA` = "Rebanho Médio UA"; `IN - Lotação Cab` = "Lotação Cab"; `IN - Lotação UA` = "Lotação UA"; `IN - % Meta` = "% Em Relação a Meta"; `IN - Indice de Mortalidade` = "Índ. Mortalidade"; `IN - Mortes (2)` = "Mortes"; `IN - Nascimentos (Label - 2)` = "NASCIMENTOS"; `IN - Compras (Label 2 )` = "Compras"; `IN - Vendas (Label)` = "Vendas"; `IN - COMPRA X VENDA` = "COMPRAS / VENDAS"; `IN - Data Análise` = "Análise :"; `IN - Separador de` = "de"; `IN - Periodo Capa` = (dinâmica, acima); `IN - Site Terra` = "terradesenvolvimento.com.br"; `IN - Periodo Envio` = (dinâmica, acima); `IN - Faturamento Planejado` = "Fat. Planejado"; `IN - Inv Realizado` = "Inv. Realizado"; `IN - Inv Planejado` = "Inv. Planejado"; `IN - Cbs Vendidas` = "Cabeças Vendidas"; `IN - Cbs Compradas` = "Cbs Compradas"; `IN - Entrada` = "ENTRADA"; `IN - Saida` = "SAÍDA"; `IN - Quantidade` = "QTD"; `Medida 3` = (vazia); `IN Peso Médio` = "PESO MÉDIO"; `IN Valor@` = "VALOR @"; `IN - TRANSFERÊNCIAS` = "TRANSFERÊNCIAS".
* **Outras de UI**: `Selected Farm` = `IF(SELECTEDVALUE(fUnidades[fazenda]) = BLANK(), "GRUPO", SELECTEDVALUE(fUnidades[fazenda]))` (cabeçalho de todas as páginas; "GRUPO" quando várias fazendas), `Sistema Produção` = "INFORMATIVO DETALHADO PG1" (não usada), `IN - Name (Abate)` = "Venda Abate" (não usada), cores (`Color …`), indicadores ±1 (`IN Venda Geral`, `IN Costing Cab Mês`, `IN Desembolso Cab Mês`, `IN Mean Month`), máximos de gauge (`MAX AVG Price @ Forecast`, `head outlat accumulated - forecast graph`), ícones (`Icon`, `Icon Acc`), wrappers (`% Variação Graph`, `% Variação Acc Graph`), `RL Mensal`, `RL Acumulado`.
* **Vazias**: `Medida` (pecuarioVendaEmPe), `Medida 2` (fMovGado), `Medida 3`, `Rebanho Median Month`, `Arroba Value`.

O inventário completo das 237 medidas, com uso por página, está no **Apêndice A**.


---

## 6. Glossário de conceitos de negócio (como a DAX/planilha os define)

| Conceito | Definição no modelo |
|---|---|
| **Fazenda / PROP_FAZ** | Unidade de análise = proprietário + fazenda (uma planilha por fazenda). Chave técnica `unaccent(replace(proprietário‖fazenda,' ',''))`. `retiro` é subdivisão interna (existe nos fatos mas não é dimensão). `projeto`/`CÓDIGO PROJETO` = código do cliente na consultoria. |
| **Sistema produtivo** | `fUnidades[SISTEMA PRODUTIVO]` ∈ {CRIA, RECRIA E ENGORDA, CICLO COMPLETO}. Este relatório filtra só **CICLO COMPLETO** (cria + recria + engorda na mesma fazenda). |
| **Tipo de ano** | `fUnidades[ano]` ∈ {CÍVIL, SAFRA} (informativo; o usuário escolhe a visão no menu). |
| **Ano civil × Safra** | Safra pecuária = **julho a junho** ("Safra 2025/26" = jul/2025–jun/2026). |
| **Categoria BI** (15) | Machos: `BEZERRO` (00–08 m, grupo BEZERROS), `MACHOS 8-12` (JOVENS), `MACHOS 13-24` (JOVENS), `MACHOS 25-36` (ADULTOS), `MACHOS + 36`, `TOUROS`, `TOUROS DESCARTES`, `SINUELO` (ADULTOS, +36). Fêmeas: `BEZERRA` (00–08, BEZERROS), `NOVILHAS 8-12` (JOVENS), `NOVILHAS 13-24` (JOVENS), `NOVILHAS 25-36` (ADULTOS), `MATRIZES`, `VACA DESCARTE`, `VACA LEITEIRA` (ADULTOS, +36). Fonte: aba `dCategorias` da planilha. |
| **Categoria fazenda** (`categ_fazenda`) | Nome livre usado pela fazenda (ex.: "Garrote 12 a 24 Meses", "Boi +36 Meses", "Multiparas +36 Meses", "Desmama Fêmea") mapeado para `categoria_bi` no `CADASTROINICIAL` da planilha (garrote = macho 13–24 m, boi = macho 25+ m, novilha = fêmea 8–36 m, matriz/multípara = vaca de cria). |
| **Grupo de categoria** | BEZERROS (0–8 m), JOVENS (8–24 m), ADULTOS (≥25 m). Em `pecuarioMortes` em maiúsculas; em rebanho médio "Bezerros/Jovens/Adultos". |
| **Era** | faixa etária em meses: `00-08`, `08-12`, `13-24`, `25-36`, `+36`. |
| **Operações de movimentação** | `Saldo Anterior`, `COMPRA`, `NASCIMENTO`, `Transf. Entrada` (entradas); `ABATE`, `EMPÉ` (venda em pé), `MORTE`, `Consumo/Doação`, `Transf. Saida` (saídas); `DESMAME` e `Mud. de Categoria` (saída de uma categoria e entrada em outra; líquido zero). |
| **Estoque** | Final = Σ movimentações assinadas até a data (inclui Saldo Anterior). Inicial = Σ até antes do 1º dia do período. |
| **Rebanho médio (cab)** | Vem pronto da planilha por mês e grupo (`qtd_cab`); o BI faz Σ dos grupos e média entre meses: `Σqtd_cab / nº meses`. |
| **UA (unidade animal)** | `qtd_ua` vem **pronta** da planilha (normalmente 1 UA = 450 kg de peso vivo, mas **a conversão não existe na DAX nem no SQL** — no `.xlsm` de exemplo a coluna está vazia, ou seja, é digitada/calculada fora). Rebanho médio UA = `Σqtd_ua / nº meses`. |
| **Área** | `fArea` mensal: `Área_pasto`, `Área_ilp` (integração lavoura-pecuária), `Área_total` (ha). Área média = `ΣÁrea_total / nº meses`. |
| **Lotação** | cab/ha = rebanho médio cab ÷ área total média; UA/ha = rebanho médio UA ÷ área total média. |
| **Arroba (@)** | **Abate**: 1 @ = 15 kg de **carcaça** (`peso_morto = peso_arroba*15`). **Em pé, compras, transferências**: 1 @ = 30 kg de **peso vivo** (equivale a 15 kg de carcaça com rendimento de 50%). |
| **Peso vivo / peso morto** | `peso_vivo` kg/cab no momento da venda/compra; `peso_morto` = kg de carcaça/cab (abate). Totais `pesovivo_total = peso_vivo*qtd`, `pesomorto_total = peso_morto*qtd`. |
| **Rendimento de carcaça** | `Σpesomorto_total / Σpesovivo_total`. |
| **Preço médio da @** | Abate: `Σfaturamento / Σ(@ carcaça)`; Em pé: `Σfaturamento / (Σkg vivo/30)`; Compra: `ΣVALOR TOTAL / (Σkg vivo/30)`; Geral de venda: `(Σfat_abate+Σfat_empe) / (Σkg_carcaça_abate/15 + Σkg_vivo_empe/30)`. |
| **Preço do kg** | Em pé: `Σfaturamento/Σkg vivo`; compra: `ΣVALOR TOTAL/Σtotal_peso`. (Na planilha de abate `valor_kg = faturamento/pesovivo_total`.) |
| **Peso médio** | `Σkg vivo total / Σcabeças` (venda, compra, transferência). |
| **Ágio** | `(preço @ compra − preço @ venda geral) / preço @ venda geral`. Positivo = a reposição custou mais por @ do que a venda rendeu. |
| **Nascimentos** | Contagem absoluta (`Σqtd`), % do planejado, % machos / % fêmeas. **Não existe taxa de natalidade** (nascimentos ÷ matrizes) no modelo. |
| **Mortalidade** | (a) **sobre rebanho médio** = `mortes do período / rebanho médio do período` (por grupo, com o rebanho médio do mesmo grupo); (b) **sobre nascimentos** = `mortes acumuladas (bezerros) / nascimentos acumulados`; (c) **% em relação à meta** = mortes / mortes planejadas. |
| **Desfrute, GMD, taxa de desmame, idade ao abate** | **Não calculados** neste BI (não há medida). O desmame só aparece como movimentação (medidas `Weaning Entry/Exit`, não usadas). |
| **Plano de contas (DRE)** | `operaÇÃo` C/D; `centro_de_custo_bi`/`sub_centro_bi` = taxonomia Metryx; `desembolso-CAT`: **DCM** = desembolso de caixa operacional, **REP.** = reposição (compra de rebanho, fretes/comissões de compra); `custeio-CAT`: **CCM** = custeio; `tipo_custeio-CAT`: **CV** custo variável, **CF** custo fixo, **Receita Pec/Agr/outras**, **Financiamentos**, **Aporte**. |
| **Receitas** | `Revenues` = C com tipo Receita Pec + Receita Agr; `All Revenues` = + Receita outras. |
| **Despesas** | `Expenses Graph` = Σ todas as operações D (inclui investimento, financiamento, dividendos). |
| **Desembolso** | Σ lançamentos DCM (sinal negativo no modelo). |
| **Custeio** | Σ lançamentos CCM. |
| **Saldo (fluxo de caixa)** | `All Revenues − Σ D`. |
| **Desembolso/Custeio por cabeça por mês** | `valor do período ÷ rebanho médio ÷ nº de meses` (= valor ÷ Σ rebanhos mensais). |
| **Planejado / Meta / Forecast / Previsto** | Mesma coisa: abas `*PLANEJADO` da planilha → tabelas `fMetas*` (e `planejadoXRealizado.meta`). % atingido = realizado ÷ planejado; % variação = (realizado − planejado) ÷ planejado. |
| **Semáforo do DRE** | Receitas: > +3% verde, < −3% vermelho, ±3% amarelo. Despesas: ≤ 0% (até −100%) verde, 0–3% amarelo, > 3% vermelho. |

---

## 7. Páginas do relatório (= telas do app)

Ordem de navegação; tamanho; slicers. **Todas as páginas** têm os mesmos slicers sincronizados e ocultos (Proprietário, Fazenda, Mês `mesano`, Safra, Ano, Parâmetro - Data), um botão "voltar ao menu" e o card `Selected Farm` no cabeçalho. Filtro de relatório travado: `SISTEMA PRODUTIVO = 'CICLO COMPLETO'`.

### 7.1 MENU 01 (visível, 1280×720) — tela de filtros
* Slicers visíveis: **Proprietário**, **Fazenda**, **Mês** (`dCalendar[mesano]`), e **Safra** ou **Ano** conforme o modo.
* Botões "Cívil/Safra Habilitado/Desabilitado" acionam os bookmarks **MENU - CIVIL** / **MENU - SAFRA** (mostram o slicer de Ano ou de Safra). Texto: "SELECIONE A FORMA DE VISUALIZAÇÃO:".
* Botão de navegação para "Previsto x Realizado" (demais páginas via abas).
* App: tela/painel lateral de filtros globais (fazenda(s), modo civil/safra, ano ou safra, meses).

### 7.2 Capa (1920×1080)
* `Selected Farm` (nome ou "GRUPO"), `IN - Periodo Capa` (mês/ano final da seleção, ex. "setembro de 2026"), `Min(dCalendar[Safra Abreviada])` ("25/26"), `IN - Periodo Envio` ("Cuiabá, outubro de 2026."), `IN - Site Terra`, rótulo "Análise :".
* App: cabeçalho/cover do boletim (útil para export PDF).

### 7.3 Previsto x Realizado (1920×1600) — DRE gerencial por centro de custo
* **Matriz**: linhas `planejadoXRealizado[classificacao]` → `[centro_de_custo_bi]`; valores `Valor Último Mês Selecionado`, `Meta Último Mês Selecionado`, `% Variação Graph` (+ ícone `Icon`), `Value Accumulated`, `Meta Accumulated`, `% Variação Acc Graph` (+ ícone `Icon Acc`). Cabeçalhos `RL Mensal` / `RL Acumulado`.
* Filtro de visual `financeiroDre[Classificacao] não vazio` (sem efeito sobre `planejadoXRealizado`).
* App: tabela hierárquica com colunas Mês (real, meta, var%, semáforo) e Acumulado (real, meta, var%, semáforo); linha de total = Receitas − (Investimentos + Custeio + Outros débitos).

### 7.4 Financeiro (1920×1080)
| Visual | Tipo | Campos |
|---|---|---|
| DESEMBOLSO | card múltiplo | `Outlay`, `Revenues` |
| REALIZADO X PLANEJADO – RECEITAS | colunas por `mesano` | `Revenues`, `Revenues Forecast` |
| REALIZADO X PLANEJADO – DESEMBOLSO | colunas por `mesano` | `Expenses Graph`, `Expenses Forecast`; filtros `financeiroDre[desembolso-CAT]='DCM'` e `fMetasDre[desembolso-CAT]='DCM'` |
| RELAÇÃO DESEMBOLSO TOTAL | colunas por `financeiroDre[centro_de_custo_bi]` | `Expenses Graph`; filtro `desembolso-CAT IN ('DCM','REP.')` |
| FLUXO DE CAIXA MENSAL | combo por `mesano` | barras `Revenues`, `Expenses Graph`; linha `Balance` |
| Realizado x Planejado – Desembolso/cab/mês | colunas por `mesano` | `head outlay mOm`, `head outlay mOm (forecast)`; filtro `head outlay mOm > 0` |
| DESEMBOLSO CABEÇA MÊS | gauge | valor `head outlay accumulated`, alvo `head outlat accumulated - forecast`, máx. `head outlat accumulated - forecast graph`, cor `Color Desemb Cab Mês` |
| CUSTEIO CABEÇA MÊS | gauge | valor `Costing head Accumulated`, alvo `Costing Head accumulated - forecast`, cor `Color Costing Cab Mês` |
| Valor de Venda @ | gauge | valor `AVG Price @ (Em Pe + Abate)`, alvo `… - Forecast`, máx. `MAX AVG Price @ Forecast`, cor `Color @ Venda Geral` |

### 7.5 Movimentação do Gado (1920×1080) — resumo zootécnico
* Cards: **Estoque final** (`Stock Accumulated Final`); **Rebanho médio Cab** (`Mean Month`); **Rebanho médio UA** (`UA Median Month`); **Lotação Cab** (`Mean Month Ha`); **Lotação UA** (`UA Median Ha`); **Nascimentos** (`Birth Quantity`, % meta `% Birth x Forecast`); **Mortes** (`Dead Quantity`, índice `% mORTALITY ( MEAN MONTH)`, % meta `% Death x Death Forecast`); **Compras** (`Sum(pecuarioCompras[qtd])`, % meta `% Purchased Quantity`); **Vendas** (`Amount Saled`, % meta `% Amount Saled`).
* Gráficos: **ESTOQUE FINAL MENSAL** (`Stock Accumulated Final` por `mesano`); **ESTOQUE POR CATEGORIA** (`Stock Accumulated Final` por `fMovGado[categoria_bi]`).

### 7.6 Venda Abate (1920×1080)
* Grade **GERAL / MACHO / FÊMEA** (filtro de visual `sexo`) × **Realizado / Planejado** com: cabeças (`Sum(pecuarioVendaAbate[qtd])` / `Sum(fMetasAbate[qtd])`), faturamento (`Invoicing (Abate)` / `Incoicing - Forecast (Abate)`), preço da @ (`AVG Price @ Dead Sale` / `… - Forecast`), peso médio vivo (`IN - AVG Live Weight` / `… (Forecast)`), rendimento de carcaça (`Rendimento Carcaça` / `IN - Rendimento Carcaça (Forecast)`).
* Gráficos: **RELAÇÃO MENSAL – FATURAMENTO** (`Invoicing (Abate)` vs `Incoicing - Forecast (Abate)`); **RELAÇÃO MENSAL – VENDA EM CABEÇAS** (`Amount Saled (Abate)` vs `Amount Saled - Forecast (Abate)`; linha `Invoicing Accumulated (Abate)` = cabeças acumuladas).

### 7.7 Venda em Pé (1920×1080)
* Mesma grade: cabeças (`Sum(pecuarioVendaEmPe[qtd])` / `Sum(fMetasEmPe[qtd])`), faturamento (`Invoicing (Em Pe )` / `Incoicing - Forecast (Em Pe)`), preço da @ (`AVG Price @ Sale Venda em Pe` / `… - Forecast`), preço do kg (`AVG Price KG Sale Venda em Pe` / `… - Forecast`), peso médio vivo (`IN - AVG Live Weight (Em Pe)` / `… (Em Pe - Forecast)`).
* Gráficos: **RELAÇÃO MENSAL – FATURAMENTO**; **RELAÇÃO MENSAL – VENDA EM CABEÇAS** (linha `Amount Saled Accumulated (Em Pe)`).

### 7.8 Compras (1920×1080)
* Grade GERAL/MACHO/FÊMEA × Realizado/Planejado: cabeças (`Sum(pecuarioCompras[qtd])` / `Sum(fMetasCompras[qtd])`), investimento (`Total Paid` / `Total Paid - Forecast`), preço do kg (`AVG Purchase Price KG` / `… (Forecast)`), peso médio (`IN AVG - Peso Médio de Compra` / `… (Forecast)`).
* Cards: **Preço da @ de compra** (`@ AVG Price Purchase`), **Ágio** (`Ágio`).
* Gráficos: **RELAÇÃO DESEMBOLSO DE COMPRAS** (`Total Paid` vs `Total Paid - Forecast`; linha `@ AVG Price Purchase`); **RELAÇÃO CABEÇAS COMPRADAS** (`Purchased Quantity` vs `Purchased Quantity - Forecast`; linha `Purchase Quantity Accumulated`).

### 7.9 Nascimentos (1920×1080)
* Cards GERAL/MACHO/FÊMEA: realizado (`Sum(pecuarioNascimento[qtd])`) e planejado (`Sum(fMetasNascimentos[qtd])`); `% Birth x Forecast`; `IN - % Male Birth`, `IN - % Female Birth`.
* Gráficos: **NASCIMENTOS – REALIZADO X PLANEJADO – MENSAL** (`Birth Quantity`, `Birth Quantity - Forecast`); **… – ACUMULADO** (`Birth Quantity Accumulated`, `Birth Quantity Accumulated - Forecast`).

### 7.10 Mortes (1920×1080)
* Grade **GERAL / BEZERROS / JOVENS / ADULTOS** × realizado (`Dead Quantity` com filtro `pecuarioMortes[grupo_categoria]`), planejado (`Dead Quantity - Forecast` com filtro `fMetasMortes[grupo_categoria]`), **% sobre rebanho médio** (`% mORTALITY ( MEAN MONTH)` com filtros casados de grupo em mortes e rebanho médio), **% sobre nascimento** (`% Mortality`, bezerros).
* Gráficos: **MORTES – REALIZADO X PLANEJADO – MENSAL** (`Dead Quantity`, `Dead Quantity forecast`; linha `Dead Quantity Accumulated`); **REALIZADO X PLANEJADO – ACUMULADO GERAL** (`Dead Quantity Accumulated`, `Dead Quantity Accumulated - Forecast`); **Causa Morte** (barras `Dead Quantity` por `pecuarioMortes[causa]`, filtro `> 0`).

### 7.11 Transferências (1920×1080)
* Grade **ENTRADA / SAÍDA** × **MACHO / FÊMEA** × **Realizado / Planejado** (filtros de visual `operaÇÃo` + `sexo`): quantidade (`IN QTD Transfer` / `IN QTD Transfer Forecast`), peso médio (`IN - AVG Weight Transfer` / `… Forecast`), valor da @ (`IN - AVG Price @ Transfer` / `… Forecas`).
* Gráfico "REALIZADO X PLANEJADO" (na verdade **Entrada × Saída realizadas**): `IN - Incoming Transfer`, `IN - Outgoing Transfer` por `mesano`.

### 7.12 Páginas ocultas (legado; não reproduzir, mas contêm ideias)
* **Duplicata de PG1** (1280×1800): versão antiga do Financeiro (usa `All Revenues` no fluxo de caixa).
* **PG3** (1280×1600): nascimentos/mortalidade antigos — "RELAÇÃO DE NASCIMENTOS" (`Birth Quantity` + acumulados), `% Birth x Forecast (Year)`, `% Mortality` (bezerros), "PREVISTO X REALIZADO ACUMULADO BEZERROS/JOVENS/ADULTOS" (`Accumulated Death` vs `Dead Quantity Accumulated - Forecast`; linha `% Forecast Indicator Accumulated` — baseada em forecast FAKE), "Causa Morte", nascimentos por sexo.
* **Duplicata de PG2** (1280×1600): boletim-resumo de 1 página (estoque, rebanho médio, lotação, nascimentos, mortes, compras, vendas por mês e por sexo (`Categorias[gender]`), faturamento por `Tabela[TipoVenda]`, rendimento, preço kg em pé, preço @ abate, `Peso em @`, estoque por categoria).

---

## 8. Problemas, inconsistências e riscos encontrados

### 8.1 Erros de cálculo (impactam números exibidos)

1. **Total do "Previsto x Realizado" ignora Outros Débitos/Créditos**: as medidas de total (`Valor/Meta Último Mês Selecionado`, `Value/Meta Accumulated`) subtraem `{"C - INVESTIMENTOS","D - CUSTEIO","E - OUTROS DÉBITOS"}`, mas o SQL gera `E - OUTROS CRÉDITOS` e `F - OUTROS DÉBITOS`. Resultado: dividendos, amortização de financiamentos e empréstimos de sócios **não entram** no total; créditos de financiamento também não. Há ainda **três codificações diferentes** da mesma classificação (SQL `classificacao`; `planejadoXRealizado[Classificacao2]`; `financeiroDre[Classificacao]`), e `Icon Acc` usa uma diferente de `Icon`.
2. **SQL do `planejadoXRealizado` pode duplicar o realizado / perder meta**: `dados` agrupa por `T1.meta` após juntar metas (granularidade dia) com realizado (granularidade dia/valor) no nível mês; se houver ≥2 lançamentos de meta com **o mesmo valor** no mesmo mês/centro, o realizado é multiplicado e a meta conta uma vez só. O `GROUP BY ... realizado` final (sem somar) também mascara o problema.
3. **`% Mortality` mistura janelas**: numerador `Dead Quantity Accumulated` (T1, desde o início da seleção) ÷ denominador `Birth Quantity Accumulated` (T3, `ALL`: desde 1º/jan ou desde 2024-07). Em visão Safra (2 anos civis) o denominador soma todos os nascimentos desde o início dos dados.
4. **Acumulados com `ALL(dCalendar)` ignoram o início da seleção** (`Birth Quantity Accumulated`, `… - Forecast`, `Accumulated Death`): na visão Safra o "acumulado" começa em jul/2024 (início do calendário), não no início da safra; na visão civil começa em 1º/jan. Outros acumulados da mesma página (`Dead Quantity Accumulated`, compras, vendas) usam `ALLSELECTED` → comportamento incoerente entre gráficos.
5. **`Count of Selected Month` conta meses-do-ano (1–12)**, não ano-mês: seleções >12 meses ficam com N ≤ 12 → médias mensais (rebanho médio, UA, área, R$/cab/mês) **infladas**. Além disso só conta meses com rebanho realizado > 0, inclusive quando divide **metas** (`Mean Month - forecast`).
6. **`Mean Month Accumulated` divide por N duas vezes** (média da janela ÷ N do contexto) — está só em medidas mortas, mas o nome sugere reuso.
7. **Fluxo de caixa inconsistente** (página Financeiro): barras usam `Revenues` (Pec+Agr) e a linha `Balance` usa `All Revenues` (inclui "Receita outras") → a linha não é barras(receita) − barras(despesa). `Expenses Graph` inclui **todas** as operações D (investimentos, financiamentos, dividendos), enquanto o gráfico "Realizado x Planejado – Desembolso" filtra só DCM e o "Relação Desembolso Total" inclui DCM + REP.
8. **Join de metas em `pecuarioVendaAbate`/`pecuarioVendaEmPe`** (SQL) não usa `retiro` nem `operaÇÃo`: se a meta tiver mais de um retiro/operação por fazenda-mês, **as linhas de venda são duplicadas** (faturamento e cabeças em dobro). As colunas obtidas (`meta_diluida`, `qtd_meta_diluida`, `diluicao_meta`, `meta_mensal`, `qtd_meta_mensal`, `mes`, `ano`) **não são usadas** em nenhuma medida → o join é risco puro.
9. **Chave de fazenda de `fMetasCompras`**: o M cria uma coluna `PROP_FAZ` concatenando `proprietÁrio & fazenda` **sem `unaccent` e sem remover espaços**, colidindo com o `prop_faz` normalizado do SQL (que virou `prop_faz 2`). A relação ativa usa `fMetasCompras[PROP_FAZ]`. Se for a coluna não normalizada, as metas de compra não casam com `fUnidades` (somem quando há filtro de fazenda/RLS). Existe até uma medida "…- TESTE" tentando contornar. **Verificar** e usar a chave normalizada.
10. **Dados "fake" de demo em produção**: `pecuarioRebanhoMedioMensal[Forecast] = qtd_cab×1,1`, `pecuarioMortes[forecast] = qtd×1,8`, `farm = "FAZENDA EXEMPLO"`; `% Forecast Indicator Accumulated` (PG3) usa o forecast fake como denominador.
11. **`Average Birth Weight`** soma `peso_nasc` (kg/cab) e divide por Σqtd → errado para lançamentos com `qtd>1` (não usada).
12. **`AVG Price @`** soma dois preços médios (não usada). **`Total de @`** (medida) depende de `Arroba Value` vazia → sempre BLANK.
13. **`% mORTALITY ( MEAN MONTH)`** e `% Atingido Outlay` usam `/` em vez de `DIVIDE` → erro/infinito sem rebanho/meta.

### 8.2 Valores fixos (hardcode)

* `Lotation = … / 2911` (área fixa de uma fazenda específica); `Lotation - Forecast` (+10%), `… - MAX` (+40%).
* Máximos de gauge: `MAX AVG Price @ Forecast` = meta × 1,15; `head outlat accumulated - forecast graph` = meta × 1,2.
* Limiares do semáforo ±3%; cores `#870000` / `#008D7D`.
* Fatores 15 (kg carcaça/@) e 30 (kg vivo/@) espalhados em colunas calculadas e medidas.
* `IN - Periodo Envio` fixa "Cuiabá"; `IN - Site Terra`.
* `dCalendar` começa em `2024-07-01` fixo e termina em `DateTime.LocalNow()` → metas de meses futuros e dados anteriores a jul/2024 ficam fora; no serviço o "agora" é UTC (o último dia pode ser cortado).
* Listas de `centro_de_custo_bi` → classificação duplicadas em 3 lugares (SQL e 2 colunas DAX) e lista de "Receita Pec/Agr/outras" escrita de 2 formas (com e sem espaço) por causa do Pentaho.

### 8.3 Resíduos e lixo do modelo (copiado do BI Metryx)

* Colunas calculadas **quebradas** que referenciam o esquema da API Metryx (`amount`, `origin`, `originEnum`, `subCenter`, `kgValue`, `totalWeight`, `valueWeight`, `weightAvg`, `Credito/Debito`, tabela `pecuarioDMG`): `fMovGado[Nascimento|Morte|Mudança de Categoria (Saída)|(Entrada)|Origin Ordenated]`, `pecuarioCompras[Paid]`, `pecuarioVendaAbate[Total Value|teste]`, `financeiroDre[Type Operation|Class subcenter|Meta C]`. → Evidência de que este modelo foi clonado do BI Metryx; a correspondência de medidas entre os dois BIs deve ser alta.
* Medidas vazias/quebradas: `Medida`, `Medida 2`, `Medida 3`, `Rebanho Median Month`, `Arroba Value`, `VALORCALC` (USERELATIONSHIP inexistente).
* ~48 medidas de negócio sem uso (ver Apêndice A), páginas duplicadas ocultas, field parameter `Parâmetro - Data` sem efeito, auto date/time ligado (`LocalDateTable`/`DateTableTemplate`), coluna `fMovGado[Vendas]` que compara com operação inexistente, `planejadoXRealizado[F/V]` comentada, `pecuarioMortes[operaÇÃo_ktl|categ_fazenda_ktl]` vazias (efeito do `SELECT *`).

### 8.4 Duplicações e nomenclatura

* Duplicatas: `Dead Quantity forecast` ≡ `Dead Quantity - Forecast`; `Invoicing Abate` ≡ `Invoicing (Abate)`; `IN - Meta` ≡ `IN - Planejado`; rótulos repetidos (`IN - Mortes`/`IN - Mortes (2)`, `IN - Nascimentos (Label)`/`(Label - 2)`, `IN - Compras (Label)`/`(Label 2 )`, `IN - Vendas (Geral)`/`(Label)`); `Purchased Quantity` vs `Sum(pecuarioCompras[qtd])` implícito nos cards; `Mean Month Accumulated - Aux (Desembolso)` ≈ `Mean Month Accumulated` sem a 2ª divisão.
* Nomes errados/enganosos: `Incoicing`, `Saled`, `outlat`, `Forecas`, `comsuption`, `% mORTALITY ( MEAN MONTH)`, `Invoicing Accumulated (Abate)` (retorna **cabeças**), `pecuarioVendaEmPe[Peso Morto]` (são **arrobas**), `IN - Nascimentos` = "% Sobre Sobre o Total", pasta `Purchase Measures` contém `UA Median Month/Ha`, pasta `Dead Measures` contém `Count of Selected Month`. Mistura EN/PT e "Forecast/Meta/Planejado/Previsto" como sinônimos.
* Cards usam **medidas implícitas** (`Sum(fMetasAbate[qtd])`, `Sum(pecuarioNascimento[qtd])` etc.) em vez de medidas explícitas.
* `USERELATIONSHIP` redundante em relações já ativas (`fMetasNascimentos`, `fMetasCompras`); três tabelas de meta com relação de data **inativa** (`fMetasMortes`, `fMetasRebanhoMedio`, `fMetasDre`) e as demais ativas — sem critério.
* Filtros de visual sem efeito (copy-paste): `fMetasMortes[grupo_categoria]='BEZERROS'` em cards de vendas/lotação da Movimentação; `pecuarioVendaAbate[sexo]` em rótulos da página Mortes; `fMetasCompras[sexo]` num card de Nascimentos; `pecuarioVendaAbate[sexo]` num card de preço kg em pé; `financeiroDre[Classificacao]` na matriz de `planejadoXRealizado`.
* Gráfico "REALIZADO X PLANEJADO" da página Transferências mostra Entrada × Saída (ambos realizados).

### 8.5 Fragilidades de dados/ETL

* **Datas como texto** nas `stg_*` com formatos misturados; cada consulta trata de um jeito (substring + replace, regex YYYYMMDD/DDMMYYYY, `to_date` 'YYYY/MM/DD' ou 'DD/MM/YYYY'). Em `pecuarioMortes` a limpeza de hora é aplicada na coluna que depois é removida (inofensivo).
* `PROP_FAZ` depende da grafia exata de proprietário e fazenda em **cada** planilha e na planilha de RLS (só remove espaços e acentos; não trata caixa nem pontuação).
* `fUnidades[PROP_FAZ]` precisa ser único (1 planilha por fazenda). Se um cliente enviar duas planilhas (ex.: 2025 e 2026) o refresh quebra ou, se a unicidade for contornada, o `Saldo Anterior` de cada planilha **duplicaria o estoque** (estoque = soma desde sempre).
* `Categorias` é derivada de `SELECT DISTINCT categoria_bi, sexo FROM stg_fmovgado`: categoria com dois sexos/sexo vazio quebra a relação; categorias que só existem em outros fatos ficam órfãs. `grupo_categoria` e `era` não estão na dimensão (estão denormalizados e com caixa diferente entre tabelas: "BEZERROS" × "Bezerros").
* `pecuarioMortes[peso_vivo]` é texto.
* **UA**: `qtd_ua` vem pronta da planilha (vazia no exemplo) → lotação UA/ha e rebanho UA dependem de preenchimento manual; não há regra de conversão auditável.
* Área média dividida por N (meses com rebanho), não por meses com área.
* RLS: sem papel administrativo; acesso depende de o e-mail estar na planilha de RLS e do nome da fazenda coincidir; filtro de segurança bidirecional obrigatório.

---

## 9. Recomendações para a reimplementação (SQL/Python, app unificado)

1. **Dimensões canônicas** no Postgres: `dim_fazenda(prop_faz PK, proprietario, fazenda, projeto, codigo_projeto, sistema_produtivo, tipo_ano, fonte {planilha|metryx})`, `dim_categoria(categoria_bi PK, sexo, grupo_categoria, era)` (seed com as 15 categorias), `dim_calendario(data, ano, mes, ano_mes, safra, ordem_safra, …)` gerada por `generate_series` sem limite em "hoje".
2. **Fatos únicos com coluna `cenario` ('realizado' | 'planejado')** em vez de pares `pecuarioX`/`fMetasX`; mesmas colunas → as medidas viram `… WHERE cenario = :c`.
3. **Movimentação assinada** (`qtd_assinada`) como coluna gerada; estoque inicial/final, entradas e saídas por operação/categoria como **view** mensal (`v_estoque_mensal`).
4. **Uma única tabela de-para** `centro_custo_bi → classificacao` (e `tipo_custeio` normalizado, sem a remoção de espaços do Pentaho) usada por DRE realizado, metas e previsto×realizado; refazer o `planejadoXRealizado` como `FULL OUTER JOIN` de agregados mensais (meta e realizado agregados **antes** do join).
5. **Semântica de tempo explícita na API**: parâmetros `modo (civil|safra)`, `periodo [ini, fim]`, `granularidade (mes|periodo)`; todos os acumulados começando em `ini` (padrão T1). Nº de meses = `count(distinct date_trunc('month'))`.
6. Constantes (15 kg, 30 kg, limiares do semáforo, multiplicadores de gauge) em tabela de configuração; eliminar `2911`, forecasts fake e colunas quebradas.
7. Considerar implementar o que o BI **não** tem e é padrão do setor (natalidade sobre matrizes, desfrute, GMD), já que o modelo Metryx pode fornecer peso/datas.
8. Paridade Metryx: o DRE da planilha já usa a taxonomia de centros de custo do Metryx (`BASEPLANODECONTAS`), e o modelo é um clone do BI Metryx (colunas residuais `amount`, `origin`, `subCenter`…). O mapeamento KPI a KPI entre os dois BIs deve ser direto.


---

## Apêndice A — Inventário completo das medidas (237)

Uso: **V** = usada diretamente num visual (campo, filtro ou formatação); **I** = usada só indiretamente (por outra medida usada); **—** = não usada. Páginas ocultas: Duplicata de PG1, PG3, Duplicata de PG2.

| # | Tabela | Medida | Pasta | Domínio | Uso | Páginas | Depende de |
|---|---|---|---|---|---|---|---|
| 1 | Analytics Measures | `Purchased Quantity` | Purchase Measures | Compras | V | Compras, Duplicata de PG2 |  |
| 2 | Analytics Measures | `Total Paid` | Purchase Measures | Compras | V | Compras |  |
| 3 | Analytics Measures | `Purchase Quantity` | Purchase Measures | Compras | — |  |  |
| 4 | Analytics Measures | `Dead KG Amount` | Dead Measures | Mortes | — |  |  |
| 5 | Analytics Measures | `Dead Quantity` | Dead Measures | Mortes | V | Duplicata de PG2, Mortes, Movimentação do Gado, PG3 |  |
| 6 | Analytics Measures | `Birth Quantity` | Birth Measures | Nascimentos | V | Duplicata de PG2, Movimentação do Gado, Nascimentos, PG3 |  |
| 7 | Analytics Measures | `Average Birth Weight` | Birth Measures | Nascimentos | — |  |  |
| 8 | Analytics Measures | `Expenses` | Finance Measures | Financeiro | I |  |  |
| 9 | Analytics Measures | `Revenues` | Finance Measures | Financeiro | V | Duplicata de PG1, Financeiro |  |
| 10 | Analytics Measures | `Balance` | Finance Measures | Financeiro | V | Duplicata de PG1, Financeiro | `All Revenues`, `Expenses` |
| 11 | Analytics Measures | `% Resultado` | Finance Measures | Financeiro | — |  | `Balance`, `Expenses` |
| 12 | Analytics Measures | `Finance Indicator` | Finance Measures | Financeiro | — |  | `% Resultado` |
| 13 | Analytics Measures | `Amount Saled` | IN - General Sales Measures | Vendas (geral) | V | Duplicata de PG2, Movimentação do Gado |  |
| 14 | Analytics Measures | `Invoicing` | IN - General Sales Measures | Vendas (geral) | V | Duplicata de PG2 |  |
| 15 | Analytics Measures | `AVG Price @ Dead Sale` | IN - Medidas Abate | Vendas abate | V | Duplicata de PG2, Venda Abate |  |
| 16 | Analytics Measures | `AVG Price @ Sale Venda em Pe` | IN - Medidas Venda Em Pe | Vendas em pé | V | Venda em Pé |  |
| 17 | Analytics Measures | `AVG Ticket Dead Sale` | IN - Medidas Abate | Vendas abate | — |  |  |
| 18 | Analytics Measures | `AVG Ticket Sale` | IN - Medidas Venda Em Pe | Vendas em pé | — |  |  |
| 19 | Analytics Measures | `Expenses Graph` | Finance Measures | Financeiro | V | Duplicata de PG1, Financeiro |  |
| 20 | Analytics Measures | `Accumulated Death` | Dead Measures | Mortes | V | PG3 | `Count of Selected Years`, `Dead Quantity` |
| 21 | Analytics Measures | `Const Death` | Dead Measures | Mortes | — |  | `Dead Quantity` |
| 22 | Analytics Measures | `Count of Selected Years` | Dead Measures | Aux. tempo | I |  |  |
| 23 | Analytics Measures | `% Death Accumulated` | Dead Measures | Mortes | — |  | `Accumulated Death`, `Const Death` |
| 24 | Analytics Measures | `head outlay mOm` | Head Outlay | Financeiro/cab | V | Duplicata de PG1, Financeiro | `Count of Selected Month`, `Mean Month`, `Outlay` |
| 25 | Analytics Measures | `head outlay accumulated` | Head Outlay | Financeiro/cab | V | Duplicata de PG1, Financeiro | `Count of Selected Month`, `Expenses Accumulated`, `Mean Month Accumulated - Aux (Desembolso)` |
| 26 | Analytics Measures | `Expenses Accumulated` | Head Outlay | Financeiro/cab | I |  | `Outlay` |
| 27 | Analytics Measures | `Mean Month` | Head Outlay | Rebanho/UA/lotação | V | Duplicata de PG2, Movimentação do Gado | `Count of Selected Month` |
| 28 | Analytics Measures | `Mean Month Accumulated` | Head Outlay | Rebanho/UA/lotação | — |  | `Count of Selected Month`, `Count of Selected Years`, `Mean Month` |
| 29 | Analytics Measures | `head outlay mOm (forecast)` | Head Outlay | Financeiro/cab | V | Duplicata de PG1, Financeiro | `Count of Selected Month`, `Mean Month - forecast`, `Outlay Forecast` |
| 30 | Analytics Measures | `Dead Quantity forecast` | Dead Measures | Mortes | V | Mortes |  |
| 31 | Analytics Measures | `% Forecast Indicator` | Dead Measures | Mortes | — |  | `Dead Quantity forecast` |
| 32 | Analytics Measures | `% Realized Indicator` | Dead Measures | Mortes | — |  | `Dead Quantity` |
| 33 | Analytics Measures | `Dead Quantity Accumulated` | Dead Measures | Mortes | V | Mortes | `Dead Quantity` |
| 34 | Analytics Measures | `% Realized Indicator Accumulated` | Dead Measures | Mortes | — |  | `Count Mean Month Accumulated`, `Dead Quantity Accumulated`, `Mean Month Accumulated` |
| 35 | Analytics Measures | `Dead Quantity Accumulated - Forecast` | Dead Measures | Mortes | V | Mortes, PG3 | `Dead Quantity forecast` |
| 36 | Analytics Measures | `Mean Month Accumulated - Forecast` | Head Outlay | Rebanho/UA/lotação | I |  |  |
| 37 | Analytics Measures | `% Forecast Indicator Accumulated` | Dead Measures | Mortes | V | PG3 | `Count Mean Month Accumulated`, `Dead Quantity Accumulated - Forecast`, `Mean Month Accumulated - Forecast` |
| 38 | Analytics Measures | `Total de @` | IN - General Sales Measures | Vendas (geral) | — |  | `Amount Saled`, `Arroba Value` |
| 39 | Analytics Measures | `Arroba Value` | IN - General Sales Measures | Vazia | — |  |  |
| 40 | Analytics Measures | `Amount Saled - Forecast` | IN - General Sales Measures | Vendas (geral) | V | Duplicata de PG2 |  |
| 41 | Analytics Measures | `Incoicing - Forecast` | IN - General Sales Measures | Vendas (geral) | V | Duplicata de PG2 |  |
| 42 | Analytics Measures | `% Death x Death Forecast` | Dead Measures | Mortes | V | Duplicata de PG2, Movimentação do Gado | `Dead Quantity`, `Dead Quantity forecast` |
| 43 | Analytics Measures | `Dead Quantity (Teens)` | Dead Measures | Mortes | — |  |  |
| 44 | Analytics Measures | `Dead Quantity (Adults)` | Dead Measures | Mortes | — |  |  |
| 45 | Analytics Measures | `Dead Quantity (Calves)` | Dead Measures | Mortes | — |  |  |
| 46 | Analytics Measures | `head outlat accumulated - forecast` | Head Outlay | Financeiro/cab | V | Duplicata de PG1, Financeiro | `Count of Selected Month`, `Expenses Accumulated - Forecast`, `Mean Month Accumulated - Aux (Desembolso) - Forecast` |
| 47 | Analytics Measures | `Mean Month - forecast` | Head Outlay | Rebanho/UA/lotação | I |  | `Count of Selected Month` |
| 48 | Analytics Measures | `Stock` | Stock Measures | Estoque | I |  |  |
| 49 | Analytics Measures | `Stock Accumulated Inicial` | Stock Measures | Estoque | — |  | `Stock` |
| 50 | Analytics Measures | `Stock Accumulated Final` | Stock Measures | Estoque | V | Duplicata de PG2, Movimentação do Gado | `Stock` |
| 51 | Analytics Measures | `Buy` | Stock Measures | Estoque | — |  | `Stock` |
| 52 | Analytics Measures | `Sell` | Stock Measures | Estoque | — |  | `Stock` |
| 53 | Analytics Measures | `Birth` | Stock Measures | Estoque | — |  | `Stock` |
| 54 | Analytics Measures | `Change Category entry` | Stock Measures | Estoque | — |  | `Stock` |
| 55 | Analytics Measures | `Death` | Stock Measures | Estoque | — |  | `Stock` |
| 56 | Analytics Measures | `comsuption / donation` | Stock Measures | Estoque | — |  | `Stock` |
| 57 | Analytics Measures | `Weaning Exit` | Stock Measures | Estoque | — |  | `Stock` |
| 58 | Analytics Measures | `Change Category exit` | Stock Measures | Estoque | — |  | `Stock` |
| 59 | Analytics Measures | `Weaning Entry` | Stock Measures | Estoque | — |  | `Stock` |
| 60 | Analytics Measures | `Invoicing Accumulated` | IN - General Sales Measures | Vendas (geral) | — |  | `Invoicing` |
| 61 | Analytics Measures | `Forecast Accumulated` | IN - General Sales Measures | Vendas (geral) | — |  | `Incoicing - Forecast` |
| 62 | Analytics Measures | `Amount Head Saled Accumulated` | IN - General Sales Measures | Vendas (geral) | — |  | `Amount Saled` |
| 63 | Analytics Measures | `Amount Head Saled - Forecast Accumulated` | IN - General Sales Measures | Vendas (geral) | — |  | `Amount Saled - Forecast` |
| 64 | Analytics Measures | `Count Mean Month` | Dead Measures | Aux. tempo | — |  | `Count of Selected Years` |
| 65 | Analytics Measures | `Count Mean Month Accumulated` | Head Outlay | Aux. tempo | I |  |  |
| 66 | Analytics Measures | `Rendimento Carcaça` | IN - Medidas Abate | Vendas abate | V | Duplicata de PG2, Venda Abate |  |
| 67 | Analytics Measures | `Peso em @ Abate` | IN - Medidas Abate | Vendas abate | — |  |  |
| 68 | Analytics Measures | `AVG Price @` | IN - General Sales Measures | Vendas (geral) | — |  | `AVG Price @ Dead Sale`, `AVG Price @ Sale Venda em Pe` |
| 69 | Analytics Measures | `Peso em @ Em Pe` | IN - Medidas Venda Em Pe | Vendas em pé | — |  |  |
| 70 | Analytics Measures | `Peso em @` | IN - General Sales Measures | Vendas (geral) | V | Duplicata de PG2 |  |
| 71 | Analytics Measures | `Outlay` | Finance Measures | Financeiro | V | Duplicata de PG1, Financeiro |  |
| 72 | Analytics Measures | `% Atingido Faturamento` | IN - General Sales Measures | Vendas (geral) | — |  | `Incoicing - Forecast`, `Invoicing` |
| 73 | Analytics Measures | `Rebanho Median Month` |  | Vazia | — |  |  |
| 74 | Analytics Measures | `UA Median Month` | Purchase Measures | Rebanho/UA/lotação | V | Duplicata de PG2, Movimentação do Gado | `Mean Month Accumulated - UA` |
| 75 | Analytics Measures | `Mean Month Accumulated - UA` | Head Outlay | Rebanho/UA/lotação | I |  | `Count of Selected Month`, `Count of Selected Years`, `Mean Month - UA` |
| 76 | Analytics Measures | `Mean Month - UA` | Head Outlay | Rebanho/UA/lotação | I |  |  |
| 77 | Analytics Measures | `Costing` | Head Outlay | Financeiro | I |  |  |
| 78 | Analytics Measures | `Costing Accumulated` | Head Outlay | Financeiro/cab | I |  | `Costing` |
| 79 | Analytics Measures | `Costing head Accumulated` | Head Outlay | Financeiro/cab | V | Duplicata de PG1, Financeiro | `Costing Accumulated`, `Count of Selected Month`, `Mean Month Accumulated - Aux (Desembolso)` |
| 80 | Analytics Measures | `Costing Head accumulated - forecast` | Head Outlay | Financeiro/cab | V | Duplicata de PG1, Financeiro | `Costing Accumulated - Forecast`, `Count of Selected Month`, `Mean Month Accumulated - Aux (Desembolso) - Forecast` |
| 81 | Analytics Measures | `AVG Price @ (Em Pe + Abate)` | IN - General Sales Measures | Vendas (geral) | V | Duplicata de PG1, Financeiro |  |
| 82 | Analytics Measures | `AVG Price @ Dead Sale - Forecast` | IN - Medidas Abate | Vendas abate | V | Venda Abate |  |
| 83 | Analytics Measures | `AVG Price @ Sale Venda em Pe - Forecast` | IN - Medidas Venda Em Pe | Vendas em pé | V | Venda em Pé |  |
| 84 | Analytics Measures | `Birth Quantity - Forecast` | Birth Measures | Nascimentos | V | Nascimentos, PG3 |  |
| 85 | Analytics Measures | `% Birth x Forecast` | Birth Measures | Nascimentos | V | Duplicata de PG2, Movimentação do Gado, Nascimentos | `Birth Quantity`, `Birth Quantity - Forecast` |
| 86 | Analytics Measures | `Birth Quantity Accumulated` | Birth Measures | Nascimentos | V | Nascimentos, PG3 | `Birth Quantity`, `Count of Selected Years` |
| 87 | Analytics Measures | `% Mortality` | Dead Measures | Mortes | V | Mortes, PG3 | `Birth Quantity Accumulated`, `Dead Quantity Accumulated` |
| 88 | Analytics Measures | `% Amount Saled` | IN - General Sales Measures | Vendas (geral) | V | Duplicata de PG2, Movimentação do Gado | `Amount Saled`, `Amount Saled - Forecast` |
| 89 | Analytics Measures | `Purchased Quantity - Forecast` | Purchase Measures | Compras | V | Compras |  |
| 90 | Analytics Measures | `% Purchased Quantity` | Purchase Measures | Compras | V | Duplicata de PG2, Movimentação do Gado | `Purchased Quantity`, `Purchased Quantity - Forecast` |
| 91 | Analytics Measures | `Dead Quantity - Forecast` | Dead Measures | Mortes | V | Mortes |  |
| 92 | Analytics Measures | `AVG Price KG Sale Venda em Pe` | IN - Medidas Venda Em Pe | Vendas em pé | V | Duplicata de PG2, Venda em Pé |  |
| 93 | Analytics Measures | `MAX AVG Price @ Forecast` | IN - General Sales Measures | UI (máx. gauge) | V | Duplicata de PG1, Financeiro | `AVG Price @ (Em Pe + Abate) - Forecast` |
| 94 | Analytics Measures | `AVG Price @ (Em Pe + Abate) - Forecast` | IN - General Sales Measures | Vendas (geral) | V | Duplicata de PG1, Financeiro |  |
| 95 | Analytics Measures | `Lotation` | Stock Measures | Rebanho/UA/lotação | — |  | `Mean Month Accumulated - UA` |
| 96 | Analytics Measures | `Lotation - Forecast` | Stock Measures | Rebanho/UA/lotação | — |  | `Lotation` |
| 97 | Analytics Measures | `Lotation - Forecast - MAX` | Stock Measures | Rebanho/UA/lotação | — |  | `Lotation - Forecast` |
| 98 | Analytics Measures | `Birth Quantity - Forecast - Const` | Birth Measures | Nascimentos | I |  | `Birth Quantity - Forecast` |
| 99 | Analytics Measures | `% Birth x Forecast (Year)` | Birth Measures | Nascimentos | V | PG3 | `Birth Quantity`, `Birth Quantity - Forecast - Const` |
| 100 | pecuarioVendaEmPe | `Medida` |  | Vazia | — |  |  |
| 101 | fMovGado | `Medida 2` |  | Vazia | — |  |  |
| 102 | Analytics Measures | `Count of Selected Month` | Dead Measures | Aux. tempo | I |  |  |
| 103 | Analytics Measures | `Invoicing Abate` | IN - Medidas Abate | Vendas abate | — |  |  |
| 104 | fMetasCompras | `VALORCALC` |  | Compras (quebrada) | — |  |  |
| 105 | Analytics Measures | `Mean Month Accumulated - Aux (Desembolso)` | Head Outlay | Rebanho/UA/lotação | I |  | `Count of Selected Years`, `Mean Month` |
| 106 | Analytics Measures | `Selected Farm` |  | UI (cabeçalho) | V | Capa, Compras, Duplicata de PG1, Duplicata de PG2, Financeiro, Mortes, Movimentação do Gado, Nascimentos, PG3, Previsto x Realizado, Transferências, Venda Abate, Venda em Pé |  |
| 107 | Analytics Measures | `Mean Month Accumulated - Aux (Desembolso) - Forecast` | Head Outlay | Rebanho/UA/lotação | I |  | `Count of Selected Years`, `Mean Month - forecast` |
| 108 | Analytics Measures | `Outlay Forecast` | Finance Measures | Financeiro | I |  |  |
| 109 | Analytics Measures | `Expenses Accumulated - Forecast` | Head Outlay | Financeiro/cab | I |  | `Outlay Forecast` |
| 110 | Analytics Measures | `Costing Forecast` | Head Outlay | Financeiro | I |  |  |
| 111 | Analytics Measures | `Costing Accumulated - Forecast` | Head Outlay | Financeiro/cab | I |  | `Costing Forecast` |
| 112 | Analytics Measures | `Birth Quantity Accumulated - Forecast` | Birth Measures | Nascimentos | V | Nascimentos, PG3 | `Birth Quantity - Forecast`, `Count of Selected Years` |
| 113 | Analytics Measures | `% Atingido Outlay` | Finance Measures | Financeiro | — |  | `Outlay`, `Outlay Forecast` |
| 114 | Analytics Measures | `Color Desemb Cab Mês` |  | UI (cor) | V | Duplicata de PG1, Financeiro | `head outlat accumulated - forecast`, `head outlay accumulated` |
| 115 | Analytics Measures | `Color Costing Cab Mês` |  | UI (cor) | V | Duplicata de PG1, Financeiro | `Costing Head accumulated - forecast`, `Costing head Accumulated` |
| 116 | Analytics Measures | `Color @ Venda Geral` |  | UI (cor) | V | Duplicata de PG1, Financeiro | `AVG Price @ (Em Pe + Abate)`, `AVG Price @ (Em Pe + Abate) - Forecast` |
| 117 | Analytics Measures | `IN Venda Geral` |  | UI (indicador) | — |  | `Incoicing - Forecast`, `Invoicing` |
| 118 | Analytics Measures | `IN Costing Cab Mês` |  | UI (indicador) | — |  | `Costing Head accumulated - forecast`, `Costing head Accumulated` |
| 119 | Analytics Measures | `IN Desembolso Cab Mês` |  | UI (indicador) | — |  | `head outlat accumulated - forecast`, `head outlay accumulated` |
| 120 | Analytics Measures | `IN Mean Month` |  | UI (indicador) | — |  | `Mean Month`, `Mean Month - forecast` |
| 121 | Analytics Measures | `Sistema Produção` |  | UI (rótulo) | — |  |  |
| 122 | Analytics Measures | `Revenues Forecast` | Finance Measures | Financeiro | V | Duplicata de PG1, Financeiro |  |
| 123 | Analytics Measures | `Expenses Forecast` | Finance Measures | Financeiro | V | Duplicata de PG1, Financeiro |  |
| 124 | Analytics Measures | `Total Paid - Forecast` | Purchase Measures | Compras | V | Compras |  |
| 125 | Analytics Measures | `Purchased Quantity FEMALE` | Purchase Measures | Compras | — |  | `Purchased Quantity` |
| 126 | Analytics Measures | `Purchased Quantity MALE` | Purchase Measures | Compras | — |  | `Purchased Quantity` |
| 127 | Analytics Measures | `@ AVG Price Purchase` | Purchase Measures | Compras | V | Compras |  |
| 128 | Analytics Measures | `% Purchased Value` | Purchase Measures | Compras | — |  | `Total Paid`, `Total Paid - Forecast` |
| 129 | Analytics Measures | `Purchased Quantity - Forecast - TESTE` | Purchase Measures | Compras | — |  |  |
| 130 | Analytics Measures | `Ágio` | Purchase Measures | Compras | V | Compras | `@ AVG Price Purchase`, `AVG Price @ (Em Pe + Abate)` |
| 131 | Analytics Measures | `Mean Month Ha` | Head Outlay | Rebanho/UA/lotação | V | Duplicata de PG2, Movimentação do Gado | `Count of Selected Month`, `Mean Month` |
| 132 | Analytics Measures | `UA Median Ha` | Purchase Measures | Rebanho/UA/lotação | V | Duplicata de PG2, Movimentação do Gado | `Count of Selected Month`, `UA Median Month` |
| 133 | Analytics Measures | `% mORTALITY ( MEAN MONTH)` | Dead Measures | Mortes | V | Duplicata de PG2, Mortes, Movimentação do Gado | `Dead Quantity`, `Mean Month` |
| 134 | Analytics Measures | `% Variação` | Finance Measures | Prev x Real DRE | I |  | `Meta Último Mês Selecionado`, `Valor Último Mês Selecionado` |
| 135 | Analytics Measures | `Value Accumulated` | Finance Measures | Prev x Real DRE | V | Previsto x Realizado |  |
| 136 | Analytics Measures | `Meta Accumulated` | Finance Measures | Prev x Real DRE | V | Previsto x Realizado |  |
| 137 | Analytics Measures | `% Variação Acc Graph` | Finance Measures | Prev x Real DRE (UI) | V | Previsto x Realizado | `%% Variação Acc` |
| 138 | Analytics Measures | `% Variação Graph` | Finance Measures | Prev x Real DRE (UI) | V | Previsto x Realizado | `% Variação` |
| 139 | Analytics Measures | `%% Variação Acc` | Finance Measures | Prev x Real DRE | I |  | `Meta Accumulated`, `Value Accumulated` |
| 140 | Analytics Measures | `Icon` | Finance Measures | Prev x Real DRE (UI) | V | Previsto x Realizado | `% Variação` |
| 141 | Analytics Measures | `RL Mensal` | Finance Measures | UI (rótulo) | V | Previsto x Realizado |  |
| 142 | Analytics Measures | `RL Acumulado` | Finance Measures | UI (rótulo) | V | Previsto x Realizado |  |
| 143 | Analytics Measures | `Icon Acc` | Finance Measures | Prev x Real DRE (UI) | V | Previsto x Realizado | `%% Variação Acc` |
| 144 | planejadoXRealizado | `Valor Último Mês Selecionado` |  | Prev x Real DRE | V | Previsto x Realizado |  |
| 145 | planejadoXRealizado | `Meta Último Mês Selecionado` |  | Prev x Real DRE | V | Previsto x Realizado |  |
| 146 | Analytics Measures | `All Revenues` | Finance Measures | Financeiro | V | Duplicata de PG1 |  |
| 147 | Analytics Measures | `Amount Saled (Abate)` | IN - Medidas Abate | Vendas abate | V | Venda Abate |  |
| 148 | Analytics Measures | `Amount Saled - Forecast (Abate)` | IN - Medidas Abate | Vendas abate | V | Venda Abate |  |
| 149 | Analytics Measures | `Invoicing (Abate)` | IN - Medidas Abate | Vendas abate | V | Venda Abate |  |
| 150 | Analytics Measures | `Incoicing - Forecast (Abate)` | IN - Medidas Abate | Vendas abate | V | Venda Abate |  |
| 151 | Analytics Measures | `IN - Name (Abate)` |  | UI (rótulo) | — |  |  |
| 152 | Analytics Measures | `IN - AVG Live Weight` | IN - Medidas Abate | Vendas abate | V | Venda Abate |  |
| 153 | Analytics Measures | `IN - Peso Médio Vivo` | IN - Data Labels | UI (rótulo) | V | Compras, Venda Abate, Venda em Pé |  |
| 154 | Analytics Measures | `IN - Valor da @` | IN - Data Labels | UI (rótulo) | V | Venda Abate, Venda em Pé |  |
| 155 | Analytics Measures | `IN - Rendimento de Carcaça` | IN - Data Labels | UI (rótulo) | V | Venda Abate |  |
| 156 | Analytics Measures | `IN - Fêmea` | IN - Data Labels | UI (rótulo) | V | Compras, Nascimentos, Transferências, Venda Abate, Venda em Pé |  |
| 157 | Analytics Measures | `IN - Macho` | IN - Data Labels | UI (rótulo) | V | Compras, Nascimentos, Transferências, Venda Abate, Venda em Pé |  |
| 158 | Analytics Measures | `IN - Cabeças` | IN - Data Labels | UI (rótulo) | V | Mortes |  |
| 159 | Analytics Measures | `IN - Geral` | IN - Data Labels | UI (rótulo) | V | Compras, Mortes, Nascimentos, Venda Abate, Venda em Pé |  |
| 160 | Analytics Measures | `IN - Faturamento` | IN - Data Labels | UI (rótulo) | V | Venda Abate, Venda em Pé |  |
| 161 | Analytics Measures | `Invoicing (Em Pe )` | IN - Medidas Venda Em Pe | Vendas em pé | V | Venda em Pé |  |
| 162 | Analytics Measures | `Incoicing - Forecast (Em Pe)` | IN - Medidas Venda Em Pe | Vendas em pé | V | Venda em Pé |  |
| 163 | Analytics Measures | `Amount Saled (Em pe)` | IN - Medidas Venda Em Pe | Vendas em pé | V | Venda em Pé |  |
| 164 | Analytics Measures | `Amount Saled - Forecast (Em Pe)` | IN - Medidas Venda Em Pe | Vendas em pé | V | Venda em Pé |  |
| 165 | Analytics Measures | `IN - Preço do KG` | IN - Data Labels | UI (rótulo) | V | Compras, Venda em Pé |  |
| 166 | Analytics Measures | `IN - AVG Live Weight (Em Pe)` | IN - Medidas Venda Em Pe | Vendas em pé | V | Venda em Pé |  |
| 167 | Analytics Measures | `IN AVG - Peso Médio de Compra` | Purchase Measures | Compras | V | Compras |  |
| 168 | Analytics Measures | `IN - Meta Valor KG` | IN - Data Labels | UI (rótulo) | — |  |  |
| 169 | Analytics Measures | `IN AVG - Peso Médio de Compra (Forecast)` | Purchase Measures | Compras | V | Compras |  |
| 170 | Analytics Measures | `AVG Purchase Price KG` | Purchase Measures | Compras | V | Compras |  |
| 171 | Analytics Measures | `AVG Purchase Price KG (Forecast)` | Purchase Measures | Compras | V | Compras |  |
| 172 | Analytics Measures | `IN - Ágio` | IN - Data Labels | UI (rótulo) | V | Compras |  |
| 173 | Analytics Measures | `IN - Valor da @ Compra` | IN - Data Labels | UI (rótulo) | V | Compras |  |
| 174 | Analytics Measures | `IN - Bezerro` | IN - Data Labels | UI (rótulo) | V | Mortes |  |
| 175 | Analytics Measures | `IN - Jovens` | IN - Data Labels | UI (rótulo) | V | Mortes |  |
| 176 | Analytics Measures | `IN - Adultos` | IN - Data Labels | UI (rótulo) | V | Mortes |  |
| 177 | Analytics Measures | `IN - Meta` | IN - Data Labels | UI (rótulo) | V | Mortes, Venda Abate |  |
| 178 | Analytics Measures | `IN - Mortalidade sobre Rebanho Médio` | IN - Data Labels | UI (rótulo) | V | Mortes |  |
| 179 | Analytics Measures | `IN - Mortalidade sobre Nascimento` | IN - Data Labels | UI (rótulo) | V | Mortes |  |
| 180 | Analytics Measures | `IN - % Male Birth` | Birth Measures | Nascimentos | V | Nascimentos | `Birth Quantity` |
| 181 | Analytics Measures | `IN - % Female Birth` | Birth Measures | Nascimentos | V | Nascimentos | `Birth Quantity` |
| 182 | Analytics Measures | `IN - Nascimentos` | IN - Data Labels | UI (rótulo) | V | Nascimentos |  |
| 183 | Analytics Measures | `IN - Relação a Meta` | IN - Data Labels | UI (rótulo) | — |  |  |
| 184 | Analytics Measures | `IN - Vendas (Geral)` | IN - Data Labels | UI (rótulo) | — |  |  |
| 185 | Analytics Measures | `IN - Compras (Label)` | IN - Data Labels | UI (rótulo) | — |  |  |
| 186 | Analytics Measures | `IN - Nascimentos (Label)` | IN - Data Labels | UI (rótulo) | V | Movimentação do Gado |  |
| 187 | Analytics Measures | `IN - Mortes` | IN - Data Labels | UI (rótulo) | V | Movimentação do Gado |  |
| 188 | Analytics Measures | `IN - Compra` | IN - Data Labels | UI (rótulo) | — |  |  |
| 189 | Analytics Measures | `IN - AVG Live Weight (Forecast)` | IN - Medidas Abate | Vendas abate | V | Venda Abate |  |
| 190 | Analytics Measures | `IN - Planejado` | IN - Data Labels | UI (rótulo) | V | Compras, Nascimentos, Transferências, Venda Abate, Venda em Pé |  |
| 191 | Analytics Measures | `IN - Realizado` | IN - Data Labels | UI (rótulo) | V | Compras, Nascimentos, Transferências, Venda Abate, Venda em Pé |  |
| 192 | Analytics Measures | `IN - Rebanho Médio` | IN - Data Labels | UI (rótulo) | V | Movimentação do Gado |  |
| 193 | Analytics Measures | `IN - Rebanho Médio Cab` | IN - Data Labels | UI (rótulo) | V | Movimentação do Gado |  |
| 194 | Analytics Measures | `IN - Rebanho Médio UA` | IN - Data Labels | UI (rótulo) | V | Movimentação do Gado |  |
| 195 | Analytics Measures | `IN - Lotação Cab` | IN - Data Labels | UI (rótulo) | V | Movimentação do Gado |  |
| 196 | Analytics Measures | `IN - Lotação UA` | IN - Data Labels | UI (rótulo) | V | Movimentação do Gado |  |
| 197 | Analytics Measures | `IN - % Meta` | IN - Data Labels | UI (rótulo) | V | Movimentação do Gado |  |
| 198 | Analytics Measures | `IN - Indice de Mortalidade` | IN - Data Labels | UI (rótulo) | V | Movimentação do Gado |  |
| 199 | Analytics Measures | `IN - Mortes (2)` | IN - Data Labels | UI (rótulo) | V | Movimentação do Gado |  |
| 200 | Analytics Measures | `IN - Nascimentos (Label - 2)` | IN - Data Labels | UI (rótulo) | V | Movimentação do Gado, Nascimentos |  |
| 201 | Analytics Measures | `IN - Compras (Label 2 )` | IN - Data Labels | UI (rótulo) | V | Movimentação do Gado |  |
| 202 | Analytics Measures | `IN - Vendas (Label)` | IN - Data Labels | UI (rótulo) | V | Movimentação do Gado |  |
| 203 | Analytics Measures | `IN - COMPRA X VENDA` | IN - Data Labels | UI (rótulo) | V | Movimentação do Gado |  |
| 204 | Analytics Measures | `IN - Data Análise` | IN - Data Labels | UI (rótulo) | V | Capa |  |
| 205 | Analytics Measures | `IN - Separador de` | IN - Data Labels | UI (rótulo) | — |  |  |
| 206 | Analytics Measures | `IN - Periodo Capa` | IN - Data Labels | UI (rótulo) | V | Capa |  |
| 207 | Analytics Measures | `IN - Site Terra` | IN - Data Labels | UI (rótulo) | V | Capa |  |
| 208 | Analytics Measures | `IN - Periodo Envio` | IN - Data Labels | UI (rótulo) | V | Capa |  |
| 209 | Analytics Measures | `IN - AVG Live Weight (Em Pe - Forecast)` | IN - Medidas Venda Em Pe | Vendas em pé | V | Venda em Pé |  |
| 210 | Analytics Measures | `AVG Price KG Sale Venda em Pe - Forecast` | IN - Medidas Venda Em Pe | Vendas em pé | V | Venda em Pé |  |
| 211 | Analytics Measures | `IN - Faturamento Planejado` | IN - Data Labels | UI (rótulo) | V | Venda em Pé |  |
| 212 | Analytics Measures | `IN - Inv Realizado` | IN - Data Labels | UI (rótulo) | V | Compras |  |
| 213 | Analytics Measures | `IN - Inv Planejado` | IN - Data Labels | UI (rótulo) | V | Compras |  |
| 214 | Analytics Measures | `IN - Rendimento Carcaça (Forecast)` | IN - Medidas Abate | Vendas abate | V | Venda Abate |  |
| 215 | Analytics Measures | `IN - Cbs Vendidas` | IN - Data Labels | UI (rótulo) | V | Venda Abate, Venda em Pé |  |
| 216 | Analytics Measures | `IN - Cbs Compradas` | IN - Data Labels | UI (rótulo) | V | Compras |  |
| 217 | Analytics Measures | `Invoicing Accumulated (Abate)` | IN - Medidas Abate | Vendas abate | V | Venda Abate |  |
| 218 | Analytics Measures | `Amount Saled Accumulated (Em Pe)` | IN - Medidas Venda Em Pe | Vendas em pé | V | Venda em Pé |  |
| 219 | Analytics Measures | `Purchase Quantity Accumulated` | Purchase Measures | Compras | V | Compras |  |
| 220 | Analytics Measures | `IN - Incoming Transfer` |  | Transferências | V | Transferências |  |
| 221 | Analytics Measures | `IN - Outgoing Transfer` |  | Transferências | V | Transferências |  |
| 222 | Analytics Measures | `IN - Incoming Transfer - Forecast` |  | Transferências | — |  |  |
| 223 | Analytics Measures | `IN - Outgoing Transfer - Forecast` |  | Transferências | — |  |  |
| 224 | Analytics Measures | `IN - Entrada` | IN - Data Labels | UI (rótulo) | V | Transferências |  |
| 225 | Analytics Measures | `IN - Saida` | IN - Data Labels | UI (rótulo) | V | Transferências |  |
| 226 | Analytics Measures | `IN - Quantidade` | IN - Data Labels | UI (rótulo) | V | Transferências |  |
| 227 | Analytics Measures | `Medida 3` | IN - Data Labels | Vazia | — |  |  |
| 228 | Analytics Measures | `IN Peso Médio` | IN - Data Labels | UI (rótulo) | V | Transferências |  |
| 229 | Analytics Measures | `IN Valor@` | IN - Data Labels | UI (rótulo) | V | Transferências |  |
| 230 | Analytics Measures | `IN QTD Transfer Forecast` | Transfer Measures | Transferências | V | Transferências |  |
| 231 | Analytics Measures | `IN QTD Transfer` | Transfer Measures | Transferências | V | Transferências |  |
| 232 | Analytics Measures | `IN - AVG Price @ Transfer` | Transfer Measures | Transferências | V | Transferências |  |
| 233 | Analytics Measures | `IN - AVG Price @ Transfer Forecas` | Transfer Measures | Transferências | V | Transferências |  |
| 234 | Analytics Measures | `IN - AVG Weight Transfer` | Transfer Measures | Transferências | V | Transferências |  |
| 235 | Analytics Measures | `IN - AVG Weight Transfer Forecast` | Transfer Measures | Transferências | V | Transferências |  |
| 236 | Analytics Measures | `IN - TRANSFERÊNCIAS` | IN - Data Labels | UI (rótulo) | V | Transferências |  |
| 237 | Analytics Measures | `head outlat accumulated - forecast graph` | Head Outlay | UI (máx. gauge) | V | Financeiro | `head outlat accumulated - forecast` |

Totais: 151 usadas diretamente, 21 só indiretamente, 65 sem uso.


---

## Apêndice B — Texto DAX integral das medidas de negócio

(Exclui as 56 medidas da pasta `IN - Data Labels`, que só retornam texto fixo — ver §5.14.)

### Analytics Measures[Purchased Quantity]  — pasta: Purchase Measures

```dax
CALCULATE(SUM(pecuarioCompras[qtd]))
```

### Analytics Measures[Total Paid]  — pasta: Purchase Measures

```dax
CALCULATE(SUM(pecuarioCompras[VALOR TOTAL]))+0
```

### Analytics Measures[Purchase Quantity]  — pasta: Purchase Measures

```dax
COUNTROWS(pecuarioCompras)
```

### Analytics Measures[Dead KG Amount]  — pasta: Dead Measures

```dax
CALCULATE(SUM(pecuarioMortes[peso_total]))
```

### Analytics Measures[Dead Quantity]  — pasta: Dead Measures

```dax
SUM(pecuarioMortes[qtd])
```

### Analytics Measures[Birth Quantity]  — pasta: Birth Measures

```dax
CALCULATE(SUM(pecuarioNascimento[qtd]))+0
```

### Analytics Measures[Average Birth Weight]  — pasta: Birth Measures

```dax
CALCULATE(SUM(pecuarioNascimento[peso_nasc])) /  CALCULATE(SUM(pecuarioNascimento[qtd])) 
```

### Analytics Measures[Expenses]  — pasta: Finance Measures

```dax
CALCULATE(
                     SUM('financeiroDre'[valor]),
                     'financeiroDre'[operaÇÃo]="D"--,
                    -- pecuarioRebanhoMedioMensal[amount] > 0
                     ) * -1
```

### Analytics Measures[Revenues]  — pasta: Finance Measures

```dax
CALCULATE(SUM('financeiroDre'[valor]),'financeiroDre'[operaÇÃo]="C",financeiroDre[tipo_custeio-CAT] IN {"Receita Pec", "Receita Agr"})
```

### Analytics Measures[Balance]  — pasta: Finance Measures

```dax
[All Revenues] + [Expenses]
```

### Analytics Measures[% Resultado]  — pasta: Finance Measures

```dax
DIVIDE([Balance],[Expenses]*-1)
```

### Analytics Measures[Finance Indicator]  — pasta: Finance Measures

```dax
IF([% Resultado] > 0, 1, 
   IF([% Resultado] < 0, -1, 0))
```

### Analytics Measures[Amount Saled]  — pasta: IN - General Sales Measures

```dax
SUM(pecuarioVendaEmPe[qtd])+SUM(pecuarioVendaAbate[qtd])
```

### Analytics Measures[Invoicing]  — pasta: IN - General Sales Measures

```dax
SUM(pecuarioVendaEmPe[Faturamento])+SUM(pecuarioVendaAbate[Faturamento])
```

### Analytics Measures[AVG Price @ Dead Sale]  — pasta: IN - Medidas Abate

```dax
CALCULATE(SUM(pecuarioVendaAbate[Faturamento]) / (SUM(pecuarioVendaAbate[Total de @])))
```

### Analytics Measures[AVG Price @ Sale Venda em Pe]  — pasta: IN - Medidas Venda Em Pe

```dax
CALCULATE(SUM(pecuarioVendaEmPe[Faturamento]) / SUM(pecuarioVendaEmPe[Total de @]))+0
```

### Analytics Measures[AVG Ticket Dead Sale]  — pasta: IN - Medidas Abate

```dax
SUM(pecuarioVendaAbate[Faturamento]) / SUM(pecuarioVendaAbate[qtd])
```

### Analytics Measures[AVG Ticket Sale]  — pasta: IN - Medidas Venda Em Pe

```dax
SUM(pecuarioVendaEmPe[Faturamento]) / SUM(pecuarioVendaEmPe[qtd])
```

### Analytics Measures[Expenses Graph]  — pasta: Finance Measures

```dax
CALCULATE(SUM('financeiroDre'[valor]),'financeiroDre'[operaÇÃo]="D") 
```

### Analytics Measures[Accumulated Death]  — pasta: Dead Measures

```dax
 VAR calc1 = 
   CALCULATE(
        [Dead Quantity],
        FILTER(
            ALL(dCalendar),  // Remove todos os filtros da tabela de calendário
            dCalendar[Data] <= MAX(dCalendar[Data]) &&
            YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  // Garante que o cálculo seja feito apenas dentro do ano corrente
        )
    )
VAR calc2 = 
    CALCULATE(
        [Dead Quantity],
        FILTER(
            ALL(dCalendar),  // Remove todos os filtros de data
            dCalendar[Data] <= MAX(dCalendar[Data])  // Inclui todas as datas até a data máxima no contexto
        )
    )
RETURN IF([Count of Selected Years] = 1,
            calc1,calc2)
```

### Analytics Measures[Const Death]  — pasta: Dead Measures

```dax
    CALCULATE(
        [Dead Quantity],
            ALLEXCEPT(dCalendar,dCalendar[Ano])

    )
```

### Analytics Measures[Count of Selected Years]  — pasta: Dead Measures

```dax
    CALCULATE(
        DISTINCTCOUNT(dCalendar[Ano]),
        ALLSELECTED(dCalendar)
    )
```

### Analytics Measures[% Death Accumulated]  — pasta: Dead Measures

```dax
DIVIDE([Accumulated Death],[Const Death])
```

### Analytics Measures[head outlay mOm]  — pasta: Head Outlay

```dax
(CALCULATE(DIVIDE([Outlay],[Mean Month])) * -1) / [Count of Selected Month]
```

### Analytics Measures[head outlay accumulated]  — pasta: Head Outlay

```dax
(DIVIDE([Expenses Accumulated], [Mean Month Accumulated - Aux (Desembolso)], 0) *-1) / [Count of Selected Month] + 0
```

### Analytics Measures[Expenses Accumulated]  — pasta: Head Outlay

```dax
VAR UltimoDiaDoMesContexto = MAX('dCalendar'[Data]) 
VAR DataLimite = EOMONTH(UltimoDiaDoMesContexto, 0)

RETURN
CALCULATE(
    [Outlay],
    FILTER(
        ALLSELECTED('dCalendar'),
        'dCalendar'[Data] <= DataLimite
    )
)
```

### Analytics Measures[Mean Month]  — pasta: Head Outlay

```dax
CALCULATE( SUM(pecuarioRebanhoMedioMensal[qtd_cab]) / [Count of Selected Month])
```

### Analytics Measures[Mean Month Accumulated]  — pasta: Head Outlay

```dax
 VAR calc1 = 
   CALCULATE(
        [Mean Month],
        FILTER(
            ALLSELECTED(dCalendar), 
            dCalendar[Data] <= MAX(dCalendar[Data]) &&
            YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  
        )
    )
VAR calc2 = 
    CALCULATE(
        [Mean Month],
        FILTER(
            ALLSELECTED(dCalendar),  
            dCalendar[Data] <= MAX(dCalendar[Data])  
        )
    )
RETURN IF([Count of Selected Years] = 1,
            calc1,calc2) / [Count of Selected Month]
```

### Analytics Measures[head outlay mOm (forecast)]  — pasta: Head Outlay

```dax
(CALCULATE(DIVIDE([Outlay Forecast],[Mean Month - forecast])) * -1) / [Count of Selected Month]
```

### Analytics Measures[Dead Quantity forecast]  — pasta: Dead Measures

```dax
CALCULATE(SUM(fMetasMortes[qtd]),USERELATIONSHIP(dCalendar[Data],fMetasMortes[DATA]))
```

### Analytics Measures[% Forecast Indicator]  — pasta: Dead Measures

```dax
DIVIDE([Dead Quantity forecast],SUM(pecuarioRebanhoMedioMensal[forecast]))
```

### Analytics Measures[% Realized Indicator]  — pasta: Dead Measures

```dax
DIVIDE([Dead Quantity],SUM(pecuarioRebanhoMedioMensal[qtd_cab]))
```

### Analytics Measures[Dead Quantity Accumulated]  — pasta: Dead Measures

```dax
    CALCULATE(
        [Dead Quantity],
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )

            
```

### Analytics Measures[% Realized Indicator Accumulated]  — pasta: Dead Measures

```dax
DIVIDE([Dead Quantity Accumulated], ([Mean Month Accumulated]/[Count Mean Month Accumulated]), 0) 
```

### Analytics Measures[Dead Quantity Accumulated - Forecast]  — pasta: Dead Measures

```dax
    CALCULATE(
        [Dead Quantity forecast],
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )
```

### Analytics Measures[Mean Month Accumulated - Forecast]  — pasta: Head Outlay

```dax
    CALCULATE(
        SUM(pecuarioRebanhoMedioMensal[Forecast]),
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        ),pecuarioRebanhoMedioMensal[Forecast] <> BLANK()
    )
```

### Analytics Measures[% Forecast Indicator Accumulated]  — pasta: Dead Measures

```dax
CALCULATE(DIVIDE([Dead Quantity Accumulated - Forecast], ([Mean Month Accumulated - Forecast]/[Count Mean Month Accumulated]), 0) )
```

### Analytics Measures[Total de @]  — pasta: IN - General Sales Measures

```dax
[Arroba Value] * [Amount Saled]
```

### Analytics Measures[Arroba Value]  — pasta: IN - General Sales Measures

```dax
--SUM(pecuarioVendaAbate[ArrobaAVG]) + SUM(pecuarioVendaEmPe[arrobaAvg])
```

### Analytics Measures[Amount Saled - Forecast]  — pasta: IN - General Sales Measures

```dax
VAR calc1 = CALCULATE(SUM(fMetasAbate[qtd]))

VAR calc2 = CALCULATE(SUM(fMetasEmPe[qtd]))

RETURN calc1+calc2
```

### Analytics Measures[Incoicing - Forecast]  — pasta: IN - General Sales Measures

```dax
VAR calc1 = CALCULATE(SUM(fMetasAbate[faturamento]))

VAR calc2 = CALCULATE(SUM(fMetasEmPe[faturamento]))

RETURN calc1+calc2
```

### Analytics Measures[% Death x Death Forecast]  — pasta: Dead Measures

```dax
DIVIDE([Dead Quantity],[Dead Quantity forecast])
```

### Analytics Measures[Dead Quantity (Teens)]  — pasta: Dead Measures

```dax
CALCULATE(SUM(pecuarioMortes[qtd]),pecuarioMortes[grupo_categoria] = "JOVENS")
```

### Analytics Measures[Dead Quantity (Adults)]  — pasta: Dead Measures

```dax
CALCULATE(SUM(pecuarioMortes[qtd]),pecuarioMortes[grupo_categoria] = "ADULTOS")
```

### Analytics Measures[Dead Quantity (Calves)]  — pasta: Dead Measures

```dax
CALCULATE(SUM(pecuarioMortes[qtd]),pecuarioMortes[grupo_categoria] = "BEZERROS")
```

### Analytics Measures[head outlat accumulated - forecast]  — pasta: Head Outlay

```dax
(DIVIDE([Expenses Accumulated - Forecast], [Mean Month Accumulated - Aux (Desembolso) - Forecast], 0) *-1) / [Count of Selected Month] + 0
```

### Analytics Measures[Mean Month - forecast]  — pasta: Head Outlay

```dax
CALCULATE(
        SUM(fMetasRebanhoMedio[qtd_cab]) / [Count of Selected Month],
        USERELATIONSHIP(dCalendar[Data],fMetasRebanhoMedio[DATA])
        )
```

### Analytics Measures[Stock]  — pasta: Stock Measures

```dax
SUM(fMovGado[QTD C])
```

### Analytics Measures[Stock Accumulated Inicial]  — pasta: Stock Measures

```dax
    CALCULATE(
        [Stock],
        FILTER(
            ALL(dCalendar),
            dCalendar[Data] < EOMONTH(MIN(dCalendar[Data]), -1) + 1
            
        )
    )
```

### Analytics Measures[Stock Accumulated Final]  — pasta: Stock Measures

```dax
CALCULATE(
    [Stock],
    FILTER(
        ALL(dCalendar), -- Remove filtros de dCalendar, permitindo acumular dados retroativos
        dCalendar[Data] <= MAX(dCalendar[Data])
    )
)
```

### Analytics Measures[Buy]  — pasta: Stock Measures

```dax
CALCULATE([Stock],fMovGado[OPERAÇÃO] = "COMPRA")
```

### Analytics Measures[Sell]  — pasta: Stock Measures

```dax
CALCULATE([Stock],fMovGado[OPERAÇÃO] IN {"EMPÉ","ABATE"})
```

### Analytics Measures[Birth]  — pasta: Stock Measures

```dax
CALCULATE([Stock],fMovGado[OPERAÇÃO] = "NASCIMENTO")
```

### Analytics Measures[Change Category entry]  — pasta: Stock Measures

```dax
CALCULATE([Stock],fMovGado[OPERAÇÃO] = "Mud. de Categoria", fMovGado[Type Operation] = "Entrada")
```

### Analytics Measures[Death]  — pasta: Stock Measures

```dax
CALCULATE([Stock],fMovGado[OPERAÇÃO] = "MORTE")
```

### Analytics Measures[comsuption / donation]  — pasta: Stock Measures

```dax
CALCULATE([Stock],fMovGado[OPERAÇÃO] = "Consumo/Doação")
```

### Analytics Measures[Weaning Exit]  — pasta: Stock Measures

```dax
CALCULATE([Stock],fMovGado[OPERAÇÃO] = "DESMAME",fMovGado[Type Operation] = "Saída")
```

### Analytics Measures[Change Category exit]  — pasta: Stock Measures

```dax
CALCULATE([Stock],fMovGado[OPERAÇÃO] = "Mud. de Categoria", fMovGado[Type Operation] = "Saída")
```

### Analytics Measures[Weaning Entry]  — pasta: Stock Measures

```dax
CALCULATE([Stock],fMovGado[OPERAÇÃO] = "Desmame",fMovGado[Type Operation] = "Entrada")
```

### Analytics Measures[Invoicing Accumulated]  — pasta: IN - General Sales Measures

```dax
    CALCULATE(
        [Invoicing],
        FILTER(
            ALL(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )

/* Invoicing Accumulated = 
VAR calc1 =
    CALCULATE(
        SUM(pecuarioVendaAbate[Total Value]),
        FILTER(
            ALL(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )

VAR calc2 =
    CALCULATE(
        SUM(pecuarioVendaEmPe[totalValue]),
        FILTER(
            ALL(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )

RETURN calc1+calc2*/
```

### Analytics Measures[Forecast Accumulated]  — pasta: IN - General Sales Measures

```dax
    CALCULATE(
        [Incoicing - Forecast],
        FILTER(
            ALL(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )
```

### Analytics Measures[Amount Head Saled Accumulated]  — pasta: IN - General Sales Measures

```dax
    CALCULATE(
        [Amount Saled],
        FILTER(
            ALL(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )
```

### Analytics Measures[Amount Head Saled - Forecast Accumulated]  — pasta: IN - General Sales Measures

```dax
    CALCULATE(
        [Amount Saled - Forecast],
        FILTER(
            ALL(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )
```

### Analytics Measures[Count Mean Month]  — pasta: Dead Measures

```dax
 VAR calc1 = 
   CALCULATE(
        COUNTROWS(pecuarioRebanhoMedioMensal),
        FILTER(
            ALL(dCalendar),  // Remove todos os filtros da tabela de calendário
            dCalendar[Data] <= MAX(dCalendar[Data]) &&
            YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  // Garante que o cálculo seja feito apenas dentro do ano corrente
        )
    )
VAR calc2 = 
    CALCULATE(
        COUNTROWS(pecuarioRebanhoMedioMensal),
        FILTER(
            ALL(dCalendar),  // Remove todos os filtros de data
            dCalendar[Data] <= MAX(dCalendar[Data])  // Inclui todas as datas até a data máxima no contexto
        )
    )
RETURN IF([Count of Selected Years] = 1,
            calc1,calc2)
```

### Analytics Measures[Count Mean Month Accumulated]  — pasta: Head Outlay

```dax
   CALCULATE(
        DISTINCTCOUNT(dCalendar[mesano]),
        FILTER(
            ALLSELECTED(dCalendar), 
            dCalendar[Data] <= MAX(dCalendar[Data]) --&&
           -- YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  
        )
    )
/*
 VAR calc1 = 
   CALCULATE(
        DISTINCTCOUNT(dCalendar[mesano]),
        FILTER(
            ALL(dCalendar), 
            dCalendar[Data] <= MAX(dCalendar[Data]) &&
            YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  
        )
    )
VAR calc2 = 
    CALCULATE(
        DISTINCTCOUNT(dCalendar[mesano]),
        FILTER(
            ALL(dCalendar),  
            dCalendar[Data] <= MAX(dCalendar[Data])  
        )
    )
RETURN IF([Count of Selected Years] = 1,
            calc1,calc2)*/
```

### Analytics Measures[Rendimento Carcaça]  — pasta: IN - Medidas Abate

```dax
SUM(pecuarioVendaAbate[pesomorto_total]) / SUM(pecuarioVendaAbate[pesovivo_total])
```

### Analytics Measures[Peso em @ Abate]  — pasta: IN - Medidas Abate

```dax
(SUM(pecuarioVendaAbate[Peso Morto Total]) / 15 ) / SUM(pecuarioVendaAbate[qtd])
```

### Analytics Measures[AVG Price @]  — pasta: IN - General Sales Measures

```dax
[AVG Price @ Dead Sale] + [AVG Price @ Sale Venda em Pe]
```

### Analytics Measures[Peso em @ Em Pe]  — pasta: IN - Medidas Venda Em Pe

```dax
(SUM( pecuarioVendaEmPe[pesovivo_total])/30) / SUM(pecuarioVendaEmPe[qtd])+0
```

### Analytics Measures[Peso em @]  — pasta: IN - General Sales Measures

```dax
VAR totalArroba = (SUM(pecuarioVendaAbate[Peso Morto Total]) / 15) + (SUM( pecuarioVendaEmPe[pesovivo_total])/30)

VAR totalCabecaVendida = SUM(pecuarioVendaAbate[qtd]) + SUM(pecuarioVendaEmPe[qtd])


RETURN totalArroba / totalCabecaVendida
```

### Analytics Measures[Outlay]  — pasta: Finance Measures

```dax
CALCULATE(SUM(financeiroDre[Desembolso])) +0
```

### Analytics Measures[% Atingido Faturamento]  — pasta: IN - General Sales Measures

```dax
DIVIDE([Invoicing],[Incoicing - Forecast]) + 0
```

### Analytics Measures[Rebanho Median Month]  — pasta: (nenhuma)

```dax
--DIVIDE([],[Count Mean Month Accumulated])
```

### Analytics Measures[UA Median Month]  — pasta: Purchase Measures

```dax
[Mean Month Accumulated - UA]
```

### Analytics Measures[Mean Month Accumulated - UA]  — pasta: Head Outlay

```dax
 VAR calc1 = 
   CALCULATE(
        [Mean Month - UA],
        FILTER(
            ALLSELECTED(dCalendar), 
            dCalendar[Data] <= MAX(dCalendar[Data]) &&
            YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  
        )
    )
VAR calc2 = 
    CALCULATE(
        [Mean Month - UA],
        FILTER(
            ALLSELECTED(dCalendar),  
            dCalendar[Data] <= MAX(dCalendar[Data])  
        )
    )
RETURN IF([Count of Selected Years] = 1,
            calc1,calc2) / [Count of Selected Month]
```

### Analytics Measures[Mean Month - UA]  — pasta: Head Outlay

```dax
SUM(pecuarioRebanhoMedioMensal[qtd_ua])
```

### Analytics Measures[Costing]  — pasta: Head Outlay

```dax
SUM('financeiroDre'[Custeio])
```

### Analytics Measures[Costing Accumulated]  — pasta: Head Outlay

```dax
VAR UltimoDiaDoMesContexto = MAX(dCalendar[Data])
VAR DataLimite = EOMONTH(UltimoDiaDoMesContexto, 0)

RETURN
    CALCULATE(
        [Costing],
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= DataLimite
        )
    )
```

### Analytics Measures[Costing head Accumulated]  — pasta: Head Outlay

```dax
DIVIDE([Costing Accumulated], ([Mean Month Accumulated - Aux (Desembolso)]), 0) / [Count of Selected Month] + 0
```

### Analytics Measures[Costing Head accumulated - forecast]  — pasta: Head Outlay

```dax
DIVIDE([Costing Accumulated - Forecast], ([Mean Month Accumulated - Aux (Desembolso) - Forecast]), 0) / [Count of Selected Month] + 0
```

### Analytics Measures[AVG Price @ (Em Pe + Abate)]  — pasta: IN - General Sales Measures

```dax
VAR fat = SUM(pecuarioVendaAbate[Faturamento]) + SUM(pecuarioVendaEmPe[Faturamento])

VAR arr = (SUM(pecuarioVendaAbate[Peso Morto Total])/15) + SUM(pecuarioVendaEmPe[Peso Morto])

RETURN fat / arr
```

### Analytics Measures[AVG Price @ Dead Sale - Forecast]  — pasta: IN - Medidas Abate

```dax
CALCULATE(SUM(fMetasAbate[Faturamento]) / (SUM(fMetasAbate[Total de @])))
```

### Analytics Measures[AVG Price @ Sale Venda em Pe - Forecast]  — pasta: IN - Medidas Venda Em Pe

```dax
CALCULATE(SUM(fMetasEmPe[Faturamento]) / SUM(fMetasEmPe[Total de @]))+0
```

### Analytics Measures[Birth Quantity - Forecast]  — pasta: Birth Measures

```dax
CALCULATE(SUM(fMetasNascimentos[qtd]),
         USERELATIONSHIP(dCalendar[Data],fMetasNascimentos[DATA])
         )
```

### Analytics Measures[% Birth x Forecast]  — pasta: Birth Measures

```dax
DIVIDE([Birth Quantity],[Birth Quantity - Forecast])
```

### Analytics Measures[Birth Quantity Accumulated]  — pasta: Birth Measures

```dax
 VAR calc1 = 
   CALCULATE(
        [Birth Quantity],
        FILTER(
            ALL(dCalendar), 
            dCalendar[Data] <= MAX(dCalendar[Data]) &&
            YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  
        )
    )
VAR calc2 = 
    CALCULATE(
        [Birth Quantity],
        FILTER(
            ALL(dCalendar),  
            dCalendar[Data] <= MAX(dCalendar[Data])  
        )
    )
RETURN IF([Count of Selected Years] = 1,
            calc1,calc2)
```

### Analytics Measures[% Mortality]  — pasta: Dead Measures

```dax
DIVIDE([Dead Quantity Accumulated],[Birth Quantity Accumulated],0)
```

### Analytics Measures[% Amount Saled]  — pasta: IN - General Sales Measures

```dax
DIVIDE([Amount Saled],[Amount Saled - Forecast])
```

### Analytics Measures[Purchased Quantity - Forecast]  — pasta: Purchase Measures

```dax
CALCULATE(
        SUM(fMetasCompras[qtd]),
        USERELATIONSHIP(dCalendar[Data],fMetasCompras[DATA])
        )
```

### Analytics Measures[% Purchased Quantity]  — pasta: Purchase Measures

```dax
DIVIDE([Purchased Quantity],[Purchased Quantity - Forecast])
```

### Analytics Measures[Dead Quantity - Forecast]  — pasta: Dead Measures

```dax
CALCULATE(SUM(fMetasMortes[qtd]),USERELATIONSHIP(dCalendar[Data],fMetasMortes[DATA]))
```

### Analytics Measures[AVG Price KG Sale Venda em Pe]  — pasta: IN - Medidas Venda Em Pe

```dax
CALCULATE(SUM(pecuarioVendaEmPe[Faturamento]) / SUM(pecuarioVendaEmPe[Peso Total]))+0
```

### Analytics Measures[MAX AVG Price @ Forecast]  — pasta: IN - General Sales Measures

```dax
[AVG Price @ (Em Pe + Abate) - Forecast] + [AVG Price @ (Em Pe + Abate) - Forecast] * 0.15
```

### Analytics Measures[AVG Price @ (Em Pe + Abate) - Forecast]  — pasta: IN - General Sales Measures

```dax
VAR fat = SUM(fMetasAbate[Faturamento]) + SUM(fMetasEmPe[Faturamento])

VAR arr = (SUM(fMetasAbate[Peso Morto Total])/15) + SUM(fMetasEmPe[Peso Morto])

RETURN fat / arr
```

### Analytics Measures[Lotation]  — pasta: Stock Measures

```dax
[Mean Month Accumulated - UA] / 2911 + 0
```

### Analytics Measures[Lotation - Forecast]  — pasta: Stock Measures

```dax
[Lotation] + [Lotation] * 0.1
```

### Analytics Measures[Lotation - Forecast - MAX]  — pasta: Stock Measures

```dax
[Lotation - Forecast] + [Lotation - Forecast] * 0.4
```

### Analytics Measures[Birth Quantity - Forecast - Const]  — pasta: Birth Measures

```dax
CALCULATE([Birth Quantity - Forecast],ALLEXCEPT(dCalendar,dCalendar[Ano]))
```

### Analytics Measures[% Birth x Forecast (Year)]  — pasta: Birth Measures

```dax
DIVIDE([Birth Quantity],[Birth Quantity - Forecast - Const])
```

### pecuarioVendaEmPe[Medida]  — pasta: (nenhuma)

```dax
(vazia)
```

### fMovGado[Medida 2]  — pasta: (nenhuma)

```dax
(vazia)
```

### Analytics Measures[Count of Selected Month]  — pasta: Dead Measures

```dax
VAR MesesComDados = 
    FILTER(
        VALUES(dCalendar[Mês]),
        CALCULATE( SUM(pecuarioRebanhoMedioMensal[qtd_cab]) ) > 0
    )
RETURN
    COUNTROWS(MesesComDados)
```

### Analytics Measures[Invoicing Abate]  — pasta: IN - Medidas Abate

```dax
SUM(pecuarioVendaAbate[Faturamento])
```

### fMetasCompras[VALORCALC]  — pasta: (nenhuma)

```dax
CALCULATE(SUM(fMetasCompras[VALOR TOTAL]),USERELATIONSHIP(fUnidades[PROPRIETARIO],pecuarioCompras[proprietÁrio]))
```

### Analytics Measures[Mean Month Accumulated - Aux (Desembolso)]  — pasta: Head Outlay

```dax
 VAR calc1 = 
   CALCULATE(
        [Mean Month],
        FILTER(
            ALLSELECTED(dCalendar), 
            dCalendar[Data] <= MAX(dCalendar[Data]) &&
            YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  
        )
    )
VAR calc2 = 
    CALCULATE(
        [Mean Month],
        FILTER(
            ALLSELECTED(dCalendar),  
            dCalendar[Data] <= MAX(dCalendar[Data])  
        )
    )
RETURN IF([Count of Selected Years] = 1,
            calc1,calc2) 
```

### Analytics Measures[Selected Farm]  — pasta: (nenhuma)

```dax
IF(SELECTEDVALUE(fUnidades[fazenda]) = BLANK(),"GRUPO",SELECTEDVALUE(fUnidades[fazenda]))
```

### Analytics Measures[Mean Month Accumulated - Aux (Desembolso) - Forecast]  — pasta: Head Outlay

```dax
 VAR calc1 = 
   CALCULATE(
        [Mean Month - forecast],
        FILTER(
            ALLSELECTED(dCalendar), 
            dCalendar[Data] <= MAX(dCalendar[Data]) &&
            YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  
        )
    )
VAR calc2 = 
    CALCULATE(
        [Mean Month - forecast],
        FILTER(
            ALLSELECTED(dCalendar),  
            dCalendar[Data] <= MAX(dCalendar[Data])  
        )
    )
RETURN IF([Count of Selected Years] = 1,
            calc1,calc2) 
```

### Analytics Measures[Outlay Forecast]  — pasta: Finance Measures

```dax
CALCULATE(
        SUM(fMetasDre[Desembolso]),
        USERELATIONSHIP(dCalendar[Data],fMetasDre[data_pag])
        )
```

### Analytics Measures[Expenses Accumulated - Forecast]  — pasta: Head Outlay

```dax
    CALCULATE(
        [Outlay Forecast],
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )
```

### Analytics Measures[Costing Forecast]  — pasta: Head Outlay

```dax
CALCULATE(
        SUM(fMetasDre[Custeio]),
        USERELATIONSHIP(dCalendar[Data],fMetasDre[data_pag])
        )
```

### Analytics Measures[Costing Accumulated - Forecast]  — pasta: Head Outlay

```dax
    CALCULATE(
        [Costing Forecast],
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )
```

### Analytics Measures[Birth Quantity Accumulated - Forecast]  — pasta: Birth Measures

```dax
 VAR calc1 = 
   CALCULATE(
        [Birth Quantity - Forecast],
        FILTER(
            ALL(dCalendar), 
            dCalendar[Data] <= MAX(dCalendar[Data]) &&
            YEAR(dCalendar[Data]) = YEAR(MAX(dCalendar[Data]))  
        )
    )
VAR calc2 = 
    CALCULATE(
        [Birth Quantity - Forecast],
        FILTER(
            ALL(dCalendar),  
            dCalendar[Data] <= MAX(dCalendar[Data])  
        )
    )
RETURN IF([Count of Selected Years] = 1,
            calc1,calc2)
```

### Analytics Measures[% Atingido Outlay]  — pasta: Finance Measures

```dax
([Outlay]-[Outlay Forecast])/[Outlay Forecast] --DIVIDE([Outlay],[Outlay Forecast])
```

### Analytics Measures[Color Desemb Cab Mês]  — pasta: (nenhuma)

```dax
    IF([head outlay accumulated] > [head outlat accumulated - forecast], "#870000","#008D7D")
```

### Analytics Measures[Color Costing Cab Mês]  — pasta: (nenhuma)

```dax
    IF([Costing head Accumulated] > [Costing Head accumulated - forecast], "#870000","#008D7D")
```

### Analytics Measures[Color @ Venda Geral]  — pasta: (nenhuma)

```dax
    IF([AVG Price @ (Em Pe + Abate)] > [AVG Price @ (Em Pe + Abate) - Forecast],"#008D7D", "#870000")
```

### Analytics Measures[IN Venda Geral]  — pasta: (nenhuma)

```dax
    IF([Invoicing] > [Incoicing - Forecast],1,-1)
```

### Analytics Measures[IN Costing Cab Mês]  — pasta: (nenhuma)

```dax
    IF([Costing head Accumulated] > [Costing Head accumulated - forecast], 1,-1)
```

### Analytics Measures[IN Desembolso Cab Mês]  — pasta: (nenhuma)

```dax
  IF([head outlay accumulated]> [head outlat accumulated - forecast], -1,1)
```

### Analytics Measures[IN Mean Month]  — pasta: (nenhuma)

```dax
    IF([Mean Month] > [Mean Month - forecast],1,-1)
```

### Analytics Measures[Sistema Produção]  — pasta: (nenhuma)

```dax
"INFORMATIVO DETALHADO PG1"
```

### Analytics Measures[Revenues Forecast]  — pasta: Finance Measures

```dax
CALCULATE(
        SUM(fMetasDre[valor]),
        USERELATIONSHIP(dCalendar[Data],fMetasDre[data_pag]),
        'fMetasDre'[operaÇÃo]="C",
        fMetasDre[tipo_custeio-CAT] IN {"ReceitasPec","ReceitasAgr","ReceitaPec","ReceitaAgr"}
        )
```

### Analytics Measures[Expenses Forecast]  — pasta: Finance Measures

```dax
CALCULATE(
        SUM(fMetasDre[valor]),
        USERELATIONSHIP(dCalendar[Data],fMetasDre[data_pag]),
        'fMetasDre'[operaÇÃo]="D"
        )
```

### Analytics Measures[Total Paid - Forecast]  — pasta: Purchase Measures

```dax
CALCULATE(
        SUM(fMetasCompras[VALOR TOTAL]),
        USERELATIONSHIP(dCalendar[Data],fMetasCompras[DATA])
        )+0
```

### Analytics Measures[Purchased Quantity FEMALE]  — pasta: Purchase Measures

```dax
CALCULATE(
    [Purchased Quantity],
    pecuarioCompras[sexo] = "FÊMEA"
)
```

### Analytics Measures[Purchased Quantity MALE]  — pasta: Purchase Measures

```dax
CALCULATE(
    [Purchased Quantity],
    pecuarioCompras[sexo] = "MACHO"
)
```

### Analytics Measures[@ AVG Price Purchase]  — pasta: Purchase Measures

```dax
CALCULATE(SUM(pecuarioCompras[VALOR TOTAL]) / (SUM(pecuarioCompras[Total de @])))
```

### Analytics Measures[% Purchased Value]  — pasta: Purchase Measures

```dax
DIVIDE([Total Paid],[Total Paid - Forecast])
```

### Analytics Measures[Purchased Quantity - Forecast - TESTE]  — pasta: Purchase Measures

```dax
CALCULATE(
        SUM(fMetasCompras[qtd]),
        USERELATIONSHIP(fMetasCompras[PROP_FAZ],fUnidades[PROP_FAZ]),
        USERELATIONSHIP(dCalendar[Data],fMetasCompras[DATA])
        )
```

### Analytics Measures[Ágio]  — pasta: Purchase Measures

```dax
/*
var Fat = CALCULATE(SUM(pecuarioVendaEmPe[Faturamento])+SUM(pecuarioVendaAbate[Faturamento]))
var Quant = CALCULATE(SUM(pecuarioVendaEmPe[qtd])+SUM(pecuarioVendaAbate[qtd]))
var pesoArr = CALCULATE(SUM(pecuarioVendaAbate[Total de @])+SUM(pecuarioVendaEmPe[Total de @]))

RETURN DIVIDE(fat,pesoArr)
*/

var avgArrobaVenda = [AVG Price @ (Em Pe + Abate)]

var avgArrobaCompra = [@ AVG Price Purchase]

RETURN DIVIDE(avgArrobaCompra - avgArrobaVenda,avgArrobaVenda)
```

### Analytics Measures[Mean Month Ha]  — pasta: Head Outlay

```dax
[Mean Month] / (SUM(fArea[Área_total]) / [Count of Selected Month])
```

### Analytics Measures[UA Median Ha]  — pasta: Purchase Measures

```dax
[UA Median Month] / (SUM(fArea[Área_total]) / [Count of Selected Month])
```

### Analytics Measures[% mORTALITY ( MEAN MONTH)]  — pasta: Dead Measures

```dax
[Dead Quantity] / [Mean Month]
```

### Analytics Measures[% Variação]  — pasta: Finance Measures

```dax
DIVIDE(
                            [Valor Último Mês Selecionado]-[Meta Último Mês Selecionado],[Meta Último Mês Selecionado]
                        )
```

### Analytics Measures[Value Accumulated]  — pasta: Finance Measures

```dax
VAR LastDate2 = MAX(dCalendar[Data])
VAR IsClassInScope = ISINSCOPE(planejadoXRealizado[classificacao])

RETURN
IF(
    IsClassInScope,
    -- Quando o usuário está vendo uma classificação específica: acumulado simples da própria linha
    CALCULATE(
        SUM(planejadoXRealizado[Valor C]),
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= LastDate2
        )
    ),
    -- Quando não está em escopo de classificacao: acumulado = Receitas acumuladas - Despesas acumuladas
    VAR ReceitasAcum =
        CALCULATE(
            SUM(planejadoXRealizado[Valor C]),
            FILTER(ALLSELECTED(dCalendar), dCalendar[Data] <= LastDate2),
            planejadoXRealizado[Classificacao] = "A - RECEITAS"
        )
    VAR DespesasAcum =
        CALCULATE(
            SUM(planejadoXRealizado[Valor C]),
            FILTER(ALLSELECTED(dCalendar), dCalendar[Data] <= LastDate2),
            planejadoXRealizado[Classificacao] IN {
                "C - INVESTIMENTOS",
                "D - CUSTEIO",
                "E - OUTROS DÉBITOS"
            }
        )
    RETURN
        ReceitasAcum - DespesasAcum
)
```

### Analytics Measures[Meta Accumulated]  — pasta: Finance Measures

```dax
VAR _MaxDate = MAX(dCalendar[Data])
VAR _IsClassInScope = ISINSCOPE(planejadoXRealizado[classificacao])

RETURN
IF(
    _IsClassInScope,
    -- Acumulado da própria classificação (quando class está no escopo)
    CALCULATE(
        SUM(planejadoXRealizado[Meta C]),
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= _MaxDate
        )
    ),
    -- Quando não há classificação no escopo: ReceitasAcum - DespesasAcum
    VAR ReceitasAcum =
        CALCULATE(
            SUM(planejadoXRealizado[Meta C]),
            FILTER(ALLSELECTED(dCalendar), dCalendar[Data] <= _MaxDate),
            planejadoXRealizado[Classificacao] = "A - RECEITAS"
        )
    VAR DespesasAcum =
        CALCULATE(
            SUM(planejadoXRealizado[Meta C]),
            FILTER(ALLSELECTED(dCalendar), dCalendar[Data] <= _MaxDate),
            planejadoXRealizado[Classificacao] IN {
                "C - INVESTIMENTOS",
                "D - CUSTEIO",
                "E - OUTROS DÉBITOS"
            }
        )
    RETURN
        ReceitasAcum - DespesasAcum
)
```

### Analytics Measures[% Variação Acc Graph]  — pasta: Finance Measures

```dax
VAR _valor = [%% Variação Acc]
VAR _icone =
    SWITCH(
        TRUE(),
        _valor >= 0, UNICHAR(10004),   -- ✅ check
        _valor < 0, UNICHAR(10060),    -- ❌ X
        BLANK()
    )
RETURN  [%% Variação Acc] 
/*IF(
        NOT ISFILTERED(planejadoXRealizado[centro_de_custo_bi]), 
      
        BLANK(), 
        [%% Variação Acc] 
    )*/
```

### Analytics Measures[% Variação Graph]  — pasta: Finance Measures

```dax
VAR _valor = [% Variação]
VAR _icone =
    SWITCH(
        TRUE(),
        _valor >= 0, UNICHAR(10004),   -- ✅ check
        _valor < 0, UNICHAR(10060),    -- ❌ X
        BLANK()
    )
RETURN [% Variação]
/*IF(
        NOT ISFILTERED(planejadoXRealizado[centro_de_custo_bi]), 
        -- OU: NOT ISINSCOPE('Sua Tabela'[Sua Coluna de Linha]),
        BLANK(), -- Se for um Total, retorna em branco
        [% Variação] -- Se for o nível de detalhe (Linha), retorna o valor
    )*/
```

### Analytics Measures[%% Variação Acc]  — pasta: Finance Measures

```dax
                DIVIDE( [Value Accumulated] - [Meta Accumulated],[Meta Accumulated])
```

### Analytics Measures[Icon]  — pasta: Finance Measures

```dax
--IF(
   -- ISINSCOPE(planejadoXRealizado[centro_de_custo_bi]),
    VAR _var = [% Variação]
    VAR _class = SELECTEDVALUE(planejadoXRealizado[classificacao])
    RETURN
        IF(
            _var <> BLANK(),
            SWITCH(
                TRUE(),
  
                _class = "A - RECEITAS" && _var > 0.03, "VERDE",
                _class = "A - RECEITAS" && _var < -0.03, "VERMELHO",
                _class = "A - RECEITAS" && _var >= -0.03 && _var <= 0.03, "AMARELO",

                _class <> "A - RECEITAS" && _var <= 0 && _var >= -1, "VERDE",
                _class <> "A - RECEITAS" && _var > 0.03, "VERMELHO",
                _class <> "A - RECEITAS" && _var > 0 && _var <= 0.03, "AMARELO",

                BLANK()
            ),
            BLANK()
        )--,
    --BLANK()
--)
```

### Analytics Measures[RL Mensal]  — pasta: Finance Measures

```dax
"MENSAL"
```

### Analytics Measures[RL Acumulado]  — pasta: Finance Measures

```dax
"ACUMULADO"
```

### Analytics Measures[Icon Acc]  — pasta: Finance Measures

```dax
--IF(
 --   ISINSCOPE(planejadoXRealizado[centro_de_custo_bi]),
    VAR _var = [%% Variação Acc]
    VAR _class = SELECTEDVALUE(planejadoXRealizado[Classificacao2])
    RETURN
        IF(
            _var <> BLANK(),
            SWITCH(
                TRUE(),
                _class = "A - RECEITAS" && _var > 0.03, "VERDE",
                _class = "A - RECEITAS" && _var < -0.03, "VERMELHO",
                _class = "A - RECEITAS" && _var >= -0.03 && _var <= 0.03, "AMARELO",

                _class <> "A - RECEITAS" && _var <= 0 && _var >= -1, "VERDE",
                _class <> "A - RECEITAS" && _var > 0.03, "VERMELHO",
                _class <> "A - RECEITAS" && _var > 0 && _var <= 0.03, "AMARELO",

                BLANK()
            ),
            BLANK()
        )--,
--    BLANK()
--)
```

### planejadoXRealizado[Valor Último Mês Selecionado]  — pasta: (nenhuma)

```dax
VAR MaxDateSelecionada =
    CALCULATE(
        MAX('dcalendar'[Data]),
        ALLSELECTED('dcalendar')
    )
VAR PrimeiroDiaDoUltimoMes =
    EOMONTH(MaxDateSelecionada, -1) + 1

VAR FiltrosDeData =
    FILTER(
        ALL('dcalendar'), 
        'dcalendar'[Data] >= PrimeiroDiaDoUltimoMes &&
        'dcalendar'[Data] <= MaxDateSelecionada
    )
    
VAR Receitas = 
    CALCULATE(
        SUM('planejadoXRealizado'[Valor C]), 
        FiltrosDeData,
        'planejadoXRealizado'[classificacao] = "A - RECEITAS"
    )

VAR Despesas = 
    CALCULATE(
        SUM('planejadoXRealizado'[Valor C]), 
        FiltrosDeData,
        'planejadoXRealizado'[classificacao] IN {"C - INVESTIMENTOS","D - CUSTEIO","E - OUTROS DÉBITOS"}
    )

RETURN 
    IF(
        ISINSCOPE('planejadoXRealizado'[Classificacao]),
        
        -- Cálculo linha a linha (dentro do escopo)
        CALCULATE(
            SUM('planejadoXRealizado'[Valor C]), 
            FiltrosDeData
        ),
        
        -- Cálculo do Total Final
        -- O COALESCE garante que se Receitas for BLANK, ele usa 0.
        -- Assim a conta fica: 0 - Despesas = -Despesas (o total aparece negativo corretamente)
        COALESCE(Receitas, 0) - COALESCE(Despesas, 0)
    )
```

### planejadoXRealizado[Meta Último Mês Selecionado]  — pasta: (nenhuma)

```dax
VAR MaxDateSelecionada =
    CALCULATE(
        MAX('dcalendar'[Data]),
        ALLSELECTED('dcalendar')
    )
VAR PrimeiroDiaDoUltimoMes =
    EOMONTH(MaxDateSelecionada, -1) + 1

VAR FiltrosDeData =
    FILTER(
        ALL(dCalendar),
        dCalendar[Data]>= PrimeiroDiaDoUltimoMes && dCalendar[Data] <=MaxDateSelecionada
    )
RETURN
    IF(
        ISINSCOPE('planejadoXRealizado'[Classificacao]),
        CALCULATE(
            SUM('planejadoXRealizado'[Meta C]), 
            FiltrosDeData
        ),
        CALCULATE(
            SUM('planejadoXRealizado'[Meta C]), 
            FiltrosDeData,
            'planejadoXRealizado'[Classificacao] = "A - RECEITAS"
        ) - 
        CALCULATE(
            SUM('planejadoXRealizado'[Meta C]), 
            FiltrosDeData,
            'planejadoXRealizado'[Classificacao] IN {"C - INVESTIMENTOS","D - CUSTEIO","E - OUTROS DÉBITOS"}
        )
    )

/*
VAR MaxDateSelecionada =
    CALCULATE(
        MAX('dcalendar'[Data]),
        ALLSELECTED('dcalendar')
    )
VAR PrimeiroDiaDoUltimoMes =
    EOMONTH(MaxDateSelecionada, -1) + 1

VAR FiltrosDeData =
    FILTER(
        ALL('dcalendar'), 
        'dcalendar'[Data] >= PrimeiroDiaDoUltimoMes &&
        'dcalendar'[Data] <= MaxDateSelecionada
    )
    
RETURN
    IF(
        ISINSCOPE('planejadoXRealizado'[Classificacao]),
        CALCULATE(
            SUM('planejadoXRealizado'[Valor C]), 
            FiltrosDeData
        ),
        CALCULATE(
            SUM('planejadoXRealizado'[Valor C]), 
            FiltrosDeData,
            'planejadoXRealizado'[Classificacao] <> "D - DESEMBOLSO"
        )
    )
*/
```

### Analytics Measures[All Revenues]  — pasta: Finance Measures

```dax
CALCULATE(SUM('financeiroDre'[valor]),'financeiroDre'[operaÇÃo]="C",financeiroDre[tipo_custeio-CAT] IN {"Receita Pec", "Receita Agr","Receita outras"})
```

### Analytics Measures[Amount Saled (Abate)]  — pasta: IN - Medidas Abate

```dax
SUM(pecuarioVendaAbate[qtd])
```

### Analytics Measures[Amount Saled - Forecast (Abate)]  — pasta: IN - Medidas Abate

```dax
VAR calc1 = CALCULATE(SUM(fMetasAbate[qtd]))


RETURN calc1
```

### Analytics Measures[Invoicing (Abate)]  — pasta: IN - Medidas Abate

```dax
SUM(pecuarioVendaAbate[Faturamento])+0
```

### Analytics Measures[Incoicing - Forecast (Abate)]  — pasta: IN - Medidas Abate

```dax
VAR calc1 = CALCULATE(SUM(fMetasAbate[faturamento]))

RETURN calc1+0
```

### Analytics Measures[IN - Name (Abate)]  — pasta: (nenhuma)

```dax
"Venda Abate"
```

### Analytics Measures[IN - AVG Live Weight]  — pasta: IN - Medidas Abate

```dax
VAR calc1 = SUM(pecuarioVendaAbate[qtd])

VAR calc2 = SUM(pecuarioVendaAbate[pesovivo_total])

RETURN DIVIDE(calc2,calc1)
```

### Analytics Measures[Invoicing (Em Pe )]  — pasta: IN - Medidas Venda Em Pe

```dax
SUM(pecuarioVendaEmPe[Faturamento])+0
```

### Analytics Measures[Incoicing - Forecast (Em Pe)]  — pasta: IN - Medidas Venda Em Pe

```dax
VAR calc1 = CALCULATE(SUM(fMetasEmPe[faturamento]))

RETURN calc1+0
```

### Analytics Measures[Amount Saled (Em pe)]  — pasta: IN - Medidas Venda Em Pe

```dax
SUM(pecuarioVendaEmPe[qtd])
```

### Analytics Measures[Amount Saled - Forecast (Em Pe)]  — pasta: IN - Medidas Venda Em Pe

```dax
VAR calc1 = CALCULATE(SUM(fMetasEmPe[qtd]))


RETURN calc1
```

### Analytics Measures[IN - AVG Live Weight (Em Pe)]  — pasta: IN - Medidas Venda Em Pe

```dax
VAR calc1 = SUM(pecuarioVendaEmPe[qtd])

VAR calc2 = SUM(pecuarioVendaEmPe[pesovivo_total])

RETURN DIVIDE(calc2,calc1)+0
```

### Analytics Measures[IN AVG - Peso Médio de Compra]  — pasta: Purchase Measures

```dax
VAR calc1 = SUM(pecuarioCompras[qtd])

VAR calc2 = SUM(pecuarioCompras[total_peso])

RETURN DIVIDE(calc2,calc1)
```

### Analytics Measures[IN AVG - Peso Médio de Compra (Forecast)]  — pasta: Purchase Measures

```dax
VAR calc1 = SUM(fMetasCompras[qtd])

VAR calc2 = SUM(fMetasCompras[total_peso])

RETURN DIVIDE(calc2,calc1)
```

### Analytics Measures[AVG Purchase Price KG]  — pasta: Purchase Measures

```dax
CALCULATE(SUM(pecuarioCompras[VALOR TOTAL]) / SUM(pecuarioCompras[total_peso]))+0
```

### Analytics Measures[AVG Purchase Price KG (Forecast)]  — pasta: Purchase Measures

```dax
CALCULATE(SUM(fMetasCompras[VALOR TOTAL]) / SUM(fMetasCompras[total_peso]))+0
```

### Analytics Measures[IN - % Male Birth]  — pasta: Birth Measures

```dax
VAR tot = [Birth Quantity]

VAR qtdmale = CALCULATE([Birth Quantity], pecuarioNascimento[sexo] = "MACHO")

RETURN DIVIDE(qtdmale,tot)
```

### Analytics Measures[IN - % Female Birth]  — pasta: Birth Measures

```dax
VAR tot = [Birth Quantity]

VAR qtdmale = CALCULATE([Birth Quantity], pecuarioNascimento[sexo] = "FÊMEA")

RETURN DIVIDE(qtdmale,tot)
```

### Analytics Measures[IN - AVG Live Weight (Forecast)]  — pasta: IN - Medidas Abate

```dax
VAR calc1 = SUM(fMetasAbate[qtd])

VAR calc2 = SUM(fMetasAbate[pesovivo_total])

RETURN DIVIDE(calc2,calc1)
```

### Analytics Measures[IN - AVG Live Weight (Em Pe - Forecast)]  — pasta: IN - Medidas Venda Em Pe

```dax
VAR calc1 = SUM(fMetasEmPe[qtd])

VAR calc2 = SUM(fMetasEmPe[pesovivo_total])

RETURN DIVIDE(calc2,calc1)+0
```

### Analytics Measures[AVG Price KG Sale Venda em Pe - Forecast]  — pasta: IN - Medidas Venda Em Pe

```dax
CALCULATE(SUM(fMetasEmPe[Faturamento]) / SUM(fMetasEmPe[Peso Total]))+0
```

### Analytics Measures[IN - Rendimento Carcaça (Forecast)]  — pasta: IN - Medidas Abate

```dax
SUM(fMetasAbate[pesomorto_total]) / SUM(fMetasAbate[pesovivo_total])
```

### Analytics Measures[Invoicing Accumulated (Abate)]  — pasta: IN - Medidas Abate

```dax
    CALCULATE(
        SUM(pecuarioVendaAbate[qtd])+0,
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )
```

### Analytics Measures[Amount Saled Accumulated (Em Pe)]  — pasta: IN - Medidas Venda Em Pe

```dax
    CALCULATE(
        SUM(pecuarioVendaEmPe[qtd])+0,
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )
```

### Analytics Measures[Purchase Quantity Accumulated]  — pasta: Purchase Measures

```dax
    CALCULATE(
        SUM(pecuarioCompras[qtd])+0,
        FILTER(
            ALLSELECTED(dCalendar),
            dCalendar[Data] <= MAX(dCalendar[Data])
        )
    )
```

### Analytics Measures[IN - Incoming Transfer]  — pasta: (nenhuma)

```dax
CALCULATE(SUM(fTransferencias[qtd]),fTransferencias[operaÇÃo] = "Transf. Entrada")
```

### Analytics Measures[IN - Outgoing Transfer]  — pasta: (nenhuma)

```dax
CALCULATE(SUM(fTransferencias[qtd]),fTransferencias[operaÇÃo] = "Transf. Saida")
```

### Analytics Measures[IN - Incoming Transfer - Forecast]  — pasta: (nenhuma)

```dax
CALCULATE(SUM(fMetasTransferencias[qtd]),fMetasTransferencias[operaÇÃo] = "Transf. Entrada")
```

### Analytics Measures[IN - Outgoing Transfer - Forecast]  — pasta: (nenhuma)

```dax
CALCULATE(SUM(fMetasTransferencias[qtd]),fMetasTransferencias[operaÇÃo] = "Transf. Saida")
```

### Analytics Measures[IN QTD Transfer Forecast]  — pasta: Transfer Measures

```dax
SUM(fMetasTransferencias[qtd])
```

### Analytics Measures[IN QTD Transfer]  — pasta: Transfer Measures

```dax
SUM(fTransferencias[qtd])
```

### Analytics Measures[IN - AVG Price @ Transfer]  — pasta: Transfer Measures

```dax
CALCULATE(SUM(fTransferencias[VALOR TOTAL]) / (SUM(fTransferencias[Peso Total @])))
```

### Analytics Measures[IN - AVG Price @ Transfer Forecas]  — pasta: Transfer Measures

```dax
CALCULATE(SUM(fMetasTransferencias[VALOR TOTAL]) / (SUM(fMetasTransferencias[Peso Total @])))
```

### Analytics Measures[IN - AVG Weight Transfer]  — pasta: Transfer Measures

```dax
VAR calc1 = SUM(fTransferencias[qtd])

VAR calc2 = SUM(fTransferencias[total_peso])

RETURN DIVIDE(calc2,calc1)
```

### Analytics Measures[IN - AVG Weight Transfer Forecast]  — pasta: Transfer Measures

```dax
VAR calc1 = SUM(fMetasTransferencias[qtd])

VAR calc2 = SUM(fMetasTransferencias[total_peso])

RETURN DIVIDE(calc2,calc1)
```

### Analytics Measures[head outlat accumulated - forecast graph]  — pasta: Head Outlay

```dax
[head outlat accumulated - forecast] + ([head outlat accumulated - forecast] * 0.2)
```
