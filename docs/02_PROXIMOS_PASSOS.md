# Projeto Terra — Próximos passos (retomada em outra máquina)

> Estado em 15/10/2026: base de integração, motor e os dois adapters implementados, com testes, e validados contra os
> BIs atuais (§0); fatia vertical (login → escopo → página Movimentação do Gado) pronta (§3). Este arquivo é o ponto
> de partida da próxima sessão.

---

## 0. Estado da implementação (atualizado em 14/10/2026)

Decisões tomadas pelo usuário em 14/10:
- **Não há tenant.** O RLS é por usuário → fazendas (N:N), e o admin vê tudo.
- As dimensões de referência são globais.
- **O número tem que bater com os BIs atuais**; a forma do cálculo é livre.
- Estoque Metryx: a referência é o SQL `fSaldoGado` (`docs/referencias/pbix_metryx/power_query.csv`).

Feito (base de integração, com testes):

| Item | Situação |
|---|---|
| 1.1 | Feito em parte: `docker-compose.yml` só com o `db` (Postgres 16 em `127.0.0.1:55432`); `.env.example`; README. Os demais serviços entram quando houver o que rodar |
| 1.2 | `pyproject.toml` pinado; config, logging, ruff, pytest com Postgres real (banco descartável por execução) |
| 1.3 | Migração 0001: papéis `app_owner`/`app_user`/`app_etl` (via `docker/postgres/init`), schemas, `unaccent`, funções `app.*` |
| 1.4 / 1.9 | `core` sem tenant + RLS por usuário; sessão com contexto por transação. Testes de isolamento: usuário A × B × AB, inativo, sem contexto, admin, sem vazamento pelo pool, token Metryx write-only |
| 1.5 | `dim` com seeds: 15 categorias, calendário 2015–2035 com safra, parâmetros, 50 centros de custo (D3 provisório). **Falta** `subcentro` / `plano_contas_map` a partir de `BASEPLANODECONTAS`/`ConsultaPlanoContas` (precisa do `.xlsm`) |
| 1.6 / 1.7 | `fato.*` com CHECKs. `fato.recalcular_estoque_mensal` testada com o exemplo do doc 01 §5.1 (815/ajuste 0; 812/ajuste −3) |
| 1.8 | `ingest.job/unidade_origem/versao_origem/ocorrencia/linha_quarentena`, `raw.payload` (particionada), `integracao.metryx_credencial` |
| 1.11 | Contrato (`etl/canonical.py`), `SourceAdapter`, de-paras, qualidade, loader e motor, com idempotência testada |

Adapters e motor (feito em 14/10, com testes):

| Item | Situação |
|---|---|
| Fase 2 (adapter de planilhas) | `app/etl/adapters/planilha/`: lê os `.xlsm` da pasta (`PLANILHAS_DIR`, hoje `G:\Meu Drive\Relatórios`, só leitura) com calamine, pelo nome do cabeçalho; identidade = código do projeto + fazenda; CADASTROINICIAL (de-para, saldo inicial, período); desmame/mudança/consumo como lançamentos; planejado (versão PLANILHA); orçamento por centro × mês |
| Fase 3 (adapter Metryx) | `app/etl/adapters/metryx/`: allow-list de GETs, cliente httpx com repetição, token cifrado (Fernet, `METRYX_CHAVE_CIFRA`), uma unidade por cliente, normalizador sobre o JSON da API (transferências entre fazendas, retiro legado das mortes, `weightTotal`, estorno), partições por endpoint com guarda de volume. **Chamada real à API ainda não feita** (precisa de autorização e token de teste) |
| Motor | guarda de volume (`SNAPSHOT_HELD`), arquivo em dobro da mesma fazenda (vale o mais recente, `DUPLICATE_UNIT_FILE`) ou com os mesmos bytes sob outro nome (`DUPLICATE_CONTENT`), recorte `desde` (a planilha da safra nova não apaga a anterior), erro de uma unidade não derruba o job, CLI `python -m app.etl` |
| Equivalência (doc 01 §7) | `tests/test_planilha.py::test_equivalencia_planilha_e_metryx`: a mesma fazenda sintética em `.xlsx` e em JSON da API gera o mesmo estoque, os mesmos fluxos e a mesma área de pasto |
| Área de pasto do Metryx (16/10) | `utilizacao-pasto` na allow-list; área do mês = pastagens de uso Pecuária no último dia do mês (o período mais recente de cada uma), do primeiro período cadastrado até o último mês do rebanho médio (`adapters/metryx/pasto.py`). A área total vai para a lotação; a produtiva fica em coluna própria. A lotação cab/ha passa a sair para o Metryx; a UA não (relatório de validação §18). A lotação segue igual ao BI mesmo quando um mês com rebanho não tem área, o que a infla (Q13, decidido em 16/10); os casos estão em `docs/validacao/2026-10-16_lotacao_meses_sem_area.md` |

Ainda falta nos adapters:
- ~~planejamento do Metryx~~ feito em 27/10/2026 (§3, "Previsto do Metryx"); a versão oficial do plano segue na D7;
- `saldo-inical-pecuario` (já vem no bruto; o normalizador ainda não usa);
- UA do Metryx: o usuário vai pedir aos desenvolvedores do Metryx que a API traga a UA (16/10/2026). Até lá o `weight`
  do rebanho médio fica de fora e os cartões "Rebanho Médio UA" e "Lotação UA" das fazendas Metryx mostram traço;
- agendamento (Celery) e Google Drive API (D8). Ler direto de `G:\` custa ~30 s por arquivo no primeiro acesso
  (download do Drive); depois só os arquivos alterados são lidos (a assinatura tamanho:mtime pula o resto).

**Clientes Metryx batem com o próprio Metryx, não com o BI (20/10/2026, decisão do usuário).** Bezerros mamando pelo
último saldo do lote no mês e causas "Consumo ..."/"Doação" como consumo/doação (relatório de validação §20, P16 e
P17). As planilhas não mudam.

Desvios do desenho original (para não estranhar):
- Os fatos apontam para `dim.categoria_map` (o de-para), não direto para `dim.categoria_bi`. Corrigir um mapeamento
  reclassifica o histórico sem recarga. Categoria pendente entra no fato, mas fica fora do estoque e dos KPIs, e gera
  a ocorrência `CATEGORY_UNMAPPED`.
- O estoque é calculado no grão (fazenda × retiro × categoria de origem) e só depois somado por categoria BI.
  Checkpoints de categorias de origem diferentes não se misturam.
- `SALDO_INICIAL` não é tipo de movimentação: saldos são checkpoints em `fato.inventario`.
- O rebanho médio aceita grupo (planilha) ou categoria (Metryx), um dos dois por linha.
- **Conta fora do plano de contas não vai para a quarentena** (decisão Q1, 14/10). O lançamento aponta para
  `dim.plano_contas_map` e, sem de-para, a linha nasce pendente: aparece como "A classificar" em
  `fato.v_lancamento_financeiro` e gera o aviso `ACCOUNT_UNCLASSIFIED`. O total bate com a fonte, e classificar
  depois reclassifica o histórico. Migração `0011`.

**Validação de paridade com os BIs (14/10):** ver [`validacao/2026-10-14_cruzamento_bi.md`](validacao/2026-10-14_cruzamento_bi.md).
Primeira rodada pela ponte das `stg_*`: fluxos 100%, estoque Metryx 98,0% (resto = defeito do BI), estoque planilha
90,7% (tudo explicado), financeiro reconciliado ao centavo. Segunda rodada com o **adapter real** nos 230 `.xlsm`
(§9 do relatório): achou e corrigiu 8 problemas, entre eles a virada de safra que apagaria o histórico. Q1–Q5
decididas em 14/10:
- Q1: conta fora do plano = "A classificar";
- Q2: empate de bezerros pela regra do BI (primeiro gravado);
- Q3: a plataforma corrige os defeitos do BI (conta o saldo de jun/24; venda sem cliente aparece nas vendas);
- Q4: centavos;
- Q5: centro novo = "A classificar".

**Requisito do adapter de planilhas (Q3/A3):** venda em pé sem CLIENTE é carregada, com aviso; nunca descartada.
Consultas de conferência em `validacao/2026-10-14_consultas_q2_q3.sql`. Reexecutar: `python -m validacao.cruzar`.

**Carga inicial do histórico (Q6, decidida e implementada em 14/10):** `python -m app.etl planilhas-historico
--ate 2026-06`, depois da carga das planilhas. Traz do snapshot do datalake do BI a safra que as planilhas viradas não
têm mais, com a mesma identidade do adapter, e o arquivo responde daí em diante (§10 do relatório de validação).

Próximo: primeira chamada real à API Metryx (com token de teste e autorização) e as etapas do roadmap (§3); a fatia
vertical (auth, KPIs de rebanho, página Movimentação) já está pronta.

---

## 1. Como retomar no outro computador

1. **Levar a pasta do projeto inteira** (`CLAUDE.md`, `docs/`, `.gitignore`). Recomendado: repositório Git **privado**.
   Alternativa: copiar a pasta para o Google Drive.
2. **Pré-requisitos**:
   - Git;
   - Docker Desktop (com WSL2 no Windows);
   - Python 3.12+ (ou só Docker);
   - Node.js 22 LTS;
   - Claude Code;
   - opcional: `uv` para o ambiente Python.
3. **Repositórios de referência** (somente leitura), clonados **fora** do projeto, ex.: `../ref/`:
   - `git clone https://github.com/matheustcw4/locks_agtech_backend ../ref/locks_agtech_backend`
   - `git clone https://github.com/matheustcw4/locks_agtech_frontend ../ref/locks_agtech_frontend`
