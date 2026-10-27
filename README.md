# Projeto Terra — plataforma unificada (planilhas + Metryx)

Banco canônico único no PostgreSQL, alimentado por adapters (planilha `.xlsm` e API Metryx) que produzem o mesmo
contrato. Contexto completo em [`CLAUDE.md`](CLAUDE.md) e [`docs/`](docs/).

## Subir o ambiente (Windows / PowerShell ou Git Bash)

```bash
cp .env.example .env            # e troque as senhas
docker compose up -d db         # Postgres 16 em 127.0.0.1:55432 (cria os papéis app_owner/app_user/app_etl)
cd backend
py -3.12 -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m pytest  # cria um banco descartável terra_test_<pid>, migra e testa com os papéis reais
```

Use `127.0.0.1`, não `localhost`: no Docker Desktop o `localhost` tenta IPv6 primeiro e a conexão trava.

## Como os dados entram

```
fonte ──► adapter.descobrir() ─► extrair() ─► normalizar() ──► LoteCanonico ──► MotorCarga ──► fato.* / dim.* / core.*
         (só o adapter sabe a fonte)                          (contrato único)   (resolve ids, valida, grava, estoque)
```

| Peça | Onde | O que faz |
|---|---|---|
| Contrato | `backend/app/etl/canonical.py` | modelos canônicos (totais físicos, identidades externas, partições) |
| Adapter | `backend/app/etl/adapters/base.py` | `SourceAdapter`: `descobrir` → `extrair` → `normalizar` (função pura) |
| De-paras | `backend/app/etl/mapping.py` | id externo → id interno (`core.fonte_vinculo`, `dim.categoria_map`, `dim.plano_contas_map`); a planilha só confirma a categoria quando o CADASTROINICIAL traz a categoria BI (em branco, fica pendente e não apaga o que o admin classificou); o pendente se resolve na tela de admin |
| Qualidade | `backend/app/etl/quality.py` | ocorrências e quarentena (linha ruim não derruba o arquivo; arquivo ruim não derruba o job); valor fora do padrão (peso médio, rendimento, R$/kg vivo fora de 4–40) e venda ou compra sem valor viram aviso; tudo aparece na aba Pendências |
| Gravação | `backend/app/etl/loaders.py` | `substituir` (recorte apagado e regravado) ou `mesclar` (upsert pela chave natural) |
| Motor | `backend/app/etl/pipeline.py` | orquestra por unidade, idempotente por sha256, guarda o bruto e reprocessa sem reler a fonte |
| Estoque | migração `0010` | `fato.recalcular_estoque_mensal`: checkpoints + fluxos → balanço mensal com ajuste de inventário |

## Rodar as cargas

```bash
cd backend
.venv/Scripts/python -m app.etl planilhas                 # todos os RELATÓRIO*.xlsm de PLANILHAS_DIR (pula o que não mudou)
.venv/Scripts/python -m app.etl planilhas --arquivo "RELATÓRIO - 85 - ITAPAJÉ - BELA VISTA.xlsm"
.venv/Scripts/python -m app.etl planilhas-historico --ate 2026-06   # carga única do histórico (snapshot do BI), após `planilhas`
.venv/Scripts/python -m app.etl metryx-credencial --cliente <idCustomer> --nome "Cliente"   # pede o token sem ecoar
.venv/Scripts/python -m app.etl metryx                    # clientes com credencial ativa
.venv/Scripts/python -m app.etl reprocessar <versao_id> --fonte planilha
```

Validação contra os BIs atuais (banco descartável `terra_validacao`; relatório em `docs/validacao/`):

```bash
.venv/Scripts/python -m validacao.cruzar --ate 2026-07      # adapter real nos .xlsm de PLANILHAS_DIR + Metryx
.venv/Scripts/python -m validacao.classificar               # separa diferença de arquivo alterado após o snapshot
.venv/Scripts/python -m validacao.cruzar_kpis --sorteios 300 # KPIs da página Movimentação × medidas do BI
.venv/Scripts/python -m validacao.cruzar_compras_e_vendas --sorteios 300   # Vendas e Compras × medidas do BI
.venv/Scripts/python -m validacao.cruzar_zootecnico --sorteios 300   # Nascimentos, Mortes e Transferências × BI
.venv/Scripts/python -m validacao.cruzar_financeiro --sorteios 300   # Financeiro × medidas do BI
.venv/Scripts/python -m validacao.cruzar_previsto --sorteios 300     # Previsto × Realizado × matriz do BI
```

| Adapter | Onde | Fonte | Unidade de origem |
|---|---|---|---|
| Planilhas | `backend/app/etl/adapters/planilha/` | `.xlsm` em `PLANILHAS_DIR` (somente leitura, calamine) | um arquivo |
| Metryx | `backend/app/etl/adapters/metryx/` | API REST, só os GET da allow-list | um cliente (token) |

