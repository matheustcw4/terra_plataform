# Projeto Terra — Plataforma unificada (Planilhas + Metryx)

Painel web que substitui os dois BIs Power BI do Projeto Terra (consultoria pecuária):
- "Ciclo Completo": clientes que mandam planilhas `.xlsm`.
- "Versão Metryx": clientes que usam o sistema Metryx.

Um único banco canônico no PostgreSQL, alimentado por dois adapters (Planilha e Metryx), com KPIs calculados no backend e RLS por usuário/fazenda.

## Leia antes de qualquer tarefa
1. `docs/02_PROXIMOS_PASSOS.md` — **estado atual e backlog da próxima fase** (comece por aqui).
2. `docs/00_PROPOSTA_UNIFICACAO.md` — arquitetura, modelo canônico, RLS, catálogo de KPIs, plano em fases, decisões D1–D10.
3. `docs/01_CONFORMACAO_DAS_FONTES.md` — como planilha e Metryx viram as MESMAS tabelas (campo a campo).
4. `docs/analises/01..05` — engenharia reversa detalhada:
   - 01 e 02: os dois PBIX;
   - 03: pipeline de planilhas e anatomia do `.xlsm`;
   - 04: API Metryx + Pentaho;
   - 05: arquitetura de referência AgTechLab.
5. `docs/referencias/` — OpenAPI Metryx e dumps dos dois PBIX (medidas DAX, M/SQL, relacionamentos, páginas), usados para paridade.

## Regras do projeto (não negociáveis)
- **A diferença entre as fontes morre no adapter.** Nenhum KPI, view, endpoint ou componente do front pode ter lógica por fonte (`if fonte == ...`). Se precisar, falta coluna ou regra no modelo canônico; corrija lá.
- O canônico guarda **grandezas físicas e totais** (cab, kg vivo total, kg carcaça total, R$ total, ha, datas). Médias, preços, arrobas, % e UA são calculados na camada de KPI.
- Classificações vêm das dimensões (`dim.categoria_bi`, `dim.centro_custo`), nunca do texto da fonte.
- **Nada some do total por falta de de-para.**
  - Categoria ou conta desconhecida entra como pendente: `dim.categoria_map` / `dim.plano_contas_map` sem destino.
  - Os fatos apontam para o de-para; classificar depois reclassifica o histórico sem recarga.
  - Conta sem classificação aparece como "A classificar" no DRE (`fato.v_lancamento_financeiro`). Decisão Q1, 14/10/2026.
  - Quarentena é só para linha que não dá para somar (sem data, sem valor, sem natureza C/D, valor absurdo).
- Identidade sempre por id resolvido em de-para (`core.fonte_vinculo`, `dim.categoria_map`), **nunca por nome**.
- Estoque = checkpoints (`fato.inventario`) + fluxos (`fato.mov_animal`); diferença vira "ajuste de inventário" visível.
- **Uma carga nunca apaga o que a fonte deixou de mostrar por mudança de período.** Na virada de safra o consultor
  começa a planilha do zero; o arquivo só substitui do início do PERÍODO dele em diante (`Particao.desde`). Snapshot
  completo (Metryx) tem guarda de volume.
- O front não calcula nada; recebe agregados prontos e **capacidades** por fazenda, nunca a fonte.
  **Exceção temporária** (pedido do usuário, 15/10/2026): o filtro "Origem" do MENU (Integração Planilhas | Metryx),
  que só escolhe quais clientes e fazendas aparecem. Fica enquanto as planilhas existirem: a equipe vai tirá-las no
  futuro e, por ora, elas ficam ao lado do Metryx para validar os números (Q9: o mesmo cliente nas duas fontes fica
  separado, sem de-para). O escopo manda `origem` por fazenda (de `core.fazenda_fonte`); nenhum cálculo usa.
