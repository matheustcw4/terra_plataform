# 04 — Pipeline Metryx (API REST → Pentaho → PostgreSQL): especificação para reescrita em Python

> **Escopo:** engenharia reversa do job `Job Extract Data .kjb` e das 22 transformações `.ktr` em `C:\Users\TerraDev\Documents\Pentaho Archives\Projeto Terra\Metryx + Planilhas\Metryx\`, cruzadas com o OpenAPI 3.0.1 oficial da API Metryx (`openapi.json`, 25 endpoints, 24 DTOs) e com as consultas SQL do Power BI (`pbix_metryx/power_query.csv`) que consomem as tabelas geradas.
> **Segurança:** nenhum token, senha ou string "Encrypted …" é reproduzido neste documento. Onde existir segredo está escrito **[REDACTED]** e é descrito apenas o local onde ele vive. A API Metryx **não** foi chamada.
> **Ferramentas:** parsing XML dos .ktr/.kjb com Python (scripts em `scratchpad/scripts/`: `summ_ktr.py`, `dump_kjb.py`, `gen_ddl.py`, `gen_api_catalog.py`, `token_fp.py`, `redact.py`). Versão do PDI no ambiente: 9.4.0.0-343 (inferida de `~/.kettle/db.cache-9.4.0.0-343`).

---

## 0. Sumário executivo

**Como funciona hoje (em uma frase):** um job Pentaho sequencial chama, para cada token de cliente gravado em `"DATABASE".stg_customers`, um endpoint GET da API Metryx sem nenhum parâmetro, decodifica o JSON inteiro com `$..campo` e faz **TRUNCATE + INSERT** em uma tabela `"DATABASE".stg_*` no banco local `METRIX` (PostgreSQL `localhost:5432`, usuário `postgres`).

Principais achados:

1. **A API não tem parâmetros**: nenhum dos 25 endpoints declara query/path params — sem filtro de data, fazenda ou paginação. O escopo é dado **exclusivamente pelo token** (`x-auth-token`, JWT HS384). Toda extração é um snapshot completo do cliente. Incremental só é possível **do nosso lado** (hash/diff).
2. **Modelo de autenticação em dois níveis:** a transformação `get_customer` usa um **token "mestre" hardcoded** para chamar `GET /api-metryx/customers` — **endpoint que não existe no Swagger oficial** — que devolve os clientes e uma `listToken` com **um token por cliente**. Esses tokens por cliente são **gravados em texto puro** na coluna `token VARCHAR(600)` de `"DATABASE".stg_customers` e lidos por todas as demais transformações.
3. **Segredos expostos em arquivos:** 22 JWTs hardcoded (1 por .ktr, em `Data grid`; 21 arquivos compartilham o mesmo token e `get_customer` tem outro, o mestre). Os JWTs **não têm `exp`** (não expiram). A senha do PostgreSQL (`postgres`, superusuário) está em cada .ktr com ofuscação reversível "Encrypted" do Kettle; a senha SMTP do Gmail está em 11 entradas de e-mail do job. Todos devem ser **rotacionados** na migração.
4. **Falhas silenciosas:** o erro do passo REST é desviado para um `Dummy` (descartado) em 20 das 22 transformações; o status HTTP nunca é lido; a tabela já foi truncada. Um 401/500 de um cliente faz os dados dele **sumirem sem alerta**. Se `/customers` falhar, `stg_customers` fica vazia e **todas** as tabelas são esvaziadas na sequência.
5. **Bugs de lógica:** `get_transferencias` (órfã) chama `mudanca-categoria-pecuario` e grava com TRUNCATE em `stg_balanco_pecuario`; `get_mudanca_cat` (órfã) lê um JSON local do Desktop de outro usuário em vez da resposta da API; `get_rebanhomedio` e `get_rebanho_medio` duplicam o mesmo endpoint em tabelas diferentes; `get_vendas` grava o JSON bruto de todos os clientes em `C:\Users\TerraDev\Documents\teste.txt` a cada execução.
6. **Perda de chaves e de versões:** vendas e compras **não gravam `idFarm`** (o BI junta por `farmname`); previsões de compra e venda **não gravam `plVersionCode`** (versões de planejamento podem ser somadas); `stg_area` não grava `idCustomer`; o DRE descarta `idFarmFiscal`, `cpfCnpj`, `idBankAccount`, `addition`, `discount`, `clientProvider`, `documents`.
7. **Números e locale:** há "gambiarras" de locale (troca `.`→`,` antes de converter para Number) e muitos campos numéricos com tipo `None`/String convertidos implicitamente; o próprio BI tem um **filtro temporário para |valor| ≥ 1 bilhão** no DRE ("erro de escala na origem, ex.: Receitas financeiras ~5e16"). O adapter deve ler números como `Decimal` direto do JSON.
8. **Endpoints não usados:** `transferencia-animal-pecuario`, `saldo-inical-pecuario`, `retiro`, `previsao-fluxo-caixa-planejamento`, `confina-tech`, `control-birth` (POST de **escrita** — nunca chamar). **Correção à premissa inicial:** `utilizacao-pasto` (get_area), `lancamento-financeiro` (get_dre) e `previsao-financeiro` (get_prevdre) **são** usados pelo job.
9. **Recomendação:** adapter Python com `httpx` + retries + limite de concorrência, credenciais por tenant cifradas, landing do JSON bruto (`raw.metryx_payload`, com hash), normalização transacional por tenant (substituição atômica de partição para entidades sem ID; UPSERT para entidades com ID), guardas de sanidade (queda brusca de linhas aborta a carga) e views de compatibilidade com os nomes `stg_*` atuais para o Power BI durante a transição (ver seção 8).

---

## 1. Catálogo da API Metryx

### 1.1 Visão geral

| Item | Valor |
|---|---|
| Spec | OpenAPI 3.0.1, `info.title = "Api-Metryx"`, `version = v1`; um único controller (`api-metryx-controller`) |
| Base URL | `https://web-srv.metryx.app:8444/mtxserver` (porta **8444** não padrão — liberar no firewall do servidor do adapter) |
| Prefixo | `/api-metryx/...` |
| Autenticação | `securitySchemes.AuthToken`: `apiKey` no header **`x-auth-token`**, `bearerFormat: JWT` (sem prefixo "Bearer"). Exigido em todas as operações. O Pentaho envia `X-Auth-Token` (headers HTTP são case-insensitive). |
| Login / refresh | **Não existe** endpoint de login, refresh ou emissão de token no Swagger. Tokens são emitidos fora da API (provavelmente pelo suporte/console Metryx). JWTs observados: alg HS384, claims `iss`, `sub`, `id` — **sem `exp`/`iat`** (token estático, não expira). |
| Autorização | Por endpoint e embutida no token (ex.: `utilizacao-pasto` diz "Exige permissão do endpoint UTILIZACAO_PASTO no token"). Esperar **403** quando o token não tiver permissão para um endpoint. |
| Parâmetros | **Nenhum** em nenhum endpoint (sem `parameters` no spec inteiro). Sem filtro por período, fazenda, cliente; **sem paginação**. |
| Resposta | Sempre `200` com `content: */*` e schema `array<DTO>` (exceto `control-birth`, que devolve `object`). Nenhuma resposta de erro documentada. |
| Métodos | 24 × `GET` (leitura) + 1 × `POST /api-metryx/control-birth` (escrita) |
| Endpoint não documentado | `GET /api-metryx/customers` — usado por `get_customer.ktr` com o token mestre; formato inferido do parsing: `[{ "idCustomer", "customer", "listToken": [ { "token", ... } ] }]`. **Não está no Swagger**: confirmar com a Metryx se é suportado/estável. |
| Erros de grafia na API | path `saldo-inical-pecuario` ("inical"); campos `idFinancialEntrie`, `banckAccount`, `idfarmDestination` (minúsculo). Manter exatamente como estão. |
| Tipos suspeitos | Muitos valores monetários e pesos declarados `integer(int64)` (ex.: `ApiMetryxLiSaleDTO.valueArroba`, `totalFaturamento`, `liveWeightAVG`; `ApiMetryxFiPrevisionDTO.valorPrevisto`). Ou a API arredonda (perda de centavos) ou o schema está impreciso — validar com payload real e tratar todo número como `Decimal`. |

### 1.2 Convenções comuns dos DTOs

- **Hierarquia:** `idCustomer` (cliente/tenant Metryx) → `idFarm` (fazenda) → `idRetiro` (retiro). Todos `string`. Em `confina-tech`, `customerId` é `int64` (inconsistência).
- **Desnormalização:** quase todos os fatos repetem `customer`, `farmName`, `retiroName`, `owner` (proprietário dos animais). Não há IDs de proprietário nos DTOs realizados (só `owner` texto); nos de planejamento há `idOwner`/`ownerName`.
- **Datas** são `string` sem `format`. Pelo uso no BI: realizado `date` = `YYYY-MM-DD` (`TO_DATE(date,'YYYY-MM-DD')`), planejamento `date` = `MM/YY` (`to_date(date,'MM/YY')`), `previsao-financeiro.date` e `lancamento-financeiro.datePayment` castáveis com `::date`. `utilizacao-pasto` documenta `yyyy-MM-dd`. Não há fuso horário (datas civis).
- **Ano-safra:** `anoSafra` (ex. "2024/2025") e `harvest` (safra/geração do lote) são strings; `birth`/`era` indicam a geração de nascimento do lote.
- **Sem ID de registro** na maioria dos fatos pecuários (venda, compra, morte, nascimento, desmame, balanço, mudança de categoria, saldo inicial, rebanho médio). Têm ID: `transferencia` (`id`, `itemId`), `lancamento-financeiro` (`idFinancialEntrie`, `idPayment`), `utilizacao-pasto` (`id` da pastagem + `tipoUsoId`), `confina-tech` (`productEntryUuid`), cadastros (`idFarm`, `idRetiro`, `idCategory`).
- **Pecuário (`*-pecuario`)** = realizado (eventos/estoque de animais). **Planejamento (`*-mensal-planejamento`, `previsao-fluxo-caixa-planejamento`)** = orçamento/metas mensais com `plVersionCode/plVersionName` (versão/cenário), `idPlHerdType` (tipo de rebanho) e moeda. **Financeiro** = `lancamento-financeiro` (realizado: títulos e baixas) e `previsao-financeiro` (previsto × realizado por centro de custo).

### 1.3 Endpoints (um a um)

Legenda: "Descrição oficial" vem do Swagger (só `utilizacao-pasto` tem descrições); "Interpretação" é inferência a partir de nomes, uso no Pentaho e consultas do Power BI — **validar com a Metryx/payload real** antes de fixar o modelo canônico.

#### 1.3.1 `GET /api-metryx/fazenda`

- **operationId:** `getFazenda` | **Domínio:** Cadastro
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxFazendasDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Lista de fazendas do cliente (escopo do token).
- **Uso no ETL atual:** USADO: get_customer (2ª chamada, por token) -> stg_customers; get_farms (fFarms) -> stg_farm.

DTO `ApiMetryxFazendasDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customer` | string | - | Nome do cliente Metryx. |
| 3 | `idFarm` | string | - | ID da fazenda (string; usado como chave da fazenda em todo o ecossistema). |
| 4 | `farmName` | string | - | Nome da fazenda. |

#### 1.3.2 `GET /api-metryx/retiro`

- **operationId:** `getRetiro` | **Domínio:** Cadastro
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxLiRetiroDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Lista de retiros (subdivisões) por fazenda.
- **Uso no ETL atual:** NÃO USADO. Valioso: dimensão retiro com ID estável (hoje o retiro só aparece desnormalizado nos fatos).

DTO `ApiMetryxLiRetiroDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customer` | string | - | Nome do cliente Metryx. |
| 3 | `idFarm` | string | - | ID da fazenda (string; usado como chave da fazenda em todo o ecossistema). |
| 4 | `farmName` | string | - | Nome da fazenda. |
| 5 | `idRetiro` | string | - | ID do retiro (subdivisão operacional/geográfica da fazenda). |
| 6 | `retiroName` | string | - | Nome do retiro. |

#### 1.3.3 `GET /api-metryx/categoria`

- **operationId:** `getCategories` | **Domínio:** Cadastro
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxLiCategoriesDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Categorias animais do cliente (com grupo, faixa etária e sexo).
- **Uso no ETL atual:** USADO: get_categories (fCategories) -> stg_category.

DTO `ApiMetryxLiCategoriesDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customer` | string | - | Nome do cliente Metryx. |
| 3 | `idCategory` | string | - | ID da categoria animal. |
| 4 | `category` | string | - | Nome da categoria animal (ex.: bezerro, novilha, vaca, boi). |
| 5 | `categoryGroup` | string | - | Grupo da categoria (ex.: "Bezerros Mamando"; usado no BI fSaldoGado). |
| 6 | `ageCategory` | string | - | Faixa etária da categoria. |
| 7 | `gender` | string | - | Sexo (código). |

#### 1.3.4 `GET /api-metryx/balanco-pecuario`

- **operationId:** `getLiBalance` | **Domínio:** Pecuário realizado
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxLiBalanceDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Movimentações de estoque por data/categoria/lote; o BI (fSaldoGado) faz soma acumulada de amount por fazenda/retiro/categoria para obter o saldo de gado.
- **Uso no ETL atual:** USADO: get_balanco (fBalanco) -> stg_balanco_pecuario. (get_transferencias, órfão, também escreveria nesta tabela - ver seção 7.)

DTO `ApiMetryxLiBalanceDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customer` | string | - | Nome do cliente Metryx. |
| 3 | `idFarm` | string | - | ID da fazenda (string; usado como chave da fazenda em todo o ecossistema). |
| 4 | `farmName` | string | - | Nome da fazenda. |
| 5 | `idRetiro` | string | - | ID do retiro (subdivisão operacional/geográfica da fazenda). |
| 6 | `retiroName` | string | - | Nome do retiro. |
| 7 | `owner` | string | - | Proprietário dos animais (pode diferir do cliente: parceria, gado de terceiros). |
| 8 | `date` | string | - | Data do evento/lançamento (string). Realizado: "YYYY-MM-DD" (o BI faz TO_DATE(date,'YYYY-MM-DD')); planejamento: "MM/YY" (o BI faz to_date(date,'MM/YY')). Confirmar por endpoint. |
| 9 | `uuidCategory` | string | - | UUID da categoria animal. |
| 10 | `category` | string | - | Nome da categoria animal (ex.: bezerro, novilha, vaca, boi). |
| 11 | `birth` | string | - | Nascimento/era do lote (ano ou mes-ano de nascimento; interpretação). String. |
| 12 | `harvest` | string | - | Safra/geração do lote de animais (interpretação: safra de nascimento). String. |
| 13 | `anoSafra` | string | - | Ano-safra pecuário (ex.: "2024/2025"; ciclo provável jul-jun). String. |
| 14 | `amount` | number(double) | - | Quantidade (cabeças). Em DTOs de estoque/balanço/rebanho médio e double (médias/saldos). |
| 15 | `gender` | string | - | Sexo (código). |

#### 1.3.5 `GET /api-metryx/saldo-inical-pecuario`

- **operationId:** `getSaldoInicialPecuario` | **Domínio:** Pecuário realizado
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxSaldoInicialPecuarioDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Saldo inicial do rebanho por fazenda/retiro/categoria (path com erro de digitação "inical" na própria API).
- **Uso no ETL atual:** NÃO USADO. Valioso: âncora de saldo para validar/reconstruir o estoque (hoje o saldo é só a soma acumulada do balanço).

DTO `ApiMetryxSaldoInicialPecuarioDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customer` | string | - | Nome do cliente Metryx. |
| 3 | `idFarm` | string | - | ID da fazenda (string; usado como chave da fazenda em todo o ecossistema). |
| 4 | `farmName` | string | - | Nome da fazenda. |
| 5 | `idRetiro` | string | - | ID do retiro (subdivisão operacional/geográfica da fazenda). |
| 6 | `retiroName` | string | - | Nome do retiro. |
| 7 | `owner` | string | - | Proprietário dos animais (pode diferir do cliente: parceria, gado de terceiros). |
| 8 | `date` | string | - | Data do evento/lançamento (string). Realizado: "YYYY-MM-DD" (o BI faz TO_DATE(date,'YYYY-MM-DD')); planejamento: "MM/YY" (o BI faz to_date(date,'MM/YY')). Confirmar por endpoint. |
| 9 | `uuidCategory` | string | - | UUID da categoria animal. |
| 10 | `category` | string | - | Nome da categoria animal (ex.: bezerro, novilha, vaca, boi). |
| 11 | `harvest` | string | - | Safra/geração do lote de animais (interpretação: safra de nascimento). String. |
| 12 | `anoSafra` | string | - | Ano-safra pecuário (ex.: "2024/2025"; ciclo provável jul-jun). String. |
| 13 | `amount` | integer(int64) | - | Quantidade (cabeças). Em DTOs de estoque/balanço/rebanho médio e double (médias/saldos). |
| 14 | `gender` | string | - | Sexo (código). |

#### 1.3.6 `GET /api-metryx/nascimento-pecuario`

- **operationId:** `getBirths` | **Domínio:** Pecuário realizado
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxLiBirthDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Nascimentos registrados.
- **Uso no ETL atual:** USADO: get_nascimentos (fNascimento) -> stg_nascimentos.

DTO `ApiMetryxLiBirthDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customer` | string | - | Nome do cliente Metryx. |
| 3 | `idFarm` | string | - | ID da fazenda (string; usado como chave da fazenda em todo o ecossistema). |
| 4 | `farmName` | string | - | Nome da fazenda. |
| 5 | `idRetiro` | string | - | ID do retiro (subdivisão operacional/geográfica da fazenda). |
| 6 | `retiroName` | string | - | Nome do retiro. |
| 7 | `owner` | string | - | Proprietário dos animais (pode diferir do cliente: parceria, gado de terceiros). |
| 8 | `date` | string | - | Data do evento/lançamento (string). Realizado: "YYYY-MM-DD" (o BI faz TO_DATE(date,'YYYY-MM-DD')); planejamento: "MM/YY" (o BI faz to_date(date,'MM/YY')). Confirmar por endpoint. |
| 9 | `anoSafra` | string | - | Ano-safra pecuário (ex.: "2024/2025"; ciclo provável jul-jun). String. |
| 10 | `idCategory` | string | - | ID da categoria animal. |
| 11 | `category` | string | - | Nome da categoria animal (ex.: bezerro, novilha, vaca, boi). |
| 12 | `harvest` | string | - | Safra/geração do lote de animais (interpretação: safra de nascimento). String. |
| 13 | `amount` | integer(int64) | - | Quantidade (cabeças). Em DTOs de estoque/balanço/rebanho médio e double (médias/saldos). |
| 14 | `gender` | string | - | Sexo (código). |

#### 1.3.7 `GET /api-metryx/desmames-pecuario`

- **operationId:** `getDesmamesPecuario` | **Domínio:** Pecuário realizado
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxDesmamesPecuariosDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Desmames (mudança de categoria de bezerro mamando para desmamado, com peso e valor/kg).
- **Uso no ETL atual:** USADO: get_desmames (fDesmame) -> stg_desmames.

DTO `ApiMetryxDesmamesPecuariosDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customer` | string | - | Nome do cliente Metryx. |
| 3 | `idFarm` | string | - | ID da fazenda (string; usado como chave da fazenda em todo o ecossistema). |
| 4 | `farmName` | string | - | Nome da fazenda. |
| 5 | `idRetiro` | string | - | ID do retiro (subdivisão operacional/geográfica da fazenda). |
| 6 | `retiroName` | string | - | Nome do retiro. |
| 7 | `owner` | string | - | Proprietário dos animais (pode diferir do cliente: parceria, gado de terceiros). |
| 8 | `anoSafra` | string | - | Ano-safra pecuário (ex.: "2024/2025"; ciclo provável jul-jun). String. |
| 9 | `date` | string | - | Data do evento/lançamento (string). Realizado: "YYYY-MM-DD" (o BI faz TO_DATE(date,'YYYY-MM-DD')); planejamento: "MM/YY" (o BI faz to_date(date,'MM/YY')). Confirmar por endpoint. |
| 10 | `oldCategory` | string | - | Categoria antes do desmame. |
| 11 | `oldCategoryId` | string | - | ID da categoria antes do desmame. |
| 12 | `birthDate` | string | - | Data de nascimento do lote desmamado. String. |
| 13 | `harvest` | string | - | Safra/geração do lote de animais (interpretação: safra de nascimento). String. |
| 14 | `newCategory` | string | - | Categoria após o desmame. |
| 15 | `newCategoryId` | string | - | ID da categoria após o desmame. |
| 16 | `amount` | integer(int64) | - | Quantidade (cabeças). Em DTOs de estoque/balanço/rebanho médio e double (médias/saldos). |
| 17 | `weight` | integer(int64) | - | Peso (kg) - médio por cabeça no contexto do DTO. |
| 18 | `valueWeight` | integer(int64) | - | Valor por kg (R$/kg). |
| 19 | `gender` | string | - | Sexo (código). |

#### 1.3.8 `GET /api-metryx/morte-pecuario`

- **operationId:** `getDeaths` | **Domínio:** Pecuário realizado
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxDeathsDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Mortes (com causa, local, peso).
- **Uso no ETL atual:** USADO: get_morte (fMortes) -> stg_mortes.