- **Planilha:**
  - leitura pelo nome do cabeçalho, com apelidos;
  - identidade = código do projeto + fazenda, conferidos com o nome do arquivo (código diferente, ou fUnidade sem
    código e com o nome de outra fazenda: o arquivo não carrega);
  - desmame, mudança e consumo entram como lançamentos;
  - venda sem cliente entra com aviso;
  - arquivo em dobro (mesma fazenda, ou os mesmos bytes com outro nome): vale o mais recente; o aviso diz se é
    cópia ou outra versão e alerta quando o arquivo ignorado tem mais dados que o mantido;
  - o arquivo só substitui do início do PERÍODO dele em diante: a planilha da safra nova começa vazia e não apaga a
    safra anterior (`Particao.desde`);
  - linha do modelo sem nenhum número é ignorada; `OPERAÇÃO = VERIFICAR` vai para a quarentena (o BI não soma);
  - totais de kg e R$: a coluna de total da planilha primeiro (é o que o BI soma); se ela não bate com o valor por
    cabeça × QTD (mais de 5%), a linha entra com aviso `TOTAL_INCONSISTENT`, que aparece em Pendências.
- **Metryx:**
  - token cifrado (`METRYX_CHAVE_CIFRA`);
  - repetição automática em falha transitória;
  - 401 marca a credencial como inválida;
  - endpoint 403 fica de fora sem apagar os dados dele;
  - guarda de volume: resposta vazia ou parcial não apaga dados;
  - regra de saldo do BI (`saldo.py`).

## API e painel web

```
navegador ──► frontend (Vite/React) ──/api──► FastAPI (app_user + RLS do usuário) ──► app/kpis/* ──► fato.*
```

| Rota (`/api/v1`) | O que devolve |
|---|---|
| `POST /auth/login`, `GET /auth/me` | token JWT (argon2 na senha; validade `JWT_MINUTOS`) e o usuário logado |
| `GET /escopo` | fazendas que o usuário vê, com o cliente (proprietário ou customer), primeiro/último mês com dado e **capacidades** |
| `GET /dashboards/movimentacao?fazendas=..&inicio=AAAA-MM&fim=AAAA-MM` | os cartões da página do BI (estoque final, rebanho médio e lotação em cab e UA, nascimentos, mortes, compras e vendas com a meta) e os gráficos de estoque mensal e por categoria |
| `GET /dashboards/vendas?tipo=abate\|em_pe&fazendas=..&inicio=..&fim=..` | quadro GERAL/MACHO/FÊMEA × realizado/planejado (cabeças, faturamento, @, preços, peso médio, rendimento) e série mensal |
| `GET /dashboards/compras?fazendas=..&inicio=..&fim=..` | quadro GERAL/MACHO/FÊMEA × realizado/planejado (cabeças, investimento, preço do kg, peso médio), preço da @ de compra, ágio e série mensal |
| `GET /dashboards/nascimentos?fazendas=..&inicio=..&fim=..` | quadro GERAL/MACHO/FÊMEA (realizado, planejado, % da meta e parte do sexo no total) e série mensal com os acumulados |
| `GET /dashboards/mortes?fazendas=..&inicio=..&fim=..` | quadro GERAL/BEZERROS/JOVENS/ADULTOS (mortes, meta, mortalidade sobre o rebanho médio do grupo e, nos bezerros, sobre os nascimentos), mortes por causa e série mensal |
| `GET /dashboards/transferencias?fazendas=..&inicio=..&fim=..` | entrada e saída × GERAL/MACHO/FÊMEA × realizado/planejado (quantidade, peso médio, valor da @) e cabeças que entraram e saíram por mês |
| `GET /dashboards/previsto_realizado?fazendas=..&inicio=..&fim=..` | a matriz do DRE: por classificação (com o subtotal de desembolso) e por conta, realizado, planejado, % de variação e semáforo, no último mês e no acumulado do período; e o resultado |
| `GET /dashboards/financeiro?fazendas=..&inicio=..&fim=..` | desembolso e receitas do período; velocímetros (realizado, meta, fim da escala) de desembolso e custeio por cabeça por mês e do preço da @ vendida; desembolso por centro de custo; série mensal (receitas, despesas, saldo, desembolso e desembolso por cabeça, com o planejado) |
| `GET /qualidade/pendencias?fazendas=..` | o que a última carga de cada arquivo deixou fora dos números (quarentena) ou marcou para conferir, com arquivo, aba, linha e como corrigir |
| `GET /admin/categorias?so_pendentes=..&busca=..`, `PUT /admin/categorias/{id}` | (só admin) de-para categoria da fonte → categoria BI: lista (pendentes primeiro, com o uso de cada uma) e classificação; classificar recalcula o estoque das fazendas que usam a categoria |
| `GET /admin/contas?so_pendentes=..&busca=..`, `PUT /admin/contas/{id}` | (só admin) de-para conta da fonte → centro de custo: lista ("A classificar" primeiro, por valor) e classificação; o DRE muda na hora |
| `GET/POST /admin/usuarios`, `PATCH /admin/usuarios/{id}`, `GET/PUT /admin/usuarios/{id}/fazendas` | (só admin) usuários (criar com nome, e-mail, senha e função; ativar/desativar, admin, trocar senha e função) e as fazendas que cada um vê |
| `GET/POST /admin/funcoes`, `PATCH/DELETE /admin/funcoes/{id}` | (só admin) cadastro de funções: criar, renomear, ativar/desativar; apagar só a que nenhum usuário tem |