- **Telas baseadas no BI Ciclo Completo** (pedido do usuário, 15/10/2026): mesma estrutura das páginas do BI (quais
  quadros e gráficos), sem precisar ser idênticas. **O visual segue o boletim de resultados da Terra** (a apresentação
  em paisagem que o usuário mandou; pedido de 10/11/2026, no lugar da paleta do BI de 16/10/2026): azul-marinho e
  marrom sobre fundo creme, a faixa marinho com o fio marrom no título de cada página, cartões brancos de borda fina
  com a faixa no alto (marinho, ou a cor do status no indicador com meta), títulos em caixa alta espaçada, tabelas de
  cabeçalho marinho, colunas com o número escrito e as séries em marinho (realizado) e bege (planejado). A casca
  continua a do AgTechLab: menu lateral recolhível (gaveta no celular), topo com as migalhas e o filtro em uso
  ("Trocar" volta ao MENU), fonte Figtree; no PDF, a faixa do título ganha o logo branco. Antes de fazer
  uma página, consulte o layout em `docs/referencias/pbix_ciclo/layout_paginas.md` (gerado do PBIX por
  `python -m validacao.layout_do_bi <pbix>`). Os filtros ficam **só na página MENU** (no BI eles se repetem ocultos em
  todas as páginas por limitação do Power BI): Origem (temporário), Cliente, Fazenda, Safra/Cívil, Safra ou Ano,
  Mês e, no quadro "Financeiro e planejamento" (10/11/2026), o status dos lançamentos e a versão do plano de cada
  fazenda (os dois também ficam no topo das páginas que usam; abaixo). O mês é de **seleção múltipla**, como no BI (pedido do usuário, 15/10/2026): as somas usam só os meses
  marcados (podem ser salteados), e o estoque final é o do último mês marcado (`app/kpis/filtro.py`). A fazenda
  também é de **seleção múltipla** (pedido do usuário, 16/10/2026): nenhuma ou todas marcadas = "GRUPO"; com algumas,
  o topo mostra os nomes separados por " | " (mais de 3: a quantidade) e a capa, todos os nomes.
  **Exceção** (pedido do usuário, 29/10/2026): nas páginas **Previsto × Realizado** e **Financeiro**, o topo da página
  escolhe de qual orçamento vem o planejado do financeiro: o **tipo** (previsão financeira, o `previsao-financeiro` do
  Metryx e o DRE planejado da planilha; ou planejamento, o fluxo de caixa do plano do Metryx) e o **status dos
  lançamentos** do realizado (pedido do usuário, 10/11/2026: conciliado, pago e em aberto, de seleção múltipla; sem
  escolha, os pagos; só aparece quando as fazendas têm mais de uma situação, pela capacidade `situacoes`;
  `FiltroDoStatus`, `app/kpis/situacao_do_lancamento.py`). As opções vêm da API (`previsto` na resposta;
  `app/kpis/previsto_financeiro.py`), sem lógica por fonte no front; a escolha fica na URL (`previsto`, `status`),
  vale nas duas páginas e vai junto no PDF. **E a versão do planejamento** (pedido do usuário, 04/11/2026; por
  fazenda desde 10/11/2026): toda página com meta (Movimentação, Vendas, Compras, Nascimentos, Mortes,
  Transferências, além das duas acima) e o MENU mostram a versão em uso e um botão que abre a janela com todas as
  fazendas do filtro, cada uma com caixas de seleção múltipla: "Mais recente" (o padrão), as versões dela (as
  marcadas somam; decisão do usuário) e "Nenhum planejamento" (`EscolhaDasVersoes`, `JanelaDasVersoes`; `plano` na
  resposta e `GET /dashboards/versoes_do_plano` no MENU, `app/kpis/versao_do_plano.py`; as funções
  `app.versoes_do_planejado` e `app.versoes_do_orcamento`, migração 0025). A escolha é do filtro (`versao` e
  `sem_plano` na URL), vem no recorte de todas as páginas e no PDF, que mostra a versão no cabeçalho das folhas.
- "Cliente" no filtro = **proprietário** (planilha, coluna PROPRIETÁRIO) ou **customer** (Metryx); o adapter grava os
  dois em `core.fazenda.proprietario`.