DTO `ApiMetryxDeathsDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customer` | string | - | Nome do cliente Metryx. |
| 3 | `idFarm` | string | - | ID da fazenda (string; usado como chave da fazenda em todo o ecossistema). |
| 4 | `farmName` | string | - | Nome da fazenda. |
| 5 | `idRetiro` | string | - | ID do retiro (subdivisão operacional/geográfica da fazenda). |
| 6 | `retiroName` | string | - | Nome do retiro. |
| 7 | `owner` | string | - | Proprietário dos animais (pode diferir do cliente: parceria, gado de terceiros). |
| 8 | `date` | string | - | Data do evento/lançamento (string). Realizado: "YYYY-MM-DD" (o BI faz TO_DATE(date,'YYYY-MM-DD')); planejamento: "MM/YY" (o BI faz to_date(date,'MM/YY')). Confirmar por endpoint. |
| 9 | `anoSafra` | string | - | Ano-safra pecuário (ex.: "2024/2025"; ciclo provável jul-jun). String. |
| 10 | `enumGroup` | string | - | Grupo da categoria (código enum). |
| 11 | `nameGroup` | string | - | Grupo da categoria (nome). |
| 12 | `enumGeneration` | string | - | Geração (código enum). |
| 13 | `nameGeneration` | string | - | Geração (nome). |
| 14 | `era` | string | - | Era (faixa de nascimento) do lote. |
| 15 | `category` | string | - | Nome da categoria animal (ex.: bezerro, novilha, vaca, boi). |
| 16 | `categoryId` | string | - | ID da categoria animal (string/UUID). |
| 17 | `cause` | string | - | Causa da morte. |
| 18 | `harvest` | string | - | Safra/geração do lote de animais (interpretação: safra de nascimento). String. |
| 19 | `birth` | string | - | Nascimento/era do lote (ano ou mes-ano de nascimento; interpretação). String. |
| 20 | `amount` | number | - | Quantidade (cabeças). Em DTOs de estoque/balanço/rebanho médio e double (médias/saldos). |
| 21 | `averageWeight` | number | - | Peso médio por cabeça (kg). |
| 22 | `totalWeight` | number | - | Peso total (kg). |
| 23 | `locale` | string | - | Local da ocorrência (o BI mapeia como "pasto"). |
| 24 | `gender` | string | - | Sexo (código). |
| 25 | `genderName` | string | - | Sexo (descrição). |
| 26 | `notes` | string | - | Observações livres. |

#### 1.3.9 `GET /api-metryx/venda-pecuario`

- **operationId:** `getSale` | **Domínio:** Pecuário realizado
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxLiSaleDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Vendas de animais (abate e em pé), com pesos, preços e faturamento.
- **Uso no ETL atual:** USADO: get_vendas (fVendas) -> stg_vendas (+ dump do JSON bruto em arquivo texto local).

DTO `ApiMetryxLiSaleDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customer` | string | - | Nome do cliente Metryx. |
| 3 | `idFarm` | string | - | ID da fazenda (string; usado como chave da fazenda em todo o ecossistema). |
| 4 | `farmName` | string | - | Nome da fazenda. |
| 5 | `idRetiro` | string | - | ID do retiro (subdivisão operacional/geográfica da fazenda). |
| 6 | `retiroName` | string | - | Nome do retiro. |
| 7 | `owner` | string | - | Proprietário dos animais (pode diferir do cliente: parceria, gado de terceiros). |
| 8 | `date` | string | - | Data do evento/lançamento (string). Realizado: "YYYY-MM-DD" (o BI faz TO_DATE(date,'YYYY-MM-DD')); planejamento: "MM/YY" (o BI faz to_date(date,'MM/YY')). Confirmar por endpoint. |
| 9 | `anoSafra` | string | - | Ano-safra pecuário (ex.: "2024/2025"; ciclo provável jul-jun). String. |
| 10 | `harvest` | string | - | Safra/geração do lote de animais (interpretação: safra de nascimento). String. |
| 11 | `birth` | string | - | Nascimento/era do lote (ano ou mes-ano de nascimento; interpretação). String. |
| 12 | `gender` | string | - | Sexo (código). |
| 13 | `client` | string | - | Comprador (cliente da venda). |
| 14 | `category` | string | - | Nome da categoria animal (ex.: bezerro, novilha, vaca, boi). |
| 15 | `categoryId` | string | - | ID da categoria animal (string/UUID). |
| 16 | `amount` | integer(int64) | - | Quantidade (cabeças). Em DTOs de estoque/balanço/rebanho médio e double (médias/saldos). |
| 17 | `liveWeightAVG` | integer(int64) | - | Peso vivo médio por cabeça (kg). |
| 18 | `weightTotal` | integer(int64) | - | Peso vivo total da operação (kg). |
| 19 | `deadArrobaAvg` | integer(int64) | - | Arrobas de carcaça médias por cabeça (@) - preenchido em venda para abate. |
| 20 | `deadWeightAvg` | integer(int64) | - | Peso de carcaça (morto) médio por cabeça (kg). |
| 21 | `valueWeight` | integer(int64) | - | Valor por kg (R$/kg). |
| 22 | `valueArroba` | integer(int64) | - | Valor por arroba (R$/@). |
| 23 | `totalFaturamento` | integer(int64) | - | Valor total da operação (R$). |
| 24 | `tipo` | string | - | Tipo da operação (ex.: abate / em pé). Em venda realizada o BI separa abate x em pé por deadArrobaAvg nulo/não nulo. |
| 25 | `additions` | integer(int64) | - | Acréscimos (R$). |
| 26 | `discounts` | integer(int64) | - | Descontos (R$). |

#### 1.3.10 `GET /api-metryx/compra-pecuario`

- **operationId:** `getBuy` | **Domínio:** Pecuário realizado
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxLiBuyDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Compras de animais.
- **Uso no ETL atual:** USADO: get_compras (fCompras) -> stg_compras.

DTO `ApiMetryxLiBuyDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customer` | string | - | Nome do cliente Metryx. |
| 3 | `idFarm` | string | - | ID da fazenda (string; usado como chave da fazenda em todo o ecossistema). |
| 4 | `farmName` | string | - | Nome da fazenda. |
| 5 | `idRetiro` | string | - | ID do retiro (subdivisão operacional/geográfica da fazenda). |
| 6 | `retiroName` | string | - | Nome do retiro. |
| 7 | `owner` | string | - | Proprietário dos animais (pode diferir do cliente: parceria, gado de terceiros). |
| 8 | `date` | string | - | Data do evento/lançamento (string). Realizado: "YYYY-MM-DD" (o BI faz TO_DATE(date,'YYYY-MM-DD')); planejamento: "MM/YY" (o BI faz to_date(date,'MM/YY')). Confirmar por endpoint. |
| 9 | `anoSafra` | string | - | Ano-safra pecuário (ex.: "2024/2025"; ciclo provável jul-jun). String. |
| 10 | `harvest` | string | - | Safra/geração do lote de animais (interpretação: safra de nascimento). String. |
| 11 | `birth` | string | - | Nascimento/era do lote (ano ou mes-ano de nascimento; interpretação). String. |
| 12 | `gender` | string | - | Sexo (código). |
| 13 | `provider` | string | - | Fornecedor (vendedor na compra). |
| 14 | `category` | string | - | Nome da categoria animal (ex.: bezerro, novilha, vaca, boi). |
| 15 | `categoryId` | string | - | ID da categoria animal (string/UUID). |
| 16 | `amount` | integer(int64) | - | Quantidade (cabeças). Em DTOs de estoque/balanço/rebanho médio e double (médias/saldos). |
| 17 | `weightTotal` | integer(int64) | - | Peso vivo total da operação (kg). |
| 18 | `averageValue` | integer(int64) | - | Valor médio por cabeça (R$/cab). |
| 19 | `valueWeight` | integer(int64) | - | Valor por kg (R$/kg). |
| 20 | `valueArroba` | integer(int64) | - | Valor por arroba (R$/@). |
| 21 | `totalFaturamento` | integer(int64) | - | Valor total da operação (R$). |
| 22 | `tipo` | string | - | Tipo da operação (ex.: abate / em pé). Em venda realizada o BI separa abate x em pé por deadArrobaAvg nulo/não nulo. |
| 23 | `additions` | integer(int64) | - | Acréscimos (R$). |
| 24 | `discounts` | integer(int64) | - | Descontos (R$). |

#### 1.3.11 `GET /api-metryx/mudanca-categoria-pecuario`

- **operationId:** `getLiCategoryChange` | **Domínio:** Pecuário realizado
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxLiCategoryChangeDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Mudanças/evoluções de categoria (origem -> destino).
- **Uso no ETL atual:** USADO SÓ EM TRANSFORMAÇÕES ÓRFÃS: get_mudanca_cat (não está no job e lê arquivo local, ignorando a API) e get_transferencias (não está no job; usa este endpoint por engano).

DTO `ApiMetryxLiCategoryChangeDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customer` | string | - | Nome do cliente Metryx. |
| 3 | `idFarm` | string | - | ID da fazenda (string; usado como chave da fazenda em todo o ecossistema). |
| 4 | `farmName` | string | - | Nome da fazenda. |
| 5 | `idRetiro` | string | - | ID do retiro (subdivisão operacional/geográfica da fazenda). |
| 6 | `retiroName` | string | - | Nome do retiro. |
| 7 | `owner` | string | - | Proprietário dos animais (pode diferir do cliente: parceria, gado de terceiros). |
| 8 | `date` | string | - | Data do evento/lançamento (string). Realizado: "YYYY-MM-DD" (o BI faz TO_DATE(date,'YYYY-MM-DD')); planejamento: "MM/YY" (o BI faz to_date(date,'MM/YY')). Confirmar por endpoint. |
| 9 | `uuidCategoryOrigin` | string | - | UUID da categoria de origem. |
| 10 | `categoryOrigin` | string | - | Categoria de origem. |
| 11 | `uuidCategoryDestiny` | string | - | UUID da categoria de destino. |
| 12 | `categoryDestiny` | string | - | Categoria de destino. |
| 13 | `harvest` | string | - | Safra/geração do lote de animais (interpretação: safra de nascimento). String. |
| 14 | `anoSafra` | string | - | Ano-safra pecuário (ex.: "2024/2025"; ciclo provável jul-jun). String. |
| 15 | `amount` | integer(int64) | - | Quantidade (cabeças). Em DTOs de estoque/balanço/rebanho médio e double (médias/saldos). |
| 16 | `gender` | string | - | Sexo (código). |

#### 1.3.12 `GET /api-metryx/transferencia-animal-pecuario`

- **operationId:** `getAnimalTransfer` | **Domínio:** Pecuário realizado
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxLiAnimalTransferDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Transferências de animais entre fazendas/retiros (origem/destino, com valores).
- **Uso no ETL atual:** NÃO USADO (get_transferencias aponta para o endpoint errado). Valioso: fecha o balanço por fazenda/retiro.

DTO `ApiMetryxLiAnimalTransferDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `id` | string | - | Identificador do registro. |
| 2 | `itemId` | string | - | Identificador do item dentro do registro (transferencia com varios itens). |
| 3 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 4 | `customer` | string | - | Nome do cliente Metryx. |
| 5 | `idFarmOrigin` | string | - | Fazenda de origem. |
| 6 | `farmNameOrigin` | string | - | Nome da fazenda de origem. |
| 7 | `idRetiroOrigin` | string | - | Retiro de origem. |
| 8 | `retiroNameOrigin` | string | - | Nome do retiro de origem. |
| 9 | `idFarmDestiny` | string | - | Fazenda de destino. |
| 10 | `farmNameDestiny` | string | - | Nome da fazenda de destino. |
| 11 | `idRetiroDestiny` | string | - | Retiro de destino. |
| 12 | `retiroNameDestiny` | string | - | Nome do retiro de destino. |
| 13 | `owner` | string | - | Proprietário dos animais (pode diferir do cliente: parceria, gado de terceiros). |
| 14 | `date` | string | - | Data do evento/lançamento (string). Realizado: "YYYY-MM-DD" (o BI faz TO_DATE(date,'YYYY-MM-DD')); planejamento: "MM/YY" (o BI faz to_date(date,'MM/YY')). Confirmar por endpoint. |
| 15 | `anoSafra` | string | - | Ano-safra pecuário (ex.: "2024/2025"; ciclo provável jul-jun). String. |
| 16 | `harvest` | string | - | Safra/geração do lote de animais (interpretação: safra de nascimento). String. |
| 17 | `birth` | string | - | Nascimento/era do lote (ano ou mes-ano de nascimento; interpretação). String. |
| 18 | `gender` | string | - | Sexo (código). |
| 19 | `category` | string | - | Nome da categoria animal (ex.: bezerro, novilha, vaca, boi). |
| 20 | `categoryId` | string | - | ID da categoria animal (string/UUID). |
| 21 | `amount` | integer(int64) | - | Quantidade (cabeças). Em DTOs de estoque/balanço/rebanho médio e double (médias/saldos). |
| 22 | `weightTotal` | integer(int64) | - | Peso vivo total da operação (kg). |
| 23 | `averageValue` | integer(int64) | - | Valor médio por cabeça (R$/cab). |
| 24 | `valueWeight` | integer(int64) | - | Valor por kg (R$/kg). |
| 25 | `valueArroba` | integer(int64) | - | Valor por arroba (R$/@). |
| 26 | `totalFaturamento` | integer(int64) | - | Valor total da operação (R$). |

#### 1.3.13 `GET /api-metryx/rebanho-medio-pecuario`

- **operationId:** `getAvgRebanho` | **Domínio:** Pecuário realizado
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxLiAvgRebanhoDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Rebanho médio mensal realizado por categoria (amount double = média de cabeças; weight = peso médio).
- **Uso no ETL atual:** USADO: get_rebanho_medio (fRebanhoMedio) -> stg_rebanho_medio. Duplicado: get_rebanhomedio (órfão) -> stg_rebanhomedio.

DTO `ApiMetryxLiAvgRebanhoDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customer` | string | - | Nome do cliente Metryx. |
| 3 | `idFarm` | string | - | ID da fazenda (string; usado como chave da fazenda em todo o ecossistema). |
| 4 | `farmName` | string | - | Nome da fazenda. |
| 5 | `idRetiro` | string | - | ID do retiro (subdivisão operacional/geográfica da fazenda). |
| 6 | `retiroName` | string | - | Nome do retiro. |
| 7 | `owner` | string | - | Proprietário dos animais (pode diferir do cliente: parceria, gado de terceiros). |
| 8 | `anoSafra` | string | - | Ano-safra pecuário (ex.: "2024/2025"; ciclo provável jul-jun). String. |
| 9 | `idCategory` | string | - | ID da categoria animal. |
| 10 | `category` | string | - | Nome da categoria animal (ex.: bezerro, novilha, vaca, boi). |
| 11 | `amount` | number(double) | - | Quantidade (cabeças). Em DTOs de estoque/balanço/rebanho médio e double (médias/saldos). |
| 12 | `month` | string | - | Mês de referência (int64 no planejamento; string no rebanho médio realizado). |
| 13 | `weight` | number(double) | - | Peso (kg) - médio por cabeça no contexto do DTO. |
| 14 | `groupCategory` | string | - | Grupo da categoria. |
| 15 | `gender` | string | - | Sexo (código). |

#### 1.3.14 `GET /api-metryx/venda-mensal-planejamento`

- **operationId:** `getPlSaleMonthly` | **Domínio:** Planejamento
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxPlSaleMonthlyDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Vendas planejadas por mês/categoria/versão (orçamento).
- **Uso no ETL atual:** USADO: get_prevvendas (fMetas Vendas) -> stg_vendasasprevisto.

DTO `ApiMetryxPlSaleMonthlyDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customerName` | string | - | Nome do cliente Metryx. |
| 3 | `idFarm` | string | - | ID da fazenda (string; usado como chave da fazenda em todo o ecossistema). |
| 4 | `farmName` | string | - | Nome da fazenda. |
| 5 | `idRetiro` | string | - | ID do retiro (subdivisão operacional/geográfica da fazenda). |
| 6 | `retiroName` | string | - | Nome do retiro. |
| 7 | `idOwner` | string | - | ID do proprietário dos animais. |
| 8 | `ownerName` | string | - | Nome do proprietário dos animais. |
| 9 | `idPlHerdType` | string | - | ID do tipo de rebanho do planejamento (ex.: cria/recria/engorda - interpretação). |
| 10 | `plHerdTypeName` | string | - | Nome do tipo de rebanho do planejamento. |
| 11 | `idCurrency` | integer(int64) | - | ID da moeda. |
| 12 | `currencyCode` | string | - | Código da moeda (ex.: BRL). |
| 13 | `currencyName` | string | - | Nome da moeda. |
| 14 | `plVersionCode` | integer(int64) | - | Código da versão/cenário do planejamento. ESSENCIAL para não somar versões diferentes. |
| 15 | `plVersionName` | string | - | Nome da versão/cenário do planejamento. |
| 16 | `month` | integer(int64) | - | Mês de referência (int64 no planejamento; string no rebanho médio realizado). |
| 17 | `date` | string | - | Data do evento/lançamento (string). Realizado: "YYYY-MM-DD" (o BI faz TO_DATE(date,'YYYY-MM-DD')); planejamento: "MM/YY" (o BI faz to_date(date,'MM/YY')). Confirmar por endpoint. |
| 18 | `harvest` | string | - | Safra/geração do lote de animais (interpretação: safra de nascimento). String. |
| 19 | `anoSafra` | string | - | Ano-safra pecuário (ex.: "2024/2025"; ciclo provável jul-jun). String. |
| 20 | `idCategory` | integer(int64) | - | ID da categoria animal. |
| 21 | `categoryName` | string | - | Nome da categoria (planejamento). |
| 22 | `reproductiveOption` | string | - | Opção/estado reprodutivo (interpretação: prenhe/vazia/etc.). |
| 23 | `idAnimalGroup` | integer(int64) | - | ID do grupo de animais do planejamento. |
| 24 | `animalGroupName` | string | - | Nome do grupo de animais. |
| 25 | `age` | string | - | Idade/faixa etária (planejamento). |
| 26 | `gender` | string | - | Sexo (código). |
| 27 | `type` | string | - | Tipo (semântica depende do DTO: tipo de venda, tipo de movimento, receita/despesa...). |
| 28 | `amount` | integer(int64) | - | Quantidade (cabeças). Em DTOs de estoque/balanço/rebanho médio e double (médias/saldos). |
| 29 | `weight` | number | - | Peso (kg) - médio por cabeça no contexto do DTO. |
| 30 | `yield` | number | - | Rendimento de carcaça (%). |
| 31 | `arrobaValue` | number | - | Preço por arroba planejado (R$/@). |
| 32 | `arrobaWeight` | number | - | Peso em arrobas por cabeça planejado (@). |
| 33 | `value` | number | - | Valor unitário/por cabeça (R$) ou valor do lançamento (conforme DTO). |
| 34 | `totalValue` | number | - | Valor total (R$). |

#### 1.3.15 `GET /api-metryx/compra-mensal-planejamento`

- **operationId:** `getMonthlyBuy` | **Domínio:** Planejamento
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxPlBuyingMonthlyDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Compras planejadas por mês/categoria/versão.
- **Uso no ETL atual:** USADO: get_prevcompras (fMetas Compras) -> stg_comprasprevisto.

DTO `ApiMetryxPlBuyingMonthlyDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customerName` | string | - | Nome do cliente Metryx. |
| 3 | `idFarm` | string | - | ID da fazenda (string; usado como chave da fazenda em todo o ecossistema). |
| 4 | `farmName` | string | - | Nome da fazenda. |
| 5 | `idRetiro` | string | - | ID do retiro (subdivisão operacional/geográfica da fazenda). |
| 6 | `retiroName` | string | - | Nome do retiro. |
| 7 | `idOwner` | string | - | ID do proprietário dos animais. |
| 8 | `ownerName` | string | - | Nome do proprietário dos animais. |
| 9 | `idPlHerdType` | string | - | ID do tipo de rebanho do planejamento (ex.: cria/recria/engorda - interpretação). |
| 10 | `plHerdTypeName` | string | - | Nome do tipo de rebanho do planejamento. |
| 11 | `idCurrency` | integer(int64) | - | ID da moeda. |
| 12 | `currencyCode` | string | - | Código da moeda (ex.: BRL). |
| 13 | `currencyName` | string | - | Nome da moeda. |
| 14 | `plVersionCode` | integer(int64) | - | Código da versão/cenário do planejamento. ESSENCIAL para não somar versões diferentes. |
| 15 | `plVersionName` | string | - | Nome da versão/cenário do planejamento. |
| 16 | `month` | integer(int64) | - | Mês de referência (int64 no planejamento; string no rebanho médio realizado). |
| 17 | `date` | string | - | Data do evento/lançamento (string). Realizado: "YYYY-MM-DD" (o BI faz TO_DATE(date,'YYYY-MM-DD')); planejamento: "MM/YY" (o BI faz to_date(date,'MM/YY')). Confirmar por endpoint. |
| 18 | `harvest` | string | - | Safra/geração do lote de animais (interpretação: safra de nascimento). String. |
| 19 | `anoSafra` | string | - | Ano-safra pecuário (ex.: "2024/2025"; ciclo provável jul-jun). String. |
| 20 | `idCategory` | integer(int64) | - | ID da categoria animal. |
| 21 | `categoryName` | string | - | Nome da categoria (planejamento). |
| 22 | `reproductiveOption` | string | - | Opção/estado reprodutivo (interpretação: prenhe/vazia/etc.). |
| 23 | `idAnimalGroup` | integer(int64) | - | ID do grupo de animais do planejamento. |
| 24 | `animalGroupName` | string | - | Nome do grupo de animais. |
| 25 | `age` | string | - | Idade/faixa etária (planejamento). |
| 26 | `gender` | string | - | Sexo (código). |
| 27 | `amount` | integer(int64) | - | Quantidade (cabeças). Em DTOs de estoque/balanço/rebanho médio e double (médias/saldos). |
| 28 | `weight` | number | - | Peso (kg) - médio por cabeça no contexto do DTO. |
| 29 | `arrobaValue` | number | - | Preço por arroba planejado (R$/@). |
| 30 | `arrobaWeight` | number | - | Peso em arrobas por cabeça planejado (@). |
| 31 | `value` | number | - | Valor unitário/por cabeça (R$) ou valor do lançamento (conforme DTO). |
| 32 | `totalValue` | number | - | Valor total (R$). |

#### 1.3.16 `GET /api-metryx/nascimento-mensal-planejamento`

- **operationId:** `getPlBirthMonthly` | **Domínio:** Planejamento
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxPlBirthMonthlyDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Nascimentos planejados por mês.
- **Uso no ETL atual:** USADO: get_prevnascimentos (fMetas Nascimento) -> stg_nascimentosprevisto.

DTO `ApiMetryxPlBirthMonthlyDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customerName` | string | - | Nome do cliente Metryx. |
| 3 | `idFarm` | string | - | ID da fazenda (string; usado como chave da fazenda em todo o ecossistema). |
| 4 | `farmName` | string | - | Nome da fazenda. |
| 5 | `idRetiro` | string | - | ID do retiro (subdivisão operacional/geográfica da fazenda). |
| 6 | `retiroName` | string | - | Nome do retiro. |
| 7 | `idOwner` | string | - | ID do proprietário dos animais. |
| 8 | `ownerName` | string | - | Nome do proprietário dos animais. |
| 9 | `idPlHerdType` | string | - | ID do tipo de rebanho do planejamento (ex.: cria/recria/engorda - interpretação). |
| 10 | `plHerdTypeName` | string | - | Nome do tipo de rebanho do planejamento. |
| 11 | `idCurrency` | integer(int64) | - | ID da moeda. |
| 12 | `currencyCode` | string | - | Código da moeda (ex.: BRL). |
| 13 | `currencyName` | string | - | Nome da moeda. |
| 14 | `plVersionCode` | integer(int64) | - | Código da versão/cenário do planejamento. ESSENCIAL para não somar versões diferentes. |
| 15 | `plVersionName` | string | - | Nome da versão/cenário do planejamento. |
| 16 | `month` | integer(int64) | - | Mês de referência (int64 no planejamento; string no rebanho médio realizado). |
| 17 | `date` | string | - | Data do evento/lançamento (string). Realizado: "YYYY-MM-DD" (o BI faz TO_DATE(date,'YYYY-MM-DD')); planejamento: "MM/YY" (o BI faz to_date(date,'MM/YY')). Confirmar por endpoint. |
| 18 | `harvest` | string | - | Safra/geração do lote de animais (interpretação: safra de nascimento). String. |
| 19 | `anoSafra` | string | - | Ano-safra pecuário (ex.: "2024/2025"; ciclo provável jul-jun). String. |
| 20 | `idCategory` | integer(int64) | - | ID da categoria animal. |
| 21 | `categoryName` | string | - | Nome da categoria (planejamento). |
| 22 | `idAnimalGroup` | integer(int64) | - | ID do grupo de animais do planejamento. |
| 23 | `animalGroupName` | string | - | Nome do grupo de animais. |
| 24 | `age` | string | - | Idade/faixa etária (planejamento). |
| 25 | `gender` | string | - | Sexo (código). |
| 26 | `amount` | integer(int64) | - | Quantidade (cabeças). Em DTOs de estoque/balanço/rebanho médio e double (médias/saldos). |

#### 1.3.17 `GET /api-metryx/morte-mensal-planejamento`

- **operationId:** `getPlDeathMonthly` | **Domínio:** Planejamento
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxPlDeathMonthlyDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Mortes planejadas por mês.
- **Uso no ETL atual:** USADO: get_prevmortes (fMetas Mortes) -> stg_mortesprevisto.

DTO `ApiMetryxPlDeathMonthlyDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customerName` | string | - | Nome do cliente Metryx. |
| 3 | `idFarm` | string | - | ID da fazenda (string; usado como chave da fazenda em todo o ecossistema). |
| 4 | `farmName` | string | - | Nome da fazenda. |
| 5 | `idRetiro` | string | - | ID do retiro (subdivisão operacional/geográfica da fazenda). |
| 6 | `retiroName` | string | - | Nome do retiro. |
| 7 | `idOwner` | string | - | ID do proprietário dos animais. |
| 8 | `ownerName` | string | - | Nome do proprietário dos animais. |
| 9 | `idPlHerdType` | string | - | ID do tipo de rebanho do planejamento (ex.: cria/recria/engorda - interpretação). |
| 10 | `plHerdTypeName` | string | - | Nome do tipo de rebanho do planejamento. |
| 11 | `idCurrency` | integer(int64) | - | ID da moeda. |
| 12 | `currencyCode` | string | - | Código da moeda (ex.: BRL). |
| 13 | `currencyName` | string | - | Nome da moeda. |
| 14 | `plVersionCode` | integer(int64) | - | Código da versão/cenário do planejamento. ESSENCIAL para não somar versões diferentes. |
| 15 | `plVersionName` | string | - | Nome da versão/cenário do planejamento. |
| 16 | `month` | integer(int64) | - | Mês de referência (int64 no planejamento; string no rebanho médio realizado). |
| 17 | `date` | string | - | Data do evento/lançamento (string). Realizado: "YYYY-MM-DD" (o BI faz TO_DATE(date,'YYYY-MM-DD')); planejamento: "MM/YY" (o BI faz to_date(date,'MM/YY')). Confirmar por endpoint. |
| 18 | `harvest` | string | - | Safra/geração do lote de animais (interpretação: safra de nascimento). String. |
| 19 | `anoSafra` | string | - | Ano-safra pecuário (ex.: "2024/2025"; ciclo provável jul-jun). String. |
| 20 | `idCategory` | integer(int64) | - | ID da categoria animal. |
| 21 | `categoryName` | string | - | Nome da categoria (planejamento). |
| 22 | `reproductiveOption` | string | - | Opção/estado reprodutivo (interpretação: prenhe/vazia/etc.). |
| 23 | `idAnimalGroup` | integer(int64) | - | ID do grupo de animais do planejamento. |
| 24 | `animalGroupName` | string | - | Nome do grupo de animais. |
| 25 | `age` | string | - | Idade/faixa etária (planejamento). |
| 26 | `gender` | string | - | Sexo (código). |
| 27 | `amount` | integer(int64) | - | Quantidade (cabeças). Em DTOs de estoque/balanço/rebanho médio e double (médias/saldos). |

#### 1.3.18 `GET /api-metryx/desmame-mensal-planejamento`

- **operationId:** `getPlWeaningMonthly` | **Domínio:** Planejamento
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxPlWeaningMonthlyDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Desmames planejados por mês (categoria/grupo de origem -> destino).
- **Uso no ETL atual:** USADO: get_prevdesmame (fMetas Desmame) -> stg_desmameprevisto (não consumida pelo BI atual).

DTO `ApiMetryxPlWeaningMonthlyDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customerName` | string | - | Nome do cliente Metryx. |
| 3 | `idFarm` | string | - | ID da fazenda (string; usado como chave da fazenda em todo o ecossistema). |
| 4 | `farmName` | string | - | Nome da fazenda. |
| 5 | `idRetiro` | string | - | ID do retiro (subdivisão operacional/geográfica da fazenda). |
| 6 | `retiroName` | string | - | Nome do retiro. |
| 7 | `idOwner` | string | - | ID do proprietário dos animais. |
| 8 | `ownerName` | string | - | Nome do proprietário dos animais. |
| 9 | `idPlHerdType` | string | - | ID do tipo de rebanho do planejamento (ex.: cria/recria/engorda - interpretação). |
| 10 | `plHerdTypeName` | string | - | Nome do tipo de rebanho do planejamento. |
| 11 | `idCurrency` | integer(int64) | - | ID da moeda. |
| 12 | `currencyCode` | string | - | Código da moeda (ex.: BRL). |
| 13 | `currencyName` | string | - | Nome da moeda. |
| 14 | `plVersionCode` | integer(int64) | - | Código da versão/cenário do planejamento. ESSENCIAL para não somar versões diferentes. |
| 15 | `plVersionName` | string | - | Nome da versão/cenário do planejamento. |
| 16 | `month` | integer(int64) | - | Mês de referência (int64 no planejamento; string no rebanho médio realizado). |
| 17 | `date` | string | - | Data do evento/lançamento (string). Realizado: "YYYY-MM-DD" (o BI faz TO_DATE(date,'YYYY-MM-DD')); planejamento: "MM/YY" (o BI faz to_date(date,'MM/YY')). Confirmar por endpoint. |
| 18 | `harvest` | string | - | Safra/geração do lote de animais (interpretação: safra de nascimento). String. |
| 19 | `anoSafra` | string | - | Ano-safra pecuário (ex.: "2024/2025"; ciclo provável jul-jun). String. |
| 20 | `oldCategoryId` | integer(int64) | - | ID da categoria antes do desmame. |
| 21 | `oldCategoryName` | string | - | Categoria de origem (antes do desmame). |
| 22 | `oldAnimalGroupId` | integer(int64) | - | Grupo de animais de origem (ID). |
| 23 | `oldAnimalGroupName` | string | - | Grupo de animais de origem. |
| 24 | `oldAge` | string | - | Idade de origem. |
| 25 | `oldGender` | string | - | Sexo de origem. |
| 26 | `newCategoryId` | integer(int64) | - | ID da categoria após o desmame. |
| 27 | `newCategoryName` | string | - | Categoria de destino (após desmame). |
| 28 | `newAnimalGroupId` | integer(int64) | - | Grupo de animais de destino (ID). |
| 29 | `newAnimalGroupName` | string | - | Grupo de animais de destino. |
| 30 | `newAge` | string | - | Idade de destino. |
| 31 | `newGender` | string | - | Sexo de destino. |
| 32 | `amount` | integer(int64) | - | Quantidade (cabeças). Em DTOs de estoque/balanço/rebanho médio e double (médias/saldos). |

#### 1.3.19 `GET /api-metryx/estoque-medio-mensal-planejamento`

- **operationId:** `getPlAverageStockMonthlies` | **Domínio:** Planejamento
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxPlAverageStockMonthlyDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Estoque (rebanho) médio mensal planejado, com o movimento de evolução de origem.
- **Uso no ETL atual:** USADO: get_prevrebanhomedio (fMetas Rebanho Médio) -> stg_rebanhomedioprevisto (não consumida pelo BI; o BI usa stg_rebanho_medio realizado em "fMetasRebanhoMedio").

DTO `ApiMetryxPlAverageStockMonthlyDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customerName` | string | - | Nome do cliente Metryx. |
| 3 | `idFarm` | string | - | ID da fazenda (string; usado como chave da fazenda em todo o ecossistema). |
| 4 | `farmName` | string | - | Nome da fazenda. |
| 5 | `idRetiro` | string | - | ID do retiro (subdivisão operacional/geográfica da fazenda). |
| 6 | `retiroName` | string | - | Nome do retiro. |
| 7 | `idOwner` | string | - | ID do proprietário dos animais. |
| 8 | `ownerName` | string | - | Nome do proprietário dos animais. |
| 9 | `idPlHerdType` | string | - | ID do tipo de rebanho do planejamento (ex.: cria/recria/engorda - interpretação). |
| 10 | `plHerdTypeName` | string | - | Nome do tipo de rebanho do planejamento. |
| 11 | `idCurrency` | integer(int64) | - | ID da moeda. |
| 12 | `currencyCode` | string | - | Código da moeda (ex.: BRL). |
| 13 | `currencyName` | string | - | Nome da moeda. |
| 14 | `plVersionCode` | integer(int64) | - | Código da versão/cenário do planejamento. ESSENCIAL para não somar versões diferentes. |
| 15 | `plVersionName` | string | - | Nome da versão/cenário do planejamento. |
| 16 | `month` | integer(int64) | - | Mês de referência (int64 no planejamento; string no rebanho médio realizado). |
| 17 | `date` | string | - | Data do evento/lançamento (string). Realizado: "YYYY-MM-DD" (o BI faz TO_DATE(date,'YYYY-MM-DD')); planejamento: "MM/YY" (o BI faz to_date(date,'MM/YY')). Confirmar por endpoint. |
| 18 | `harvest` | string | - | Safra/geração do lote de animais (interpretação: safra de nascimento). String. |
| 19 | `anoSafra` | string | - | Ano-safra pecuário (ex.: "2024/2025"; ciclo provável jul-jun). String. |
| 20 | `idCategory` | integer(int64) | - | ID da categoria animal. |
| 21 | `categoryName` | string | - | Nome da categoria (planejamento). |
| 22 | `reproductiveOption` | string | - | Opção/estado reprodutivo (interpretação: prenhe/vazia/etc.). |
| 23 | `idAnimalGroup` | integer(int64) | - | ID do grupo de animais do planejamento. |
| 24 | `animalGroupName` | string | - | Nome do grupo de animais. |
| 25 | `age` | string | - | Idade/faixa etária (planejamento). |
| 26 | `gender` | string | - | Sexo (código). |
| 27 | `idEvolution` | string | - | ID do movimento de evolução de rebanho que originou o estoque planejado. |
| 28 | `type` | string | - | Tipo (semântica depende do DTO: tipo de venda, tipo de movimento, receita/despesa...). |
| 29 | `originMovement` | string | - | Movimento de origem do estoque planejado (ex.: compra, nascimento, mudança). |
| 30 | `amount` | integer(int64) | - | Quantidade (cabeças). Em DTOs de estoque/balanço/rebanho médio e double (médias/saldos). |

#### 1.3.20 `GET /api-metryx/previsao-fluxo-caixa-planejamento`

- **operationId:** `getPlPrevisions` | **Domínio:** Planejamento financeiro
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxPlPrevisionDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Previsões de fluxo de caixa do planejamento (por centro/subcentro/classe, versão, projeto).
- **Uso no ETL atual:** NÃO USADO. Valioso: orçamento de caixa por versão (complementa previsao-financeiro).

DTO `ApiMetryxPlPrevisionDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customerName` | string | - | Nome do cliente Metryx. |
| 3 | `idFarm` | string | - | ID da fazenda (string; usado como chave da fazenda em todo o ecossistema). |
| 4 | `farmName` | string | - | Nome da fazenda. |
| 5 | `idCurrency` | integer(int64) | - | ID da moeda. |
| 6 | `currencyName` | string | - | Nome da moeda. |
| 7 | `plVersionCode` | integer(int64) | - | Código da versão/cenário do planejamento. ESSENCIAL para não somar versões diferentes. |
| 8 | `plVersionName` | string | - | Nome da versão/cenário do planejamento. |
| 9 | `typeActivity` | string | - | Tipo de atividade (pecuária/agricultura...). |
| 10 | `yearType` | string | - | Tipo de ano (civil x safra - interpretação). |
| 11 | `type` | string | - | Tipo (semântica depende do DTO: tipo de venda, tipo de movimento, receita/despesa...). |
| 12 | `cultivationName` | string | - | Cultura. |
| 13 | `idSubCenter` | string | - | ID do subcentro. |
| 14 | `subCenterName` | string | - | Subcentro. |
| 15 | `subCenterCode` | string | - | Código do subcentro. |
| 16 | `idCostCenter` | string | - | ID do centro de custo. |
| 17 | `costCenterName` | string | - | Centro de custo. |
| 18 | `costCenterCode` | string | - | Código do centro de custo. |
| 19 | `idClass` | string | - | ID da classe. |
| 20 | `className` | string | - | Classe (plano de contas). |
| 21 | `classCode` | string | - | Código da classe. |
| 22 | `date` | string | - | Data do evento/lançamento (string). Realizado: "YYYY-MM-DD" (o BI faz TO_DATE(date,'YYYY-MM-DD')); planejamento: "MM/YY" (o BI faz to_date(date,'MM/YY')). Confirmar por endpoint. |
| 23 | `harvest` | string | - | Safra/geração do lote de animais (interpretação: safra de nascimento). String. |
| 24 | `anoSafra` | string | - | Ano-safra pecuário (ex.: "2024/2025"; ciclo provável jul-jun). String. |
| 25 | `value` | number | - | Valor unitário/por cabeça (R$) ou valor do lançamento (conforme DTO). |
| 26 | `idClassificationAnalytic` | string | - | ID da classificação analítica. |
| 27 | `classificationAnalyticDescription` | string | - | Descrição da classificação analítica. |
| 28 | `classificationAnalyticDisbursement` | boolean | - | Indicador se a classificação é desembolso (string aqui; boolean no PlPrevision). |
| 29 | `plProjectName` | string | - | Projeto do planejamento. |

#### 1.3.21 `GET /api-metryx/lancamento-financeiro`

- **operationId:** `getLancamentoFinanceiro` | **Domínio:** Financeiro realizado
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxLancamentoFinanceiroDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Lançamentos financeiros (contas a pagar/receber e baixas) - base do DRE realizado.
- **Uso no ETL atual:** USADO: get_dre (fDre) -> stg_dre.

DTO `ApiMetryxLancamentoFinanceiroDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 2 | `customer` | string | - | Nome do cliente Metryx. |
| 3 | `idFarmFiscal` | string | - | ID da fazenda/unidade fiscal (emissora) do lançamento. |
| 4 | `farmFiscal` | string | - | Fazenda/unidade fiscal do lançamento. |
| 5 | `idfarmDestination` | string | - | ID da fazenda de destino/rateio do custo (sic: "idfarm" minúsculo). Usado como chave de fazenda no BI. |
| 6 | `farmDestination` | string | - | Fazenda de destino/rateio do custo. |
| 7 | `owner` | string | - | Proprietário dos animais (pode diferir do cliente: parceria, gado de terceiros). |
| 8 | `idFinancialEntrie` | string | - | ID do lançamento financeiro (sic "Entrie"). |
| 9 | `idPayment` | string | - | ID do pagamento/baixa (parcela). |
| 10 | `anoSafra` | string | - | Ano-safra pecuário (ex.: "2024/2025"; ciclo provável jul-jun). String. |
| 11 | `costCenter` | string | - | Centro de custo (base do mapeamento DRE no BI: custeio/CF/CV/desembolso). |
| 12 | `description` | string | - | Histórico/descrição do lançamento. |
| 13 | `code` | integer(int64) | - | Código do lançamento/conta (int64). |
| 14 | `classe` | string | - | Classe (plano de contas). |
| 15 | `subCenter` | string | - | Subcentro de custo. |
| 16 | `activity` | string | - | Atividade (ex.: pecuária, agricultura). |
| 17 | `clientProvider` | string | - | Cliente/fornecedor do lançamento. |
| 18 | `cpfCnpj` | string | - | CPF/CNPJ do cliente/fornecedor (DADO PESSOAL - LGPD). |
| 19 | `documents` | string | - | Número(s) do documento. |
| 20 | `docType` | string | - | Tipo de documento (NF, boleto, ...). |
| 21 | `idBankAccount` | string | - | ID da conta bancária. |
| 22 | `banckAccount` | string | - | Conta bancária (sic "banck"). |
| 23 | `emissionDate` | string | - | Data de emissão. |
| 24 | `parcel` | string | - | Parcela (ex.: "1/3"). |
| 25 | `project` | string | - | Projeto. |
| 26 | `conciliationDate` | string | - | Data de conciliação bancária. |
| 27 | `datePayment` | string | - | Data de pagamento (regime de caixa; usada como data do realizado no BI). |
| 28 | `dueDate` | string | - | Data de vencimento. |
| 29 | `type` | string | - | Tipo (semântica depende do DTO: tipo de venda, tipo de movimento, receita/despesa...). |
| 30 | `amountPayable` | number(double) | - | Valor a pagar/receber (previsto no título). |
| 31 | `amountPaid` | number(double) | - | Valor efetivamente pago/recebido (usado como "realizado" no BI). |
| 32 | `addition` | number(double) | - | Acréscimos (juros/multa). |
| 33 | `discount` | number(double) | - | Descontos. |
| 34 | `currency` | string | - | Moeda. |
| 35 | `status` | string | - | Status do título (ex.: pago/aberto). |

#### 1.3.22 `GET /api-metryx/previsao-financeiro`

- **operationId:** `getFiPrevision` | **Domínio:** Financeiro previsto
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxFiPrevisionDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Previsto x realizado financeiro por centro de custo/classe/produto/atividade.
- **Uso no ETL atual:** USADO: get_prevdre (fMetas DRE) -> stg_dreprevisto.

DTO `ApiMetryxFiPrevisionDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `valorPrevisto` | integer(int64) | - | Valor previsto/orçado (int64 no Swagger: possível perda de centavos). |
| 2 | `valorRealizado` | integer(int64) | - | Valor realizado correspondente (int64 no Swagger). |
| 3 | `costCenter` | string | - | Centro de custo (base do mapeamento DRE no BI: custeio/CF/CV/desembolso). |
| 4 | `cultivation` | string | - | Cultura (atividade agrícola) associada. |
| 5 | `uuidCostCenter` | string | - | UUID do centro de custo. |
| 6 | `className` | string | - | Classe (plano de contas). |
| 7 | `uuidClass` | string | - | UUID da classe. |
| 8 | `subCenter` | string | - | Subcentro de custo. |
| 9 | `uuidSubCenter` | string | - | UUID do subcentro. |
| 10 | `product` | string | - | Produto/insumo. |
| 11 | `uuidProduct` | string | - | UUID do produto. |
| 12 | `farmName` | string | - | Nome da fazenda. |
| 13 | `idFarm` | string | - | ID da fazenda (string; usado como chave da fazenda em todo o ecossistema). |
| 14 | `activity` | string | - | Atividade (ex.: pecuária, agricultura). |
| 15 | `uuidActivity` | string | - | UUID da atividade. |
| 16 | `project` | string | - | Projeto. |
| 17 | `uuidProject` | string | - | UUID do projeto. |
| 18 | `date` | string | - | Data do evento/lançamento (string). Realizado: "YYYY-MM-DD" (o BI faz TO_DATE(date,'YYYY-MM-DD')); planejamento: "MM/YY" (o BI faz to_date(date,'MM/YY')). Confirmar por endpoint. |
| 19 | `dueDate` | string | - | Data de vencimento. |
| 20 | `type` | string | - | Tipo (semântica depende do DTO: tipo de venda, tipo de movimento, receita/despesa...). |
| 21 | `idCustomer` | string | - | ID do cliente Metryx (tenant/produtor). Escopo definido pelo token. |
| 22 | `customer` | string | - | Nome do cliente Metryx. |
| 23 | `classificationAnalyticUuid` | string | - | UUID da classificação analítica. |
| 24 | `classificationAnalyticDescription` | string | - | Descrição da classificação analítica. |
| 25 | `classificationAnalyticDisbursement` | string | - | Indicador se a classificação é desembolso (string aqui; boolean no PlPrevision). |

#### 1.3.23 `GET /api-metryx/utilizacao-pasto`

- **operationId:** `getPastureUtilization` | **Domínio:** Áreas/pastagens
- **Swagger (oficial):** Utilização de pasto - Lista as pastagens do cliente com a fazenda, o retiro, o módulo e cada período de tipo de uso (utilização da área, status pecuário, datas e áreas). Uma pastagem aparece uma vez por tipo de uso. Pastagens, módulos e fazendas excluídos, centros de manejo e a pastagem NONE ficam de fora. Exige permissão do endpoint UTILIZACAO_PASTO no token.
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxPastureUtilizationDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Pastagens com fazenda, retiro, módulo e períodos de tipo de uso (descrição oficial no Swagger).
- **Uso no ETL atual:** USADO: get_area (fArea) -> stg_area (não consumida pelo BI atual).

DTO `ApiMetryxPastureUtilizationDTO` - Tipo de uso (utilização de área) de uma pastagem. Cada pastagem retorna uma linha por período de uso.:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `fazendaId` | string | Id da fazenda | - |
| 2 | `fazendaNome` | string | Nome da fazenda | - |
| 3 | `retiroId` | integer(int64) | Id do retiro | - |
| 4 | `retiroName` | string | Nome do retiro | Nome do retiro. |
| 5 | `moduloId` | string | Id do módulo | - |
| 6 | `moduloNome` | string | Nome do módulo | - |
| 7 | `id` | string | Id da pastagem | Identificador do registro. |
| 8 | `name` | string | Nome da pastagem | - |
| 9 | `tipoUsoId` | string | Id do tipo de uso | - |
| 10 | `utilizacaoArea` | string, enum=Pecuária / Agricultura / Arrendamento / APP / Benfeitorias / Estruturas | Utilização da área | - |
| 11 | `statusPecuaria` | string, nullable, enum=Disponível / Manutenção / Reforma / Alagado / Produção de Volumosos | Status pecuário da área (pode ser nulo) | - |
| 12 | `dataInicio` | string, ex. 2024-07-01 | Início do tipo de uso (yyyy-MM-dd) | - |
| 13 | `dataFim` | string, nullable, ex. 2025-06-30 | Fim do tipo de uso (yyyy-MM-dd); nulo quando é o uso atual | - |
| 14 | `areaCalculada` | number(double), nullable | Área calculada (ha) | - |
| 15 | `areaProdutiva` | number(double) | Área produtiva (ha) | - |
| 16 | `areaTotal` | number(double) | Área total (ha) | - |

#### 1.3.24 `GET /api-metryx/confina-tech`

- **operationId:** `getConfinaTechWaMovements` | **Domínio:** Confinamento/almoxarifado
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Resposta 200:** `array<ApiMetryxConfinaTechWaMovementDTO>` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** Movimentos de produtos (entradas/saídas de almoxarifado - "WaMovement") do módulo ConfinaTech.
- **Uso no ETL atual:** NÃO USADO. Valioso para clientes com confinamento (custo de dieta/insumos).

DTO `ApiMetryxConfinaTechWaMovementDTO`:

| # | Campo | Tipo (Swagger) | Descrição oficial | Interpretação |
|---|---|---|---|---|
| 1 | `customerId` | integer(int64) | - | ID do cliente (aqui numérico int64, diferente dos demais DTOs que usam string). |
| 2 | `farmId` | string | - | ID da fazenda. |
| 3 | `productEntryUuid` | string | - | UUID do movimento de produto (entrada/saida de almoxarifado). |
| 4 | `date` | string | - | Data do evento/lançamento (string). Realizado: "YYYY-MM-DD" (o BI faz TO_DATE(date,'YYYY-MM-DD')); planejamento: "MM/YY" (o BI faz to_date(date,'MM/YY')). Confirmar por endpoint. |
| 5 | `type` | string | - | Tipo (semântica depende do DTO: tipo de venda, tipo de movimento, receita/despesa...). |
| 6 | `codProduct` | integer(int64) | - | Código do produto/insumo. |
| 7 | `clientProviderName` | string | - | Cliente/fornecedor do movimento. |
| 8 | `document` | string | - | Documento do movimento. |
| 9 | `amount` | number(double) | - | Quantidade (cabeças). Em DTOs de estoque/balanço/rebanho médio e double (médias/saldos). |
| 10 | `unitValue` | number(double) | - | Valor unitário. |
| 11 | `totalValue` | number(double) | - | Valor total (R$). |

#### 1.3.25 `POST /api-metryx/control-birth`

- **operationId:** `updateControlBirth` | **Domínio:** Escrita (!)
- **Segurança:** header `x-auth-token` (JWT). **Parâmetros de query/path:** nenhum declarado (sem filtro de data, fazenda ou paginação).
- **Corpo:** `application/json` obrigatório, schema `boolean`.
- **Resposta 200:** `object` (content-type declarado `*/*`).
- **Significado de negócio (interpretação):** POST que altera um flag booleano de "controle de nascimento" (operationId updateControlBirth). Operação de ESCRITA.
- **Uso no ETL atual:** NÃO USADO. NÃO deve ser chamado pelo adapter (somente leitura).


### 1.4 Matriz de uso dos endpoints

| Endpoint | Domínio | Transformação (entrada do job) | Tabela destino | Consumida pelo BI? | Status / valor potencial |
|---|---|---|---|---|---|
| `GET /customers` (não documentado) | Auth/cadastro | get_customer (fCustomer) | stg_customers | sim (`fUnidades`: idcustomer, customer, idfarm, farmname) | Usado; depende de endpoint fora do contrato |
| `fazenda` | Cadastro | get_customer (2ª chamada) + get_farms (fFarms) | stg_customers, stg_farm | sim | Usado (chamado 2× por token) |
| `categoria` | Cadastro | get_categories (fCategories) | stg_category | sim | Usado |
| `retiro` | Cadastro | — | — | — | **Não usado**; útil como dimensão |
| `balanco-pecuario` | Realizado | get_balanco (fBalanco) | stg_balanco_pecuario | sim (base do `fSaldoGado`) | Usado |
| `saldo-inical-pecuario` | Realizado | — | — | — | **Não usado**; âncora de estoque inicial |
| `nascimento-pecuario` | Realizado | get_nascimentos (fNascimento) | stg_nascimentos | sim | Usado |
| `desmames-pecuario` | Realizado | get_desmames (fDesmame) | stg_desmames | sim | Usado |
| `morte-pecuario` | Realizado | get_morte (fMortes) | stg_mortes | sim | Usado |
| `venda-pecuario` | Realizado | get_vendas (fVendas) | stg_vendas | sim | Usado (sem idFarm) |
| `compra-pecuario` | Realizado | get_compras (fCompras) | stg_compras | sim | Usado (sem idFarm) |
| `mudanca-categoria-pecuario` | Realizado | get_mudanca_cat (**órfã**), get_transferencias (**órfã**, uso errado) | stg_mudanca_categoria / stg_balanco_pecuario | não | Efetivamente **não usado** pelo job |
| `transferencia-animal-pecuario` | Realizado | — | — | — | **Não usado**; necessário para fechar estoque por fazenda/retiro |
| `rebanho-medio-pecuario` | Realizado | get_rebanho_medio (fRebanhoMedio); get_rebanhomedio (**órfã**) | stg_rebanho_medio; stg_rebanhomedio | sim (stg_rebanho_medio, inclusive em "fMetasRebanhoMedio") | Usado; duplicado |
| `venda-mensal-planejamento` | Planejamento | get_prevvendas (fMetas Vendas) | stg_vendasasprevisto | sim (`fMetasAbate`, `fMetasEmPe`) | Usado (sem plVersionCode) |
| `compra-mensal-planejamento` | Planejamento | get_prevcompras (fMetas Compras) | stg_comprasprevisto | sim | Usado (sem plVersionCode) |
| `nascimento-mensal-planejamento` | Planejamento | get_prevnascimentos | stg_nascimentosprevisto | sim | Usado |
| `morte-mensal-planejamento` | Planejamento | get_prevmortes | stg_mortesprevisto | sim | Usado |
| `desmame-mensal-planejamento` | Planejamento | get_prevdesmame | stg_desmameprevisto | não | Usado pelo ETL, ignorado pelo BI |
| `estoque-medio-mensal-planejamento` | Planejamento | get_prevrebanhomedio | stg_rebanhomedioprevisto | não | Usado pelo ETL, ignorado pelo BI |
| `previsao-fluxo-caixa-planejamento` | Planejamento financeiro | — | — | — | **Não usado**; orçamento de caixa por versão/projeto |
| `lancamento-financeiro` | Financeiro realizado | get_dre (fDre) | stg_dre | sim (`financeiroDre`, `fPlanejadoxRealizado`) | Usado |
| `previsao-financeiro` | Financeiro previsto | get_prevdre (fMetas DRE) | stg_dreprevisto | sim (`fMetasDre`, `fPlanejadoxRealizado`) | Usado |
| `utilizacao-pasto` | Áreas | get_area (fArea) | stg_area | não | Usado pelo ETL, ignorado pelo BI; base para lotação (UA/ha) |
| `confina-tech` | Confinamento | — | — | — | **Não usado**; custo de insumos/dieta |
| `POST control-birth` | Escrita | — | — | — | **Nunca chamar** (altera estado no Metryx) |

**Endpoints de maior valor ainda não usados (prioridade sugerida):**
1. `transferencia-animal-pecuario` — sem ele o saldo por fazenda/retiro não fecha quando há movimentação entre fazendas do mesmo cliente (o balanço pode já refletir isso; validar).
2. `saldo-inical-pecuario` — permite reconstruir/validar o estoque `saldo inicial + Σ movimentos` e detectar furos no balanço.
3. `retiro` — dimensão estável para RLS e filtros (hoje só nome desnormalizado).
4. `previsao-fluxo-caixa-planejamento` — orçamento financeiro por versão, complementa `previsao-financeiro`.
5. `utilizacao-pasto` (já extraído, não modelado) — área produtiva × rebanho médio = taxa de lotação, KPI clássico de consultoria.
6. `confina-tech` — apenas para clientes com confinamento.

---

## 2. Fluxo de autenticação e iteração de clientes/fazendas

### 2.1 Como o token é obtido e usado

```
[Data grid de get_customer]                      token MESTRE hardcoded [REDACTED] (JWT HS384, sem exp)
        │  header X-Auth-Token
        ▼
GET /api-metryx/customers  (endpoint fora do Swagger)
        │  JSON: [{idCustomer, customer, listToken:[{token}, ...]}, ...]
        ▼
Decode Customer ($..idCustomer, $..customer, $..listToken)  →  Decode ListToken ($..token)
        │  1 linha por (cliente, token)
        ▼
GET /api-metryx/fazenda   header X-Auth-Token = token DO CLIENTE
        │  1 linha por (cliente, token, fazenda)
        ▼
TRUNCATE + INSERT "DATABASE".stg_customers (idcustomer, customer, idfarm, farmname, token)   ← token em TEXTO PURO
```

Em **todas** as outras 18 transformações do job:

```
Select Customers (SQL):  SELECT idcustomer, customer, token AS auth
                         FROM "DATABASE".stg_customers GROUP BY idcustomer, customer, token
        +  Data grid (url do endpoint + token hardcoded NÃO usado)
        →  Merge Join FULL OUTER sem chaves (= produto cartesiano 1 × N)
        →  Replace in string: remove "{" e "}" de auth (resto do antigo ARRAY_AGG, hoje comentado)
        →  REST Client GET url, header X-Auth-Token = auth   (1 chamada sequencial por token)
```

Conclusões:

- **Não há login nem refresh.** São tokens estáticos (JWT sem `exp`). O token mestre (consultoria/integração) só serve para descobrir clientes e seus tokens; os dados são sempre lidos com o **token do cliente**.
- **Iteração:** "loop" implícito do Pentaho — cada linha de `stg_customers` (deduplicada por `GROUP BY idcustomer, customer, token`) gera uma chamada. Se um cliente tiver 2 tokens na `listToken`, os dados dele são baixados 2× e **duplicados** na tabela (nenhuma deduplicação posterior).
- **Fazendas não são iteradas:** como a API não aceita `idFarm`, cada chamada já traz todas as fazendas do cliente. `stg_customers` tem 1 linha por fazenda apenas por causa da 2ª chamada a `/fazenda`.
- **Os tokens hardcoded nos outros 21 .ktr não são usados nas chamadas** (o header aponta para o campo `auth`), mas continuam expostos em arquivo. Fingerprint (SHA-256, sem revelar valor): 21 arquivos com o mesmo token "A"; `get_customer` com o token "B"; `sub` e `id` diferentes entre A e B (identidades distintas no Metryx); nenhum com `exp`.
- **Variáveis/parâmetros entre entradas do job:** nenhum. Não há `${VAR}` em nenhum arquivo, `kettle.properties` está vazio (só comentários), o job não define parâmetros; todas as entradas TRANS têm `pass_all_parameters=Y` sem efeito. A única "passagem de estado" entre transformações é **pela tabela `stg_customers`** (acoplamento por banco).
- **`idcustomer`/`customer` nas tabelas de fatos vêm de `stg_customers`, não do JSON:** o PDI trata nomes de campo sem diferenciar maiúsculas; o `idCustomer` decodificado colide com `idcustomer` da consulta e é renomeado para `idCustomer_1`; o `Select values` pega o primeiro (`stg_customers`). Exceções: `get_prevdesmame` e `get_prevrebanhomedio` usam explicitamente `idCustomer_1` (JSON) e gravam `customername`; `get_prevmortes`/`get_prevnascimentos` gravam `customerName` do JSON na coluna `customer`.

### 2.2 Onde ficam os segredos (todos [REDACTED])

| Segredo | Onde | Forma |
|---|---|---|
| Token mestre Metryx | `get_customer.ktr`, passo `Data grid`, coluna `X-Auth-Token` | JWT em texto puro |
| Token de cliente (dev) | `Data grid` dos outros 21 .ktr, coluna `X-Auth-Token` | JWT em texto puro (mesmo valor nos 21) |
| Tokens de todos os clientes | tabela `"DATABASE".stg_customers.token` (banco METRIX) | texto puro, legível por qualquer usuário com SELECT (o DSN ODBC `DATALAKE_METRYX` do Power BI lê esse schema) |
| Senha PostgreSQL (`postgres`) | `<connection><password>` de cada .ktr (conexões `METRIX` e `METRYX`, mesmo valor) | "Encrypted …" do Kettle (ofuscação reversível, equivale a texto puro) |
| Senha SMTP Gmail | `auth_password` das 11 entradas MAIL do job | "Encrypted …" do Kettle |
| Usuário SMTP | `auth_user` das 11 entradas MAIL | texto puro |
| Dump de dados | `get_vendas` → `Text file output` → `C:\Users\TerraDev\Documents\teste.txt` | JSON bruto de vendas de todos os clientes |

---

## 3. Fluxo do job `Job Extract Data .kjb`

- **33 entradas:** `Start`, `Success`, 20 entradas TRANS (19 transformações Metryx + `dRls` de outro projeto), 11 entradas MAIL. Execução **estritamente sequencial** (`parallel=N` em todas). Nenhum agendamento interno (`Start.repeat=N`): o disparo é externo (Spoon manual ou Kitchen via Agendador do Windows — nenhum `.bat`/`.cmd` encontrado em `Pentaho Archives`).
- Todas as transformações são referenciadas por **caminho absoluto** (`C:/Users/TerraDev/Documents/...`), `run_configuration = Pentaho local`, `loglevel = Basic`, sem arquivo de log, sem tabela de log (`job-log-table` vazio).

### 3.1 Sequência e condições

| # | Entrada | Transformação | Hop para a próxima | Em caso de falha |
|---|---|---|---|---|
| 1 | Start | — | incondicional | — |
| 2 | **Start (2)** (MAIL "Start Service") | — | **só se OK** | (sem hop) → **job para sem extrair nada se o SMTP falhar** |
| 3 | fCustomer | get_customer | só se OK | Erro 1 (assunto "Erro na Transform fCadastro") e para |
| 4 | fFarms | get_farms | só se OK | Erro 01 (assunto **"fArea"** — rótulo errado) e para |
| 5 | fCategories | get_categories | só se OK | **sem e-mail**, para |
| 6 | fVendas | get_vendas | só se OK | Erro 2 ("fVendas") e para |
| 7 | fBalanco | get_balanco | **incondicional** | Erro 3 (assunto **"fMovimentacao"**) e continua |
| 8 | fMetas Vendas | get_prevvendas | incondicional | sem e-mail, continua |
| 9 | fMetas Nascimento | get_prevnascimentos | incondicional | sem e-mail, continua |
| 10 | fMetas Rebanho Medio | get_prevrebanhomedio | incondicional | sem e-mail, continua |
| 11 | fMetas Compras | get_prevcompras | incondicional | Erro 4 ("fMetas") e continua |
| 12 | fMetas DRE | get_prevdre | incondicional | sem e-mail, continua |
| 13 | fMetas Mortes | get_prevmortes | incondicional | sem e-mail, continua |
| 14 | fMetas Desmame | get_prevdesmame | incondicional | sem e-mail, continua |
| 15 | fCompras | get_compras | só se OK | Erro 5 ("fCompras") e para |
| 16 | fNascimento | get_nascimentos | só se OK (hop direto p/ dRls **desabilitado**) | Erro 6 ("fNascimento") e para |
| 17 | fArea | get_area | **incondicional** | Erro 8 (assunto **"fNascimento"** — rótulo errado) e continua |
| 18 | dRls | `..\Base de Planilhas\TerraDesenvolvimento\d_rls.ktr` | só se OK | Erro 7 ("dRls") e para |
| 19 | fDesmame | get_desmames | só se OK | **sem e-mail**, para |
| 20 | fDre | get_dre | só se OK | **sem e-mail**, para |
| 21 | fRebanhoMedio | get_rebanho_medio | só se OK | **sem e-mail**, para |
| 22 | fMortes | get_morte | só se OK | **sem e-mail**, para |
| 23 | Success | — | só se OK | — |
| 24 | Success - Mail ("Execução Concluida") | — | — | — |

Observações:
- **Não estão no job:** `get_mudanca_cat`, `get_rebanhomedio`, `get_transferencias` (órfãs). Logo `stg_mudanca_categoria` e `stg_rebanhomedio` não são atualizadas pelo job (dados antigos ou vazios) e o bug de `get_transferencias` (sobrescrever `stg_balanco_pecuario`) só ocorre se alguém rodá-la manualmente.
- **`dRls`** pertence ao projeto de planilhas: lê `C:\Users\TerraDev\Meu Drive\Levantamento Clientes para Power BI.xlsx` (aba `Planilha1`; colunas BASE, CÓDIGO DO CLIENTE, PROPRIETÁRIO, CLIENTE, NOME DO PROJETO (FAZENDA), TÉCNICO, EMAIL, EMAIL - GERENTE, email- REGIONAL) e faz TRUNCATE+INSERT em `"DATABASE".STG_RLS` de **outro banco** (`DATALAKE_PLAN`). É a tabela de segurança em nível de linha do Power BI (e-mails de técnico/gerente/regional por cliente/fazenda). Na nova plataforma isso vira cadastro de usuários × fazendas + RLS do PostgreSQL.
- **E-mails:** SMTP `smtp.gmail.com:465` SSL com autenticação, destino e reply-to = conta Gmail **pessoal** do desenvolvedor; `replytoname = "Job - Datalake Plan - Terra"` (copiado do job de planilhas); sem anexos/logs (`include_files=N`), então o e-mail de erro não diz qual cliente/endpoint falhou.
- **Tratamento de erro real:** como os erros HTTP são engolidos dentro das transformações (seção 4.0), as entradas quase nunca falham por problema de API — falham apenas por erro de banco, conversão de tipo ou exceção de conexão no `get_customer` (único sem desvio de erro junto com `get_categories`).
- **Volume de chamadas por execução:** `1 + N_tokens × 20` (19 transformações Metryx, `/fazenda` chamado duas vezes), todas sequenciais, sem timeout configurado.

---

## 4. Transformações (uma a uma)

### 4.0 Padrão comum (template) — vale para 21 das 22 transformações (todas exceto `get_customer`)

Passos (nomes reais):
1. **`Select Customers`** (Table Input, conexão `METRIX`/`METRYX` → `localhost:5432/METRIX`): `SELECT t0.idcustomer, t0.customer, t0.token AS auth FROM "DATABASE".stg_customers t0 GROUP BY t0.idcustomer, t0.customer, t0.token` (há um `ARRAY_AGG(DISTINCT t0.token)` comentado).
2. **`Data grid`**: 1 linha com `url` = URL completa do endpoint e `X-Auth-Token` = token [REDACTED] (não usado).
3. **`Merge join`** FULL OUTER, `step1 = Data grid`, `step2 = Select Customers`, **sem chaves** → produto cartesiano (cada cliente recebe a URL).
4. **`Replace in string`** (às vezes `Param Auth`): remove `{` e `}` do campo `auth`.
5. **`get <x>`** (REST Client): `GET`, `urlInField=Y` (`url`), header `X-Auth-Token ← auth`, `applicationType = TEXT PLAIN`, resultado no campo `result`. Sem campo de status HTTP, sem tempo de resposta, sem proxy, sem truststore, sem timeout. **Tratamento de erro do passo habilitado com destino `Dummy (do nothing)`** (erros descartados, sem limite).
6. **`Decode Categories`** (JSON Input, `IsInFields=Y`, `valueField=result`, `ignoreMissingPath=Y`, `defaultPathLeafToNull=Y`): um campo por propriedade do DTO com **caminho `$..campo`** (busca recursiva). Os arrays resultantes são "zipados" por índice. Há um nome de arquivo local de desenvolvimento esquecido no passo (`C:\Users\matheus.santos\Desktop\*.json`), inofensivo quando `IsInFields=Y`.
7. **`Filter rows`** (nem todas): descarta linhas com campo-chave nulo (`amount IS NULL`, `fazendaId IS NULL`, `idCustomer_1 IS NULL`, `totalValue IS NULL`) para `Dummy (do nothing) 2`.
8. **`Param Amount`** (algumas): troca `.` por `,` em `amount` (texto) para a conversão String→Number funcionar com locale pt-BR.
9. **`Select values`**: seleciona/renomeia e define metadados (String com comprimento, Number). Datas ficam **String**.
10. **`INSERT …`** (Table Output): schema `DATABASE`, `truncate=Y`, `commit=1000`, batch, `specify_fields=Y`, `ignore_errors=N`. Como `DATABASE` é palavra reservada e `PRESERVE_RESERVED_WORD_CASE=Y`, o schema é `"DATABASE"` (maiúsculo, entre aspas); tabelas e colunas não são citadas e caem para **minúsculas** (confirmado pelas consultas do BI: `"DATABASE".stg_vendas`, `liveweightavg` etc.).

**Estratégia de carga em todas:** `TRUNCATE` + `INSERT` completo (full reload), sem transação única (`unique_connections=N`, commit a cada 1000 linhas) — leitores podem ver tabela vazia/parcial durante a carga. **Nenhuma lógica incremental** em nenhuma transformação; nenhum lookup, nenhuma data de corte, nenhum campo derivado além de renomeações.

### 4.1 `get_customer.ktr` → `stg_customers` (job: fCustomer)

- Data grid: `url = …/api-metryx/customers`, `urlfarm = …/api-metryx/fazenda`, `X-Auth-Token` = **token mestre** [REDACTED].
- `get customers` (REST GET `url`, header `X-Auth-Token ← X-Auth-Token`) → `Decode Customer`: `idcustomer ← $..idCustomer`, `Customer ← $..customer`, `listtoken ← $..listToken` (String com o JSON do array) → `Decode ListToken` (`valueField=listtoken`): `token ← $..token`.
- `get farm` (REST GET `urlfarm`, header `X-Auth-Token ← token`) → `Decode Farm` (`valueField=result_1`, pois `result` já existia): `idFarm ← $..idFarm`, `farmName ← $..farmName`.
- `Select values`: idcustomer, Customer, idFarm, farmName (String 100), token (String 600).
- Destino: `"DATABASE".stg_customers` (idcustomer, customer, idfarm, farmname, token), TRUNCATE+INSERT.
- **Sem desvio de erro** no REST: exceção de conexão falha a transformação (gera "Erro 1"). Mas um HTTP 401/500 com corpo JSON de erro não é exceção → zero linhas → `stg_customers` vazia → todo o resto do job esvazia as tabelas sem erro.
- Observação: `$..token` dentro de `listToken` e `$..idCustomer` no topo — se o objeto de token também contiver `idCustomer`, a busca recursiva desalinha cliente × token.

### 4.2 `get_farms.ktr` → `stg_farm` (fFarms)

- Endpoint `fazenda`. JSON: `idCustomer`, `customer`, `idFarm`, `farmName` (String). Filtro: descarta `idCustomer_1 IS NULL` (o idCustomer do JSON). Select: idcustomer, customer (de stg_customers), idFarm, farmName (200).
- Destino `stg_farm` (idcustomer, customer, idfarm, farmname). TRUNCATE+INSERT. Redundante com as colunas de fazenda de `stg_customers` (mesma chamada feita 2×).

### 4.3 `get_categories.ktr` → `stg_category` (fCategories)

- Endpoint `categoria`. Template sem `Replace in string` e **sem desvio de erro** (erro de REST falha a transformação, mas o job não manda e-mail).
- JSON: idcustomer, Customer, idCategory, category, categoryGroup, ageCategory, gender (String). Select: tudo String(100).
- Destino `stg_category` (idcustomer, customer, idcategory, category, categorygroup, agecategory, gender). Todos os campos do DTO usados.

### 4.4 `get_vendas.ktr` → `stg_vendas` (fVendas)

- Endpoint `venda-pecuario`. JSON: idCustomer, customer, farmName, idRetiro, retiroName, owner, date, anoSafra, gender, client, category, categoryId, harvest, birth, tipo (String); amount, liveWeightAVG, weightTotal, deadArrobaAvg, deadWeightAvg, valueWeight, valueArroba, totalFaturamento, discounts, additions (**tipo None** → texto convertido para Number no Select values, dependente de locale).
- **`idFarm` não é extraído** (o DTO tem). O BI compensa com `LEFT JOIN stg_farm ON idcustomer AND farmname` (frágil a homônimos/renomeação).
- Filtro `amount IS NULL` → descarta. Select: Strings (date 20, gender 10, tipo 15…) e Numbers.
- **Passo extra `Text file output`**: grava o campo `result` (JSON bruto de cada cliente) em `C:\Users\TerraDev\Documents\teste.txt` (separador `;`, cabeçalho, sobrescreve) — resto de depuração, vaza dados para disco.
- Destino `stg_vendas` (25 colunas, ver DDL). Não usados: `idFarm`.

### 4.5 `get_balanco.ktr` → `stg_balanco_pecuario` (fBalanco)

- Endpoint `balanco-pecuario`. JSON: idCustomer, customer, idFarm, farmName, idRetiro, retiroName, owner, date, uuidCategory, category, harvest (mapeado 2×), anoSafra, gender, birth (String); amount (Number).
- Filtro `amount IS NULL`. Passo `Param Amount` existe mas os hops estão **desabilitados** (amount vai direto como Number).
- Select: date String(10), birth/harvest String(10), amount Number.
- Destino `stg_balanco_pecuario` (idcustomer, customer, idfarm, farmname, idretiro, retironame, owner, anosafra, amount, gender, uuidcategory, category, date, harvest, birth). Todos os campos do DTO usados. É a tabela mais usada pelo BI (`fSaldoGado`: soma acumulada de `amount` por proprietário/fazenda/retiro/categoria ordenada por `date`, com regras para "Bezerros Mamando").

### 4.6 `get_prevvendas.ktr` → `stg_vendasasprevisto` (fMetas Vendas)

- Endpoint `venda-mensal-planejamento` (passos com nomes copiados de prevcompras: "get prevcompras", "INSERT PREV COMPRAS").
- JSON: Strings para ids/nomes, `date`, `harvest`, `anoSafra`, `age`, `gender`; **tipo None** para idCurrency, plVersionCode, month, idCategory, idAnimalGroup, amount, weight, arrobaValue, arrobaWeight, value, totalValue, `tipo ← $..type`, yield.
- Filtro `amount IS NULL`. Select: idCurrency/month/idCategory/idAnimalGroup como String; numéricos Number.
- Destino `stg_vendasasprevisto` (nome com erro "vendasas"). **Não gravados:** `plVersionCode`, `plVersionName` (extraídos mas não selecionados), `currencyCode`, `reproductiveOption`, `customerName` (usa o de stg_customers).

### 4.7 `get_prevnascimentos.ktr` → `stg_nascimentosprevisto` (fMetas Nascimento)

- Endpoint `nascimento-mensal-planejamento`. JSON: plVersionCode/month/amount Number; demais String. Filtro `amount IS NULL`. Select: `customerName → customer`, month **Number**, plVersionCode String.
- Destino com plversioncode/plversionname. Não gravados: `currencyCode`.

### 4.8 `get_prevrebanhomedio.ktr` → `stg_rebanhomedioprevisto` (fMetas Rebanho Medio)

- Endpoint `estoque-medio-mensal-planejamento`. JSON com tipo None para ids numéricos/month/amount. Filtro `amount IS NULL`. Select usa `idCustomer_1 → idCustomer` (JSON) e `customerName`.
- Destino inclui idevolution, type, originmovement, reproductiveoption, plversion*. Não gravados: `currencyCode`. **Não consumida pelo BI.**

### 4.9 `get_prevcompras.ktr` → `stg_comprasprevisto` (fMetas Compras)

- Endpoint `compra-mensal-planejamento`. Igual a prevvendas, com **dois filtros**: `totalValue IS NULL` → descarta; depois `idcustomer = ''` → descarta.
- Destino `stg_comprasprevisto`. **Não gravados:** `plVersionCode/plVersionName` (extraídos, não selecionados), `currencyCode`, `reproductiveOption`, `customerName`. No BI, `date` é convertido com `to_date(date,'MM/YY')`.

### 4.10 `get_prevdre.ktr` → `stg_dreprevisto` (fMetas DRE)

- Endpoint `previsao-financeiro`. JSON: valorPrevisto, valorRealizado (Number); costCenter, uuidCostCenter, className, uuidClass, subCenter, uuidSubCenter, product, uuidProduct, farmName, idFarm, activity, uuidActivity, project, uuidProject, date, type, idCustomer, customer, classificationAnalyticUuid, classificationAnalyticDescription (String).
- Filtro `idCustomer_1 IS NULL`. Destino `stg_dreprevisto` (20 colunas). **Não gravados:** `cultivation`, `dueDate`, `project`, `uuidProject`, `classificationAnalyticDisbursement`. `product`/`uuidProduct` sem metadado no Select (vão como texto livre).

### 4.11 `get_prevmortes.ktr` → `stg_mortesprevisto` (fMetas Mortes)

- Endpoint `morte-mensal-planejamento` (passos chamados "get prevcompras"/"INSERT PREV COMPRAS"). JSON numéricos Number (idCurrency, plVersionCode, month, idCategory, amount). Select: `customerName → customer`, ids e month para String.
- Destino com plversioncode/plversionname. Não gravados: `currencyCode`, `reproductiveOption`.

### 4.12 `get_prevdesmame.ktr` → `stg_desmameprevisto` (fMetas Desmame)

- Endpoint `desmame-mensal-planejamento` (passo de saída chamado "INSERT PREV REBANHOMEDIO"). Usa `idCustomer_1` (JSON) e `customerName`.
- Destino com todos os campos old*/new*, plversion*. Não gravado: `currencyCode`. `oldanimalgroupid` com comprimento 1001 (erro de digitação). **Não consumida pelo BI.**