Usuários: no painel, em **Administração → Usuários e acesso** (só admin). Pela linha de comando, para montar o primeiro
admin (rodam como dono do banco; a senha vem de `SENHA_NOVA` ou é perguntada sem eco):

```bash
cd backend
.venv/Scripts/python -m app.comandos criar-usuario --email maria@terra.com --nome "Maria" --admin
.venv/Scripts/python -m app.comandos dar-acesso --email joao@cliente.com --cliente 85      # todas as fazendas do projeto 85
.venv/Scripts/python -m app.comandos importar-equipe "Levantamento Clientes para Power BI.xlsx"   # simula
.venv/Scripts/python -m app.comandos importar-equipe "Levantamento Clientes para Power BI.xlsx" --aplicar
```

O `importar-equipe` cria os técnicos e gerentes da planilha de levantamento, com a função e as fazendas de cada um
(regras em `app/services/equipe.py`). Sem `--aplicar`, só mostra o relatório. Pode rodar de novo, porque só
acrescenta: não apaga usuário nem acesso e não troca nome, senha ou função já escolhidos. Usuário novo nasce sem
senha: o admin define a senha na tela de usuários.

Rodar em desenvolvimento (precisa de `JWT_SEGREDO` no `.env`, 32+ caracteres aleatórios):

```bash
cd backend
.venv/Scripts/python -m uvicorn app.main:app --port 8010                                   # banco do .env
.venv/Scripts/python -m uvicorn app.main:app --port 8010 --env-file validacao/api_validacao.env   # banco de validação
cd ../frontend
npm install
npm run dev          # http://localhost:5173; o Vite repassa /api para 127.0.0.1:8010
npm test             # Vitest
npm run lint         # oxlint
```

Os tipos TypeScript saem do contrato da API. Depois de mudar um schema ou rota:

```bash
cd backend
.venv/Scripts/python -m app.exportar_openapi ../frontend/src/core/api/openapi.json
cd ../frontend
npm run tipos        # gera src/core/api/esquema.d.ts (não editar à mão)
```