- RLS de verdade:
  - **por usuário → fazendas**, não por tenant: `core.usuario_fazenda` é N:N (um usuário vê as fazendas x, y, z…;
    uma fazenda pode ser vista por vários usuários); admin vê tudo (decisão do usuário em 14/10/2026);
  - **não existe tenant**: nenhuma tabela tem `tenant_id`;
  - API conecta como `app_user` (NOSUPERUSER, NOBYPASSRLS); ETL como `app_etl` (NOBYPASSRLS, política própria);
  - contexto via `set_config(..., true)` por transação, num listener `after_begin`;
  - políticas `FOR ALL` com `USING` e `WITH CHECK`;
  - `mart.*` são tabelas com RLS, não materialized views;
  - todo PR que cria tabela de negócio cria a migração `rls_<tabela>` e um teste de isolamento.
- **O número tem que bater** com os BIs atuais (salvo os bugs catalogados P1–P15). A forma do cálculo é livre.
  **Clientes Metryx: o número bate SEMPRE com os relatórios do próprio Metryx** (inventário, Consolidado Pecuário,
  DMG; pedido do usuário, 20/10/2026). Onde o BI Metryx diverge do Metryx, vale o Metryx, e a regra do BI vira defeito
  catalogado que a plataforma não reproduz (relatório de validação §20). Onde o relatório do Metryx e o BI de planilhas
  contam um centro de custo de jeitos diferentes (a compra de animais no desembolso, os financiamentos no custeio), a
  exceção da fonte fica em `dim.centro_custo_fonte` (migração 0022; decisão do usuário, 10/11/2026), que as views dos
  lançamentos e do orçamento usam: nenhum KPI olha a fonte. Estoque Metryx: a base é o SQL `fSaldoGado`
  em `docs/referencias/pbix_metryx/power_query.csv`, menos nos bezerros mamando (`adapters/metryx/saldo.py`).
- Equivalência testada em CI: a mesma fazenda sintética, em `.xlsm` e em JSON Metryx, precisa gerar o mesmo canônico e os mesmos KPIs.

## Estilo de código (pedido do usuário, 15/10/2026)
- **Simples de ler vem antes de compacto**: um programador sênior tem de entender de primeira.
- Funções curtas, com um propósito e nome descritivo em pt-BR; **complexidade ciclomática ≤ 10** (o ruff confere,
  regra C90).
- Montagem longa (normalizadores) = uma classe pequena com etapas nomeadas, chamadas na ordem por uma função de
  entrada. Modelo: `app/etl/adapters/planilha/normalizar.py`.
- Sem funções dentro de funções, `:=`, `**{...}` com filtro, ternário encadeado ou truque de linguagem; laço `for`
  explícito no lugar de compreensão com várias condições (compreensão só quando é óbvia e cabe numa linha).
- Nomes completos (nada de `r`, `mid`, `cid`, `ep`); variáveis intermediárias com nome; `if/else` explícito.
- Comentário explica o porquê, não o quê.
- Refatoração só com a mesma funcionalidade comprovada: testes e comparação com uma referência gravada antes.
- Front: componente pequeno, um por arquivo quando passa de uma tela; lógica pura (filtro, meses, formatação) em
  `src/logic/` com teste; sem hooks/contextos próprios quando o React Router ou o TanStack Query já resolvem
  (ex.: o filtro do MENU chega às páginas por `useArea()`, que é o `useOutletContext` da `AreaAutenticada`; cada
  página usa a `Moldura caminho="/..."` (a `Casca` com o menu lateral; título e ícone saem de `paginasDoBoletim.ts`)
  e os quadros `Painel`/`Linha` de `src/core/ui`; gráfico usa o estilo comum de `src/core/ui/estiloDosGraficos.ts`;
  cor só pelas variáveis de `src/estilos.css`). Dentro de um `<svg>`, o estilo vai em **atributo**, nunca em classe:
  o `html-to-image` do PDF copia o `<svg>` sem o estilo calculado dos filhos (o velocímetro saía preto).