### 4.13 `get_compras.ktr` → `stg_compras` (fCompras)

- Endpoint `compra-pecuario`. JSON numéricos Number; **`idFarm` não extraído**; `tipo`, `additions`, `discounts` não extraídos. Sem filtro.
- Destino `stg_compras` (20 colunas). BI junta com `stg_farm` por `farmname`.

### 4.14 `get_nascimentos.ktr` → `stg_nascimentos` (fNascimento)

- Endpoint `nascimento-pecuario`. Todos os campos do DTO usados; amount Number; date String(10). Sem filtro.

### 4.15 `get_area.ktr` → `stg_area` (fArea)

- Endpoint `utilizacao-pasto`. JSON: fazendaId, fazendaNome, retiroId (String, embora o DTO diga int64), retiroName, moduloId, moduloNome, id, name, tipoUsoId, utilizacaoArea, statusPecuaria (String); **dataInicio/dataFim Timestamp `yyyy-MM-dd`** (únicas datas tipadas do pipeline); areaCalculada/areaProdutiva/areaTotal Number.
- Filtro `fazendaId IS NULL`. Select sem metadados (tipos herdados do JSON).
- Destino `stg_area` (16 colunas). **Não grava `idcustomer`** (único fato sem tenant). Não consumida pelo BI. Arquivo modificado hoje (14/10/2026), provavelmente em desenvolvimento.

### 4.16 `get_desmames.ktr` → `stg_desmames` (fDesmame)

- Endpoint `desmames-pecuario`. Todos os campos do DTO usados; amount/weight/valueWeight Number. Sem filtro.

### 4.17 `get_dre.ktr` → `stg_dre` (fDre)

- Endpoint `lancamento-financeiro`. JSON extrai 29 campos (inclui clientProvider, documents, project), amountPayable/amountPaid Number, `code` como String.
- Select remove clientProvider e project; Table Output não grava `documents`.
- Destino `stg_dre` (26 colunas). **Não gravados:** `idFarmFiscal`, `clientProvider`, `cpfCnpj`, `documents`, `idBankAccount`, `banckAccount`, `project`, `addition`, `discount`. É a fonte do DRE realizado no BI (`amountpaid`, `datepayment`, `costcenter`, chave `idcustomer+idfarmdestination`), onde há filtro temporário para |valor| ≥ 1e9 por erro de escala.

### 4.18 `get_rebanho_medio.ktr` → `stg_rebanho_medio` (fRebanhoMedio) — **versão em uso**

- Endpoint `rebanho-medio-pecuario`. JSON: amount **tipo None** (texto) → `Param Amount` troca `.`→`,` → Select converte para Number (gambiarra de locale pt-BR). `AnoSafra ← $..anoSafra`. **Não extrai `weight` nem `groupCategory`.**
- Filtro `amount IS NULL`. Destino `stg_rebanho_medio` (13 colunas). Consumida pelo BI tanto em `pecuarioRebanhoMedioMensal` quanto em `fMetasRebanhoMedio` (este último deveria usar o previsto).

### 4.19 `get_morte.ktr` → `stg_mortes` (fMortes)

- Endpoint `morte-pecuario`. Todos os campos exceto **`notes`**. amount/averageWeight/totalWeight Number; cause String(500).

### 4.20 Órfãs (não chamadas pelo job)

| Transformação | Endpoint chamado | Destino | Problema |
|---|---|---|---|
| `get_rebanhomedio.ktr` | `rebanho-medio-pecuario` | `stg_rebanhomedio` | Duplicata de 4.18, mais completa (tem `weight`, `groupCategory`, amount Number sem gambiarra). Tabela desatualizada. |
| `get_mudanca_cat.ktr` | `mudanca-categoria-pecuario` | `stg_mudanca_categoria` | JSON Input com **`IsInFields=N`**: ignora a resposta da API e lê `C:\Users\matheus.santos\Desktop\presrebanho.json`; com `doNotFailIfNoFile=Y`, na máquina atual gera 0 linhas após TRUNCATE (ou carrega arquivo velho). Tem gambiarra `.`→`,`. |
| `get_transferencias.ktr` | **`mudanca-categoria-pecuario`** (errado; deveria ser `transferencia-animal-pecuario`) | **`stg_balanco_pecuario`** com TRUNCATE | Cópia mal adaptada de get_balanco: extrai `uuidCategory`/`category` que não existem no DTO de mudança de categoria. Se executada, **apaga o balanço** usado pelo BI. |


---

## 5. DDL PostgreSQL reconstruída (tabelas alimentadas pelo Metryx)

Notas de reconstrução:
- Gerada automaticamente a partir dos metadados do Pentaho (`scripts/gen_ddl.py`): tipo do `Select values` quando definido (String(n) → `VARCHAR(n)`, Number → `DOUBLE PRECISION`), senão o tipo do JSON Input (String sem tamanho → `TEXT`, Timestamp → `TIMESTAMP`). É o que o botão "SQL" do PDI geraria; **confirmar com `\d "DATABASE".stg_*`** no banco real (alguém pode ter criado as tabelas manualmente com outros tipos).
- Banco `METRIX` em `localhost:5432`; schema `"DATABASE"` (maiúsculo, citado); tabelas/colunas em minúsculas. Nenhuma PK, FK, índice ou constraint é criada pelo Pentaho.
- O comentário de cada coluna indica o caminho JSON de origem; `stg_customers (via Merge Join)` = valor vindo da consulta a `stg_customers`, não do payload.
- `stg_balanco_pecuario` também é alvo de `get_transferencias` (órfã) com um subconjunto das colunas; omitido abaixo.