4. **Dados de exemplo (não versionados)**: copie para `dados_exemplo/` 2 ou 3 planilhas reais de `Meu Drive\Relatórios\`,
   por exemplo `RELATÓRIO - 85 - ITAPAJÉ - BELA VISTA.xlsm` e um arquivo de CRIA. Servem para:
   - escrever o `template_v1.yaml` do adapter;
   - extrair os seeds de `dCategorias`, `BASEPLANODECONTAS` e `ConsultaPlanoContas`;
   - gerar a fazenda sintética.
5. **Metryx (quando autorizado)**: um token de cliente de **teste** no `.env` (nunca no git), para baixar 1 payload de cada
   endpoint GET e validar as regras pendentes do §5.
6. Abrir o Claude Code na pasta e pedir algo como:
   *"Leia o CLAUDE.md e o docs/02_PROXIMOS_PASSOS.md e comece a Fase 1 pelo item 1.1."*

> A **Fase 0 (contenção de segurança)** é feita no servidor atual do Pentaho, não na máquina nova. Ver §6.

---

## 2. Fase 1 — Fundação (backlog com critério de pronto)

| # | Item | Pronto quando |
|---|---|---|
| 1.1 | Monorepo: `backend/`, `frontend/`, `docker-compose.yml` (db Postgres 16, redis, minio, api, worker, beat, web), `.env.example`, README com `docker compose up` | `docker compose up` sobe tudo; `GET /api/v1/health` = 200 |
| 1.2 | Backend base: `pyproject.toml` com dependências pinadas, `core/config.py` (pydantic-settings), `core/logging.py`, `main.py` (CORS, handlers), ruff, pytest com Postgres real (testcontainers ou o serviço do compose) | `pytest` roda verde no CI local |
| 1.3 | Migração 0001: papéis `app_owner`/`app_user`/`app_etl`, schemas (`core, dim, fato, mart, ingest, raw, integracao, compat, app`), funções `app.usuario_id()/tenant_id()/eh_admin()/fazendas_visiveis()`, extensões (`pgcrypto`, `unaccent`) | migração sobe e desce limpa |
| 1.4 | `core`: `tenant`, `cliente`, `fazenda`, `retiro`, `usuario`, `usuario_fazenda`, `fonte_vinculo`, `fazenda_fonte` + migrações `rls_*` | ver 1.9 |
| 1.5 | `dim` com seeds: `categoria_bi` (15 categorias, ver relatório 03 §2.4), `categoria_map`, `centro_custo` (unificado a partir dos relatórios 01 §1.3 e 02 §1.4; aplicar D3 provisório), `subcentro`, `plano_contas_map`, `calendario` (2015–2035, civil + safra jul–jun), `parametro` (15 / 30 / 450 / 0,03 …), `versao_plano` | seeds idempotentes; teste confere as 15 categorias e a safra de jul/2025 = "2025/26" |
| 1.6 | `fato`: `mov_animal`, `inventario`, `rebanho_medio_mensal`, `area_mensal`, `lancamento_financeiro`, `orcamento_financeiro` (DDL base na proposta §3.5) com CHECKs (qtd ≥ 0, natureza C/D, cenário) e índices | constraints testadas |
| 1.7 | Função/procedure SQL de estoque: checkpoints + fluxos → `fato.estoque_mensal` (saldo inicial, entradas e saídas por tipo, ajuste, saldo final), recalculável por fazenda; desmame e mudança de categoria geram −origem/+destino | teste com o exemplo do doc 01 §5.1 (planilha 815 / ajuste 0; Metryx 812 / ajuste −3) |
| 1.8 | `ingest` / `raw` / `integracao`: `job`, `source_file`, `file_version`, `template_version`, `issue`, `quarantine_row`, `raw.metryx_payload` (particionada), `sync_run(_item)`, `metryx_credencial` (token cifrado) | migrações + RLS |
| 1.9 | Sessão com contexto RLS (`db/session.py`, listener `after_begin` com `set_config(..., true)`), `api/deps.py` (`get_db_autenticado`, `exige_papel`) | **teste de isolamento**: conectado como `app_user`, o usuário A não lê nem grava linhas da fazenda de B em nenhuma tabela `fato`/`core`; admin vê tudo |
| 1.10 | Auth: `POST /auth/login` → `{token, usuario}`, `GET /auth/me`, hash argon2/bcrypt, JWT com expiração curta, login via função `SECURITY DEFINER`, comando CLI para criar o primeiro admin | testes de login, token expirado e papel insuficiente |
| 1.11 | Contratos do ETL (sem adapters ainda): `etl/canonical.py` (modelos pydantic das linhas canônicas), `etl/adapters/base.py` (`SourceAdapter` Protocol), `etl/loaders.py` (`replace_partition`, `upsert`, COPY), `etl/quality.py` (códigos de issue) | testes unitários do loader (idempotência: carregar 2× = mesmo resultado) |
| 1.12 | Especificação da **fazenda sintética** (`backend/tests/fixtures/fazenda_sintetica.yaml`): 1 ano com saldo inicial, compras, abates, vendas em pé, nascimentos, mortes (incl. consumo), desmame, mudança, transferência, área, rebanho médio, DRE e planejado, além do canônico esperado | YAML revisado; geradores `.xlsm`/JSON ficam para as Fases 2/3 |
| 1.13 | Frontend base: Vite + React 19 + TS strict, React Router 7 (`AreaAutenticada`, `RequireAuth`), `core/api/{sessao,http}.ts`, `AuthProvider`, Hub com `moduleRegistry`, tokens CSS, `EscopoProvider` (stub: fazendas + modo + período, em localStorage e na URL), Vitest, oxlint, geração de tipos do OpenAPI | login → hub funcionando contra a API do compose |

Ordem sugerida: 1.1 → 1.2 → 1.3 → 1.4/1.9/1.10 (auth + RLS cedo) → 1.5 → 1.6 → 1.7 → 1.8 → 1.11 → 1.12 → 1.13.

---

## 3. Roadmap das próximas camadas (proposto em 15/10/2026)

As Fases 2 e 3 da proposta (adapters) estão prontas e validadas; da Fase 1 faltam auth, API e front. O caminho
abaixo entrega primeiro uma **fatia vertical** (login → escopo → KPIs de rebanho → página Movimentação do Gado), que
prova a arquitetura de ponta a ponta sobre números já validados, e depois alarga domínio a domínio.

| Etapa | O que entra | Pronto quando | Decisões |
|---|---|---|---|
| **A. API base e auth** (1.10, 1.9 na API) | login/me (JWT curto, argon2, login por função `SECURITY DEFINER`), papéis admin/consultor/cliente, `get_db_autenticado` → contexto RLS, `exige_papel`, CLI do 1º admin, `GET /escopo` (clientes, fazendas visíveis, períodos, **capacidades** por fazenda), serviço `api` no compose | teste pela API: usuário A não vê a fazenda de B; token expirado e papel insuficiente recusados | D10 |
| **B. Motor de KPIs** (Fase 4) | `app/kpis/`: contexto único (fazendas ∩ RLS, civil/safra, início/fim, granularidade, recortes, cenário), registro declarativo, SQL por domínio sobre o canônico; agregados mensais em `mart.*` (tabelas com RLS) recalculados pelo motor após cada carga. Ordem: rebanho (estoque, balanço, rebanho médio, lotação) → vendas → compras/ágio → nascimentos/mortes → transferências/desmame → financeiro → P×R | paridade com os cards dos PBIX por fazenda × período em filtros sortidos (estender `validacao/bi.py` com as medidas derivadas); diferença só nos bugs catalogados | D1, D3, D5 (D4 fica para a etapa F) |
| **C. API de painéis e operação** | `/dashboards/{pagina}` (1 chamada por página), `/kpis` e séries; `/etl/jobs`, `/qualidade/issues` (quarentena, "A classificar", categorias pendentes, arquivo em dobro, histórico sem planilha); admin de mapeamentos, usuários/acessos, credenciais Metryx (write-only); tipos TS gerados do OpenAPI | contrato estável e testado; o front não calcula nada | — |
| **D. Frontend** (1.13 + Fase 5) | base (Vite, React 19, TS strict, Router 7 com `AreaAutenticada`, TanStack Query, `EscopoProvider` na URL e no localStorage, tokens CSS, Vitest, oxlint); páginas na ordem Movimentação → Vendas → Compras → Nascimentos/Mortes → Transferências/Desmame → Financeiro → P×R → Capa/PDF; telas de dados & qualidade e admin | homologação de cada página com 2–3 consultores | — |
| **E. Operação** (em paralelo a partir de A) | deploy (D8: VPS + compose com db, redis, api, worker, beat, web; backup); Celery beat para planilhas (Drive API ou pasta sincronizada) e Metryx diário; 1ª chamada real ao Metryx e as validações do §5; planejamento Metryx (D7), `utilizacao-pasto`, saldo inicial; alertas (job com erro, credencial inválida, guarda de volume) | cargas rodando sozinhas com alerta; Metryx real conferido contra o `stg_*` | D7, D8 |
| **F. Corte** (Fase 6) | 1 ciclo de boletim mensal emitido pela plataforma em paralelo ao BI; desligar Pentaho e PBIX; KPIs novos (natalidade, desmame, desfrute) | boletim do mês saiu só pela plataforma | D4 |

Fatia vertical (primeiro marco): A completa + B só o domínio rebanho + C só `/dashboards/movimentacao` + D base e a
página Movimentação do Gado.

### Andamento (15/10/2026): fatia vertical feita

| Etapa | Feito | Ainda não |
|---|---|---|
| A | login/me (JWT HS256, argon2, função `app.dados_de_login` na migração 0012, e-mail sem diferenciar maiúscula; usuário desativado perde o acesso na hora); `SessaoDoUsuario` = sessão com o RLS do usuário em toda rota de dados; `GET /escopo` com capacidades e primeiro/último mês com dado; `python -m app.comandos criar-usuario / dar-acesso` | papéis consultor/cliente e `exige_papel` (hoje só admin × não admin, D10); serviço `api` no compose |
| B | `app/kpis/movimentacao.py`: estoque inicial/final, balanço por tipo com ajuste, estoque por categoria, série mensal, rebanho médio, área média e lotação. Paridade com o BI em 300 filtros sorteados (relatório de validação §12) | registro declarativo e `mart.*`: com o volume atual o SQL direto no canônico responde em milissegundos, então ficam para quando um domínio precisar |
| C | `GET /dashboards/movimentacao` (403 para fazenda fora do acesso); OpenAPI exportado (`app.exportar_openapi`) → tipos TS | `/etl/jobs`, `/qualidade/issues`, admin |
| D | `frontend/`: login, área logada (`AreaAutenticada`), filtro do topo na URL + localStorage, página Movimentação do Gado (cards, balanço, gráfico mês a mês, estoque por categoria); 13 testes Vitest; oxlint | demais páginas, telas de qualidade e admin, homologação com consultores |

**Página Vendas (15/10/2026), feita:** `app/kpis/vendas.py` + `GET /dashboards/vendas?tipo=abate|em_pe`; no front,
`/vendas/abate` e `/vendas/em_pe` (cartões do geral com o planejado, gráficos mensais de faturamento e de cabeças com o
acumulado, quadro GERAL/MACHO/FÊMEA × realizado/planejado). Paridade com o BI em 900 filtros sorteados: abate 100%;
em pé com diferenças só de A3, A17 e A20 (relatório §13). Pendente: decisão Q8 (meta com data "DDMM/AAAA").
Q8 decidida: a meta com data "DDMM/AAAA" fica na quarentena e aparece em Pendências.

**Pendências de lançamento (15/10/2026), feita:** aba "Pendências" no painel (pedido do usuário) com o que a última
carga de cada arquivo deixou fora dos números (quarentena: data ilegível, quantidade faltando, VERIFICAR, valor
absurdo…) e o que entrou mas parece errado (peso médio, rendimento e preço por kg fora da faixa, venda sem valor ou
sem cliente), com arquivo, aba, linha, o que está escrito e como corrigir. Respeita o RLS (função
`app.pendencias_de_carga`, migração 0013). Na carga: aviso sem fazenda própria herda a da unidade quando ela é uma
só (toda planilha); antes, o RLS escondia esses avisos de todos menos do admin. Falta: o que não tem fazenda (planilha que nem
carregou, ex.: identidade recusada, A19; 798 lançamentos do Metryx com fazenda de destino fora do cadastro) fica fora
desta tela e vai para a futura tela de cargas do admin.

**Telas refeitas a partir do BI (15/10/2026, pedido do usuário):** as páginas seguem a estrutura e o visual do BI
Ciclo Completo (layout extraído do PBIX em `docs/referencias/pbix_ciclo/layout_paginas.md`). Filtros só na página
MENU, como o BI sugere (Cliente = proprietário ou customer, Fazenda ou GRUPO, Safra/Cívil, Safra ou Ano, Mês). A
fazenda passou a ser de seleção múltipla em 16/10/2026 (pedido do usuário): a API já recebia a lista (`fazendas`
repetido); nenhuma ou todas marcadas = GRUPO, e o seletor do MENU é o mesmo dos meses (`SeletorMultiplo`). O mês
é de seleção múltipla, como o filtro do BI (pedido do usuário, 15/10/2026). As somas usam só os meses marcados, que
podem ser salteados; o estoque final é o do último mês marcado, como as medidas do BI (`MAX(dCalendar[Data])`). A API
recebe `meses` (repetido) além de `inicio` e `fim`. A
Movimentação ganhou os cartões do BI (rebanho médio e lotação em UA, nascimentos, mortes, compras e vendas com a meta)
e perdeu o balanço e as tabelas, que o BI não tem. Pendente: Q9 (o mesmo cliente nas duas fontes com grafias
diferentes, relatório §7). Enquanto isso, o MENU tem o filtro temporário **Origem** (Integração Planilhas | Metryx),
pedido do usuário: só escolhe quais clientes e fazendas aparecem. Q9 decidida em 15/10: as duas fontes ficam
separadas, com esse filtro, enquanto as planilhas existirem (a equipe vai tirá-las no futuro).

**Visual com a base do AgTechLab (16/10/2026, pedido do usuário):** menus, navegação, gráficos e disposição seguem o
AgTechLab, com a paleta da Terra. A casca (`src/core/ui/Casca.tsx`) tem o menu lateral em azul-marinho com as páginas
em grupos (Boletim, Qualidade, Geral; o admin vê Administração), recolhível (a escolha fica no navegador) e em gaveta
no celular; o topo tem as migalhas, o filtro em uso com "Trocar" (os filtros continuam só no MENU, escolha do
usuário), o "Exportar PDF", o nome e o "Sair". O MENU e as telas de admin usam a mesma casca. Cartões de borda fina com
cabeçalho, tabelas com cabeçalho em caixa-alta, gráficos com eixo e grade discretos e colunas arredondadas
(`estiloDosGraficos.ts`), fonte Figtree. Na folha do PDF somem o menu e o topo, e o cabeçalho ganha o logo (a moldura
do BI); a capa mantém a fonte em que foi medida.

**Página Compras (15/10/2026), feita:** `app/kpis/compras.py` + `GET /dashboards/compras`, com as contas de lote
comuns a Vendas e Compras em `app/kpis/lotes.py`; no front, `/compras` com os quadros Fêmea / Macho / Geral, preço da
@ de compra e ágio, investimento × planejado e os gráficos de desembolso (com a linha do preço da @) e de cabeças.
Paridade (relatório §13): cabeças, investimento, preço do kg e peso médio 100%; preço da @ e ágio só com A21
(arredondamento da @ na planilha) e A22 (total errado na linha, agora avisado em Pendências).

**Páginas Nascimentos, Mortes e Transferências (15/10/2026), feitas:** `app/kpis/nascimentos.py`, `mortes.py` e
`transferencias.py` + `GET /dashboards/{nascimentos,mortes,transferencias}`; `lotes.py` agora soma por sexo ou por
grupo e dá a série de contagem (mensal e acumulada). No front, `/nascimentos` (quadros Fêmea / Macho / Geral, gráficos
mensal e acumulado), `/mortes` (quadros Bezerros / Jovens / Adultos / Geral com a mortalidade sobre o rebanho médio e,
nos bezerros, sobre os nascimentos; gráficos acumulado e mensal; mortes por causa) e `/transferencias` (Macho e Fêmea
em Entrada | Saída × Realizado | Planejado; entradas × saídas por mês). Paridade (relatório §14): nascimentos 100%;
mortes 100% no realizado, com a mortalidade sobre nascimentos diferindo só por P3; transferências 100% nas cabeças
realizadas, e o resto só com A17, A21, A22 e dois achados novos (A23: o ETL do BI trunca a QTD fracionária da meta de
transferência; A24: QTD com mais de 3 casas na planilha). Pergunta nova: Q10 do relatório (ajuste de estoque lançado
como morte).

**Página Financeiro (15/10/2026), feita:** `app/kpis/financeiro.py` + `GET /dashboards/financeiro`; no front,
`/financeiro` (primeira aba, como no BI) com os velocímetros de desembolso e custeio por cabeça por mês e do preço da @
vendida (verde dentro da meta, vermelho fora), o quadro Desembolso × Receitas, o desembolso por centro de custo, o
fluxo de caixa mensal e os gráficos realizado × planejado de desembolso por cabeça, desembolso e receitas. A
classificação das contas vem de `dim.centro_custo` (doc 01 §5.5), com `TODO(D3)`. Paridade (relatório §15): receitas
e despesas 100%; desembolso e custeio diferem do BI de planilhas pela classificação das contas (P4): pela dimensão
atual, "Rebanho Investimento" (compra de gado) e "Financiamentos débitos" entram no desembolso, e a planilha os deixa
fora. Isso põe o desembolso das planilhas 63,6% acima do BI. Pergunta nova: Q11 do relatório (que contas entram no
desembolso; resolve junto com a D3).

**Página Previsto × Realizado (15/10/2026), feita:** `app/kpis/previsto_realizado.py` +
`GET /dashboards/previsto_realizado`; no front, `/previsto_realizado` (primeira aba, como no BI): a matriz do DRE com as
classificações (A Receitas, B Desembolso = investimentos + custeio, C Investimentos, D Custeio, E/F Outros, Neutro, A
classificar) que abrem as contas, MENSAL (último mês do período) e ACUMULADO (o período), realizado, planejado, %
de variação e o semáforo do BI; no fim, o resultado pela recomendação da D1 (`TODO(D1)`). Paridade (relatório §16):
investimentos e outros débitos e créditos batem; o resto difere só por P1 (o total do BI deixa os outros débitos e
créditos de fora), P4 ("Culturas - Despesa" fora do CASE do BI), P9 e três achados novos do `planejadoXRealizado`
(A25: soma débito e crédito do mesmo lado; A26: soma as linhas VERIFICAR; A27: descarta as linhas sem centro BI).

Com isso, todas as páginas visíveis do BI Ciclo Completo existem na plataforma, menos a Capa. A capa e a exportação do
boletim (PDF) ficam para depois (pedido do usuário, 15/10/2026).

**Capa e exportação em PDF (15/10/2026), feitas:**
- **Botão "Exportar PDF"** em todas as páginas do boletim e no MENU. O diálogo tem as páginas com seleção múltipla
  (capa e as 9 páginas do boletim, todas marcadas de início; Pendências fica de fora) e a cidade da capa.
- **Capa:** a arte da capa da consultoria (`frontend/src/assets/bi/capa-fundo.png`, sem o "SAFRA" impresso, para
  servir também ao ano civil). Mostra:
  - SAFRA 24/25 (ou ANO 2025), conforme o filtro;
  - a fazenda escolhida ou as fazendas do grupo, separadas por " | ";
  - "Análise: <mês de hoje>";
  - no rodapé, o site e "<cidade>, <mês de hoje>.".
- **A cidade** é digitada na hora e vai só no estado da navegação: não entra na URL, no navegador nem no banco.
- **Como o PDF é gerado** (`frontend/src/modules/exportacao/`): a rota `/exportar` desenha a capa e as páginas
  escolhidas com o filtro do MENU, espera os dados e as animações dos gráficos, fotografa cada folha
  (`html-to-image`) e monta o arquivo (`jsPDF`). As duas bibliotecas carregam só na hora de exportar.
- **Formato do arquivo:** largura fixa e altura de cada página igual à da folha, sem cortar nem espremer; a capa é
  16:9. Nome: "Boletim - <seleção> - <período>.pdf".
- **Conferido no navegador:** 10 páginas em cerca de 15 segundos, 4 MB.

**Boletim analítico (20/10/2026), feito:** o diálogo do "Exportar PDF" ganhou o seletor **Padrão | Analítico**. O
modo Analítico segue a ideia do boletim mensal da consultoria (o PDF de exemplo da Jaraguá), sem copiá-lo: o que o
exemplo explica, a plataforma explica com os números e os gráficos que já tem.
- **Folhas** (A4 em pé, 1240 × 1754 px; a que tem mais conteúdo cresce para baixo), na ordem: capa (a mesma do
  padrão, com "Análise: <mês de referência>"), movimentação do estoque, lotação, placar zootécnico, vendas abate,
  vendas em pé, mortes, financeiro e fluxo de caixa. Cada folha tem o cabeçalho (título, fazenda(s), mês de referência,
  período e o logo), a **"Leitura do mês"** (frases escritas pela API a partir dos números) e os quadros.
- **Três recortes** (`app/kpis/analitico/recortes.py`): o **mês de referência** (o último mês do filtro do MENU), o
  **acumulado** (do início do período até ele) e o **período inteiro** (safra jul–jun ou ano civil jan–dez), que é a
  meta. Os números são os KPIs das páginas (`movimentacao`, `lotes`, `mortes`, `financeiro`, `previsto_realizado`...)
  rodados nesses três recortes: o analítico não tem cálculo próprio de rebanho, venda, morte ou dinheiro.
- **Status** (bolinha verde, amarela ou vermelha): depende do lado bom do indicador (nascer e vender mais é bom;
  morrer e gastar mais é ruim; rebanho, lotação, compras e transferências não têm lado e ficam sem status). Verde = no
  lado bom; amarelo = do lado ruim até o limiar `semaforo_limiar` de `dim.parametro` (o mesmo do Previsto ×
  Realizado); vermelho = além dele. A folha do caixa usa o semáforo da própria página Previsto × Realizado.
- **Sem meta no período, sem previsto:** se o período inteiro não tem meta para o indicador (fazenda sem plano, ou o
  plano não prevê aquilo), o previsto fica "—", sem variação nem status (`comparar.linha_do_placar`), em vez de um
  previsto 0 que pareceria meta zerada.
- **Lotação prevista** (o BI não tem um agregado para copiar; regra decidida pelo usuário em 20/10/2026): Σ rebanho
  planejado ÷ Σ área planejada **só dos meses em que o plano tem área**. Na Serra Dourada (planilha) julho e agosto/2025 têm rebanho planejado e nenhuma área no
  plano: somados, a prevista ia para 1,93 cab/ha contra 1,65 dos meses com área. A lotação realizada continua como no
  BI (Q13).
- **Desembolso × caixa:** a folha Financeiro usa o desembolso da página Financeiro (contas marcadas como desembolso,
  que podem incluir financiamentos pagos); a folha do caixa usa a matriz do Previsto × Realizado, em que os
  financiamentos ficam em "Outros débitos". Uma nota na folha explica a diferença. O saldo do caixa não tem previsto
  (o BI não planeja o saldo).
- **Leitura do mês quando falta dado** (20/10/2026): a descrição nunca some. Cada frase só entra quando o dado
  dela existe, e a que sobra diz o que falta, sem um zero que pareceria resultado:
  - sem lançamento financeiro: "Não há lançamentos financeiros no período (até <mês>)", com o previsto, se houver
    (antes dizia "receitas de R$ 0 e desembolso de R$ 0");
  - sem rebanho (fazenda agrícola ou administrativa): "Não há rebanho nem movimentação de animais no período"; sem
    rebanho médio, a lotação diz que não há lotação; sem indicador nenhum, o placar diz isso;
  - sem venda ou morte no período: "Nenhuma venda deste tipo no período" e "Nenhuma morte no período";
  - **mês depois do último lançamento de rebanho** (`app/kpis/analitico/ultimo_dado.py`, a mesma regra do
    `ultimo_mes` do escopo): as folhas de rebanho abrem com "Os lançamentos de rebanho vão até <mês>; depois disso o
    saldo só se repete" e não dizem mais "nenhum animal entrou ou saiu". Se só parte do grupo parou, a frase nomeia
    essas fazendas. Fazenda parada com saldo zero (vendida, encerrada) não gera aviso;
  - concordância: "morreu 1 cabeça", "saiu 1 cabeça", "1 indicador tem status".
- **Arquivo:** "Boletim analítico - <seleção> - <mês>.pdf" (ex.: "Boletim analítico - GRUPO - jun-26.pdf").

**Boletim personalizado (20/10/2026), feito:** o terceiro modo do "Exportar PDF", para a pessoa escolher o que vai no
boletim (pedido do usuário). Os números e as frases são os mesmos do analítico (`GET /dashboards/analitico`).
- **Assuntos:** capa, movimentação do estoque, lotação, placar zootécnico, **nascimentos**, **compras**, vendas abate,
  vendas em pé, **transferências**, mortes, financeiro e fluxo de caixa. Os três em negrito são novos na API
  (`app/kpis/analitico/{nascimentos,compras,transferencias}.py`); vendas, compras, transferências e nascimentos usam o
  mesmo bloco de lotes (`lotes_do_mes.py`: lançamentos do mês, cabeças mês a mês e o resumo previsto × realizado).
  Compras e transferências não têm lado certo em cabeças (sem status); na compra, pagar menos pelo kg e pela @ é bom.
- **O que mostrar em cada assunto** (`src/logic/personalizado.ts`): Leitura do mês, Previsto × realizado, Lançamentos
  do mês, Gráficos, Números do período (cartões, distribuição, causas, centros de custo) e Notas e legendas. Cada
  assunto tem só algumas dessas partes (o estoque não tem gráfico, por exemplo); um assunto sem nenhuma parte marcada
  que ele tenha fica de fora, e nota sozinha não faz bloco.
- **Paginação:** os blocos vão um depois do outro em folhas A4 com o cabeçalho "Boletim mensal". Primeiro eles são
  desenhados numa folha de medição (fora do PDF); com a altura de cada peça (o título com a leitura e cada quadro), o
  `paginar` reparte: o que não cabe continua na folha seguinte, quebrando entre dois quadros, com "(continuação)" no
  título; o título nunca fica sozinho no fim da folha; um quadro maior que a folha vai sozinho numa folha que cresce.
- **O analítico não mudou:** as folhas dele passaram a ser montadas pelos mesmos conteúdos, com todas as partes, e o
  texto das 9 folhas da Serra Dourada (safra 25/26) ficou idêntico ao gravado antes da mudança.
- **Conferido no navegador:** só a leitura dos 11 assuntos coube em 2 folhas; nascimentos, compras, vendas em pé,
  transferências e mortes com leitura, lançamentos, gráficos e previsto foram de 5 folhas (um assunto por folha) para
  4, todas dentro da A4. Arquivo: "Boletim personalizado - <seleção> - <mês>.pdf".

**Notas técnicas no PDF (21/10/2026), feitas:** o diálogo do "Exportar PDF" tem, nos três modos, dois campos
opcionais: "Nota técnica no início do PDF" e "Nota técnica no fim do PDF" (até 4.000 caracteres cada; linha em branco
separa os parágrafos, a quebra simples continua dentro do parágrafo).
- **Padrão e Analítico:** cada nota é uma folha A4 própria ("Nota técnica", com o cabeçalho das folhas analíticas:
  fazenda, mês de referência e período). A do início vem logo depois da capa (ou abre o PDF, sem capa); a do fim é a
  última folha (`FolhaDaNota.tsx`; o padrão monta as folhas em `FolhasDoPainel.tsx`).
- **Personalizado:** as notas são o primeiro e o último bloco do fluxo; cada parágrafo é uma peça, e a folha pode
  quebrar entre eles (`PaginasPersonalizadas.tsx`).
- **Nota vazia não gera nada**, e o texto vai só no pedido do PDF (estado da navegação), como a cidade da capa: não
  entra na URL, no navegador nem no banco.
- **Conferido no navegador:** sem notas, as 9 folhas do analítico continuam idênticas à referência; com notas, a do
  início veio depois da capa e a do fim fechou o PDF nos três modos.
- **Conferido no navegador** (20/10/2026), sem baixar o arquivo: Serra Dourada (planilha), safra 25/26 até jun/2026, com
  metas; e GRUPO U6 (Metryx), ano civil até mai/2026, sem metas (o estoque bate com o Metryx: 7.593 cabeças, 12 mortes,
  2 de consumo/doação). 9 folhas em cerca de 15 segundos, todas dentro do A4.

**Previsto do Metryx (27/10/2026), feito e carregado pela API real (Serra Dourada, U6 e Maister):** até aqui as
telas das fazendas Metryx não tinham meta nenhuma; agora a carga traz o planejamento
(`app/etl/adapters/metryx/planejamento.py`).
- **Endpoints** (só GET, na allow-list): `compra-`, `venda-`, `nascimento-`, `morte-`, `desmame-` e
  `estoque-medio-mensal-planejamento`, mais o `previsao-financeiro` (DRE previsto, o que o BI usa). O
  `previsao-fluxo-caixa-planejamento` (orçamento de caixa por versão) vai só para o bruto, para comparar antes de
  escolher a fonte do orçamento.
- **Versão do plano (D7, provisório):** cada fazenda tem as suas versões (o número se repete entre fazendas, e uma
  versão pode cobrir várias safras) e o Metryx guarda várias por fazenda e safra. O BI soma todas, o que dobra as
  metas (Serra Dourada 25/26: versões 1 e 3). Entra só a **mais recente de cada fazenda e safra**, escolhida olhando
  todos os endpoints juntos (as metas de uma safra vêm de um plano só); as outras aparecem no aviso
  `PLAN_VERSION_CHOSEN`. No datalake, a regra escolhe versões que não parecem as certas: U6 BONITO 26/27 fica com a 4,
  "26/27 - Bonito (erro)"; U6 BONITO 25/26 fica com a 2, que só tem julho; ADMINISTRATIVO (U6) 26/27 fica com a 6,
  "Versao p/ financiament"; Maister 26/27 fica com a 4, "Global (24.06.26 teste)". Por isso a D7 continua aberta:
  recomendação, a versão ativa escolhida pelo consultor numa tela de admin, e a mais recente só quando ninguém
  escolheu.
- **Categorias:** o planejamento tem catálogo próprio (idCategory 1 a 19, o mesmo para todos os clientes, com grupo,
  idade e sexo). Entra como de-para à parte ("Metryx (plano)" na tela de categorias), com a sugestão de categoria BI.
  Até alguém confirmar, as metas dessas categorias ficam fora do rebanho médio previsto, como no realizado (D6).
- **Compra e venda:** `weight` é por cabeça e `totalValue` é o total; a carcaça do abate é weight × yield/100 por
  cabeça (a coluna `pesomorto_total` do BI); venda de tipo "Abate" é abate, e as outras, venda em pé.
- **Rebanho médio previsto:** o BI não tem (o `fMetasRebanhoMedio` lê o realizado). O endpoint traz a evolução do
  rebanho: o saldo inicial da safra, sem data, e as entradas e saídas de cada mês. O rebanho médio do mês é a média
  entre o saldo do começo e o do fim do mês, por categoria. A evolução não fecha por categoria, só no total da
  fazenda: o plano desmama bezerros que o saldo inicial não tem e vende vaca de descarte antes de a vaca mudar de
  categoria. A categoria negativa no mês conta zero, e o aviso `PLAN_NEGATIVE_STOCK` diz quanto ficou de fora (Serra
  Dourada 25/26: 21 cab·mês depois da correção de junho, abaixo). **Conferir** essa conta contra a tela de
  planejamento do Metryx; se o Metryx mostrar o total com os negativos, a troca é numa função só (`Evolucao.medias`).
- **DRE previsto:** o `previsao-financeiro` não tem versão; entra numa versão própria ("previsao-financeiro"), com a
  natureza pelo sinal do valor (no datalake, todo débito vem negativo e todo crédito positivo) e a mesma conta do
  realizado (centro e subcentro do Metryx, de-para de contas). A soma fica igual à do BI (`fMetasDre`).
- **Partições:** uma por endpoint do planejamento que veio, no cenário planejado e para todas as versões da fazenda:
  quando a versão escolhida muda, as metas da anterior saem. Guarda de volume como no realizado.
- **Ponte do datalake** (`validacao/ponte_metryx.py`): lê nascimentos, mortes, desmames, a evolução do rebanho e o DRE
  previstos (os inteiros que o Pentaho gravou como "1,0" voltam a ser inteiros). Compras e vendas previstas ficam de
  fora: a stg perdeu a versão do plano e as casas decimais do peso, do rendimento e dos valores (4800 no lugar de
  480,0). Elas só vêm certas pela API.
- **Testes:** `tests/test_metryx_planejamento.py` (versão por fazenda e safra, totais, evolução, DRE, partições e a
  troca de versão no banco) e o teste de equivalência, que agora compara também nascimentos e rebanho médio
  previstos.
- **Carga pela API real** (27/10/2026): datas "M/AA", `yield` em % e `weight` por cabeça confirmados; banco de
  validação recarregado. O `previsao-financeiro` da Serra Dourada vem vazio (no BI também): o orçamento dela só existe
  no `previsao-fluxo-caixa-planejamento`.
- **Mês das metas (30/10/2026):** sai do `month` e da safra, e não do `date`: os endpoints `*-mensal-planejamento`
  escrevem o mês 6 com o ano do início da safra ("6/25" na 25-26), em todos os clientes e safras, e o BI herda isso
  (defeito P19, relatório de validação §22). Com junho no fim da safra, as vendas planejadas batem mês a mês com a
  "Venda de Rebanho" do fluxo de caixa, e a evolução da Serra Dourada quase fecha (5.780 cab·mês negativos → 21).
- **Falta:** conferir contra a tela de planejamento do Metryx o rebanho médio previsto. O plano consolidado da fazenda
  ADMINISTRATIVO (U6) soma com o das fazendas na visão GRUPO, como no BI; decidir se ela fica de fora.

**Planejado do financeiro: previsão financeira ou planejamento (29/10/2026), feito:** pedido do usuário. O fluxo de
caixa do plano (`previsao-fluxo-caixa-planejamento`) entra como um segundo orçamento, por versão, e as páginas
Previsto × Realizado e Financeiro escolhem qual comparar com o realizado.
- **Canônico** (migração 0018): `fato.orcamento_financeiro.tipo` = `previsao` (o DRE previsto: o `previsao-financeiro`
  do Metryx e o DRE planejado da planilha) ou `planejamento` (o fluxo de caixa do plano); `dim.versao_plano.ordem`
  (maior = mais recente). As partições do orçamento são por tipo, e as duas cargas não se apagam.
- **Adapter** (`planejamento.py`): o fluxo entra de todas as versões; natureza pelo `type`; valor negativo (a versão 1
  da Serra Dourada tem R$ 417 mil assim em "Nutrição - Previsão de Compras") é estorno e inverte a natureza; o
  subcentro genérico "Subcentro de Custo" (692 de 713 itens na Serra Dourada) fica de fora da conta, e o item cai no
  centro de custo.
- **Tela** (`app/kpis/previsto_financeiro.py`, `SeletorDoPrevisto`): "Planejado do financeiro" mostra só os tipos que
  as fazendas do filtro têm (padrão: a previsão financeira, se houver, como o BI); "Versão do planejamento" aparece
  quando alguma fazenda tem mais de uma versão no período (padrão: a mais recente de cada fazenda e safra; a escolhida
  substitui a mais recente na fazenda e nas safras que cobre). Numa fazenda e safra entra uma versão só. A escolha
  fica na URL, vale nas duas páginas e no PDF; o boletim analítico usa o padrão.
- **Pendência de classificação:** no plano, a venda de gado vem com o subcentro "Venda de Rebanho" pendurado num centro
  que não é de receita (Serra Dourada: "Corretivos, fertilizantes e adubos", R$ 6,83 mi na safra 25/26; U6:
  "Comunicação e energia da fazenda", R$ 40,8 mi). O de-para não acha a conta e ela entra como "A classificar"; o
  admin classifica em Administração → Contas (é a receita de venda de gado: os valores batem com as vendas planejadas).
- **Testes:** `tests/test_previsto_financeiro.py` (padrão, tipo, versão escolhida e a mesma escolha no Financeiro) e
  dois testes do fluxo em `tests/test_metryx_planejamento.py`; no front, `src/logic/previsto.test.ts`.

**Rebanho médio do Metryx pelo balanço (27/10/2026), feito:** o usuário comparou jul–set/2026 com os relatórios do
Metryx e o rebanho médio estava alto (U6: 8.505 no painel e 7.705 no Metryx; Maister: 35.629 e 30.667). O endpoint
`rebanho-medio-pecuario`, que o BI usa, conta animais a mais. Agora o rebanho médio do mês é a média do saldo de cada dia
do balanço, por categoria (`app/etl/adapters/metryx/rebanho.py`), como o relatório do Metryx; o endpoint fica só no
bruto. Defeito P18 do BI (relatório de validação §21).
- A Maister passou a vir pela API real (token do usuário, cifrado nos bancos `terra` e `terra_validacao`): o datalake
  parou em 06/10/2026 e faltavam 20 nascimentos e 2 mortes de jul–set. O token não tem a permissão do
  `utilizacao-pasto` (401, A33).
- Jul–set/2026 batem com o Metryx nos dois grupos: rebanho médio, nascimentos, mortes, compras e vendas.
- Mudam junto, nas fazendas Metryx, a lotação, a mortalidade sobre o rebanho médio, o desembolso por cabeça e o
  boletim analítico. Na primeira carga com a regra nova, a guarda de volume segura o rebanho médio (o endpoint
  gravava linhas zeradas e meses futuros): conferir e aplicar com `--ignorar-guarda`.

**Telas de admin (15/10/2026), feitas:** `Administração` (link no MENU e na barra das páginas, só para admin):
- **De-para de categorias** (`/admin/categorias`): a categoria da fonte sem categoria BI (pendente, fora do estoque e do
  rebanho médio) é classificada num select; o histórico se reclassifica e o estoque das fazendas que a usam é
  recalculado na hora (migração 0014: a API pode chamar `fato.recalcular_estoque_mensal`, e o RLS só deixa o admin
  gravar). No banco de validação: 107 pendentes;
- **De-para de contas** (`/admin/contas`): a conta "A classificar" ganha centro de custo e o DRE muda na hora. No banco
  de validação: 56 contas; as maiores são grafias do Metryx que não casam com o plano ("Outro débitos", R$ 189 mi;
  "Outro créditos", R$ 125 mi; "Outros Créditos", R$ 37 mi);
- **Usuários e acesso** (`/admin/usuarios`): criar (senha inicial), ativar/desativar, dar/tirar admin, trocar senha e
  escolher as fazendas que cada um vê (por cliente, com "marcar todas"); o admin não consegue tirar o próprio acesso.
- **Funções** (`/admin/funcoes`, pedido do usuário em 15/10/2026): o cadastro de funções (`core.funcao`, migrações
  0016 e 0017). No cadastro de usuário, a função é obrigatória e escolhida nessa lista (nome, e-mail, senha e função;
  a senha só é gravada como hash argon2).
  - O nome é único, sem diferenciar maiúsculas.
  - Desativar tira a função da lista dos cadastros novos; quem já a tem continua com ela.
  - Só se apaga a função que nenhum usuário tem.
  - Usuários anteriores ficam sem função até o admin escolher uma.
  - A função ainda não dá permissão: quem entra na administração continua sendo o `eh_admin` (papéis por função
    ficam para a D10).

**Equipe da consultoria (15/10/2026), importada:** a planilha "Levantamento Clientes para Power BI.xlsx" (uma linha
por fazenda, com o técnico, o e-mail do gerente e o do gerente regional) vira usuários e acessos:
`python -m app.comandos importar-equipe <planilha> [--aplicar]` (regras em `app/services/equipe.py`, testes em
`tests/test_equipe.py`).
- **Regras:**
  - o nome vem da coluna TÉCNICO; quem só aparece como gerente ou regional ganha um nome provisório tirado do e-mail;
  - a função é "Gerente" para quem aparece como gerente ou regional (o regional é gerente igual), e "Técnico" para os
    demais;
  - cada pessoa vê as fazendas das linhas em que aparece. As de planilha casam pelo código e o nome; as do Metryx,
    pelo cliente (os nomes das fazendas no Metryx não seguem os da planilha).
- **No banco de validação:** 36 pessoas (17 gerentes e 19 técnicos) e 767 acessos. O Francys, que já tinha sido
  cadastrado pela tela, manteve o nome, a senha e a função.
- **Pendências:**
  - 12 nomes provisórios a corrigir na tela de usuários (a tela agora edita o nome);
  - senhas: os usuários importados nascem sem senha e só entram quando o admin definir uma;
  - 68 linhas da planilha sem fazenda no painel, a maioria de clientes que ainda não estão carregados. Rode o comando
    de novo quando entrarem;
  - 4 clientes Metryx do painel com outro nome na planilha (Maister, Grupo Resende, Grupo U6 Uehara e Reunidas
    Itapajé) e 8 fazendas de planilha sem linha correspondente: vincular pela tela;
  - na planilha: a linha 27 (CPN) tem o técnico "Pedro" com o e-mail da Deise (valeu o e-mail); rafaelnogueira@ aparece
    com o nome "Pedro Pereira"; matheus@ (técnico) e mateus@ (gerente) são e-mails diferentes.

Correção na carga que as telas revelaram: quando o CADASTROINICIAL da planilha tinha a categoria BI em branco, a carga
gravava uma "confirmação" vazia e, a cada recarga, regravava a categoria com o valor da planilha, apagando o que o admin
tivesse classificado. Agora a planilha só confirma com a categoria preenchida (`app/etl/mapping.py`); em branco, o
de-para fica pendente e a classificação do admin sobrevive à recarga (teste em `tests/test_admin.py`). A migração 0014
limpa as confirmações vazias já gravadas.

Próximos passos sugeridos: a equipe classificar os pendentes nas telas de admin (começando pelas contas de maior
valor); depois, operação (agendamento das cargas e deploy na VPS).

**Operação (15/10/2026), feita:**
- **Cargas agendadas** (`backend/app/tasks/`): Celery com o Redis como fila. O beat dispara e o worker executa, uma
  carga por vez (trava consultiva no Postgres, que segura também uma segunda instância do worker). Planilhas a cada
  2 horas; o estoque de todas as fazendas no dia 1 de cada mês (a carga só recalcula as fazendas que mudaram, e sem
  isso a fazenda parada ficaria sem o mês novo); o Metryx fica desligado até a autorização das chamadas à API real.
  As agendas vêm do `.env` (`AGENDA_*`, formato do cron). Testes em `tests/test_tarefas.py`.
- **"Atualizar agora" (16/10/2026, pedido do usuário):** botão pequeno, só do admin, no topo de todas as telas
  (`core/ui/BotaoAtualizarAgora.tsx`, dentro da `Casca`). `POST /admin/atualizacao` põe `cargas.atualizar_agora` na
  fila (409 se já tem carga rodando; 503 se o Redis não responde) e `GET /admin/atualizacao` diz se a trava está presa
  e qual foi a última carga. A tarefa carrega as planilhas e, só com `AGENDA_METRYX` ligada (a autorização), o Metryx,
  com a trava presa do começo ao fim; o job guarda quem pediu (`ingest.job.usuario_id`). A tela pergunta a cada 4 s
  enquanto espera, relê todos os números quando a carga pedida termina e avisa se o worker não começar em 2 minutos
  (`logic/atualizacao.ts`). As tarefas passaram para a fila `terra` (o Redis desta máquina de dev é o do
  agro_platform); no compose de produção a API ganhou `REDIS_URL` e o worker, `AGENDA_METRYX`.
- **Deploy na VPS** (`docker-compose.prod.yml`, guia em `docs/03_DEPLOY_VPS.md`): Postgres (só em 127.0.0.1), Redis,
  migração automática a cada subida, API (app_user), worker (app_etl), beat, Caddy (o painel e `/api` num endereço,
  HTTPS automático) e backup diário com retenção. Validado subindo tudo no Docker Desktop: migrações, painel e API pelo
  Caddy, beat disparando, worker carregando (e pulando o arquivo sem mudança na passada seguinte), primeiro admin pelo
  comando, login de ponta a ponta e backup restaurado num banco novo com RLS e políticas.

**Decisão pendente (D8, parte que falta):** como as planilhas chegam à VPS. Hoje elas estão no Google Drive, lidas
pelo Drive para desktop do Windows (`G:\Meu Drive\Relatórios`). A proposta (D8) recomenda a API do Google Drive com
uma service account. Recomendação: **rclone no próprio compose com essa service account** (perfil `drive`, já pronto:
sincroniza a cada 10 minutos, escopo só leitura, preserva a data de modificação); é a mesma credencial da D8, sem
escrever um adapter novo para o Drive. Alternativa: Syncthing a partir de uma máquina que já tem o Drive. Também falta
escolher a VPS e o domínio do painel.

Próximo passo sugerido: o primeiro deploy, seguindo `docs/03_DEPLOY_VPS.md`.

**DMG do Metryx × plataforma (15/10/2026):** o relatório de DMG da Serra Dourada difere da plataforma em 75 bezerros.
A primeira consulta à API real do Metryx (autorizada, só GETs, um cliente) achou a causa: 75 "mortes" com a causa
"AJUSTE DE SALDO", lançadas depois do snapshot de 13/10 com data de 30/06/2026 (relatório de validação §17, Q12; o
tratamento dessas mortes é a Q10).

A consulta e a primeira recarga real também acharam quatro defeitos no payload da API, já corrigidos no adapter com
testes no formato real:
- A29: a mudança de categoria vem com o `idCustomer` errado e derrubaria a carga do cliente;
- A30: venda, compra e destino da transferência vêm sem o id da fazenda;
- A31: as transferências antigas vêm sem quantidade, e nenhuma traz o retiro de origem;
- A32: a mudança de categoria repete os desmames e traz o retiro legado.

Recarregada pela API, a Serra Dourada bate 100% com o DMG no banco de validação: todas as colunas do trimestre, com
ajuste zero. No caminho, apareceu e foi corrigido o
A28 (migração 0015): o movimento que abre uma série nova no estoque deixava de contar e virava "ajuste". No Metryx,
isso só trocava a coluna; nas planilhas, duas categorias do histórico perdiam a safra 25/26 inteira.

Observação para a homologação: quando o período inclui o mês do primeiro saldo da fazenda, esse saldo aparece na
linha "Ajuste de inventário" (é um checkpoint, pela regra do estoque). O período padrão já começa no mês seguinte;
se os consultores estranharem, separar uma linha "Saldo de abertura" no balanço.

---

## 4. Decisões pendentes com o usuário (padrão provisório até decidir)

| # | Tema | Padrão provisório (recomendação) |
|---|---|---|
| D1 | Total do Previsto×Realizado | Resultado = Receitas + Outros créditos − (Investimentos + Custeio + Outros débitos) |
| D2 | Financeiro Metryx: data / fazenda | data de pagamento; fazenda destino (fiscal disponível como filtro) |
| D3 | Investimentos no custeio? | não (custeio = CCM operacional) |
| D4 | Natalidade, desfrute, desmame | fórmulas da proposta §6.4, a validar |
| D5 | UA sem informação | estimada = Σ(cab × peso_ref_categoria) ÷ 450, marcada como "estimada" |
| D6 | Quem confirma o mapeamento de categorias Metryx | consultor responsável pela fazenda; mapeamento por cliente |
| D7 | Versão oficial do plano Metryx | escolhida pelo consultor; senão, a mais recente. **Provisório no código (27/10/2026):** a mais recente de cada fazenda e safra, com aviso (§3, "Previsto do Metryx") |
| D8 | Onde roda / acesso ao Drive | **Decidido em parte (15/10/2026):** produção numa VPS Linux; por enquanto tudo é desenvolvido e testado no Windows. Acesso ao Drive: em aberto (proposta: Google Drive API com service account) |
| D9 | Arquivos duplicados | vale o mais recente + override manual |
| D10 | Clientes finais acessam? | **Adiado (15/10/2026):** por ora só os técnicos da Terra consultam; o permissionamento (papéis consultor/cliente) fica para o final. O RLS por usuário → fazendas já existe |

---

## 5. Validações pendentes com payload real do Metryx

1. `compra-pecuario.weightTotal`: peso total ou por cabeça? (O BI atual usa dos dois jeitos.)
2. `desmames-pecuario.weight` e `rebanho-medio-pecuario.weight`: médio por cabeça ou total?
3. ~~`utilizacao-pasto`: como `dataInicio`/`dataFim`/`statusPecuaria` definem a área em uso por mês.~~ Resolvida
   (16/10/2026) com os dados reais da Serra Dourada (`stg_area`): o fim de um período é o começo do seguinte; vale o
   período mais recente no último dia do mês; entram as pastagens de uso Pecuária, de qualquer status (relatório §18).
4. `balanco-pecuario`: já inclui transferências e saldo inicial? Qual a convenção de sinal de `amount`?
5. Campos declarados `int64` no Swagger (`totalFaturamento`, `valueArroba`, `liveWeightAVG`…) vêm com decimais?
6. Formato real de `date`, `month`, `birth`, `harvest`, `anoSafra` e de `MM/YY` no planejamento. No datalake, o
   planejamento vem com `date` "M/AA" (ex.: "7/25"), `anoSafra` "25-26" e o saldo inicial da evolução sem data
   (`month` 0); falta conferir no payload real.
7. `GET /api-metryx/customers` (fora do Swagger): contrato e se é suportado.
8. **Respondida (15/10/2026), com a primeira consulta real** (cliente da Serra Dourada; relatório de validação §17):
   - **DMG × balanço:** o DMG tinha 75 bezerros a menos porque o Metryx recebeu, depois de 13/10, mortes de
     "AJUSTE DE SALDO" datadas de 30/06/2026. O balanço de hoje já bate com o DMG.
   - **`saldo-inical-pecuario`:** é o saldo de implantação (uma data só, 30/06/2023), não um saldo por data. Agora
     está na allow-list e vai para o bruto, mas o normalizador não usa.
   - **Defeitos do payload, corrigidos no adapter** (A29–A32):
     - a mudança de categoria vem com o `idCustomer` errado: esse endpoint é conferido pela fazenda;
     - venda, compra e destino da transferência vêm sem o id da fazenda: ele sai do retiro;
     - as transferências antigas vêm sem quantidade e ficam de fora, com um aviso; sem o retiro de origem, dentro da
       mesma fazenda, as duas pontas ficam sem retiro e se anulam;
     - a mudança de categoria repete os desmames (a repetição fica de fora) e traz o retiro legado (resolvido pelo
       nome).
   - **Ainda a validar com o payload real:** os itens 1, 2, 3, 5 e 7 acima. A carga da Serra Dourada não deu aviso de
     peso, mas um cliente não basta.
   - **Formato real:** `date` vem como `AAAA-MM-DD`; `birth` e `harvest`, como `MM/AA` e `AA/AA` (`birth` só nos
     bezerros); `gender`, como "Fêmea"/"Macho". Na morte é ao contrário: `gender` vem como "FEMALE"/"MALE", e
     `genderName`, como "Fêmea"/"Macho".

---

## 6. Fase 0 — contenção de segurança (no servidor atual, independente do projeto)

- Rotacionar com a Metryx o **token mestre** e os **tokens de cliente**. Hoje estão em texto puro em `"DATABASE".stg_customers.token` e nos `.ktr`.
- Revogar `SELECT` em `stg_customers.token` para o usuário usado pelo DSN ODBC do Power BI (ou usar um usuário só de leitura sem essa coluna).
- Trocar a senha do `postgres`, que está nos `.ktr` com ofuscação reversível, e criar usuários dedicados para o Pentaho e para o BI.
- Trocar a senha SMTP (`.kjb`) e usar uma conta de serviço.
- Apagar `C:\Users\TerraDev\Documents\teste.txt` e remover o passo `Text file output` do `get_vendas.ktr`.
- No repositório AgTechLab: tirar as credenciais root do MinIO do `docker-compose.yml` e o arquivo `backend/app/schemas/testeevogo.py` (chave de API + telefone), e rotacionar o que tiver sido exposto.