## Segurança e dados
- **Nunca** versionar tokens, senhas, `.env`, planilhas reais de clientes (`dados_exemplo/` é ignorado pelo git) nem `.pbix`.
- API Metryx: somente GETs da allow-list. **Nunca chamar `POST /api-metryx/control-birth`** (escreve no Metryx). Chamadas reais à API só com autorização explícita do usuário e token de teste no `.env`.
- Tokens Metryx ficam cifrados no banco (`integracao.metryx_credencial`), em campo write-only na UI.

## Stack e convenções (espelham o AgTechLab, com as correções do relatório 05 §14)
- **Backend:**
  - Python 3.12+, FastAPI, SQLAlchemy 2 (`Mapped`), psycopg 3, Alembic, Celery + Redis, pydantic v2, httpx + tenacity, openpyxl/python-calamine;
  - testes com pytest e Postgres real;
  - estrutura `app/{api/v1/endpoints, api/deps.py, core, db, models, schemas, repositories, services, kpis, etl/{adapters/{planilha,metryx}, canonical.py, mapping.py, quality.py, loaders.py, pipeline.py, duplicatas.py, diagnostico.py}, tasks}`.
- **Frontend:**
  - React 19 + TypeScript (`strict: true`) + Vite, React Router 7 com rota de layout `AreaAutenticada`, TanStack Query global, Recharts, CSS com tokens em `:root`, Vitest, oxlint;
  - estrutura `src/{core/{api,auth,escopo,ui}, modules/<modulo>/{XxxModule,XxxShell,XxxContexto}.tsx + api.ts, hooks/, logic/, pages/, componentes/}`;
  - tipos gerados do OpenAPI do FastAPI.
- **Banco:**
  - schemas `core`, `dim`, `fato`, `mart`, `ingest`, `raw`, `integracao`, `compat`, `app`;
  - nomes de tabela no singular, em pt-BR, snake_case;
  - PK `uuid` (`gen_random_uuid()`), exceto dimensões pequenas;
  - dimensões de referência (`dim.categoria_bi`, `dim.centro_custo`, `dim.subcentro`, `dim.calendario`,
    `dim.parametro`) são **globais**;
  - migração `create_<tabela>` seguida de `rls_<tabela>`.
- **API:** `/api/v1`, rotas sem prefixo duplicado, um único padrão de nomes (snake_case).
- **Infra:** tudo em `docker-compose` (db Postgres 16, redis, minio, api, worker, beat, web).
- **Idioma:** documentação, UI e mensagens em pt-BR.

## Status (15/10/2026)
- **Páginas prontas, no desenho do BI:** MENU (filtros), Previsto × Realizado, Financeiro, Movimentação do Gado,
  Vendas (abate e em pé), Compras, Nascimentos, Mortes e Transferências, com paridade contra o BI (relatório
  §12–§16), e
  Pendências de lançamento (quarentena + avisos da última carga, por fazenda, sob RLS: `app.pendencias_de_carga`) e
  Importar planilhas (menu Dados: o envio dos `.xlsm`, a fila do worker e o resultado de cada arquivo).