```sql
CREATE SCHEMA IF NOT EXISTS "DATABASE";

-- origem: get_area.ktr / passo "INSERT AREA" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_area (
    fazendaid                          TEXT             , -- $..fazendaId
    fazendanome                        TEXT             , -- $..fazendaNome
    retiroid                           TEXT             , -- $..retiroId
    retironame                         TEXT             , -- $..retiroName
    moduloid                           TEXT             , -- $..moduloId
    modulonome                         TEXT             , -- $..moduloNome
    id                                 TEXT             , -- $..id
    name                               TEXT             , -- $..name
    tipousoid                          TEXT             , -- $..tipoUsoId
    utilizacaoarea                     TEXT             , -- $..utilizacaoArea
    statuspecuaria                     TEXT             , -- $..statusPecuaria
    datainicio                         TIMESTAMP        , -- $..dataInicio
    datafim                            TIMESTAMP        , -- $..dataFim
    areacalculada                      DOUBLE PRECISION , -- $..areaCalculada
    areaprodutiva                      DOUBLE PRECISION , -- $..areaProdutiva
    areatotal                          DOUBLE PRECISION   -- $..areaTotal
);

-- origem: get_balanco.ktr / passo "INSERT Balanço" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_balanco_pecuario (
    idcustomer                         VARCHAR(100)     , -- stg_customers (via Merge Join)
    customer                           VARCHAR(100)     , -- stg_customers (via Merge Join)
    idfarm                             VARCHAR(100)     , -- $..idFarm
    farmname                           VARCHAR(200)     , -- $..farmName
    idretiro                           VARCHAR(100)     , -- $..idRetiro
    retironame                         VARCHAR(100)     , -- $..retiroName
    owner                              VARCHAR(200)     , -- $..owner
    anosafra                           VARCHAR(20)      , -- $..anoSafra
    amount                             DOUBLE PRECISION , -- $..amount
    gender                             VARCHAR(100)     , -- $..gender
    uuidcategory                       VARCHAR(100)     , -- $..uuidCategory
    category                           VARCHAR(200)     , -- $..category
    date                               VARCHAR(10)      , -- $..date
    harvest                            VARCHAR(10)      , -- $..harvest
    birth                              VARCHAR(10)        -- $..birth
);

-- origem: get_categories.ktr / passo "INSERT Categories" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_category (
    idcustomer                         VARCHAR(100)     , -- stg_customers (via Merge Join)
    customer                           VARCHAR(100)     , -- stg_customers (via Merge Join)
    idcategory                         VARCHAR(100)     , -- $..idCategory
    category                           VARCHAR(100)     , -- $..category
    categorygroup                      VARCHAR(100)     , -- $..categoryGroup
    agecategory                        VARCHAR(100)     , -- $..ageCategory
    gender                             VARCHAR(100)       -- $..gender
);

-- origem: get_compras.ktr / passo "INSERT Compras" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_compras (
    idcustomer                         VARCHAR(100)     , -- stg_customers (via Merge Join)
    customer                           VARCHAR(100)     , -- stg_customers (via Merge Join)
    farmname                           VARCHAR(200)     , -- $..farmName
    idretiro                           VARCHAR(100)     , -- $..idRetiro
    retironame                         VARCHAR(100)     , -- $..retiroName
    owner                              VARCHAR(200)     , -- $..owner
    date                               VARCHAR(20)      , -- $..date
    anosafra                           VARCHAR(20)      , -- $..anoSafra
    gender                             VARCHAR(20)      , -- $..gender
    provider                           VARCHAR(100)     , -- $..provider
    category                           VARCHAR(100)     , -- $..category
    categoryid                         VARCHAR(100)     , -- $..categoryId
    amount                             DOUBLE PRECISION , -- $..amount
    weighttotal                        DOUBLE PRECISION , -- $..weightTotal
    averagevalue                       DOUBLE PRECISION , -- $..averageValue
    valueweight                        DOUBLE PRECISION , -- $..valueWeight
    valuearroba                        DOUBLE PRECISION , -- $..valueArroba
    totalfaturamento                   DOUBLE PRECISION , -- $..totalFaturamento
    harvest                            VARCHAR(20)      , -- $..harvest
    birth                              VARCHAR(20)        -- $..birth
);

-- origem: get_customer.ktr / passo "INSERT Customers and Farms" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_customers (
    idcustomer                         VARCHAR(100)     , -- GET /customers $..idCustomer
    customer                           VARCHAR(100)     , -- GET /customers $..customer
    idfarm                             VARCHAR(100)     , -- GET /fazenda (token do cliente) $..idFarm
    farmname                           VARCHAR(100)     , -- GET /fazenda (token do cliente) $..farmName
    token                              VARCHAR(600)       -- GET /customers $..listToken[*].token  (SEGREDO EM TEXTO PURO)
);

-- origem: get_desmames.ktr / passo "INSERT Desmames" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_desmames (
    idcustomer                         VARCHAR(100)     , -- stg_customers (via Merge Join)
    customer                           VARCHAR(100)     , -- stg_customers (via Merge Join)
    idfarm                             VARCHAR(100)     , -- $..idFarm
    farmname                           VARCHAR(200)     , -- $..farmName
    idretiro                           VARCHAR(100)     , -- $..idRetiro
    retironame                         VARCHAR(100)     , -- $..retiroName
    owner                              VARCHAR(200)     , -- $..owner
    anosafra                           VARCHAR(20)      , -- $..anoSafra
    date                               VARCHAR(20)      , -- $..date
    oldcategory                        VARCHAR(100)     , -- $..oldCategory
    oldcategoryid                      VARCHAR(100)     , -- $..oldCategoryId
    birthdate                          VARCHAR(20)      , -- $..birthDate
    harvest                            VARCHAR(20)      , -- $..harvest
    newcategory                        VARCHAR(100)     , -- $..newCategory
    newcategoryid                      VARCHAR(100)     , -- $..newCategoryId
    amount                             DOUBLE PRECISION , -- $..amount
    weight                             DOUBLE PRECISION , -- $..weight
    valueweight                        DOUBLE PRECISION , -- $..valueWeight
    gender                             VARCHAR(20)        -- $..gender
);

-- origem: get_dre.ktr / passo "INSERT DRE" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_dre (
    idcustomer                         VARCHAR(100)     , -- stg_customers (via Merge Join)
    customer                           VARCHAR(100)     , -- stg_customers (via Merge Join)
    farmfiscal                         VARCHAR(100)     , -- $..farmFiscal
    idfarmdestination                  VARCHAR(200)     , -- $..idfarmDestination
    farmdestination                    VARCHAR(200)     , -- $..farmDestination
    owner                              VARCHAR(200)     , -- $..owner
    idfinancialentrie                  VARCHAR(100)     , -- $..idFinancialEntrie
    idpayment                          VARCHAR(100)     , -- $..idPayment
    anosafra                           VARCHAR(100)     , -- $..anoSafra
    costcenter                         VARCHAR(200)     , -- $..costCenter
    description                        VARCHAR(500)     , -- $..description
    code                               VARCHAR(100)     , -- $..code
    classe                             VARCHAR(200)     , -- $..classe
    subcenter                          VARCHAR(200)     , -- $..subCenter
    activity                           VARCHAR(100)     , -- $..activity
    doctype                            VARCHAR(100)     , -- $..docType
    emissiondate                       VARCHAR(10)      , -- $..emissionDate
    parcel                             VARCHAR(100)     , -- $..parcel
    conciliationdate                   VARCHAR(20)      , -- $..conciliationDate
    datepayment                        VARCHAR(20)      , -- $..datePayment
    duedate                            VARCHAR(20)      , -- $..dueDate
    type                               VARCHAR(20)      , -- $..type
    amountpayable                      DOUBLE PRECISION , -- $..amountPayable
    amountpaid                         DOUBLE PRECISION , -- $..amountPaid
    currency                           VARCHAR(20)      , -- $..currency
    status                             VARCHAR(20)        -- $..status
);

-- origem: get_farms.ktr / passo "INSERT FARMS" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_farm (
    idcustomer                         VARCHAR(100)     , -- stg_customers (via Merge Join)
    customer                           VARCHAR(100)     , -- stg_customers (via Merge Join)
    idfarm                             VARCHAR(100)     , -- $..idFarm
    farmname                           VARCHAR(200)       -- $..farmName
);

-- origem: get_morte.ktr / passo "INSERT Mortes" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_mortes (
    idcustomer                         VARCHAR(100)     , -- stg_customers (via Merge Join)
    customer                           VARCHAR(100)     , -- stg_customers (via Merge Join)
    idfarm                             VARCHAR(100)     , -- $..idFarm
    farmname                           VARCHAR(200)     , -- $..farmName
    idretiro                           VARCHAR(100)     , -- $..idRetiro
    retironame                         VARCHAR(100)     , -- $..retiroName
    owner                              VARCHAR(200)     , -- $..owner
    date                               VARCHAR(20)      , -- $..date
    anosafra                           VARCHAR(20)      , -- $..anoSafra
    enumgroup                          VARCHAR(100)     , -- $..enumGroup
    namegroup                          VARCHAR(100)     , -- $..nameGroup
    enumgeneration                     VARCHAR(100)     , -- $..enumGeneration
    namegeneration                     VARCHAR(100)     , -- $..nameGeneration
    era                                VARCHAR(20)      , -- $..era
    category                           VARCHAR(100)     , -- $..category
    categoryid                         VARCHAR(100)     , -- $..categoryId
    cause                              VARCHAR(500)     , -- $..cause
    harvest                            VARCHAR(20)      , -- $..harvest
    birth                              VARCHAR(20)      , -- $..birth
    amount                             DOUBLE PRECISION , -- $..amount
    averageweight                      DOUBLE PRECISION , -- $..averageWeight
    totalweight                        DOUBLE PRECISION , -- $..totalWeight
    locale                             VARCHAR(100)     , -- $..locale
    gender                             VARCHAR(20)      , -- $..gender
    gendername                         VARCHAR(20)        -- $..genderName
);

-- origem: get_mudanca_cat.ktr / passo "INSERT Mudança Categoria" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_mudanca_categoria (
    idcustomer                         VARCHAR(100)     , -- stg_customers (via Merge Join)
    customer                           VARCHAR(100)     , -- stg_customers (via Merge Join)
    idfarm                             VARCHAR(100)     , -- $..idFarm
    farmname                           VARCHAR(200)     , -- $..farmName
    idretiro                           VARCHAR(100)     , -- $..idRetiro
    retironame                         VARCHAR(100)     , -- $..retiroName
    owner                              VARCHAR(200)     , -- $..owner
    anosafra                           VARCHAR(20)      , -- $..anoSafra
    amount                             DOUBLE PRECISION , -- $..amount
    gender                             VARCHAR(100)     , -- $..gender
    uuidcategorydestiny                VARCHAR(100)     , -- $..uuidCategoryDestiny
    categorydestiny                    VARCHAR(200)     , -- $..categoryDestiny
    date                               VARCHAR(10)      , -- $..date
    uuidcategoryorigin                 VARCHAR(100)     , -- $..uuidCategoryOrigin
    categoryorigin                     VARCHAR(200)       -- $..categoryOrigin
);

-- origem: get_nascimentos.ktr / passo "INSERT Nascimentos" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_nascimentos (
    idcustomer                         VARCHAR(100)     , -- stg_customers (via Merge Join)
    customer                           VARCHAR(100)     , -- stg_customers (via Merge Join)
    idfarm                             VARCHAR(100)     , -- $..idFarm
    farmname                           VARCHAR(200)     , -- $..farmName
    idretiro                           VARCHAR(100)     , -- $..idRetiro
    retironame                         VARCHAR(100)     , -- $..retiroName
    owner                              VARCHAR(200)     , -- $..owner
    anosafra                           VARCHAR(20)      , -- $..anoSafra
    idcategory                         VARCHAR(100)     , -- $..idCategory
    category                           VARCHAR(100)     , -- $..category
    harvest                            VARCHAR(20)      , -- $..harvest
    amount                             DOUBLE PRECISION , -- $..amount
    gender                             VARCHAR(20)      , -- $..gender
    date                               VARCHAR(10)        -- $..date
);

-- origem: get_prevcompras.ktr / passo "INSERT PREV COMPRAS" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_comprasprevisto (
    idcustomer                         VARCHAR(100)     , -- stg_customers (via Merge Join)
    customer                           VARCHAR(100)     , -- stg_customers (via Merge Join)
    idfarm                             VARCHAR(100)     , -- $..idFarm
    farmname                           VARCHAR(200)     , -- $..farmName
    idretiro                           VARCHAR(100)     , -- $..idRetiro
    retironame                         VARCHAR(100)     , -- $..retiroName
    idowner                            VARCHAR(100)     , -- $..idOwner
    ownername                          VARCHAR(200)     , -- $..ownerName
    idplherdtype                       VARCHAR(100)     , -- $..idPlHerdType
    plherdtypename                     VARCHAR(100)     , -- $..plHerdTypeName
    idcurrency                         VARCHAR(100)     , -- $..idCurrency
    currencyname                       VARCHAR(200)     , -- $..currencyName
    month                              VARCHAR(20)      , -- $..month
    date                               VARCHAR(20)      , -- $..date
    harvest                            VARCHAR(10)      , -- $..harvest
    anosafra                           VARCHAR(10)      , -- $..anoSafra
    idcategory                         VARCHAR(100)     , -- $..idCategory
    categoryname                       VARCHAR(100)     , -- $..categoryName
    idanimalgroup                      VARCHAR(100)     , -- $..idAnimalGroup
    animalgroupname                    VARCHAR(100)     , -- $..animalGroupName
    age                                VARCHAR(20)      , -- $..age
    gender                             VARCHAR(20)      , -- $..gender
    amount                             DOUBLE PRECISION , -- $..amount
    weight                             DOUBLE PRECISION , -- $..weight
    arrobavalue                        DOUBLE PRECISION , -- $..arrobaValue
    arrobaweight                       DOUBLE PRECISION , -- $..arrobaWeight
    value                              DOUBLE PRECISION , -- $..value
    totalvalue                         DOUBLE PRECISION   -- $..totalValue
);

-- origem: get_prevdesmame.ktr / passo "INSERT PREV REBANHOMEDIO" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_desmameprevisto (
    idcustomer                         VARCHAR(100)     , -- $..idCustomer
    customername                       VARCHAR(200)     , -- $..customerName
    idfarm                             VARCHAR(100)     , -- $..idFarm
    farmname                           VARCHAR(200)     , -- $..farmName
    idretiro                           VARCHAR(100)     , -- $..idRetiro
    retironame                         VARCHAR(200)     , -- $..retiroName
    idowner                            VARCHAR(100)     , -- $..idOwner
    ownername                          VARCHAR(200)     , -- $..ownerName
    idplherdtype                       VARCHAR(100)     , -- $..idPlHerdType
    plherdtypename                     VARCHAR(100)     , -- $..plHerdTypeName
    idcurrency                         VARCHAR(100)     , -- $..idCurrency
    currencyname                       VARCHAR(100)     , -- $..currencyName
    plversioncode                      VARCHAR(100)     , -- $..plVersionCode
    plversionname                      VARCHAR(100)     , -- $..plVersionName
    month                              VARCHAR(10)      , -- $..month
    date                               VARCHAR(20)      , -- $..date
    harvest                            VARCHAR(20)      , -- $..harvest
    anosafra                           VARCHAR(20)      , -- $..anoSafra
    oldcategoryid                      VARCHAR(100)     , -- $..oldCategoryId
    oldcategoryname                    VARCHAR(100)     , -- $..oldCategoryName
    oldanimalgroupid                   VARCHAR(1001)    , -- $..oldAnimalGroupId
    oldanimalgroupname                 VARCHAR(100)     , -- $..oldAnimalGroupName
    oldage                             VARCHAR(10)      , -- $..oldAge
    oldgender                          VARCHAR(20)      , -- $..oldGender
    newcategoryid                      VARCHAR(100)     , -- $..newCategoryId
    newcategoryname                    VARCHAR(100)     , -- $..newCategoryName
    newanimalgroupid                   VARCHAR(100)     , -- $..newAnimalGroupId
    newanimalgroupname                 VARCHAR(100)     , -- $..newAnimalGroupName
    newage                             VARCHAR(10)      , -- $..newAge
    newgender                          VARCHAR(20)      , -- $..newGender
    amount                             DOUBLE PRECISION   -- $..amount
);

-- origem: get_prevdre.ktr / passo "INSERT PREV DRE" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_dreprevisto (
    idcustomer                         VARCHAR(100)     , -- stg_customers (via Merge Join)
    customer                           VARCHAR(100)     , -- stg_customers (via Merge Join)
    valorprevisto                      DOUBLE PRECISION , -- $..valorPrevisto
    valorrealizado                     DOUBLE PRECISION , -- $..valorRealizado
    costcenter                         VARCHAR(200)     , -- $..costCenter
    uuidcostcenter                     VARCHAR(100)     , -- $..uuidCostCenter
    classname                          VARCHAR(200)     , -- $..className
    uuidclass                          VARCHAR(100)     , -- $..uuidClass
    subcenter                          VARCHAR(200)     , -- $..subCenter
    uuidsubcenter                      VARCHAR(200)     , -- $..uuidSubCenter
    product                            TEXT             , -- $..product
    uuidproduct                        TEXT             , -- $..uuidProduct
    farmname                           VARCHAR(200)     , -- $..farmName
    idfarm                             VARCHAR(100)     , -- $..idFarm
    activity                           VARCHAR(100)     , -- $..activity
    uuidactivity                       VARCHAR(100)     , -- $..uuidActivity
    date                               VARCHAR(20)      , -- $..date
    type                               VARCHAR(10)      , -- $..type
    classificationanalyticuuid         VARCHAR(100)     , -- $..classificationAnalyticUuid
    classificationanalyticdescription  VARCHAR(100)       -- $..classificationAnalyticDescription
);

-- origem: get_prevmortes.ktr / passo "INSERT PREV COMPRAS" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_mortesprevisto (
    idcustomer                         VARCHAR(100)     , -- stg_customers (via Merge Join)
    customer                           VARCHAR(100)     , -- $..customerName
    idfarm                             VARCHAR(100)     , -- $..idFarm
    farmname                           VARCHAR(200)     , -- $..farmName
    idretiro                           VARCHAR(100)     , -- $..idRetiro
    retironame                         VARCHAR(200)     , -- $..retiroName
    idowner                            VARCHAR(100)     , -- $..idOwner
    ownername                          VARCHAR(200)     , -- $..ownerName
    idplherdtype                       VARCHAR(100)     , -- $..idPlHerdType
    plherdtypename                     VARCHAR(100)     , -- $..plHerdTypeName
    idcurrency                         VARCHAR(100)     , -- $..idCurrency
    currencyname                       VARCHAR(100)     , -- $..currencyName
    plversioncode                      VARCHAR(100)     , -- $..plVersionCode
    plversionname                      VARCHAR(100)     , -- $..plVersionName
    month                              VARCHAR(10)      , -- $..month
    date                               VARCHAR(10)      , -- $..date
    harvest                            VARCHAR(100)     , -- $..harvest
    anosafra                           VARCHAR(10)      , -- $..anoSafra
    idcategory                         VARCHAR(100)     , -- $..idCategory
    categoryname                       VARCHAR(100)     , -- $..categoryName
    idanimalgroup                      VARCHAR(100)     , -- $..idAnimalGroup
    animalgroupname                    VARCHAR(100)     , -- $..animalGroupName
    age                                VARCHAR(20)      , -- $..age
    gender                             VARCHAR(20)      , -- $..gender
    amount                             DOUBLE PRECISION   -- $..amount
);

-- origem: get_prevnascimentos.ktr / passo "INSERT PREV NASCIMENTOS" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_nascimentosprevisto (
    idcustomer                         VARCHAR(100)     , -- stg_customers (via Merge Join)
    customer                           VARCHAR(100)     , -- stg_customers (via Merge Join)
    idfarm                             VARCHAR(100)     , -- $..idFarm
    farmname                           VARCHAR(200)     , -- $..farmName
    idretiro                           VARCHAR(100)     , -- $..idRetiro
    retironame                         VARCHAR(100)     , -- $..retiroName
    idowner                            VARCHAR(100)     , -- $..idOwner
    ownername                          VARCHAR(200)     , -- $..ownerName
    idplherdtype                       VARCHAR(100)     , -- $..idPlHerdType
    plherdtypename                     VARCHAR(100)     , -- $..plHerdTypeName
    idcurrency                         VARCHAR(100)     , -- $..idCurrency
    currencyname                       VARCHAR(100)     , -- $..currencyName
    plversioncode                      VARCHAR(100)     , -- $..plVersionCode
    plversionname                      VARCHAR(100)     , -- $..plVersionName
    month                              DOUBLE PRECISION , -- $..month
    date                               VARCHAR(20)      , -- $..date
    harvest                            VARCHAR(20)      , -- $..harvest
    anosafra                           VARCHAR(10)      , -- $..anoSafra
    idcategory                         VARCHAR(100)     , -- $..idCategory
    categoryname                       VARCHAR(100)     , -- $..categoryName
    idanimalgroup                      VARCHAR(100)     , -- $..idAnimalGroup
    animalgroupname                    VARCHAR(100)     , -- $..animalGroupName
    age                                VARCHAR(20)      , -- $..age
    gender                             VARCHAR(20)      , -- $..gender
    amount                             DOUBLE PRECISION   -- $..amount
);

-- origem: get_prevrebanhomedio.ktr / passo "INSERT PREV REBANHOMEDIO" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_rebanhomedioprevisto (
    idcustomer                         VARCHAR(100)     , -- $..idCustomer
    customername                       VARCHAR(100)     , -- $..customerName
    idfarm                             VARCHAR(100)     , -- $..idFarm
    farmname                           VARCHAR(200)     , -- $..farmName
    idretiro                           VARCHAR(100)     , -- $..idRetiro
    retironame                         VARCHAR(200)     , -- $..retiroName
    idowner                            VARCHAR(100)     , -- $..idOwner
    ownername                          VARCHAR(200)     , -- $..ownerName
    idplherdtype                       VARCHAR(100)     , -- $..idPlHerdType
    plherdtypename                     VARCHAR(100)     , -- $..plHerdTypeName
    idcurrency                         VARCHAR(100)     , -- $..idCurrency
    currencyname                       VARCHAR(100)     , -- $..currencyName
    plversioncode                      VARCHAR(100)     , -- $..plVersionCode
    plversionname                      VARCHAR(100)     , -- $..plVersionName
    month                              VARCHAR(10)      , -- $..month
    harvest                            VARCHAR(20)      , -- $..harvest
    anosafra                           VARCHAR(20)      , -- $..anoSafra
    idcategory                         VARCHAR(100)     , -- $..idCategory
    categoryname                       VARCHAR(100)     , -- $..categoryName
    idanimalgroup                      VARCHAR(100)     , -- $..idAnimalGroup
    animalgroupname                    VARCHAR(100)     , -- $..animalGroupName
    age                                VARCHAR(10)      , -- $..age
    gender                             VARCHAR(20)      , -- $..gender
    idevolution                        VARCHAR(100)     , -- $..idEvolution
    type                               VARCHAR(20)      , -- $..type
    originmovement                     VARCHAR(100)     , -- $..originMovement
    amount                             DOUBLE PRECISION , -- $..amount
    reproductiveoption                 VARCHAR(100)     , -- $..reproductiveOption
    date                               VARCHAR(20)        -- $..date
);

-- origem: get_prevvendas.ktr / passo "INSERT PREV COMPRAS" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_vendasasprevisto (
    idcustomer                         VARCHAR(100)     , -- stg_customers (via Merge Join)
    customer                           VARCHAR(100)     , -- stg_customers (via Merge Join)
    idfarm                             VARCHAR(100)     , -- $..idFarm
    farmname                           VARCHAR(200)     , -- $..farmName
    idretiro                           VARCHAR(100)     , -- $..idRetiro
    retironame                         VARCHAR(100)     , -- $..retiroName
    idowner                            VARCHAR(100)     , -- $..idOwner
    ownername                          VARCHAR(200)     , -- $..ownerName
    idplherdtype                       VARCHAR(100)     , -- $..idPlHerdType
    plherdtypename                     VARCHAR(100)     , -- $..plHerdTypeName
    idcurrency                         VARCHAR(100)     , -- $..idCurrency
    currencyname                       VARCHAR(200)     , -- $..currencyName
    month                              VARCHAR(20)      , -- $..month
    date                               VARCHAR(20)      , -- $..date
    harvest                            VARCHAR(10)      , -- $..harvest
    anosafra                           VARCHAR(10)      , -- $..anoSafra
    idcategory                         VARCHAR(100)     , -- $..idCategory
    categoryname                       VARCHAR(100)     , -- $..categoryName
    idanimalgroup                      VARCHAR(100)     , -- $..idAnimalGroup
    animalgroupname                    VARCHAR(100)     , -- $..animalGroupName
    age                                VARCHAR(20)      , -- $..age
    gender                             VARCHAR(20)      , -- $..gender
    amount                             DOUBLE PRECISION , -- $..amount
    weight                             DOUBLE PRECISION , -- $..weight
    arrobavalue                        DOUBLE PRECISION , -- $..arrobaValue
    arrobaweight                       DOUBLE PRECISION , -- $..arrobaWeight
    value                              DOUBLE PRECISION , -- $..value
    totalvalue                         DOUBLE PRECISION , -- $..totalValue
    yield                              DOUBLE PRECISION , -- $..yield
    tipo                               VARCHAR(20)        -- $..type
);

-- origem: get_rebanho_medio.ktr / passo "INSERT REBANHO MÉDIO" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_rebanho_medio (
    idcustomer                         VARCHAR(100)     , -- stg_customers (via Merge Join)
    customer                           VARCHAR(100)     , -- stg_customers (via Merge Join)
    idfarm                             VARCHAR(100)     , -- $..idFarm
    farmname                           VARCHAR(200)     , -- $..farmName
    idretiro                           VARCHAR(100)     , -- $..idRetiro
    retironame                         VARCHAR(100)     , -- $..retiroName
    owner                              VARCHAR(200)     , -- $..owner
    anosafra                           VARCHAR(20)      , -- $..anoSafra
    amount                             DOUBLE PRECISION , -- $..amount
    gender                             VARCHAR(100)     , -- $..gender
    idcategory                         VARCHAR(100)     , -- $..idCategory
    category                           VARCHAR(200)     , -- $..category
    month                              VARCHAR(10)        -- $..month
);

-- origem: get_rebanhomedio.ktr / passo "INSERT RebanhoMedio" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_rebanhomedio (
    idcustomer                         VARCHAR(100)     , -- stg_customers (via Merge Join)
    customer                           VARCHAR(100)     , -- stg_customers (via Merge Join)
    idfarm                             VARCHAR(100)     , -- $..idFarm
    farmname                           VARCHAR(200)     , -- $..farmName
    idretiro                           VARCHAR(100)     , -- $..idRetiro
    retironame                         VARCHAR(100)     , -- $..retiroName
    owner                              VARCHAR(200)     , -- $..owner
    anosafra                           VARCHAR(20)      , -- $..anoSafra
    idcategory                         VARCHAR(100)     , -- $..idCategory
    category                           VARCHAR(100)     , -- $..category
    amount                             DOUBLE PRECISION , -- $..amount
    month                              VARCHAR(10)      , -- $..month
    weight                             DOUBLE PRECISION , -- $..weight
    groupcategory                      VARCHAR(100)     , -- $..groupCategory
    gender                             VARCHAR(100)       -- $..gender
);

-- origem: get_vendas.ktr / passo "INSERT Vendas" (truncate=Y)
CREATE TABLE IF NOT EXISTS "DATABASE".stg_vendas (
    idcustomer                         VARCHAR(100)     , -- stg_customers (via Merge Join)
    customer                           VARCHAR(100)     , -- stg_customers (via Merge Join)
    farmname                           VARCHAR(200)     , -- $..farmName
    idretiro                           VARCHAR(100)     , -- $..idRetiro
    retironame                         VARCHAR(100)     , -- $..retiroName
    owner                              VARCHAR(200)     , -- $..owner
    date                               VARCHAR(20)      , -- $..date
    anosafra                           VARCHAR(10)      , -- $..anoSafra
    gender                             VARCHAR(10)      , -- $..gender
    client                             VARCHAR(100)     , -- $..client
    category                           VARCHAR(100)     , -- $..category
    categoryid                         VARCHAR(100)     , -- $..categoryId
    amount                             DOUBLE PRECISION , -- $..amount
    liveweightavg                      DOUBLE PRECISION , -- $..liveWeightAVG
    weighttotal                        DOUBLE PRECISION , -- $..weightTotal
    deadarrobaavg                      DOUBLE PRECISION , -- $..deadArrobaAvg
    deadweightavg                      DOUBLE PRECISION , -- $..deadWeightAvg
    valueweight                        DOUBLE PRECISION , -- $..valueWeight
    valuearroba                        DOUBLE PRECISION , -- $..valueArroba
    totalfaturamento                   DOUBLE PRECISION , -- $..totalFaturamento
    discounts                          DOUBLE PRECISION , -- $..discounts
    harvest                            VARCHAR(20)      , -- $..harvest
    birth                              VARCHAR(20)      , -- $..birth
    additions                          DOUBLE PRECISION , -- $..additions
    tipo                               VARCHAR(15)        -- $..tipo
);
```