Front: as telas seguem o BI Ciclo Completo. O boletim abre pelo **MENU** (Origem — temporário, Integração Planilhas
ou Metryx —, Cliente, Fazendas e Meses de seleção múltipla — nenhuma fazenda = "GRUPO" —, Safra/Cívil, Safra ou Ano), e as páginas
mostram só o resultado. O visual tem a base do AgTechLab nas cores da Terra: menu lateral com as páginas (recolhível;
no celular vira gaveta), topo com o filtro em uso e o "Trocar" (volta ao MENU), cartões de borda fina e gráficos com
um estilo comum (`src/core/ui/estiloDosGraficos.ts`). Na folha do PDF o cabeçalho leva o logo, a seleção e o título.
O filtro fica na URL, para o link poder ser compartilhado, e o navegador lembra o último.
O botão **Exportar PDF** (em todas as páginas e no MENU) gera o boletim em PDF com a capa e as páginas escolhidas
(`src/modules/exportacao/`), em três modos: **Padrão** (as páginas do painel, como na tela), **Analítico** (folhas A4
do mês de referência, o último mês do filtro: o mês e o acumulado contra o previsto, a meta do período e uma "Leitura
do mês" em frases; dados de `GET /api/v1/dashboards/analitico`, folhas em `src/modules/exportacao/analitico/`) e
**Personalizado** (a pessoa escolhe os assuntos e o que mostrar em cada um; os blocos se encaixam nas folhas A4). Nos
três modos dá para escrever uma nota técnica para o começo e outra para o fim do PDF.
Pastas: `src/core/` (cliente da API, login, casca, moldura, quadros e gráficos), `src/logic/` (funções puras com teste, como o filtro
do MENU), `src/modules/<domínio>/` (páginas e chamadas de cada domínio), `src/assets/bi/` (logo e ícones do BI).
O layout das páginas do BI, para as próximas telas, está em `docs/referencias/pbix_ciclo/layout_paginas.md`.

## Cargas agendadas e produção

Em produção, as cargas rodam sozinhas: o **beat** (Celery) dispara e o **worker** executa, uma por vez
(`backend/app/tasks/`): planilhas a cada 2 horas, o estoque no dia 1 de cada mês e o Metryx só depois de autorizado
(`AGENDA_METRYX` vazia = desligado). As agendas vêm do `.env` no formato do cron (`AGENDA_PLANILHAS`, `AGENDA_METRYX`,
`AGENDA_ESTOQUE`). Em desenvolvimento, as cargas continuam pela linha de comando (`python -m app.etl ...`).

O admin tem um botão discreto **"Atualizar agora"** (o ↻ no topo de todas as telas): ele põe a tarefa
`cargas.atualizar_agora` na fila do worker (planilhas e, se `AGENDA_METRYX` estiver ligada, o Metryx), gira enquanto a
carga roda e, quando ela termina, faz as páginas relerem os números. Com uma carga já rodando, o pedido é recusado; se
o worker não começar em 2 minutos, o botão avisa. As tarefas da Terra usam a fila `terra` (num Redis compartilhado, só
o worker da Terra as pega).

O deploy na VPS Linux (docker compose com Postgres, Redis, API, worker, beat, Caddy com HTTPS automático e backup
diário) está em **[docs/03_DEPLOY_VPS.md](docs/03_DEPLOY_VPS.md)**: `docker-compose.prod.yml`, `.env.producao.example`,
`backend/Dockerfile`, `docker/web/Dockerfile` e `docker/caddy/Caddyfile`.

## Rodar e testar pelo PyCharm

Uma vez por máquina (nesta já está feito: `backend/.venv`, `frontend/node_modules`, `.env` e o banco `terra_validacao`
com os dados reais carregados):

1. `docker compose up -d db` na raiz (o Postgres sobe em `127.0.0.1:55432`).
2. No PyCharm: *File → Open* → `C:\Workspace	erra_boletim` (a raiz, não a pasta `backend`).
3. *Settings → Project → Python Interpreter → Add Interpreter → Add Local Interpreter → Select existing* →
   `C:\Workspace	erra_boletimackend\.venv\Scripts\python.exe`.
4. Clique com o botão direito na pasta `backend` → *Mark Directory as → Sources Root* (para o `from app...` resolver).

As configurações de execução já vêm na pasta `.run/` e aparecem no seletor do canto superior direito:

| Configuração | O que faz |
|---|---|
| **Painel (API + front)** | sobe as duas de uma vez |
| API (banco de validação) | `uvicorn app.main:app --port 8010 --reload`, no banco `terra_validacao`; dá para rodar em *Debug* com breakpoint |
| Front (npm run dev) | Vite em http://localhost:5173 (se a porta estiver ocupada, ele usa a 5174 e mostra no console) |
| Testes do backend | `pytest` em `backend/tests` (cria e apaga um banco descartável) |

A configuração do front é do tipo npm, que só existe no PyCharm Professional. No Community, abra o *Terminal* do
PyCharm e rode `cd frontend` e `npm run dev`.

Para entrar no painel, use os usuários de desenvolvimento cujo e-mail e senha estão no `.env` (`DEV_CONSULTOR_*`:
consultor do projeto 46; `DEV_ADMIN_*`: vê tudo). Usuário novo: `python -m app.comandos criar-usuario` (seção
anterior).

Por onde começar a leitura do código:
- carga: `backend/app/etl/pipeline.py` (o motor, em etapas) e `backend/app/etl/adapters/planilha/normalizar.py`
  (a planilha virando o canônico);
- números das páginas: `backend/app/kpis/movimentacao.py` e `backend/app/kpis/vendas.py`;
- pendências: `backend/app/services/pendencias.py` e a função `app.pendencias_de_carga` (migração 0013);
- front: `frontend/src/core/auth/AreaAutenticada.tsx` (login + filtro do topo) e `frontend/src/modules/*`.

## Segurança

- A API conecta como `app_user` e os workers como `app_etl`, ambos sem `BYPASSRLS`.
- O RLS é por usuário → fazendas (`core.usuario_fazenda`); o admin vê tudo.
- O contexto do usuário vale por transação (`set_config(..., true)` no listener `after_begin` em `app/db/session.py`).
- O `.env`, as planilhas reais (`dados_exemplo/`) e os `.pbix` nunca entram no git.