- **Capa e exportação em PDF:** botão "Exportar PDF" em todas as páginas e no MENU, com seleção múltipla das páginas
  e a cidade da capa (não é gravada em lugar nenhum); os três modos usam a capa do boletim de resultados
  (`modules/exportacao/boletim/CapaDoBoletim.tsx`, com o conteúdo de cada modo; 10/11/2026); o PDF sai de
  `frontend/src/modules/exportacao/` (`html-to-image` + `jsPDF`, carregados só ao exportar). **Três modos** (pedidos
  do usuário, 20/10/2026): o **Padrão** (as páginas do painel), o **Boletim Resumido** (chave `analitico`; até
  10/11/2026 se chamava Analítico: o **boletim de resultados** da Terra em folhas de paisagem 16:9, no desenho do **gerador oficial**
  `gerar_boletim.py` que o usuário mandou; versão 2, 10/11/2026; a versão 1, feita a partir da apresentação, está na
  tag git `boletim-v1`): capa marinho e marrom com o ano ou a safra, 01 Resumo · Previsto × Realizado com a lateral
  marinho, 02 Financeiro, 03 Rebanho (com os quadros "Sem nascimentos" e "Sem transferências" quando não houve) e 04
  Comercialização numa folha só (venda abate com a tabela Fêmea / Macho / Geral quando os dois sexos venderam, e a
  venda em pé numa faixa; compras e reposição com o ágio). Fontes Archivo larga e Arimo, dos pacotes
  `@fontsource-variable`; o logo e o símbolo oficiais em `src/assets/boletim/`; o resultado com a regra do gerador
  (verde quando o realizado chega ao planejado: `resumo.status_do_resultado_*` da API). `modules/exportacao/boletim/`,
  lógica em `src/logic/boletim.ts`; colunas e barras em HTML, não em SVG) e o **Personalizado** (os assuntos do boletim em folhas
  A4, no visual novo; a pessoa marca os assuntos e o que mostrar em cada um: leitura, previsto × realizado,
  lançamentos, gráficos, números do período, notas; os blocos se encaixam nas folhas, quebrando entre quadros;
  `modules/exportacao/analitico/`). Nos três modos há dois campos de **nota técnica** (início e fim do PDF; pedido do
  usuário, 21/10/2026), que, como a cidade da capa, não são gravados em lugar nenhum. O mês de referência é o último
  mês do filtro; as folhas comparam o mês e o acumulado do período (safra ou ano) com o previsto, mostram a meta e
  trazem a leitura dos números em frases. Tudo vem pronto de `GET /dashboards/analitico` (`app/kpis/analitico/`, que
  reusa os KPIs das páginas, com as séries mês a mês do caixa, do estoque e do valor dos lotes). Regras em
  `docs/02_PROXIMOS_PASSOS.md` ("Boletim analítico").
- **Operação:** cargas agendadas com Celery + Redis (`app/tasks/`: beat dispara, worker executa uma por vez, trava
  consultiva no Postgres; agendas `AGENDA_*` no formato do cron; Metryx desligado até a autorização; fila com nome
  próprio, `terra`), botão **"Atualizar agora"** só para o admin no topo de todas as telas (`POST /admin/atualizacao`
  põe `cargas.atualizar_agora` na fila: a carga do Metryx, e por isso o botão só aparece com `AGENDA_METRYX` ligada,
  pelo `disponivel` da situação; a tela acompanha pela trava e pelo `ingest.job` mais recente e, no fim, relê os
  números) e deploy na VPS
  (`docker-compose.prod.yml`, imagens `backend/Dockerfile` e `docker/web/Dockerfile` com Caddy, backup diário; guia
  em `docs/03_DEPLOY_VPS.md`, validado subindo tudo no Docker Desktop).
- **Administração (só admin):** de-para de categorias (classificar recalcula o estoque), de-para de contas (o DRE
  muda na hora), usuários (nome, e-mail, senha só como hash argon2 e função), cadastro de funções (`core.funcao`: a
  função do usuário é escolhida nessa lista, não digitada) e acesso às fazendas;
  `app/services/{de_paras,usuarios,funcoes}.py` + `/api/v1/admin/*`. A função ainda não dá permissão: quem entra na
  administração é o `eh_admin` (papéis por função ficam para a D10).
- **Fatia vertical pronta** (login → escopo → KPIs de rebanho → página Movimentação do Gado):
  - API: `POST /auth/login`, `GET /auth/me`, `GET /escopo`, `GET /dashboards/{previsto_realizado,financeiro,movimentacao,vendas,compras,nascimentos,mortes,transferencias,analitico}`, `GET /qualidade/pendencias`, `/admin/*` (JWT + argon2, login pela
    função `app.dados_de_login`, migração 0012; RLS do usuário em toda rota de dados);
  - KPIs em `app/kpis/` (`filtro.py` comum, `movimentacao.py`, `lotes.py` com `vendas.py`, `compras.py`,
    `nascimentos.py`, `mortes.py`, `transferencias.py`, `financeiro.py`, `previsto_realizado.py` e o pacote
    `analitico/` do PDF analítico), com paridade
    contra o BI em `validacao/cruzar_kpis.py`, `cruzar_compras_e_vendas.py`, `cruzar_zootecnico.py`,
    `cruzar_financeiro.py` e `cruzar_previsto.py` (relatório §12 a §16);
  - front em `frontend/` (Vite, React 19, Router 7, TanStack Query, Recharts), tipos gerados do OpenAPI;
  - usuários na tela de admin; o primeiro admin pelo `python -m app.comandos` (`criar-usuario`, `dar-acesso`); a
    equipe da consultoria pela planilha de levantamento (`importar-equipe`, `app/services/equipe.py`).