---

## 6. Mapeamento endpoint → tabela atual → campos do DTO

Legenda: **gravados/total** = campos do DTO que chegam à tabela vindos do payload (`idCustomer`/`customer` normalmente vêm de `stg_customers` e não entram na contagem, exceto em prevdesmame/prevrebanhomedio/prevmortes/prevnascimentos, onde vêm do JSON); **extraídos e descartados** = lidos pelo JSON Input mas não gravados; **ignorados** = nem extraídos; **caminhos inexistentes** = `$..x` que não existem no DTO (sempre nulos). Gerado por `scripts/gen_mapping.py`.

| Endpoint | Transformação (status) | Tabela | DTO | Gravados/total | Extraídos e descartados | Ignorados (não extraídos) | Caminhos inexistentes no DTO |
|---|---|---|---|---|---|---|---|
| `balanco-pecuario` | get_balanco (job) | `stg_balanco_pecuario` | `ApiMetryxLiBalanceDTO` | 13/15 | — | — | — |
| `categoria` | get_categories (job) | `stg_category` | `ApiMetryxLiCategoriesDTO` | 5/7 | — | — | — |
| `compra-mensal-planejamento` | get_prevcompras (job) | `stg_comprasprevisto` | `ApiMetryxPlBuyingMonthlyDTO` | 26/32 | plVersionCode, plVersionName | currencyCode, reproductiveOption | — |
| `compra-pecuario` | get_compras (job) | `stg_compras` | `ApiMetryxLiBuyDTO` | 18/24 | — | idFarm, tipo, additions, discounts | — |
| `desmame-mensal-planejamento` | get_prevdesmame (job) | `stg_desmameprevisto` | `ApiMetryxPlWeaningMonthlyDTO` | 31/32 | — | currencyCode | — |
| `desmames-pecuario` | get_desmames (job) | `stg_desmames` | `ApiMetryxDesmamesPecuariosDTO` | 17/19 | — | — | — |
| `estoque-medio-mensal-planejamento` | get_prevrebanhomedio (job) | `stg_rebanhomedioprevisto` | `ApiMetryxPlAverageStockMonthlyDTO` | 29/30 | — | currencyCode | — |
| `fazenda` | get_farms (job) | `stg_farm` | `ApiMetryxFazendasDTO` | 2/4 | — | — | — |
| `lancamento-financeiro` | get_dre (job) | `stg_dre` | `ApiMetryxLancamentoFinanceiroDTO` | 24/35 | clientProvider, documents, project | idFarmFiscal, cpfCnpj, idBankAccount, banckAccount, addition, discount | — |
| `morte-mensal-planejamento` | get_prevmortes (job) | `stg_mortesprevisto` | `ApiMetryxPlDeathMonthlyDTO` | 24/27 | — | currencyCode, reproductiveOption | — |
| `morte-pecuario` | get_morte (job) | `stg_mortes` | `ApiMetryxDeathsDTO` | 23/26 | notes | — | — |
| `nascimento-mensal-planejamento` | get_prevnascimentos (job) | `stg_nascimentosprevisto` | `ApiMetryxPlBirthMonthlyDTO` | 24/26 | — | currencyCode | — |
| `nascimento-pecuario` | get_nascimentos (job) | `stg_nascimentos` | `ApiMetryxLiBirthDTO` | 12/14 | — | — | — |
| `previsao-financeiro` | get_prevdre (job) | `stg_dreprevisto` | `ApiMetryxFiPrevisionDTO` | 18/25 | project, uuidProject | cultivation, dueDate, classificationAnalyticDisbursement | — |
| `rebanho-medio-pecuario` | get_rebanho_medio (job) | `stg_rebanho_medio` | `ApiMetryxLiAvgRebanhoDTO` | 11/15 | — | weight, groupCategory | — |
| `utilizacao-pasto` | get_area (job) | `stg_area` | `ApiMetryxPastureUtilizationDTO` | 16/16 | — | — | — |
| `venda-mensal-planejamento` | get_prevvendas (job) | `stg_vendasasprevisto` | `ApiMetryxPlSaleMonthlyDTO` | 28/34 | plVersionCode, plVersionName | currencyCode, reproductiveOption | — |
| `venda-pecuario` | get_vendas (job) | `stg_vendas` | `ApiMetryxLiSaleDTO` | 23/26 | — | idFarm | — |
| `mudanca-categoria-pecuario` | get_mudanca_cat (ÓRFÃ) | `stg_mudanca_categoria` | `ApiMetryxLiCategoryChangeDTO` | 13/16 | — | harvest | — |
| `mudanca-categoria-pecuario` | get_transferencias (ÓRFÃ) | `stg_balanco_pecuario` | `ApiMetryxLiCategoryChangeDTO` | 9/16 | harvest | uuidCategoryOrigin, categoryOrigin, uuidCategoryDestiny, categoryDestiny | category, uuidCategory |
| `rebanho-medio-pecuario` | get_rebanhomedio (ÓRFÃ) | `stg_rebanhomedio` | `ApiMetryxLiAvgRebanhoDTO` | 13/15 | — | — | — |

Linha especial — `GET /customers` (não documentado) via `get_customer`: grava `idCustomer`, `customer`, `listToken[].token` (em texto puro) + `idFarm`, `farmName` de `/fazenda` em `stg_customers`.

Consumo pelo Power BI (`pbix_metryx/power_query.csv`, DSN ODBC `DATALAKE_METRYX`): `stg_balanco_pecuario` (fSaldoGado), `stg_category`, `stg_compras` (2 consultas), `stg_comprasprevisto`, `stg_customers` (só idcustomer/customer/idfarm/farmname), `stg_desmames`, `stg_dre` e `stg_dreprevisto` (financeiroDre, fMetasDre, fPlanejadoxRealizado), `stg_farm` (join por nome com vendas/compras), `stg_mortes`, `stg_mortesprevisto`, `stg_nascimentos`, `stg_nascimentosprevisto`, `stg_rebanho_medio` (realizado **e** "metas"), `stg_vendas` (abate × em pé por `deadarrobaavg` nulo), `stg_vendasasprevisto` (`tipo ilike '%abate%'` / `'%em%'`). **Não consumidas:** `stg_area`, `stg_desmameprevisto`, `stg_rebanhomedioprevisto`, `stg_rebanhomedio`, `stg_mudanca_categoria`.

---

## 7. Fragilidades e riscos

Severidade: **C** crítica, **A** alta, **M** média, **B** baixa.

### 7.1 Segurança

| # | Sev. | Fragilidade | Evidência |
|---|---|---|---|
| S1 | C | Tokens JWT hardcoded em 22 arquivos .ktr (token mestre + token de cliente), sem expiração | `Data grid.X-Auth-Token` em todos os .ktr; claims sem `exp` |
| S2 | C | Tokens de **todos** os clientes gravados em texto puro em `"DATABASE".stg_customers.token`, no mesmo schema lido pelo Power BI via ODBC | `get_customer` → `INSERT Customers and Farms` |
| S3 | A | Senha do PostgreSQL com ofuscação reversível "Encrypted" do Kettle em cada .ktr; ETL usa o **superusuário `postgres`** | `<connection>` de todos os .ktr |
| S4 | A | Senha SMTP (Gmail) com ofuscação reversível em 11 entradas; alertas indo para conta pessoal | entradas MAIL do job |
| S5 | A | JSON bruto de vendas de todos os clientes gravado em disco a cada execução | `get_vendas` → `Text file output` → `C:\Users\TerraDev\Documents\teste.txt` |
| S6 | M | API expõe `cpfCnpj` (lançamentos) — dado pessoal (LGPD); hoje não carregado, cuidado ao ampliar | DTO `ApiMetryxLancamentoFinanceiroDTO` |
| S7 | M | Arquivos com segredos ficam em `Documents` sem controle de acesso/versão; tokens provavelmente também em backups/cópias | — |

### 7.2 Confiabilidade

| # | Sev. | Fragilidade | Evidência |
|---|---|---|---|
| R1 | C | Erros do REST Client desviados para `Dummy` e status HTTP nunca verificado: 401/403/500/timeout de um cliente = dados do cliente **somem** sem alerta (tabela já truncada) | `step_error_handling` → `Dummy (do nothing)` em 20 .ktr; `result.code` vazio |
| R2 | C | Esvaziamento em cascata: se `/customers` responder erro, `stg_customers` fica vazia e as 18 transformações seguintes truncam suas tabelas e inserem 0 linhas | Template `Select Customers` + `truncate=Y` |
| R3 | A | TRUNCATE + INSERT não atômico (`commit=1000`, `unique_connections=N`): BI vê tabela vazia/parcial durante a carga; falha no meio deixa a tabela parcial | Table Output |
| R4 | A | Sem timeout, retry, backoff ou limite de taxa; chamadas sequenciais | REST Client sem opções |
| R5 | A | Falha do e-mail "Start Service" impede toda a extração (hop "só se OK") | `Start (2) → fCustomer` |
| R6 | M | 11 entradas sem e-mail de erro (fCategories, fDesmame, fDre, fRebanhoMedio, fMortes, 6 fMetas) e assuntos trocados (fFarms → "fArea", fArea → "fNascimento", fBalanco → "fMovimentacao"); e-mail sem log/detalhe | Hops do job |
| R7 | M | Sem log persistente (sem log table/arquivo), sem histórico de execuções/volumes | `job-log-table` vazio, `set_logfile=N` |
| R8 | M | Caminhos absolutos no perfil do usuário; dependência cruzada com o projeto de planilhas (`d_rls.ktr`, banco `DATALAKE_PLAN`, Excel no Google Drive local) | entradas TRANS |
| R9 | M | Agendamento externo não versionado/não localizado | `Start.repeat=N` |
| R10 | M | Colunas de data com `VARCHAR(10)`: se a API passar a mandar data-hora, o INSERT falha **depois** do TRUNCATE | Select values (length 10) |

### 7.3 Corretude dos dados

| # | Sev. | Fragilidade | Evidência |
|---|---|---|---|
| D1 | C | `get_transferencias` chama o endpoint errado e grava com TRUNCATE em `stg_balanco_pecuario` (apaga o balanço se executada) | Data grid `mudanca-categoria-pecuario`; Table Output `STG_BALANCO_PECUARIO` |
| D2 | A | `get_mudanca_cat` lê arquivo local (`IsInFields=N`) em vez da resposta da API | JSON Input |
| D3 | A | Versões de planejamento misturadas: `plVersionCode/Name` não gravados em compras e vendas previstas | get_prevcompras, get_prevvendas |
| D4 | A | `idFarm` não gravado em vendas e compras; BI faz join por `farmname` (homônimos, renomeações, espaços invisíveis — o BI já usa `translate()` para remover U+200B etc. em outra consulta) | get_vendas, get_compras; consultas `pecuarioVenda*`, `pecuarioCompras` |
| D5 | A | Conversão numérica dependente de locale: campos tipo `None` (texto) convertidos para Number; gambiarra `.`→`,`; BI tem filtro temporário para valores ≥ 1e9 no DRE ("erro de escala na origem") — causa provável no parsing (notação científica/separadores) ou na própria API; precisa ser verificada com payload real | `Param Amount`; `fPlanejadoxRealizado` |
| D6 | M | Duplicação silenciosa se um cliente tiver mais de um token na `listToken` (cada token baixa tudo de novo) | `GROUP BY idcustomer, customer, token` |
| D7 | M | `$..campo` (busca recursiva) + "zip" por índice: se a API omitir chaves nulas ou aninhar objetos, campos desalinham entre linhas sem erro | JSON Input em todos |
| D8 | M | Linhas com `amount`/`totalValue` nulos descartadas sem registro de rejeição | Filter rows → Dummy 2 |
| D9 | M | `stg_area` sem `idcustomer`; nomes de coluna de cliente inconsistentes (`customer` × `customername`); origem do `idcustomer` varia (stg_customers × JSON) | ver 2.1 |
| D10 | M | Rebanho médio duplicado (`stg_rebanho_medio` × `stg_rebanhomedio`); BI "fMetasRebanhoMedio" lê o **realizado**; `stg_rebanhomedioprevisto` não usado | get_rebanho_medio / get_rebanhomedio |
| D11 | M | Datas como texto em formatos diferentes (`YYYY-MM-DD`, `MM/YY`); `month` às vezes Number, às vezes String | DDL seção 5 |
| D12 | B | `dataInicio/dataFim` (área) convertidas para `TIMESTAMP` no fuso da JVM: em datas de início do antigo horário de verão brasileiro (até 2019) a meia-noite não existe e o valor vira 01:00 — usar `DATE` | get_area |
| D13 | B | DTO com valores monetários `int64` (possível arredondamento na API) | Swagger |

### 7.4 Desempenho e escala

| # | Sev. | Fragilidade |
|---|---|---|
| P1 | A | Recarga completa de tudo a cada execução: `1 + 20 × N_tokens` downloads completos, sem detecção de mudança; `/fazenda` baixado 2× |
| P2 | M | Resposta inteira mantida em um campo String por linha (memória) — risco com `lancamento-financeiro` de clientes grandes |
| P3 | M | Uma chamada por vez; o tempo total cresce linearmente com o número de clientes |

### 7.5 Manutenibilidade

| # | Sev. | Fragilidade |
|---|---|---|
| M1 | M | Transformações copiadas com nomes enganosos ("get prevcompras" em prevmortes/prevvendas, "INSERT PREV REBANHOMEDIO" em prevdesmame, "get rebanhomedio" em balanço/farms/transferências, "Decode Categories" em todas) |
| M2 | B | Duas conexões (`METRIX`, `METRYX`) para o mesmo banco; tabela com erro de digitação (`stg_vendasasprevisto`); comprimento `1001` em `oldanimalgroupid` |
| M3 | B | Restos de desenvolvimento: tokens não usados no Data grid, `ARRAY_AGG` comentado + `Replace in string` de chaves, hops desabilitados, arquivos JSON de Desktop configurados |
| M4 | B | Sem testes, sem versionamento, sem documentação; Spoon como único "IDE" |

---

## 8. Especificação do Metryx API Adapter (Python)

### 8.1 Princípios

1. **Somente leitura.** Allow-list de endpoints GET; `POST control-birth` nunca é registrado.
2. **Snapshot completo + diff do nosso lado.** A API não filtra nem pagina; "incremental" = não reprocessar quando o payload não mudou e aplicar mudanças de forma atômica e auditável.
3. **Bruto primeiro (landing), canônico depois.** Todo payload é guardado (jsonb + hash) antes de qualquer transformação; normalização é reexecutável a partir do bruto (replay sem chamar a API).
4. **Atomicidade por (tenant, endpoint).** Nada de TRUNCATE global: cada tenant é substituído em uma transação; leitores nunca veem tabela vazia.
5. **Falhar alto, isolar o dano.** Erro de um tenant/endpoint não afeta os outros, mas sempre gera registro e alerta; guardas impedem que uma resposta vazia/parcial apague dados bons.
6. **Mesmo modelo canônico do adapter de planilhas** (`source_system = 'metryx' | 'planilha'`), com `tenant_id`/`farm_id` em todas as linhas para RLS.
7. **Segredos fora do código e do banco em claro.**

### 8.2 Módulos

```
metryx_adapter/
  config.py          # pydantic-settings: base_url, timeouts, concorrência, chaves de cifra (via env/secret manager)
  client.py          # MetryxClient (httpx + tenacity + rate limiter), classificação de erros
  credentials.py     # CredentialStore: busca/decifra token por tenant, valida, marca inválido
  endpoints.py       # Registro declarativo dos endpoints (path, DTO, estratégia, chave, frequência, janela)
  models/            # Pydantic v2 por DTO (extra="allow" para detectar campos novos), parse de datas/decimais
  landing.py         # grava raw.metryx_payload (jsonb + sha256) e etl.sync_run_item
  normalize/         # 1 módulo por entidade: DTO -> linhas canônicas (+ row_hash/occurrence)
  loaders.py         # replace_partition() e upsert() transacionais, guardas de volume
  sync.py            # orquestração: tenants × endpoints, locks, métricas
  compat_views.sql   # views "DATABASE".stg_* para o Power BI durante a transição
  cli.py             # `metryx sync --tenant X --endpoint Y`, `metryx replay --run-id`, `metryx check-credentials`
tests/               # fixtures sanitizadas por DTO, testes de contrato, testes de paridade com stg_*
```

### 8.3 Cliente HTTP

| Aspecto | Especificação |
|---|---|
| Biblioteca | `httpx` (sync ou async; recomendado `httpx.AsyncClient` com HTTP/1.1, `http2=False` até confirmar suporte do servidor) |
| Base URL | `https://web-srv.metryx.app:8444/mtxserver` (configurável por ambiente) |
| Headers | `x-auth-token: <token do tenant>`, `Accept: application/json`, `Accept-Encoding: gzip`, `User-Agent: projeto-terra-metryx-adapter/<versão>` |
| Timeouts | `connect=10s`, `read=180s` (lançamentos financeiros podem ser grandes), `write=10s`, `pool=30s` |
| Retries | `tenacity`: até 5 tentativas, `wait_exponential_jitter(initial=2, max=60)`; repetir em `httpx.TransportError`/`TimeoutException`, HTTP 429, 500, 502, 503, 504; respeitar `Retry-After` |
| Sem retry | 400, 401 (`CredentialInvalid`), 403 (`EndpointForbidden`), 404 (`EndpointGone`) |
| Concorrência | Semáforo global (padrão 3) + no máximo 1 requisição simultânea por tenant + token bucket global (padrão 2 req/s). Ajuste adaptativo: em 429, reduzir para 1 e dobrar o intervalo |
| Circuit breaker | Se > 50% das chamadas falharem em 5 min (ou 5 falhas seguidas de rede), abrir por 10 min e alertar |
| Validação | Corpo deve ser JSON **array** (o content-type é `*/*`, então não confiar no header); objeto/HTML = `UnexpectedPayload`; `json.loads(body, parse_float=Decimal)` para não perder precisão |
| Tamanho | Logar bytes; alerta se > 50 MB; usar `client.stream()` e acumular em memória com limite (ou `ijson` se crescer) |
| Logs | Event hook que **remove** `x-auth-token` de logs/exceções; logar tenant, endpoint, status, bytes, duração, tentativa, hash |
| TLS | Verificação padrão (certifi); nunca `verify=False` |

### 8.4 Credenciais por tenant e "refresh"

- **Não existe refresh de token na API.** Os JWTs não têm `exp`. "Refresh" = **rotação controlada** + **verificação periódica**.
- Tabela (schema `integration`, acesso só da role `etl_adapter`):

```sql
CREATE TABLE integration.metryx_credential (
    credential_id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           uuid NOT NULL REFERENCES core.tenant(tenant_id),
    metryx_customer_id  text NOT NULL,                 -- idCustomer esperado no payload
    kind                text NOT NULL CHECK (kind IN ('customer','master')),
    token_ciphertext    bytea NOT NULL,                -- envelope encryption (Fernet/AES-GCM; chave no secret manager)
    token_fingerprint   text NOT NULL,                 -- sha256(token)[:12], só para auditoria
    jwt_sub             text, jwt_id text,             -- metadados do JWT (decode sem verificar assinatura)
    status              text NOT NULL DEFAULT 'active' CHECK (status IN ('active','invalid','revoked','rotating')),
    last_validated_at   timestamptz, last_error text,
    created_at          timestamptz NOT NULL DEFAULT now(), rotated_at timestamptz,
    UNIQUE (tenant_id, metryx_customer_id, token_fingerprint)
);
CREATE TABLE integration.metryx_entitlement (      -- permissões por endpoint descobertas (403)
    credential_id uuid REFERENCES integration.metryx_credential, endpoint text,
    allowed boolean NOT NULL, checked_at timestamptz NOT NULL, PRIMARY KEY (credential_id, endpoint));
```

- **Onboarding:** (a) manual — admin cadastra o token do cliente pela UI (campo write-only), o adapter chama `/fazenda` para validar e confere que `idCustomer` do payload = `metryx_customer_id`; (b) descoberta opcional — com credencial `master`, chamar `GET /customers` (se a Metryx confirmar o contrato) e **propor** os clientes/tokens para aprovação; nunca persistir tokens sem cifrar.
- **Validação diária:** `GET /fazenda` por credencial (barato). 401 → `status='invalid'`, pula o tenant, alerta "token inválido/revogado". 403 em um endpoint → `metryx_entitlement.allowed=false`, pula só esse endpoint (reverifica semanalmente).
- **Um token por tenant ativo:** se houver mais de um, usar só o mais recente válido (elimina a duplicação D6).
- **Rotação pós-migração:** pedir à Metryx novos tokens (mestre e por cliente) e revogar os que estão em `.ktr`, em `stg_customers` e em backups; depois `ALTER TABLE "DATABASE".stg_customers DROP COLUMN token`.

### 8.5 Registro de endpoints, chaves e janelas de sincronização

Como não há parâmetros, toda chamada traz o histórico completo. A "janela" define **quais linhas canônicas podem ser alteradas** por uma sincronização: `full` = substitui todo o histórico do tenant naquele endpoint; `aberto` = aplica apenas anos-safra abertos (atual + anterior) e, se o snapshot trouxer mudanças em anos-safra fechados, **não aplica** e gera alerta de "alteração retroativa" para revisão do consultor (protege relatórios já entregues). Recomenda-se começar com `full` em tudo e ativar `aberto` por tenant quando houver processo de fechamento de safra.