- **Base de integração e adapters prontos** (ver `README.md` e o §0 de `docs/02_PROXIMOS_PASSOS.md`):
  - Postgres no compose; migrações 0001–0025 (core/dim/fato/ingest/raw/integracao, RLS, seeds, estoque, "A classificar",
    login, pendências, recálculo do estoque pela API, série nova do estoque começa no início da fazenda, cadastro de
    funções e o RLS dele, tipo do orçamento, versões do planejado, fila da importação de planilhas e o RLS dela, a
    exceção de cada fonte às marcas do centro de custo e o RLS dela, a situação do lançamento e a versão por fazenda);
  - contrato canônico, motor (guarda de volume, arquivo em dobro, recorte `desde`), CLI `python -m app.etl`;
  - **adapter de planilhas**: as planilhas chegam pela tela **Importar planilhas** (09/11/2026, D8; todo usuário,
    só nas fazendas a que tem acesso, e fazenda nova só o admin; `ingest.importacao`, `app/etl/importacao.py`,
    `adapters/planilha/enviada.py`, migrações 0020–0021). **O Google Drive deixou de ser fonte** (pedido do
    usuário, 10/11/2026): as planilhas chegam só pela tela e o Metryx pela API; não há `PLANILHAS_DIR` nem agenda
    de planilhas, e a carga em massa de uma pasta local (uma cópia dos arquivos) continua só pela linha de comando
    (`python -m app.etl planilhas --pasta DIR`). O adapter foi validado nos 230 `.xlsm` reais;
  - **adapter Metryx** (cliente HTTP com allow-list, token cifrado, normalizador com a regra de saldo do BI),
    ajustado ao payload real (A29–A32 do relatório de validação §17), com a área de pasto do `utilizacao-pasto` para a
    lotação cab/ha (16/10/2026, §18); a UA do Metryx fica de fora até a API trazê-la; e o **planejamento** (27/10/2026,
    `adapters/metryx/planejamento.py`): metas de compra, venda, nascimento, morte e desmame, rebanho previsto pela
    evolução do rebanho (o saldo do fim do mês, como o relatório financeiro do Metryx; 10/11/2026) e DRE previsto, com todas as versões (`plVersionCode` dá a ordem, `plVersionName` o
    nome; o BI soma todas): numa fazenda e safra vale a versão escolhida na tela ou, sem escolha, a mais recente
    (`app.versoes_do_planejado`, migração 0019; 04/11/2026), com o mês pelo `month` e pela safra, porque o `date` da API erra o ano de junho (defeito P19, relatório
    §22). A ponte do datalake traz o previsto menos compras e vendas (a stg perdeu a versão e as decimais). O
    **rebanho médio realizado** sai da média do saldo de cada dia do balanço, como o relatório do Metryx
    (`adapters/metryx/rebanho.py`, 27/10/2026); o endpoint `rebanho-medio-pecuario` do BI conta animais a mais e fica
    só no bruto (defeito P18, relatório de validação §21). O `previsao-fluxo-caixa-planejamento` entra como orçamento
    de tipo `planejamento`, com todas as versões (29/10/2026; migração 0018: `fato.orcamento_financeiro.tipo` e
    `dim.versao_plano.ordem`); o subcentro genérico "Subcentro de Custo" fica de fora da conta; a natureza vem só do
    `type`, com o valor absoluto (a despesa do plano vem negativa com `type` Débito; tratá-la como estorno punha a meta
    do desembolso negativa, 10/11/2026); nos lançamentos, a situação do título (conciliado, pago ou em aberto, este
    pelo vencimento e pelo valor a pagar; o excluído no Metryx não entra; migração 0024);
  - **carga do histórico** das planilhas a partir do snapshot do BI (Q6): `python -m app.etl planilhas-historico`;
  - 191 testes com Postgres real (incluindo a equivalência planilha × Metryx, a API, o admin, as cargas agendadas, o
    boletim analítico e a importação pela tela) + 96 testes do front (Vitest);
  - validação contra os BIs em `docs/validacao/`; scripts em `backend/validacao/` (`cruzar`, `classificar`,
    `cruzar_kpis`, `cruzar_compras_e_vendas`, `cruzar_zootecnico`, `cruzar_financeiro`, `cruzar_previsto`,
    `layout_do_bi`, `lotacao_sem_area`). A lotação fica igual ao BI mesmo quando um mês com rebanho não tem área, o
    que a infla (Q13, decidido em 16/10/2026; anotação em `docs/validacao/2026-10-16_lotacao_meses_sem_area.md`).
    A lotação **prevista** do PDF analítico, que o BI não tem, usa só os meses em que o plano tem área (decidido em
    20/10/2026).