| Endpoint | Entidade canônica | Freq. sugerida | Estratégia de carga | Chave idempotente (upsert/partição) | Janela |
|---|---|---|---|---|---|
| `fazenda` | `core.farm` | diária + no onboarding | UPSERT + soft-delete de ausentes | `(tenant_id, source_system, source_farm_id=idFarm)` | full |
| `retiro` | `core.retiro` | diária | UPSERT + soft-delete | `(tenant_id, source_retiro_id=idRetiro)` | full |
| `categoria` | `core.animal_category` | diária | UPSERT + soft-delete | `(tenant_id, source_category_id=idCategory)` | full |
| `balanco-pecuario` | `fact.herd_movement` | 2×/dia | replace partition | partição `(tenant_id, 'balanco')`; PK `(tenant_id, source_endpoint, row_hash, occurrence)` | full → aberto |
| `saldo-inical-pecuario` | `fact.herd_event` (`SALDO_INICIAL`) | diária | replace partition | idem | full |
| `nascimento-pecuario` | `fact.herd_event` (`NASCIMENTO`) | 2×/dia | replace partition | idem | full → aberto |
| `desmames-pecuario` | `fact.herd_event` (`DESMAME`) | 2×/dia | replace partition | idem | full → aberto |
| `morte-pecuario` | `fact.herd_event` (`MORTE`) | 2×/dia | replace partition | idem | full → aberto |
| `venda-pecuario` | `fact.herd_event` (`VENDA`) | 2×/dia | replace partition | idem (+ `farm_id` resolvido por `idFarm`) | full → aberto |
| `compra-pecuario` | `fact.herd_event` (`COMPRA`) | 2×/dia | replace partition | idem | full → aberto |
| `mudanca-categoria-pecuario` | `fact.herd_event` (`MUDANCA_CATEGORIA`) | 2×/dia | replace partition | idem | full → aberto |
| `transferencia-animal-pecuario` | `fact.herd_event` (`TRANSFERENCIA`) | 2×/dia | UPSERT + delete de ausentes | `(tenant_id, source_id=id, source_item_id=itemId)` | full |
| `rebanho-medio-pecuario` | `fact.herd_avg_monthly` | diária | replace partition | `(tenant_id, row_hash, occurrence)` | full |
| `*-mensal-planejamento` (6) | `fact.plan_herd_monthly` + `plan.scenario` | diária (ou sob demanda após revisão do orçamento) | replace partition **por versão** | partição `(tenant_id, endpoint, plVersionCode)`; PK `(tenant_id, source_endpoint, pl_version_code, row_hash, occurrence)` | full |
| `previsao-fluxo-caixa-planejamento` | `fact.fin_cashflow_plan` | diária | replace partition por versão | `(tenant_id, pl_version_code, row_hash, occurrence)` | full |
| `lancamento-financeiro` | `fact.fin_entry` | 2×/dia | UPSERT + delete de ausentes | `(tenant_id, id_financial_entry, coalesce(id_payment,''), coalesce(parcel,''))` — validar unicidade no 1º payload; se não for única, cair para replace partition | full → aberto |
| `previsao-financeiro` | `fact.fin_forecast` | diária | replace partition | `(tenant_id, row_hash, occurrence)` | full |
| `utilizacao-pasto` | `fact.pasture_use` | semanal | UPSERT + delete de ausentes | `(tenant_id, pasture_id=id, tipo_uso_id)` | full |
| `confina-tech` | `fact.input_movement` | diária (só tenants habilitados) | UPSERT + delete de ausentes | `(tenant_id, product_entry_uuid)` (validar) | full |
| `control-birth` | — | **nunca** | — | — | — |

`row_hash` = SHA-256 do objeto do DTO serializado de forma canônica (chaves ordenadas, decimais normalizados, strings `strip()`); `occurrence` = ordinal 1..k entre objetos idênticos do mesmo snapshot (preserva duplicatas legítimas, ex.: duas vendas iguais no mesmo dia, sem inventar unicidade).

### 8.6 Landing bruto e controle de execução

```sql
CREATE SCHEMA IF NOT EXISTS raw;  CREATE SCHEMA IF NOT EXISTS etl;

CREATE TABLE etl.sync_run (
    run_id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    trigger      text NOT NULL,                 -- schedule | manual | replay | onboarding
    started_at   timestamptz NOT NULL DEFAULT now(), finished_at timestamptz,
    status       text NOT NULL DEFAULT 'running' CHECK (status IN ('running','success','partial','failed')),
    adapter_version text NOT NULL
);
CREATE TABLE etl.sync_run_item (
    run_id uuid REFERENCES etl.sync_run, tenant_id uuid NOT NULL, endpoint text NOT NULL,
    status text NOT NULL CHECK (status IN ('success','unchanged','skipped','held','failed')),
    http_status int, attempts int, bytes bigint, duration_ms int, payload_sha256 text,
    rows_in int, rows_inserted int, rows_deleted int, rows_rejected int,
    error_class text, error_message text,          -- sem token, sem payload
    PRIMARY KEY (run_id, tenant_id, endpoint)
);
CREATE TABLE raw.metryx_payload (
    payload_id     bigserial,
    run_id         uuid NOT NULL,
    tenant_id      uuid NOT NULL,
    endpoint       text NOT NULL,
    fetched_at     timestamptz NOT NULL DEFAULT now(),
    http_status    int NOT NULL,
    payload_sha256 text NOT NULL,                  -- hash do JSON canônico
    item_count     int NOT NULL,
    payload        jsonb NOT NULL,                 -- array original (TOAST comprime)
    PRIMARY KEY (fetched_at, payload_id)
) PARTITION BY RANGE (fetched_at);                 -- partição mensal; retenção 90 dias, mas sempre manter o último por (tenant, endpoint)
CREATE INDEX ON raw.metryx_payload (tenant_id, endpoint, fetched_at DESC);
-- Opcional (LGPD): mascarar cpfCnpj antes de gravar o bruto, ou cifrar a coluna payload para lancamento-financeiro.
```

### 8.7 Modelo canônico (compartilhado com o adapter de planilhas) e RLS

Colunas técnicas em **todas** as tabelas canônicas: `tenant_id uuid NOT NULL`, `farm_id uuid NULL`, `source_system text NOT NULL`, `source_endpoint text`, `row_hash text`, `occurrence int`, `ingestion_run_id uuid`, `loaded_at timestamptz DEFAULT now()`, `source_extra jsonb` (campos do DTO não mapeados — nada se perde).

```sql
CREATE TABLE fact.herd_event (
    tenant_id uuid NOT NULL, farm_id uuid, retiro_id uuid,
    source_system text NOT NULL, source_endpoint text NOT NULL, row_hash text NOT NULL, occurrence int NOT NULL,
    event_type text NOT NULL CHECK (event_type IN ('NASCIMENTO','MORTE','VENDA','COMPRA','DESMAME',
                                                   'MUDANCA_CATEGORIA','TRANSFERENCIA','SALDO_INICIAL')),
    event_date date NOT NULL, event_date_raw text,
    ano_safra text, ano_safra_inicio smallint, harvest text, birth text,
    owner_name text, owner_source_id text,
    category_id uuid, category_from_id uuid, category_to_id uuid,     -- FK para core.animal_category
    gender text, qty numeric(14,3) NOT NULL,
    weight_total_kg numeric(16,3), weight_avg_kg numeric(12,3), carcass_weight_avg_kg numeric(12,3),
    carcass_arroba_avg numeric(12,4), price_per_kg numeric(14,4), price_per_arroba numeric(14,4),
    avg_value_per_head numeric(16,4), total_value numeric(18,2), additions numeric(18,2), discounts numeric(18,2),
    sale_type text, counterparty text, cause text, locale text, notes text,
    farm_from_id uuid, farm_to_id uuid, retiro_from_id uuid, retiro_to_id uuid,   -- transferências
    source_record_id text, source_item_id text,
    source_extra jsonb, ingestion_run_id uuid, loaded_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, source_endpoint, row_hash, occurrence)
);
CREATE INDEX ON fact.herd_event (tenant_id, farm_id, event_type, event_date);

CREATE TABLE plan.scenario (
    scenario_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL,
    source_system text NOT NULL, source_version_code text NOT NULL, name text, is_official boolean DEFAULT false,
    UNIQUE (tenant_id, source_system, source_version_code));

CREATE TABLE fact.plan_herd_monthly (
    tenant_id uuid NOT NULL, farm_id uuid, retiro_id uuid, scenario_id uuid NOT NULL REFERENCES plan.scenario,
    source_endpoint text NOT NULL, row_hash text NOT NULL, occurrence int NOT NULL,
    plan_type text NOT NULL CHECK (plan_type IN ('VENDA','COMPRA','NASCIMENTO','MORTE','DESMAME','ESTOQUE_MEDIO')),
    month_ref date NOT NULL, month_raw text, ano_safra text, harvest text,
    herd_type text, owner_source_id text, owner_name text, currency_code text,
    category_source_id text, category_name text, animal_group text, age text, gender text,
    category_to_source_id text, category_to_name text, animal_group_to text, age_to text, gender_to text,  -- desmame
    reproductive_option text, sale_type text, evolution_id text, origin_movement text,
    qty numeric(14,3), weight_kg numeric(12,3), yield_pct numeric(8,4), arroba_value numeric(14,4),
    arroba_weight numeric(12,4), unit_value numeric(16,4), total_value numeric(18,2),
    source_extra jsonb, ingestion_run_id uuid, loaded_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, source_endpoint, scenario_id, row_hash, occurrence)
);

CREATE TABLE fact.fin_entry (
    tenant_id uuid NOT NULL, farm_id uuid, farm_fiscal_id uuid,
    source_system text NOT NULL, id_financial_entry text NOT NULL, id_payment text NOT NULL DEFAULT '', parcel text NOT NULL DEFAULT '',
    entry_type text, status text, ano_safra text,
    emission_date date, due_date date, payment_date date, conciliation_date date,
    cost_center text, sub_center text, class_name text, code text, activity text, project text,
    description text, counterparty text, counterparty_doc_masked text,  -- cpfCnpj mascarado (LGPD)
    doc_type text, documents text, bank_account text, owner_name text, currency text,
    amount_payable numeric(18,2), amount_paid numeric(18,2), addition numeric(18,2), discount numeric(18,2),
    source_extra jsonb, ingestion_run_id uuid, loaded_at timestamptz NOT NULL DEFAULT now(), deleted_at timestamptz,
    PRIMARY KEY (tenant_id, source_system, id_financial_entry, id_payment, parcel)
);
-- Demais: core.farm, core.retiro, core.animal_category (+ core.category_map para categoria padrão Projeto Terra),
-- fact.herd_movement (balanço), fact.herd_avg_monthly, fact.fin_forecast, fact.fin_cashflow_plan,
-- fact.pasture_use, fact.input_movement — mesmo padrão de colunas técnicas.

-- RLS (exemplo): usuário vê apenas fazendas concedidas (substitui STG_RLS / planilha do Google Drive)
ALTER TABLE fact.herd_event ENABLE ROW LEVEL SECURITY;
CREATE POLICY herd_event_read ON fact.herd_event FOR SELECT TO app_reader USING (
    EXISTS (SELECT 1 FROM auth.user_farm_access a
            WHERE a.user_id = current_setting('app.user_id')::uuid
              AND a.tenant_id = herd_event.tenant_id
              AND (a.farm_id IS NULL OR a.farm_id = herd_event.farm_id)));
-- O adapter grava com a role etl_adapter (políticas próprias de INSERT/DELETE ou BYPASSRLS restrito a ela).
```

Regras de normalização importantes:
- **Datas:** realizado `YYYY-MM-DD` → `date`; planejamento `MM/YY` → primeiro dia do mês (`month_ref`); guardar o texto original em `*_raw`. Rejeitar (para `etl.rejected_row`) o que não parsear — nunca descartar em silêncio. Nada de `timestamp`: são datas civis, sem fuso. Agendamentos em `America/Sao_Paulo`; colunas técnicas `timestamptz` em UTC.
- **Números:** `Decimal` do JSON → `numeric`; nunca passar por `str` com locale. Checar faixas plausíveis (ex.: |valor| < 1e9, peso médio 0–1500 kg, preço por arroba 0–1000) e marcar outliers em vez de filtrar no BI.
- **Fazenda:** resolver `farm_id` sempre por `idFarm` (nunca por nome). Para DTOs sem `idFarm` (nenhum dos usados — vendas e compras **têm** `idFarm` no DTO), usar `farmName` apenas como fallback com alerta.
- **Cliente:** `idCustomer` do payload deve bater com o `metryx_customer_id` da credencial; divergência = erro de segurança (token trocado) → não carregar.
- **Versões de planejamento:** sempre gravar `plVersionCode`; `plan.scenario.is_official` definido pelo consultor (ou pela Metryx, se houver flag).

### 8.8 Algoritmo de sincronização (por tenant × endpoint)

```python
# metryx_adapter/sync.py (esqueleto)
import hashlib, json
from decimal import Decimal

async def sync_endpoint(run, tenant, ep, client, store, db):
    cred = await store.get_active(tenant.id)                      # decifra em memória; nunca loga
    async with db.advisory_lock(f"metryx:{tenant.id}:{ep.name}"):  # evita execuções concorrentes
        try:
            resp = await client.get_json_array(ep.path, token=cred.token)   # retries/limites dentro do client
        except CredentialInvalid:
            await store.mark_invalid(cred, "401"); return run.item(tenant, ep, "failed", error_class="CredentialInvalid")
        except EndpointForbidden:
            await store.set_entitlement(cred, ep.name, allowed=False); return run.item(tenant, ep, "skipped", http_status=403)

        items = resp.items                                          # list[dict] com Decimal
        canon = json.dumps(items, sort_keys=True, default=str, separators=(",", ":"))
        sha = hashlib.sha256(canon.encode()).hexdigest()
        await db.insert_raw(run.id, tenant.id, ep.name, resp.status, sha, len(items), items)

        last = await db.last_applied(tenant.id, ep.name)
        if last and last.sha256 == sha:
            return run.item(tenant, ep, "unchanged", payload_sha256=sha, rows_in=len(items))

        models = [ep.model.model_validate(i) for i in items]       # pydantic; extra="allow" -> drift report
        await report_schema_drift(ep, models)
        rows, rejected = ep.normalizer(tenant, models)              # canônico + row_hash/occurrence
        guard = volume_guard(previous=last.rows_in if last else None, current=len(rows))
        if guard.hold:                                              # ex.: 0 linhas ou queda > 50%
            return run.item(tenant, ep, "held", payload_sha256=sha, error_message=guard.reason)

        async with db.transaction():                                # atômico: leitores nunca veem parcial
            if ep.strategy == "replace_partition":
                stats = await db.replace_partition(ep.table, tenant.id, ep.partition_keys(models), rows)
            else:
                stats = await db.upsert_and_soft_delete(ep.table, tenant.id, ep.natural_key, rows)
            await db.write_rejects(run.id, tenant.id, ep.name, rejected)
            await db.mark_applied(tenant.id, ep.name, sha, len(rows))
        return run.item(tenant, ep, "success", payload_sha256=sha, rows_in=len(items), **stats)
```

```python
# metryx_adapter/client.py (esqueleto)
import asyncio, json, httpx
from decimal import Decimal
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt, wait_exponential_jitter

RETRY_STATUS = {429, 500, 502, 503, 504}

class MetryxClient:
    def __init__(self, base_url: str, max_concurrency: int = 3, rps: float = 2.0):
        self._http = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(connect=10, read=180, write=10, pool=30),
            headers={"Accept": "application/json", "User-Agent": "projeto-terra-metryx-adapter"},
            limits=httpx.Limits(max_connections=max_concurrency, max_keepalive_connections=max_concurrency),
        )
        self._sem = asyncio.Semaphore(max_concurrency)
        self._bucket = TokenBucket(rps)                      # implementação simples de rate limit

    async def get_json_array(self, path: str, token: str) -> "Payload":
        assert path in ALLOWED_GET_PATHS                       # allow-list: nunca control-birth
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(5), wait=wait_exponential_jitter(initial=2, max=60),
            retry=retry_if_exception(is_retryable), reraise=True):
            with attempt:
                async with self._sem:
                    await self._bucket.acquire()
                    r = await self._http.get(path, headers={"x-auth-token": token})
                if r.status_code == 401: raise CredentialInvalid(path)
                if r.status_code == 403: raise EndpointForbidden(path)
                if r.status_code == 404: raise EndpointGone(path)
                if r.status_code in RETRY_STATUS: raise RetryableHTTP(r.status_code, r.headers.get("Retry-After"))
                r.raise_for_status()
                data = json.loads(r.content, parse_float=Decimal)
                if not isinstance(data, list): raise UnexpectedPayload(path, type(data).__name__)
                return Payload(status=r.status_code, items=data, nbytes=len(r.content))
```

### 8.9 Qualidade de dados (checks por execução)

| Check | Ação |
|---|---|
| `idCustomer` do payload ≠ credencial | bloquear carga do tenant, alerta de segurança |
| Snapshot vazio quando o anterior tinha linhas / queda > 50% / crescimento > 300% | `held` + alerta; aplicar só após 2 snapshots consecutivos iguais ou aprovação manual |
| Campos obrigatórios nulos (`idFarm`, `date`, `amount`) | linha para `etl.rejected_row` (com motivo), contagem no item |
| Data/número não parseável ou fora de faixa | rejeição ou flag `is_outlier` (nunca filtro escondido no BI) |
| Campos novos no DTO / campos ausentes | relatório de schema drift (`etl.schema_drift`) + alerta |
| Duplicatas exatas (`occurrence > 1`) | métrica (não erro) |
| Fazenda/categoria desconhecida (sem `core.farm`/`core.animal_category`) | cria registro "pendente de mapeamento" + alerta para o consultor |
| Reconciliação de estoque | `saldo inicial + Σ balanço` × rebanho médio/estoque informado (quando `saldo-inical-pecuario` for ativado) |

### 8.10 Operação

- **Agendador:** cron/systemd timer, APScheduler, ou orquestrador (Prefect/Dagster) — com o código e o agendamento versionados. Fila por tenant; `pg_advisory_lock` por (tenant, endpoint).
- **Alertas:** canal corporativo (e-mail de serviço/Teams/Slack), um alerta consolidado por execução com a tabela de `sync_run_item` em falha/held; nada de conta pessoal.
- **Métricas:** duração, bytes, linhas, taxa de erro por endpoint/tenant, idade do último snapshot aplicado ("freshness") exposta no dashboard da plataforma.
- **Replay:** `metryx replay --run-id` renormaliza a partir de `raw.metryx_payload` (correções de mapeamento sem chamar a API).
- **Backfill/onboarding:** um novo tenant roda todos os endpoints uma vez com janela `full`.

### 8.11 Compatibilidade com o Power BI atual (transição)

Criar views com os nomes e colunas atuais para não quebrar o `.pbix` enquanto ele é migrado para o novo dashboard React — já corrigindo o que for compatível (ex.: incluir `idfarm` em vendas/compras e `plversioncode` nas previsões):

```sql
CREATE OR REPLACE VIEW "DATABASE".stg_vendas AS
SELECT t.metryx_customer_id AS idcustomer, t.customer_name AS customer, f.source_farm_id AS idfarm, f.name AS farmname,
       e.source_extra->>'idRetiro' AS idretiro, r.name AS retironame, e.owner_name AS owner, e.event_date_raw AS date,
       e.ano_safra AS anosafra, e.gender, e.counterparty AS client, c.name AS category, c.source_category_id AS categoryid,
       e.qty AS amount, e.weight_avg_kg AS liveweightavg, e.weight_total_kg AS weighttotal,
       e.carcass_arroba_avg AS deadarrobaavg, e.carcass_weight_avg_kg AS deadweightavg, e.price_per_kg AS valueweight,
       e.price_per_arroba AS valuearroba, e.total_value AS totalfaturamento, e.discounts, e.harvest, e.birth,
       e.additions, e.sale_type AS tipo
FROM fact.herd_event e
JOIN core.tenant_metryx t ON t.tenant_id = e.tenant_id
LEFT JOIN core.farm f ON f.farm_id = e.farm_id
LEFT JOIN core.retiro r ON r.retiro_id = e.retiro_id
LEFT JOIN core.animal_category c ON c.category_id = e.category_id
WHERE e.event_type = 'VENDA' AND e.source_system = 'metryx';
-- idem para as demais 15 tabelas consumidas (seção 6). Nunca recriar a coluna token.
```

### 8.12 Plano de migração e paridade

1. **Contenção imediata (antes do adapter):** apagar `teste.txt` e remover o `Text file output`; criar usuário PostgreSQL de leitura para o BI sem acesso a `stg_customers.token` (ou revogar `SELECT` na coluna); trocar o destino dos e-mails.
2. **Adapter em paralelo** gravando em `raw`/`fact` (sem tocar `"DATABASE".stg_*`) por 2–4 semanas.
3. **Testes de paridade diários** contra as `stg_*`: contagem por (cliente, endpoint), somas de `amount`/`totalfaturamento`/`amountpaid` por (cliente, fazenda, mês). Diferenças esperadas e documentadas: duplicatas por múltiplos tokens (D6), escala numérica (D5), versões de planejamento (D3), linhas antes descartadas por nulos (D8).
4. **Corte:** substituir as tabelas `stg_*` pelas views da 8.11, desligar o job Pentaho, **rotacionar todos os tokens e senhas** (S1–S4), remover `token` de `stg_customers`.
5. **Expansão:** ativar `transferencia-animal-pecuario`, `saldo-inical-pecuario`, `retiro`, `previsao-fluxo-caixa-planejamento`; modelar `utilizacao-pasto` (lotação UA/ha).

### 8.13 Perguntas em aberto para a Metryx

1. `GET /api-metryx/customers` é suportado oficialmente? Qual o contrato (campos de `listToken`)? Um cliente pode ter vários tokens?
2. Existem parâmetros não documentados (período, `idFarm`, `updatedSince`, paginação)? Limite de tamanho/tempo de resposta? Rate limit?
3. Ciclo de vida dos tokens: expiram? Como revogar/rotacionar? Lista de permissões por endpoint (como `UTILIZACAO_PASTO`)?
4. Formato oficial de cada campo de data (`date`, `month`, `birth`, `harvest`, `anoSafra`) e tipos numéricos reais (os `int64` monetários arredondam?).
5. É possível expor IDs estáveis para os eventos pecuários (venda, compra, morte, nascimento, desmame, balanço)? Isso permitiria upsert/CDC real.
6. `balanco-pecuario` já inclui transferências e saldo inicial? Qual a convenção de sinal de `amount`?
7. Planejamento: como identificar a versão "oficial/ativa" (`plVersionCode`)?
8. O que faz exatamente `POST control-birth` (para documentar a proibição)?