- O datalake de planilhas do BI é um snapshot de ago/2026; 55 planilhas já viraram para a safra 26/27 e não trazem
  mais a 25/26. Esse histórico entra pela carga única `planilhas-historico` (decisão Q6), que roda depois de
  `planilhas` e só preenche o que vem antes do que os arquivos cobrem.
- **API Metryx real: três clientes até agora.** Em 27/10/2026, com o token passado pelo usuário (cifrado nos bancos
  `terra` e `terra_validacao`), a Maister passou a vir pela API, porque o datalake dela parou em 06/10; jul–set/2026 do
  U6 e da Maister batem com o Metryx (rebanho médio, nascimentos, mortes, compras e vendas; relatório §21). O token da
  Maister também não tem a permissão do `utilizacao-pasto` (401). Em 20/10/2026, com o token passado pelo usuário, o grupo U6 também foi
  recarregado pela API no banco de validação (relatório §19): o token não tem permissão para transferências nem para
  pastagens, e a API responde 401 nesses endpoints (A33: num opcional, só ele fica de fora). Em 15/10/2026, com autorização do usuário, foi consultado o cliente da
  Serra Dourada (Maria Cecília), com o token cifrado nos bancos `terra` e `terra_validacao`. Essa fazenda foi
  recarregada pela API no banco de validação e bate 100% com o DMG do Metryx; em 16/10 foi recarregada de novo com o
  `utilizacao-pasto` (lotação cab/ha 1,26 na safra 25/26 e 0,93 na 26/27, relatório §18). Outros clientes e a agenda do Metryx
  continuam dependendo de autorização explícita (`python -m app.etl metryx-credencial`).
- Próximos passos: o primeiro deploy (as planilhas chegam pela tela de importação: D8 decidida); classificar os pendentes nas
  telas de admin (roadmap A–F em `docs/02_PROXIMOS_PASSOS.md` §3).
- Decisões D1–D10 (proposta §11): D8 decidida (VPS Linux em produção, desenvolvimento no Windows, planilhas pela tela
  de importação) e D10 adiada (só técnicos consultam por ora; permissionamento no final); as demais seguem pendentes. Até lá, use as recomendações da proposta como padrão provisório, marcado com `# TODO(D<n>)`.
- Como rodar: `docker compose up -d db`; em `backend/`, `.venv/Scripts/python -m pytest` (Python 3.12 via `py -3.12`; host `127.0.0.1:55432`).
  Em `frontend/`: `npm test`, `npm run lint`, `npm run build`. API em dev na porta **8010** (a 8000 costuma estar
  ocupada nesta máquina); o Vite repassa `/api` para ela (outra porta: `TERRA_API_PORTA`). `.claude/launch.json` sobe
  os dois (`api-validacao`, `web`; com a 8010 ocupada, `api-validacao-8011` e `web-8011`, este na porta 5175);
  no PyCharm, as configurações da pasta `.run/` (guia no README, "Rodar e testar pelo PyCharm").
