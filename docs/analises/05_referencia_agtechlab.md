# 05 — Arquitetura de referência: Locks AgTechLab

> Objetivo: documentar com precisão a estrutura lógica dos dois repositórios de referência ("Locks AgTechLab") para que a nova plataforma de pecuária (React + TS + Vite / API Python / PostgreSQL com RLS por usuário / ETL em background com adaptadores Metryx REST e Excel) **espelhe as convenções boas e evite as fracas**.
>
> Fontes lidas (somente leitura, nada foi executado/instalado):
> - `ref/locks_agtech_backend` — 1 commit visível: `2acd354 Criação de índices e otimização das telas do Fly`. Migrações datadas de 2026-07-28 a 2026-09-19.
> - `ref/locks_agtech_frontend` — 1 commit visível: `4d34735 feat(fly): integração com o backend novo...`. Specs datadas de 2026-08-23 a 2026-09-16.
>
> Segredos encontrados no código foram substituídos por **[REDACTED]** neste relatório.

---

## Sumário executivo (o que importa em 12 linhas)

1. **Backend**: FastAPI 0.115 + SQLAlchemy 2.0 (sync, psycopg2) + Alembic + Celery 5 (Redis) + PostGIS 16-3.4 + MinIO (S3) + Athena (fonte de dados). Layout `app/{api/v1/endpoints, core, models, schemas, services, tasks}`. **Não há camada de repositório nem de serviço de verdade**: os endpoints executam SQL cru (`text()`) direto na sessão.
2. **Multi-tenancy**: coluna `tenant_id` em todas as tabelas + RLS do Postgres lendo o GUC customizado `app.current_tenant_id` via `current_setting('app.current_tenant_id', true)`. O GUC é gravado com `SET` (nível de sessão, f-string) em **cada endpoint e em cada task**, e no dependency `validate_token`.
3. **O RLS da referência NÃO protege nada na prática**: o app conecta com o mesmo usuário criado como `POSTGRES_USER` no container (superusuário → ignora RLS mesmo com `FORCE`); as políticas cobrem só SELECT e INSERT (`WITH CHECK (true)`), não há UPDATE/DELETE; não existem papéis separados (owner × app). O isolamento real é o `AND tenant_id = :tenant_id` escrito à mão nas queries. **Copiar a ideia, não a implementação.**
4. **Escopo "unidade → fazendas"** existe só no frontend (filtro client-side); não há vínculo usuário↔fazenda no banco do backend. O documento `docs/esquema/` (no repo do front) propõe `usuario_fazenda` e RLS por `organizacao_id` com `SET LOCAL`, mas declara "RLS não está escrita".
5. **Auth**: login `POST /api/v1/auth/auth` → bcrypt (passlib) → JWT HS256 com `sub`, `tenant_id`, `role`; `HTTPBearer`. Role (`viewer`/`admin`) **nunca é verificada no servidor**. Rotas de criar tenant/usuário são públicas.
6. **ETL**: tabela de job (`etl_jobs`, `shp_import_jobs`, `imports` no Fly) + endpoint que cria o job e dispara `task.delay()` + endpoint de status; task muda `pending → processing → done/error`, faz upsert `INSERT ... ON CONFLICT DO UPDATE` linha a linha, grava "erros brandos" (ex.: `Fazendas sem match: [...]`). Celery beat cria jobs por tenant a cada 10 min.
7. **Adaptadores de formato** (decoder do Fly): `identificar(arquivo) → parse_<formato>() → modelo canônico → montar_missao()`, com dicionário de **apelidos de coluna** normalizados — é o melhor modelo para o adaptador de Excel do novo projeto. Upload de SHP tem fluxo **upload → preview das colunas → confirmação do mapeamento → task**.
8. **Frontend**: React 19 + Vite 8 + TS 6 + React Router 7 + TanStack Query 5 (só no módulo Soil) + Recharts 3 + Leaflet/MapLibre + ExcelJS. **Sem** axios, zod, react-hook-form, Zustand/Redux, Tailwind/shadcn/MUI, i18n. CSS puro com tokens em `:root` e um tema por módulo.
9. **Estrutura do front**: `src/core/{api,auth,escopo,ui,geo,relatorio}` + `src/modules/<modulo>/{XxxModule.tsx, XxxShell.tsx, XxxContexto.tsx, api, hooks, pages, componentes, logic}` + `src/pages/{Login,Hub}` + `moduleRegistry.ts` (um card por linha).
10. **Filtro global**: `EscopoUnidadeProvider` (unidade ativa persistida em `localStorage`, expõe `fazendasDaUnidade[]`), exibido numa barra fixa no rodapé (`BarraUnidade`). Hooks de dados fazem *fan-out* uma query por fazenda (`useQueries`) e fundem com tratamento de falha parcial (`mesclarPorFazenda` + `AvisoDadosParciais`).
11. **CRUD dirigido por configuração**: `EntityConfig` (colunas, campos, escopo) + `EntityCrudPage` genérico + adaptador `CrudApi` — ótimo para cadastros do novo projeto.
12. **Deploy**: não existe. Sem Dockerfile da API/worker, sem CI, sem testes no backend; o front é servido por `vite dev` exposto na LAN com proxy. Há ~84 testes Vitest no front.

---

# PARTE A — BACKEND (`locks_agtech_backend`)

## 1. Árvore de pastas (sem `.git`, `.idea`, `__pycache__`)

```
locks_agtech_backend/
├── .gitignore                      # venv/, __pycache__/, *.pyc, .env, alembic_fly/versions/__pycache__/
├── docker-compose.yml              # SÓ infraestrutura: postgis 16-3.4 (porta 5433), redis 7, minio (9000/9001)
└── backend/
    ├── requirements.txt            # dependências pinadas (incompletas — ver §2)
    ├── alembic.ini                 # Alembic do banco PRINCIPAL ("agro") → script_location = alembic
    ├── alembic/
    │   ├── env.py                  # URL vem de settings.database_url; importa app.models; include_object
    │   ├── script.py.mako          # template padrão
    │   └── versions/               # 36 migrações (tenants→users→fazendas→safras→RLS→talhão→análises→ETL→unidade→mapas)
    ├── alembic_fly.ini             # Alembic do banco do MÓDULO Locks Fly (aviação agrícola) → script_location = alembic_fly
    ├── alembic_fly/
    │   ├── env.py                  # usa engine_fly e Base_fly (outro banco: settings.fly_db_name)
    │   └── versions/               # 26 migrações (service_orders, applications, flights, imports... + RLS + índices)
    ├── teste_celery.py             # script ad-hoc (referencia task inexistente `task_teste` — quebrado)
    ├── teste_shp.py                # script ad-hoc de inserção de talhão via geopandas (caminho local + UUIDs fixos)
    └── app/
        ├── main.py                 # FastAPI(title="Agro Platform API"), include_router(prefix="/api/v1"), GET /health
        ├── api/v1/
        │   ├── router.py           # agregador: include_router(<mod>.router, prefix="/<recurso>", tags=[...])
        │   └── endpoints/
        │       ├── auth.py         # POST/GET /auth/tenants, POST /auth/auth (login)
        │       ├── user.py         # POST /users/users (cria usuário — sem autenticação)
        │       ├── fazendas.py     # CRUD /fazendas/fazendas
        │       ├── safras.py       # CRUD /safras/safras (filtro ?fazenda_id)
        │       ├── culturas.py     # CRUD /culturas/
        │       ├── periodos.py     # CRUD /periodos/periodos (filtro ?safra_id)
        │       ├── unidades.py     # CRUD /unidades/
        │       ├── talhoes.py      # CRUD talhão + upload/preview/confirm de SHP + GeoJSON
        │       ├── solos.py        # leituras analíticas (fertilidade com classificação em SQL, nematologia, balanço, adubação)
        │       ├── etl.py          # dispara ETL (cria etl_jobs + Celery) e consulta status
        │       ├── mapas.py        # importação de limites de talhão (histórico, ativar limite)
        │       └── fly/            # módulo Locks Fly (outro banco)
        │           ├── service_orders.py  # ordens de serviço (lista paginada, detalhe, arquivos) — código "mais novo"
        │           ├── applications.py    # aplicações (detalhe, geometria)
        │           └── imports.py         # upload de pacotes de voo → MinIO → Celery
        ├── core/                   # infraestrutura transversal (equivale a core/ + db/ + deps/)
        │   ├── config.py           # Settings (pydantic-settings) lendo <raiz do repo>/.env
        │   ├── database.py         # engine, SessionLocal, Base(DeclarativeBase), get_db()
        │   ├── database_fly.py     # engine_fly, SessionLocalFly, Base_fly, get_db_fly()
        │   ├── dependencies.py     # validate_token (HTTPBearer + jwt.decode + SET app.current_tenant_id)
        │   ├── security.py         # bcrypt (passlib) + generate_jwt
        │   ├── celery_app.py       # Celery("agro_platform", broker/backend=redis) + beat_schedule
        │   ├── storage.py          # boto3 S3/MinIO: upload_file / download_file
        │   └── athena.py           # pyathena connect + query_athena(sql) -> DataFrame (FONTE do ETL)
        ├── models/                 # SQLAlchemy 2.0 (Mapped/mapped_column), um arquivo por tabela
        │   ├── __init__.py         # importa todos os models (para o Alembic enxergar)
        │   ├── tenant.py users.py unidade.py fazenda.py safra.py cultura.py periodo_safra.py talhao.py
        │   ├── analise_solo.py analise_nemat.py analise_balanco.py analise_adubacao.py
        │   ├── etl_jobs.py shp_import_job.py mapa.py (ImportacaoMapa, LimiteTalhao)
        │   └── fly/                # Base_fly: service_order, so_plot, application, flight, product, provider,
        │                           #           operator, vehicle, application_* (N:N), import_job
        ├── schemas/                # Pydantic v2: XxxCreate / XxxResponse / XxxUpdate
        │   ├── auth.py user.py tenant.py fazendas.py unidade.py safra.py cultura.py periodo_safra.py
        │   ├── talhao.py solos.py balanco.py adubacao.py etl.py
        │   ├── testeevogo.py       # !!! script de teste de WhatsApp com API key e telefone no código ([REDACTED]) — lixo no lugar errado
        │   └── fly/                # _camel.py (alias_generator camelCase) + application/flight/product/service_order
        ├── services/
        │   └── fly_import.py       # ÚNICO "service": espalha o pacote decodificado nas 8 tabelas do Fly
        ├── tasks/                  # Celery
        │   ├── etl_tasks.py        # 3.234 linhas: 2 queries Athena gigantes embutidas + 4 tasks
        │   ├── shp_tasks.py        # processar_shp (MinIO → geopandas → upsert talhão)
        │   └── fly_tasks.py        # processing_import_fly (advisory lock → subprocess bridge.py → importar_pacote)
        └── fly_decoder/            # decodificador de voo independente (stdlib), chamado via subprocess
            ├── agnav_decoder.py        # 4.154 linhas — formato binário AG-NAV (engenharia reversa)
            ├── formatos_universais.py  # 1.505 linhas — GPX/KML/KMZ/GeoJSON/SHP/CSV/NMEA → modelo canônico
            ├── bridge.py               # CLI: decodifica e imprime JSON {"ok":..., "missao":..., ...} no stdout
            ├── FORMATO_AGNAV.md        # documentação do formato
            └── GPS_MERCADO.md
```

Observações estruturais:
- **"alembic_fly" não tem relação com Fly.io.** É o Alembic do segundo banco de dados, do módulo *Locks Fly* (auditoria de aplicação aérea). Os dois bancos ficam no mesmo servidor Postgres, mesmo usuário, nomes diferentes (`db_name` × `fly_db_name`).
- Não existem pastas `repositories/`, `db/`, `deps/`, `tests/`, nem `Dockerfile`.

### Inventário de rotas reais (prefixo do router + caminho do endpoint)

O agregador aplica `prefix="/fazendas"` e o endpoint declara `@router.get("/fazendas/")` → **URL final duplicada**. O front já depende disso.

| Grupo | Rotas finais (`/api/v1` +) | Auth |
|---|---|---|
| Health | `GET /health` (fora do /api/v1) | não |
| Auth | `POST /auth/tenants`, `GET /auth/tenants/{slug}`, `POST /auth/auth` | **não** |
| Users | `POST /users/users` | **não** (cria usuário com qualquer `tenant_id` e `role`) |
| Fazendas | `POST /fazendas/fazendas`, `GET /fazendas/fazendas/`, `GET/PUT/DELETE /fazendas/fazendas/{id}` | sim |
| Safras | `POST /safras/safras`, `GET /safras/safras/?fazenda_id=`, `GET/PUT/DELETE /safras/safras/{id}` | sim |
| Culturas | `GET/POST /culturas/`, `GET/PUT/DELETE /culturas/{id}` | sim |
| Períodos | `GET/POST /periodos/periodos/`, `GET/PUT/DELETE /periodos/periodos/{id}` | sim |
| Unidades | `GET/POST /unidades/`, `GET/PUT/DELETE /unidades/{id}` | sim |
| Talhões | `POST /talhoes/talhoes`, `POST /talhoes/shp/upload`, `GET /talhoes/shp/status/{job}`, `GET /talhoes/shp/preview/{job}`, `POST /talhoes/shp/confirm/{job}`, `GET /talhoes/talhoes/geojson/{fazenda}`, `GET /talhoes/mapas`, `GET /talhoes/talhoes/{fazenda}[/{safra}]` | sim |
| Solos | `GET /solos/fertilidade/{fazenda}/{depth}`, `/solos/nematologia/{fazenda}`, `/solos/balanco/{fazenda}`, `/solos/adubacao/{fazenda}` | sim |
| ETL | `POST /etl/etl/sync`, `POST /etl/sync-balanco`, `POST /etl/sync-adubacao`, `GET /etl/etl/status/{job}` | sim |
| Mapas | `POST/GET /mapas/importacoes`, `GET /mapas/importacoes/{id}/limites`, `DELETE /mapas/importacoes/{id}`, `POST /mapas/limites/{id}/ativar` | sim |
| Fly | `POST/GET /fly/service-orders`, `GET /fly/service-orders/{id}`, `GET /fly/service-orders/{id}/files`, `POST /fly/applications`, `GET /fly/applications/{id}[/geometry]`, `GET /fly/imports/status`, `POST/GET /fly/imports`, `GET /fly/auth/me` | sim (exceto `/imports/status`) |

---

## 2. Stack e versões

### `backend/requirements.txt` (pinado)

| Pacote | Versão | Uso |
|---|---|---|
| fastapi | 0.115.0 | API |
| uvicorn | 0.30.6 | ASGI server |
| sqlalchemy | 2.0.35 | ORM/Core (modo **síncrono**) |
| alembic | 1.13.3 | migrações |
| psycopg2-binary | 2.9.9 | driver Postgres |
| pydantic | 2.9.2 | schemas |
| pydantic-settings | 2.5.2 | config |
| python-dotenv | 1.0.1 | .env |
| passlib[bcrypt] | 1.7.4 | hash de senha |
| bcrypt | 4.0.1 | (pin para compatibilidade com passlib) |
| python-jose[cryptography] | 3.3.0 | JWT |
| geopandas | 1.1.4 | leitura de shapefile (traz pandas) |
| celery[redis] | 5.6.3 | jobs |
| pyathena | 3.10.0 | fonte do ETL (AWS Athena) |

**Importados no código mas ausentes do requirements**: `boto3` (storage.py), `geoalchemy2` (models/migrações), `httpx` (services/fly_import.py), `requests` (schemas/testeevogo.py); `pandas` vem só transitivamente via geopandas. → O ambiente não é reprodutível a partir do arquivo.

### `docker-compose.yml` (só infraestrutura — a API e o worker NÃO estão no compose)

| Serviço | Imagem | Porta host | Notas |
|---|---|---|---|
| `db` (`agro_db`) | `postgis/postgis:16-3.4` | 5433→5432 | `POSTGRES_DB=agro_platform`, `POSTGRES_USER=agro_user`, `POSTGRES_PASSWORD=${DB_PASSWORD}`; volume `pgdata`. **Esse usuário é superusuário do cluster** (comportamento da imagem oficial). |
| `redis` (`agro_redis`) | `redis:7-alpine` | 6379 | broker + result backend do Celery |
| `minio` (`agro_minio`) | `minio/minio` (sem tag) | 9000/9001 | credenciais root **hard-coded no compose** → [REDACTED] |

Não há serviço de `celery worker`/`celery beat` nem `api`; eles rodam na máquina do desenvolvedor (Windows — ver caminho fixo em `fly_tasks.py`).

---

## 3. Camadas, convenções e fatia vertical

### 3.1 Organização das camadas (o que existe de fato)

| Camada "esperada" | Na referência | Comentário |
|---|---|---|
| Routers/endpoints | `app/api/v1/endpoints/<recurso>.py` com `router = APIRouter()`; agregados em `app/api/v1/router.py` | 1 arquivo por recurso; subpasta por módulo (`fly/`) |
| Schemas | `app/schemas/<recurso>.py` (Pydantic v2) | `XxxCreate`, `XxxUpdate`, `XxxResponse`; `model_config = {"from_attributes": True}`; aliases pt↔front (`Field(None, alias="municipio")` + `populate_by_name`) |
| Models | `app/models/<tabela>.py` (SQLAlchemy 2.0 tipado) | `Mapped[...]`/`mapped_column`, **sem `relationship()` em lugar nenhum** |
| Services | `app/services/fly_import.py` (único) | regra de negócio fica no endpoint ou dentro do SQL |
| Repositories | **não existe** | SQL cru com `text()` dentro do endpoint |
| core/config | `app/core/config.py` | `Settings(BaseSettings)` + propriedade `database_url` |
| db/session | `app/core/database.py` (+ `database_fly.py`) | `create_engine`, `sessionmaker(autocommit=False, autoflush=False)`, `get_db()` gerador |
| deps | `app/core/dependencies.py` | só `validate_token` |
| tasks | `app/tasks/*_tasks.py` | Celery |
| integrações | `app/core/storage.py` (S3), `app/core/athena.py` (fonte), `app/fly_decoder/` (parsers) | |

Os models são usados quase só para **INSERT via ORM** (`db.add(Fazenda(...))`) e para o Alembic autogenerate. **Toda leitura, UPDATE e DELETE é SQL cru** (`db.execute(text("SELECT * FROM fazendas WHERE id = :id"), {...})`) e o resultado é convertido com `row._asdict()` e remapeado à mão para o formato do front.

### 3.2 Convenções de nomes observadas

- **Idioma**: português no domínio (tabelas, colunas, funções de endpoint: `criar_fazenda`, `buscar_fazendas`, `atualizar_fazenda`, `deletar_fazenda`, `listar_unidades`), inglês no módulo Fly (tabelas `service_orders`, `applications`, colunas `name`, `code`, `status`) e mistura nas tasks (`processing_etl`, `processar_shp`).
- **Tabelas**: inconsistentes — plural (`tenants`, `users`, `fazendas`, `safras`, `etl_jobs`, `shp_import_jobs`) e singular (`talhao`, `cultura`, `unidade`, `periodo_safra`, `analise_solo`, `importacao_mapa`). O esquema-alvo em `docs/esquema` padroniza **singular, snake_case, português**.
- **Colunas padrão**: `id uuid` (PK, `default=uuid.uuid4` no ORM / `gen_random_uuid()` no SQL cru), `tenant_id uuid NOT NULL FK tenants(id) ON DELETE CASCADE`, `ativo boolean`, `criado_em timestamptz server_default now()`, `atualizado_em timestamptz onupdate now()` (tabelas de job).
- **Constraints**: `uq_<tabela>_<colunas>` com `tenant_id` primeiro (`uq_users_tenant_email`, `uq_talhao_tenant_fazenda_safra`, `uq_adubacao_chave`). Índices `idx_...` no banco principal e `ix_<tabela>_<cols>` no Fly.
- **Políticas RLS**: `tenant_isolation`, `tenant_insert`, `tenant_select`.
- **Status de job**: `pending | processing | done | error` (banco principal); `FILA | DECODIFICANDO | IMPORTANDO | CONCLUIDO | ERRO` (Fly). Mensagens humanas mapeadas no endpoint de status.
- **API camelCase** só no Fly: `app/schemas/fly/_camel.py`:

```python
def to_camel(campo: str) -> str:
    partes = campo.split('_')
    return partes[0] + ''.join(p.capitalize() for p in partes[1:])

CAMEL_CONFIG = {"alias_generator": to_camel, "populate_by_name": True, "from_attributes": True}
```

### 3.3 Fatia vertical 1 — CRUD de Fazenda (padrão dominante)

`router.py` → `endpoints/fazendas.py` → (sem service/repo) → SQL cru + `models/fazenda.py` → `schemas/fazendas.py`

```python
# app/api/v1/router.py
router.include_router(fazendas.router, prefix="/fazendas", tags=["Fazendas"])
```

```python
# app/api/v1/endpoints/fazendas.py  (trechos)
@router.post("/fazendas", response_model=FazendaResponse, status_code=201)
def criar_fazenda(payload: FazendaCreate, db: Session = Depends(get_db), sessao_atual = Depends(validate_token)):
    tenant_id = sessao_atual["tenant_id"]
    fazenda = Fazenda(tenant_id=tenant_id, nome=payload.nome, cidade=payload.cidade,
                      area_total_ha=payload.area_total_ha, unidade_id=payload.unidade_id)
    db.add(fazenda)
    db.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))   # repetido em TODO endpoint
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Fazenda Já Existe!")
    db.refresh(fazenda)
    d = fazenda.__dict__.copy()
    d["codigo"] = d["nome"]; d["municipio"] = d.pop("cidade"); d["area_ha"] = d.pop("area_total_ha")
    return d

@router.get("/fazendas/", response_model=list[FazendaResponse])
def buscar_fazendas(db: Session = Depends(get_db), sessao_atual = Depends(validate_token)):
    tenant_id = sessao_atual["tenant_id"]
    db.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))
    result = db.execute(text("SELECT * FROM fazendas")).fetchall()   # confia 100% no RLS aqui
    ...
```

```python
# app/models/fazenda.py
class Fazenda(Base):
    __tablename__ = "fazendas"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    unidade_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("unidade.id", ondelete="SET NULL"), nullable=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    ...
    ativo: Mapped[bool] = mapped_column(default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

```python
# app/schemas/fazendas.py
class FazendaCreate(BaseModel):
    unidade_id: uuid.UUID | None = None
    nome: str
    cidade: str | None = Field(None, alias="municipio")
    area_total_ha: float | None = Field(None, alias="area_ha")
    model_config = {"populate_by_name": True}
```

Observações: a dependência `validate_token` e o endpoint recebem **a mesma** `Session` (FastAPI faz cache de dependência por requisição), então o `SET` feito no dependency já valeria — o `SET` repetido no endpoint é redundante. A tradução de nomes (`cidade`→`municipio`) é feita duas vezes: alias no schema de entrada e `dict.pop` manual na saída.

### 3.4 Fatia vertical 2 — ETL disparado por endpoint (o mais próximo do que o novo projeto precisa)

`POST /etl/etl/sync` → cria `EtlJob(status="pending")` → `processing_etl.delay(job_id, tenant_id, tipo_origem, tipo_destino)` → task lê Athena → upsert em `analise_solo` → atualiza job.

```python
# endpoints/etl.py
job = EtlJob(tenant_id=uuid.UUID(tenant_id), fazenda_id=payload.fazenda_id, safra_id=payload.safra_id,
             tipo_origem=payload.tipo_origem, tipo_destino=payload.tipo_destino, status="pending")
db.add(job); db.commit(); db.refresh(job)
processing_etl.delay(str(job.id), str(tenant_id), payload.tipo_origem, payload.tipo_destino)
return EtlResponse(job_id=job.id, status=job.status, mensagem="ETL iniciado em background")
```

```python
# tasks/etl_tasks.py (resumo)
@celery_app.task(bind=True)
def processing_etl(self, job_id, tenant_id, tipo_origem, tipo_destino):
    engine = get_engine()                                  # create_engine() a cada execução
    with engine.connect() as conn:
        conn.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))
        conn.execute(text("UPDATE etl_jobs SET status = 'processing' where id = :id"), {"id": job_id}); conn.commit()
    try:
        df = query_athena("SELECT * FROM stg_fields_monitoring")   # ignora tipo_origem!
        with engine.connect() as conn:
            conn.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))
            for _, row in df.iterrows():
                talhao = conn.execute(text("""SELECT t.id ... JOIN fazendas f ... WHERE f.nome = :unidade
                                              AND t.nome = :talhao AND s.nome = :safra AND t.tenant_id = :tenant_id"""), ...).fetchone()
                if not talhao: continue                                    # casamento por NOME
                conn.execute(text("""INSERT INTO analise_solo (...) VALUES (...)
                    ON CONFLICT (tenant_id, fazenda_id, safra_id, talhao_id, element, depth)
                    DO UPDATE SET value = EXCLUDED.value"""), {...})
            conn.execute(text("UPDATE etl_jobs SET status = 'done', total_processado = :total WHERE id = :id"), ...)
            conn.commit()
    except Exception as e:
        with engine.connect() as conn:
            ...  UPDATE etl_jobs SET status = 'error', erro = :erro ...   # (sem commit nesta task → erro se perde)
```

---

## 4. Multi-tenancy e RLS (crítico)

### 4.1 Modelo de dados de tenancy

```
tenants (id, nome, slug UNIQUE, ativo, criado_em)
  ├── users      (tenant_id FK CASCADE, email, senha_hash, role default 'viewer', ativo)  UNIQUE(tenant_id, email)
  ├── unidade    (tenant_id FK, nome)                                                    UNIQUE(tenant_id, nome)
  ├── fazendas   (tenant_id FK, unidade_id FK unidade ON DELETE SET NULL — NULLABLE)
  ├── safras     (tenant_id FK, fazenda_id FK)                                           UNIQUE(fazenda_id, nome)
  ├── cultura / periodo_safra (tenant_id FK, safra_id, cultura_id)
  ├── talhao     (tenant_id, fazenda_id, safra_id, geom GEOMETRY 4326)                   UNIQUE(tenant_id, fazenda_id, safra_id, nome)
  ├── analise_solo / analise_nemat / analise_balanco / analise_adubacao (tenant_id, fazenda_id, ...)
  ├── etl_jobs / shp_import_jobs (tenant_id, fazenda_id?, safra_id?)
  └── importacao_mapa / limite_talhao  (tenant_id SEM FK e SEM RLS)

Banco Fly (separado): service_orders, so_plots, applications, flights, products, providers, operators,
vehicles, application_*, imports — todos com tenant_id NOT NULL mas SEM FK (não existe tabela tenants lá).
```

- **Um usuário pertence a exatamente um tenant** (`users.tenant_id`). Não existe tabela usuário↔fazenda nem usuário↔unidade no backend.
- **Unidade** é agrupador administrativo de fazendas (`fazendas.unidade_id`, opcional). Criado em 2026-09-06.
- Não há conceito de "fazenda permitida por usuário" no banco do backend; o front espera `fazendas_permitidas`/`unidades_permitidas` (vindos do servidor antigo do Fly, Node/SQLite, fora destes repos).

### 4.2 Qual configuração do Postgres é usada

GUC customizado **`app.current_tenant_id`** (texto contendo um UUID), lido nas políticas com:

```sql
current_setting('app.current_tenant_id', true)   -- missing_ok = true: retorna NULL se nunca foi definido
```

O guard `current_setting(...) != ''` existe porque, depois de um `RESET`/valor vazio, o cast `''::uuid` lançaria erro; com NULL a comparação resulta NULL → linha invisível.

### 4.3 Onde o GUC é definido

1. **Dependency** `app/core/dependencies.py`:

```python
bearer_scheme = HTTPBearer()

def validate_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
                   db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        content = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    tenant_id = content["tenant_id"]
    db.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))
    return content          # dict com sub, tenant_id, role, exp
```

2. **Em todo endpoint**, de novo, como primeira linha: `db.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))`. Isso é **necessário** nos endpoints do Fly porque eles usam outra sessão (`get_db_fly`), na qual o dependency não executou o `SET`.
3. **Em toda task Celery**, em cada `engine.connect()` (`SET` no início de cada bloco).
4. **Versão "corrigida" (só no Fly)** — `fly/service_orders.py`:

```python
def definir_tenant(db: Session, tenant_id: str) -> None:
    """`SET` não aceita parâmetro — por isso o código antigo montava a string com f-string.
    `set_config` é a mesma coisa em forma de função e aceita parâmetro."""
    db.execute(text("SELECT set_config('app.current_tenant_id', :tenant, false)"), {"tenant": tenant_id})
```

Pontos técnicos importantes:
- `SET` e `set_config(..., false)` são **de sessão (conexão)**, não de transação. Como o engine usa *pool*, o valor **sobrevive na conexão devolvida ao pool** e é herdado pela próxima requisição que pegar a mesma conexão e esquecer de definir o tenant.
- Depois de `db.commit()`, a `Session` do SQLAlchemy 2.0 devolve a conexão ao pool; a próxima instrução (ex.: `db.refresh`, o `SELECT` pós-`UPDATE`) pode pegar **outra conexão**, com o tenant de outra requisição. Nunca é usado `SET LOCAL` / `set_config(..., true)` nem evento `after_begin`.
- O `SET` com f-string é injetável em tese (o valor vem de um JWT assinado, o que limita o risco, mas o padrão é ruim e foi reconhecido no próprio código).

### 4.4 Políticas — inventário completo

| Migração | Tabelas | ENABLE | FORCE | Políticas |
|---|---|---|---|---|
| `create_rls.py` (rev `rls_foundation`) | tenants, users, fazendas, safras | sim | sim | `tenant_isolation` **sem `FOR`** (vale para ALL) `USING (tenant_id = current_setting(...)::uuid)`; em `tenants`: `USING (id = ...)` |
| `2932b16c983a_fix_rls_tenants` | tenants | — | — | remove `tenant_isolation`; cria `tenant_insert FOR INSERT WITH CHECK (true)` e `tenant_select FOR SELECT USING (current_setting(...) != '' AND id = ...)` |
| `ee486d967a4c_rls_solos` | talhao, analise_solo, analise_nemat, shp_import_jobs | sim | sim | `tenant_isolation FOR SELECT USING (... != '' AND tenant_id = ...)` + `tenant_insert FOR INSERT WITH CHECK (true)` |
| `bdda07450df6_rls_etl_jobs` | etl_jobs | sim | sim | idem (SELECT + INSERT true) |
| `3c9d09d7f43d_rls_cultura_periodo_safra` | cultura, periodo_safra | sim | sim | idem |
| `11e66c29e057_rls_unidade` | unidade | sim | sim | idem |
| `2654eb1ed265_rls_analise_balanco` | analise_balanco | sim | sim | idem |
| `d7f8ed3c0cc0_rls_analise_adubacao` | analise_adubacao | sim | sim | idem |
| Fly: `432e8dccde60`, `189d1be0558d`, `c1e45967d382`, `5b29201ee5ba`, `4eb8e5d49d88`, `6b9b39433e24`, `968e1c8c80db`, `45dca3715a0a`, `2214a881089a` | service_orders, so_plots, applications, flights, application_operators, application_vehicles, products, application_products, providers/operators/vehicles/imports | sim | sim | idem |
| — | importacao_mapa, limite_talhao | **não** | — | **nenhuma** |

Padrão de migração: **uma migração `create_<tabela>` (autogerada) seguida de uma `rls_<tabela>` manual** com `op.execute(...)`, downgrade com `DROP POLICY IF EXISTS` + `DISABLE ROW LEVEL SECURITY`.

### 4.5 SQL de uma migração de política representativa

`backend/alembic/versions/ee486d967a4c_rls_solos.py` (padrão "B", o mais usado):

```python
def upgrade() -> None:
    for tabela in ['talhao', 'analise_solo', 'analise_nemat', 'shp_import_jobs']:
        op.execute(f"ALTER TABLE {tabela} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {tabela} FORCE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY tenant_isolation ON {tabela}
            FOR SELECT
            USING (
                current_setting('app.current_tenant_id', true) != ''
                AND tenant_id = current_setting('app.current_tenant_id', true)::uuid
            )
        """)
        op.execute(f"""
            CREATE POLICY tenant_insert ON {tabela}
            FOR INSERT WITH CHECK (true)
        """)

def downgrade() -> None:
    for tabela in ['talhao', 'analise_solo', 'analise_nemat', 'shp_import_jobs']:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {tabela}")
        op.execute(f"DROP POLICY IF EXISTS tenant_insert ON {tabela}")
        op.execute(f"ALTER TABLE {tabela} DISABLE ROW LEVEL SECURITY")
```

Padrão "A" (`create_rls.py`, primeiras tabelas):

```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON users
  USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);   -- sem FOR → ALL; USING vira WITH CHECK
```

### 4.6 Papéis do banco, FORCE e bypass

- **Não há `CREATE ROLE`, `GRANT`, `ALTER ROLE ... NOBYPASSRLS`** em nenhuma migração. Um único usuário (`settings.db_user`) roda migrações, API e workers, nos dois bancos.
- `FORCE ROW LEVEL SECURITY` faz o **dono** da tabela também obedecer o RLS — mas **superusuários e papéis com `BYPASSRLS` sempre ignoram RLS**, com ou sem FORCE. O `POSTGRES_USER` da imagem `postgis/postgis` é superusuário → **em dev, o RLS está desligado de fato**.
- Evidências de que o sistema *depende* do bypass para funcionar:
  - **Login** faz `SELECT * FROM users WHERE email = :email` **sem** tenant definido (com RLS ativo, retornaria zero linhas).
  - `criar_etl_job_agendado` faz `SELECT id FROM tenants WHERE ativo = true` sem tenant.
  - Todos os `UPDATE ... SET status = ...` em `etl_jobs`, `shp_import_jobs`, `talhao`, `fazendas`, `limite_talhao` — as tabelas do padrão B **não têm política de UPDATE nem DELETE**; para um papel sem bypass, essas instruções afetariam 0 linhas silenciosamente.
- Por isso o código também filtra manualmente: `WHERE t.tenant_id = :tenant_id`, `WHERE so.tenant_id = :tenant_id` etc. (defesa em profundidade que, na prática, é a **única** defesa).
- `INSERT WITH CHECK (true)` permite a um tenant inserir linha com `tenant_id` de outro.

### 4.7 Mapeamento usuário → tenant → unidade → fazenda

| Nível | Onde está | Aplicado por |
|---|---|---|
| usuário → tenant | `users.tenant_id` → JWT `tenant_id` | RLS (teórico) + `WHERE tenant_id` manual |
| tenant → unidade | `unidade.tenant_id` | idem |
| unidade → fazendas | `fazendas.unidade_id` (nullable) | **somente o frontend** (`EscopoUnidade` filtra listas no navegador) |
| usuário → fazendas permitidas | **não existe no backend**; o front tem `Usuario.fazendas_permitidas` vindo do servidor legado do Fly | ninguém no servidor |
| papel (`role`) | `users.role` (`viewer` default, `admin`) → JWT `role` | **ninguém no servidor**; o front decide módulos visíveis via `PapelAcesso.modulos_permitidos` guardado em mock/localStorage |

O esquema-alvo `docs/esquema/01-nucleo.sql` (no repo do front) propõe a correção: `organizacao` (raiz do RLS), `usuario(organizacao_id, papel_id, unidades_permitidas uuid[] cache)`, `usuario_fazenda(usuario_id, fazenda_id)` ("sem nenhuma linha = todas da organização"), `papel_acesso(modulos_permitidos modulo_key[], pode_editar_cadastros)`, e registra explicitamente: *"Row Level Security não está escrita... dependem de como a aplicação vai propagar a identidade (`SET LOCAL app.organizacao_id`)"*.

### 4.8 Bypass de superusuário/admin

Não existe bypass explícito (nenhuma política para admin, nenhum papel de serviço). O único "bypass" é o implícito do superusuário do Postgres. O `role == 'admin'` do JWT não tem efeito no servidor (o `/fly/auth/me` devolve `permissions: []` com comentário "não temos sistema de permissão real ainda").

### 4.9 Recomendação para o novo projeto (RLS por usuário que funcione)

Manter a *forma* (GUC + `current_setting(..., true)` + migração `rls_*` dedicada + `ENABLE`/`FORCE`), corrigindo o conteúdo:

```sql
-- 1) Papéis: dono (migrações) ≠ aplicação (API/worker), aplicação SEM superuser/BYPASSRLS
CREATE ROLE app_owner NOLOGIN;                       -- dono das tabelas (Alembic roda com SET ROLE app_owner ou login próprio)
CREATE ROLE app_user  LOGIN NOSUPERUSER NOBYPASSRLS; -- usado pela API e pelos workers
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;

-- 2) Funções auxiliares (STABLE, leem o contexto da transação)
CREATE SCHEMA IF NOT EXISTS app;
CREATE FUNCTION app.usuario_id() RETURNS uuid LANGUAGE sql STABLE AS
$$ SELECT nullif(current_setting('app.usuario_id', true), '')::uuid $$;
CREATE FUNCTION app.tenant_id() RETURNS uuid LANGUAGE sql STABLE AS
$$ SELECT nullif(current_setting('app.tenant_id', true), '')::uuid $$;
CREATE FUNCTION app.eh_admin() RETURNS boolean LANGUAGE sql STABLE AS
$$ SELECT coalesce(current_setting('app.eh_admin', true), '') = 'true' $$;

-- 3) Tabela de acesso usuário ↔ fazenda (o "por usuário")
CREATE TABLE usuario_fazenda (
  usuario_id uuid NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
  fazenda_id uuid NOT NULL REFERENCES fazenda(id) ON DELETE CASCADE,
  PRIMARY KEY (usuario_id, fazenda_id)
);

-- 4) Política FOR ALL com USING + WITH CHECK (cobre SELECT/INSERT/UPDATE/DELETE)
ALTER TABLE pesagem ENABLE ROW LEVEL SECURITY;
ALTER TABLE pesagem FORCE ROW LEVEL SECURITY;
CREATE POLICY pesagem_acesso ON pesagem
  FOR ALL
  USING (
    tenant_id = app.tenant_id()
    AND (app.eh_admin() OR fazenda_id IN (SELECT uf.fazenda_id FROM usuario_fazenda uf
                                          WHERE uf.usuario_id = app.usuario_id()))
  )
  WITH CHECK (
    tenant_id = app.tenant_id()
    AND (app.eh_admin() OR fazenda_id IN (SELECT uf.fazenda_id FROM usuario_fazenda uf
                                          WHERE uf.usuario_id = app.usuario_id()))
  );
```

```python
# Python: contexto POR TRANSAÇÃO (nunca SET de sessão), aplicado num único lugar
from sqlalchemy import event, text

@event.listens_for(SessionLocal, "after_begin")
def _aplicar_contexto_rls(session, transaction, connection):
    ctx = session.info.get("rls")            # preenchido pelo dependency get_db_autenticado()
    if ctx:
        connection.execute(text("SELECT set_config('app.tenant_id', :t, true), "
                                "set_config('app.usuario_id', :u, true), "
                                "set_config('app.eh_admin', :a, true)"),
                           {"t": ctx.tenant_id, "u": ctx.usuario_id, "a": "true" if ctx.eh_admin else "false"})
```

- Login e jobs de sistema que precisam ver todos os tenants: usar uma função `SECURITY DEFINER` específica (ex.: `app.autenticar(email)`) ou um papel de serviço separado — nunca "rodar tudo como superusuário".
- Workers ETL: o job carrega `tenant_id` (+ `usuario_id` do disparador ou um usuário técnico por tenant) e abre transação com o mesmo listener.
- Teste automatizado obrigatório: conectar como `app_user`, setar tenant/usuário A e provar que linhas de B são invisíveis e não-graváveis.

---

## 5. Autenticação

| Item | Implementação |
|---|---|
| Endpoint de login | `POST /api/v1/auth/auth` body `{"email", "senha"}` → `{"token", "tipo": "bearer"}` |
| Busca do usuário | `SELECT * FROM users where email = :email` (sem tenant, sem `ativo = true`; e-mail igual em dois tenants → pega o primeiro) |
| Mensagens | "Cadastro não encontrado" (401) × "Credenciais inválidas" (401) → permite enumerar e-mails |
| Hash | `passlib CryptContext(schemes=["bcrypt"])`; trunca a senha em 72 bytes (`senha[:72]`); funções `genetare_hash` (sic) e `verify_hash` |
| JWT | `python-jose`, payload `{"sub": user_id, "tenant_id", "role", "exp": utcnow + ACCESS_TOKEN_EXPIRE_MINUTES}`; **encode com `"HS256"` fixo**, decode com `settings.algorithm` |
| Transporte | `HTTPBearer` (header `Authorization: Bearer <token>`); token guardado no `localStorage` (`agro_token`) pelo front |
| Refresh / logout server-side / revogação | não existem |
| `/auth/me` | **não existe no banco principal** (o front chama `GET /api/v1/auth/me` e espera `{token, user}` no login — contrato divergente do backend clonado). Existe só `GET /fly/auth/me`, que devolve usuário fictício (`"Usuário de desenvolvimento"`) |
| Cadastro | `POST /auth/tenants` e `POST /users/users` **sem autenticação**; o corpo do usuário aceita `tenant_id` e `role` livres |
| Modelo de usuário | `users(id, tenant_id, nome, email, senha_hash, role='viewer', ativo, criado_em)`, `UNIQUE(tenant_id, email)` |
| Permissões | nenhuma verificação de `role` no servidor; autorização apenas visual no front (`PapelAcesso.modulos_permitidos`, `pode_editar_cadastros`) |
| Token de serviço | `services/fly_import.py` chama a própria API via HTTP com `settings.agroapi_dev_token` (token fixo de desenvolvimento) — [REDACTED] |

---

## 6. ETL e jobs em background

### 6.1 Celery

```python
# app/core/celery_app.py
celery_app = Celery("agro_platform", broker=settings.redis_url, backend=settings.redis_url,
                    include=["app.tasks.shp_tasks", "app.tasks.etl_tasks", "app.tasks.fly_tasks"])
celery_app.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"],
    timezone="America/Cuiaba", enable_utc=True,
    beat_schedule={
        "etl-solo-diario":  {"task": "app.tasks.etl_tasks.criar_etl_job_agendado",
                             "schedule": datetime.timedelta(minutes=10),
                             "args": ["stg_fields_monitoring", "analise_solo"]},
        "etl-nemat-diario": {"task": "app.tasks.etl_tasks.criar_etl_job_agendado",
                             "schedule": datetime.timedelta(minutes=10),
                             "args": ["stg_fields_monitoring_nemat", "analise_nemat"]},
    })
```

- **Agendamento com fan-out por tenant**: `criar_etl_job_agendado(tipo_origem, tipo_destino)` lista `tenants WHERE ativo`, insere um `etl_jobs` por tenant e chama `processing_etl.delay(job_id, tenant_id, ...)`. (Nome "diário", periodicidade 10 min.)
- Sem `autoretry_for`, `max_retries`, `acks_late`, `time_limit`, filas separadas ou idempotência por chave de job. `bind=True` declarado e não usado.

### 6.2 Tabelas de job

| Tabela | Colunas-chave | Status |
|---|---|---|
| `etl_jobs` | `tenant_id`, `fazenda_id?`, `safra_id?`, `tipo_origem` (ex.: `athena_balanco_nutricional`), `tipo_destino` (ex.: `analise_balanco`), `status`, `total_processado`, `erro varchar(500)`, `criado_em`, `atualizado_em` | `pending → processing → done/error` |
| `shp_import_jobs` | `tenant_id`, `fazenda_id`, `safra_id`, `status`, `shp_arquivo_s3` (chave no MinIO), `coluna_nome_talhao`, `coluna_area_ha`, `erro`, timestamps; `UNIQUE(tenant, fazenda, safra, arquivo)` | idem |
| `imports` (Fly) | `tenant_id`, `user_id?`, `filename`, `stored` (chave MinIO), `size`, `status`, `format`, `message`, `detail` (JSON texto: missão, resumo, alertas, notas, métricas, `combinado_com`), `service_order_id?`, `applications`, `cell_m`, `duration_ms`, `external_ref`, `mission_context`, `criado_em`, `finished_at` | `FILA → DECODIFICANDO → IMPORTANDO → CONCLUIDO/ERRO` |

Endpoint de status (padrão reaproveitável):

```python
mensagens = {"pending": "Aguardando processamento", "processing": "Processando...",
             "done": "Processamento concluído", "error": "Erro no processamento"}
return EtlStatusResponse(job_id=result.id, status=result.status,
                         mensagem=mensagens.get(result.status, "Status desconhecido"),
                         total_processado=result.total_processado, erro=result.erro)
```

### 6.3 Fontes e "adaptadores"

| Fonte | Onde | Forma |
|---|---|---|
| AWS Athena (datalake) | `core/athena.py` + `QUERY_BALANCO` / `QUERY_ADUBACAO` (strings SQL de ~1.700 e ~1.200 linhas embutidas em `etl_tasks.py`) | `query_athena(sql) -> pandas.DataFrame`; a task itera `df.iterrows()` |
| Shapefile (upload) | `endpoints/talhoes.py` + `tasks/shp_tasks.py` | zip no MinIO → geopandas → reprojeção EPSG:4326 → upsert `talhao` |
| Pacotes de voo (upload) | `endpoints/fly/imports.py` + `tasks/fly_tasks.py` + `fly_decoder/` + `services/fly_import.py` | subprocess `bridge.py` → JSON → service grava 8 tabelas |

Não há classe/protocolo de adaptador. O "strategy" é **funcional** dentro do decoder:

```python
# fly_decoder/formatos_universais.py
def identificar(caminho): ...            # extensão + sniff do conteúdo → "gpx"|"kml"|"kmz"|"geojson"|"shp"|"csv"|"nmea"|None
def decodificar_arquivo(caminho, cell_m=2.0, tz_offset_h=None, ...):
    tipo = identificar(caminho)
    if tipo is None: ... m["avisos"].append("Formato ... nao reconhecido."); return m
    try:
        if tipo == "shp": colheita = parse_shp(caminho)
        elif tipo == "kmz": colheita = parse_kmz(caminho)
        else:
            dados = open(caminho, "rb").read()
            colheita = {"gpx": parse_gpx, "kml": parse_kml, "geojson": parse_geojson,
                        "nmea": parse_nmea}.get(tipo, lambda d: parse_csv(d, nome))(dados)   # (equivalente)
    except Exception as exc:
        colheita = _colheita(); colheita["avisos"].append(f"Falha lendo {nome}: {exc}")
    return montar_missao(colheita, ...)   # modelo canônico único
```

E o **mapeamento automático de cabeçalhos** (ótima base para o adaptador de Excel):

```python
_ALIASES = {
    "lat":  ("lat", "latitude", "latdd", "y"),
    "lon":  ("lon", "long", "longitude", "lng", "x"),
    "hora": ("time", "hora", "horario", "timestamp", "datetime", ...),
    "taxa": ("rate", "taxa", "dose", "apprateappliedlha", ...),   # comentário explica por que a coluna "planejada" NÃO entra
    ...
}
def _mapear_colunas(nomes):
    # 1ª passada: igualdade após normalizar (minúsculas, sem acento/pontuação);
    # 2ª passada: prefixo ("velocidade (km/h)" -> "velocidadekmh")
```

Princípio declarado e seguido: *"Quando uma informação não existe no arquivo, a métrica fica vazia e um aviso explícito é registrado — nunca se inventa dado."*

### 6.4 Upload de arquivo (fluxo em 4 passos — modelo para o Excel)

1. `POST /talhoes/shp/upload` (multipart: `fazenda_id`, `safra_id`, `arquivo`) → valida fazenda/safra no tenant → grava no MinIO em `"{tenant_id}/fazendas/{fazenda_id}/safras/{safra_id}/{arquivo.filename}"` → cria `shp_import_jobs(status="pending")` (task **não** é disparada aqui).
2. `GET /talhoes/shp/preview/{job_id}` → baixa o zip, lê com geopandas, devolve `{"colunas": [...]}`.
3. `POST /talhoes/shp/confirm/{job_id}` body `{coluna_nome_talhao, coluna_area_ha?}` → grava o mapeamento no job, `status='pending'` → `processar_shp.delay(job_id, tenant_id, coluna_nome, coluna_area)`.
4. `GET /talhoes/shp/status/{job_id}` → polling.

No Fly: `POST /fly/imports` aceita **vários arquivos**, valida extensão contra `EXTENSOES_VALIDAS`, grava inválidos já com `status='ERRO'` e mensagem, envia válidos para `fly/imports/{tenant_id}/{import_id}-{filename}`, faz um único `commit` e só depois dispara `processing_import_fly.delay()` para cada um.

### 6.5 Boas práticas presentes na importação do Fly (copiar)

- **Identidade de reimportação** (`external_ref`): reimportar a mesma OS **substitui** filhos (DELETE + INSERT) em vez de duplicar; a chave nunca é um campo editável pelo usuário.
- **Trava por entidade**: `SELECT pg_advisory_xact_lock(hashtext('fly-import:{tenant}:{ref}'))` dentro de `engine.begin()` → dois uploads da mesma OS não se atropelam; a trava solta sozinha no fim/erro.
- **Deduplicação por conteúdo**: `hashlib.sha256(bytes)` para ignorar o mesmo arquivo enviado duas vezes.
- **Transação única** para gravar o resultado (`importar_pacote(conn, ...)` + `commit`); falha → nada gravado; o status `ERRO` é gravado numa **conexão nova** no `except`.
- **Relatório estruturado** no job (`detail` JSON com `alertas[{nivel,titulo,detalhe}]`, `notas`, `resumo`) — muito melhor que `erro varchar(500)`.
- **Valores derivados persistidos** na importação (`service_orders.acerto/uniformidade/nao_aplicado/plots_area_ha` + `indices_fonte`) para listas e dashboards não recalcularem JSON a cada leitura; migração de *backfill* acompanha a coluna nova (`84a0e8283a2b`), usando `pg_input_is_valid` para não abortar.
- **"Soft errors"** no ETL do Athena: linhas sem fazenda correspondente são puladas e listadas (`erro = "Fazendas sem match: [...]"`) mesmo com `status='done'`.

### 6.6 Problemas a não repetir

- `processing_etl` ignora `tipo_origem` (sempre lê `stg_fields_monitoring`) → o agendamento de "nemat" grava em `analise_solo`.
- `except` de `processing_etl` sem `commit` → status de erro nunca persiste.
- `create_engine()` a cada execução de task; inserção linha a linha com `iterrows()` + um `SELECT` por linha para casar talhão por **nome**.
- Casamento de entidades por nome cru (`f.nome = :unidade`), sem tabela de-para.
- `subprocess.run(..., cwd="C:\\Workspace\\agro_platform\\backend")` fixo; o service chama a própria API por HTTP em `http://localhost:8000` com token de dev.
- Arquivos temporários com `tempfile.mkdtemp()` nunca removidos em `shp_tasks`/`talhoes.py`.

---

## 7. Alembic

- **Dois ambientes**: `alembic.ini` (`script_location = alembic`, banco principal) e `alembic_fly.ini` (`script_location = alembic_fly`, banco do módulo Fly). Uso: `alembic -c alembic_fly.ini upgrade head`. **Não é Fly.io.**
- `sqlalchemy.url =` vazio no `.ini`; `alembic/env.py` injeta `settings.database_url` (bom: credencial fica só no `.env`). `alembic_fly/env.py` usa `engine_fly` diretamente (online) e lê `sqlalchemy.url` (vazio) no modo offline — offline do Fly não funciona.
- `env.py` principal: `sys.path.insert` + `import app.models` (para popular `Base.metadata`) + filtro:

```python
def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and reflected and compare_to is None:   # tabela do banco sem model (ex.: spatial_ref_sys do PostGIS)
        return False
    return True
```

- Nomes de arquivo: `<rev>_<verbo>_<objeto>.py` em snake_case (`create_fazendas`, `rls_unidade`, `alter_talhao_geom_to_geometry`, `add_fk_fazendas_unidade`, `indices_de_consulta_fly`). Exceção: `create_rls.py` com revisão textual `'rls_foundation'`.
- Convenção: `create_<tabela>` autogerada → `rls_<tabela>` manual logo em seguida; índices em migração própria; dados derivados com *backfill* SQL na mesma migração da coluna.
- Migração de índices declarativa e comentada (copiar):

```python
INDICES = [
    # GET /fly/service-orders: filtra por tenant e ordena por criado_em
    ('ix_service_orders_tenant_criado_em', 'service_orders', ['tenant_id', 'criado_em']),
    # toda FK sem índice obriga varredura da filha quando o pai é apagado
    ('ix_flights_application_id', 'flights', ['application_id']),
    ...
]
def upgrade():   [op.create_index(n, t, c) for n, t, c in INDICES]
def downgrade(): [op.drop_index(n, table_name=t) for n, t, _ in reversed(INDICES)]
```

- Problemas: o autogenerate de `a51ce0daf45e_create_cultura` **removeu índices e alterou colunas não relacionadas** (drift entre models e banco aceito sem revisão); `e4a3c7b3db2e_create_periodo_safra` é uma migração vazia duplicada; enum `formato_arquivo` criado com `create_type=False` + `checkfirst`.
- Cadeia (banco principal): `tenants → users → fazendas → safras → rls_foundation → fix_rls_tenants → talhoes → analise_solo → analise_nemat → shp_import_jobs → rls_solos → alter geom → fix constraint → coluna_nome shp → etl_jobs → rls_etl_jobs → etl optional → índices → value nullable → talhoes.codigo → cultura → periodo_safra(vazia) → periodo_safra → rls_cultura_periodo → unidade_id em fazendas → unidade → rls_unidade → fk fazendas→unidade → analise_balanco → rls_balanco → analise_adubacao → rls_adubacao → chave adubação → importacao_mapa/limite_talhao`.

---

## 8. Config, logging, testes, Docker/deploy

### 8.1 Config

`app/core/config.py` (pydantic-settings), `.env` na **raiz do repositório** (`ROOT_DIR = parents[3]` de `config.py`), compartilhado com o docker-compose (`${DB_PASSWORD}`). Todos os campos obrigatórios, sem defaults, sem `.env.example`:

```
DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, FLY_DB_NAME,
SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
REDIS_URL,
AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_BUCKET_NAME, AWS_ENDPOINT_URL,   (MinIO)
ATHENA_ACCESS_KEY_ID, ATHENA_SECRET_ACCESS_KEY, ATHENA_REGION, ATHENA_DATABASE, ATHENA_S3_OUTPUT,
AGROAPI_DEV_TOKEN
```

Valores: [REDACTED] (não estão no repo; apenas os nomes).

```python
@property
def database_url(self) -> str:
    return f"postgresql+psycopg2://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
```

### 8.2 Logging
Nenhum. `print()` em endpoints e tasks (14 ocorrências fora do decoder), nenhum `logging.getLogger`, nenhum middleware de request-id, nenhuma métrica.

### 8.3 Testes
Nenhum teste automatizado no backend (sem pytest, sem pasta `tests/`). Só scripts manuais `teste_celery.py` (quebrado) e `teste_shp.py` (caminho local + UUIDs fixos).

### 8.4 Docker/deploy
- Sem `Dockerfile` da API/worker, sem compose de app, sem CI, sem config de servidor. Sem `CORSMiddleware` (o front contorna com o proxy do Vite).
- Execução implícita: `uvicorn app.main:app` (porta 8000), `celery -A app.core.celery_app worker` / `beat` na máquina local.
- `.idea/` versionado (PyCharm, `agro_platform.iml`).

### 8.5 Itens sensíveis encontrados (todos [REDACTED] aqui)
- `docker-compose.yml`: usuário/senha root do MinIO em texto puro.
- `backend/app/schemas/testeevogo.py`: chave de API de um gateway WhatsApp (Evolution GO) e um número de telefone, em texto puro, dentro da pasta de schemas.
- `teste_shp.py`: caminho de usuário Windows e UUIDs de tenant/fazenda/safra reais.

---

# PARTE B — FRONTEND (`locks_agtech_frontend`)

## 9. Árvore de pastas (sem `node_modules` e sem detalhar binários)

```
locks_agtech_frontend/
├── index.html                    # lang pt-BR, Google Fonts (Figtree; Archivo + IBM Plex Mono do Fly), <title>Acesso | LOCKS AgTech Lab
├── package.json                  # scripts: dev | build (tsc -b && vite build) | lint (oxlint) | test (vitest run) | preview
├── vite.config.ts                # porta 5190, host:true (LAN), proxies /api, /fly-api, /soil-api
├── vitest.config.ts              # jsdom, include src/**/*.test.{ts,tsx}
├── tsconfig.json / tsconfig.app.json / tsconfig.node.json   # project references, bundler mode, noUnused*
├── .oxlintrc.json                # plugins react/typescript/oxc; rules-of-hooks = error
├── .env.example                  # VITE_LOCKS_TRACKER_WS_URL, VITE_DEV_TOKEN (vazios)
├── README.md                     # template do Vite (sem documentação do projeto)
├── .claude/                      # comandos /opsx:* e skills openspec-* (fluxo de mudanças guiado por IA); launch.json (npm run dev :5190)
├── .superpowers/                 # artefatos de revisão (diff + relatório)
├── openspec/                     # "spec-driven": config.yaml (pt-BR), changes/<mudanca>/{proposal,design,tasks}.md + specs/<cap>/spec.md
├── docs/
│   ├── esquema/                  # ESQUEMA-ALVO: 01-nucleo.sql … 05-campo.sql (74 tabelas), schema.py (SQLAlchemy), schema.ts, README
│   └── superpowers/{specs,plans,notas,fixtures}/  # design docs e planos datados "AAAA-MM-DD-tema-design.md"
├── public/                       # favicon.svg, fly-brand/, fly-sim/plane.png
├── scripts/                      # subir-tudo.ps1/.bat (sobe Fly :4000, Soil :8000, front :5190), parar-tudo, gerar-fixture-shapefile.mjs
└── src/
    ├── main.tsx                  # createRoot + StrictMode; importa index.css, responsivo.css, movimento.css
    ├── App.tsx                   # AuthProvider > BrowserRouter > EscopoUnidadeProvider > Routes (todas as rotas declaradas aqui)
    ├── index.css                 # TOKENS de design (:root) — cores da marca, tipografia, raios, sombras, movimento
    ├── vite-env.d.ts             # tipagem de import.meta.env
    ├── assets/                   # logos e ícones PNG/WebP por módulo
    ├── pages/                    # telas fora dos módulos: LoginPage, HubPage (+ hubClima.ts) com CSS próprio
    ├── core/                     # TUDO que é transversal
    │   ├── moduleRegistry.ts     # MODULE_REGISTRY (um card no Hub por linha) + moduloDaRota()
    │   ├── types.ts              # tipos de domínio compartilhados (Fazenda, Talhao, Safra, Unidade, Usuario, PapelAcesso…)
    │   ├── uuid.ts               # novoUuid() seguro em contexto não-HTTPS
    │   ├── api/
    │   │   ├── sessao.ts         # ÚNICA fonte do token (localStorage 'agro_token'), evento 'locks:sessao-expirada'
    │   │   ├── agroApi.ts        # cliente fetch do backend da plataforma (/api/v1), AgroApiError, 401 → sessaoExpirou()
    │   │   ├── flyApi.ts         # cliente do Fly: roteia por lista de caminhos para /api/v1/fly (novo) ou /fly-api (legado)
    │   │   ├── plataformaApi.ts  # "camada unificada" de Cadastros: implementa CrudApi escolhendo a fonte por coleção
    │   │   ├── mapasApi.ts, cercasPlataformaApi.ts
    │   │   └── mockDb.ts         # banco provisório em localStorage (papéis de acesso etc.)
    │   ├── auth/                 # AuthProvider.tsx, authContextObject.ts (só o createContext), useAuth.ts, RequireAuth.tsx
    │   ├── escopo/               # EscopoUnidade.tsx (filtro global), useFazendaEscolhidaDaUnidade.ts (+ testes)
    │   ├── geo/                  # parseKml, parseShp, normalize, matching (casar polígono↔talhão), zoomNativoEsri
    │   ├── relatorio/            # relatorio.ts (documento de impressão em iframe), planilha.ts (ExcelJS com marca)
    │   └── ui/                   # EntityCrudPage (+css, types), ShellControles (rail, busca global ⌘K, seletor de unidade),
    │                             # BarraUnidade (rodapé), SeletorModulo, Icone (SVG inline), TransicaoDeTela,
    │                             # hooks useMediaQuery/useFechamentoAnimado/useRecuoDoRail, ModuleShell.css, movimento.css, responsivo.css
    └── modules/                  # um diretório por módulo de negócio (Hub mostra um card por módulo)
        ├── cadastros/            # CadastrosModule.tsx (shell + Outlet), entities.ts (EntityConfig de cada cadastro),
        │   ├── pages/entityPages.tsx   # <EntityCrudPage config={...} api={plataformaApi}/> por entidade
        │   └── mapas/            # wizard de importação de limites: Upload → Mapa/atributos → Mapear colunas → Vínculo → Revisão
        ├── locksSoil/            # LocksSoilModule.tsx (QueryClientProvider + .soil-app + Outlet), SoilShell.tsx, soilApi.ts, soilTipos.ts,
        │   ├── hooks/            # useXxxDaUnidade (useQueries por fazenda) + mesclarPorFazenda
        │   ├── componentes/      # primitives (Banner, Loading, Empty…), FilterPills/DepthToggle, AvisoDadosParciais
        │   ├── mapas/            # SoilMapa (Leaflet), basemaps, controles
        │   └── pages/            # Inicio, HistoricoFertilidade, MapasFertilidade, Adubacao, Balanco, Evolucao, Coletas, …
        ├── locksFly/             # LocksFlyModule (Provider + guarda), FlyShell, FlyContexto, flyHooks (useFetch), flyFormato,
        │   │                     # FlyComponentes, FlyGeoMap (MapLibre), FlyFlightSim
        │   └── pages/            # PainelPage (dashboard Recharts), OrdensServico, OrdemDetalhe, AplicacaoDetalhe, Importacao, …
        ├── locksCampo/           # LocksCampoModule, CampoShell, CampoContexto, campoApi, campoLogica, ndvi*, pages/
        └── locksTracker/         # LocksTrackerModule (vários Providers), api/ (trackerSocket WebSocket + REST),
            ├── logic/            # funções PURAS (kpis, viagens, severidade, sobreposições…) cada uma com .test.ts
            └── pages/            # Dashboard (Recharts), MapaAoVivo, Historico, Reproducao, Ranking, Cercas, …
```

Tamanho: ~48,7 mil linhas TS/TSX (sem testes), **84 arquivos de teste** colocados ao lado do código, ~11,5 mil linhas de CSS (`tracker-theme.css` sozinho tem 3.951).

---

## 10. Stack e versões (`package.json`)

| Categoria | Pacote | Versão |
|---|---|---|
| UI | react / react-dom | ^19.2.8 |
| Build | vite | ^8.2.0 (`@vitejs/plugin-react` ^6.0.4) |
| Linguagem | typescript | ~6.0.2 |
| Roteamento | react-router-dom | ^7.18.2 (`BrowserRouter` + `<Routes>`, rotas aninhadas com `<Outlet/>`) |
| Dados/cache | @tanstack/react-query | ^5.102.5 (**só no módulo Soil**, QueryClient local ao módulo) |
| Gráficos | recharts | ^3.10.1 (Fly Painel, Tracker Dashboard/Ranking/Relatórios); Soil desenha barras com `<div>` |
| Mapas | leaflet ^1.9.4, react-leaflet ^5.0.0, leaflet-draw ^1.0.4, maplibre-gl ^4.7.1 | |
| Geo | shpjs ^6.2.0, @tmcw/togeojson ^7.1.2, @turf/buffer ^7.4.0, polygon-clipping ^0.15.7 (dev: @mapbox/shp-write) | |
| Excel | exceljs ^4.4.0 (exportação de relatórios) | |
| Testes | vitest ^4.1.11, jsdom ^30.0.1, @testing-library/react ^16.3.3 | |
| Lint | oxlint ^1.75.0 | |
| **Ausentes** | axios, zod, react-hook-form, Zustand/Redux/Jotai, Tailwind/shadcn/MUI/Chakra, i18next, ECharts | |

Estado global = **React Context** (Auth, EscopoUnidade, FlyContexto, CampoContexto, contextos do Tracker) + `localStorage`. HTTP = `fetch` com wrappers próprios. Formulários = estado local (`useState`) e validação manual.

---

## 11. Arquitetura do frontend

### 11.1 Organização por módulo (feature folders)

Contrato informal de um módulo (`src/modules/<chave>/`):

| Arquivo | Papel |
|---|---|
| `LocksXxxModule.tsx` | Raiz da rota do módulo: Providers do módulo (QueryClient no Soil, `FlyProvider`, contextos do Tracker), classe raiz do tema (`.soil-app`), guarda de disponibilidade do backend e `<Outlet/>` |
| `XxxShell.tsx` | Layout: rail lateral recolhível com grupos, topbar com breadcrumb (`crumbs`), busca global, link "Central de módulos", `<TransicaoDeTela>` |
| `XxxContexto.tsx` | Estado do módulo + reexpõe o escopo global já "traduzido" (`fazendaIds`, `semFazendas`, `unidadeSemFazendas`, `carregandoEscopo`, `erroEscopo`) |
| `xxxApi.ts` / `api/` | Funções de acesso (objeto `campoApi = { criarTarefa: (...) => flyApi.post(...) }`) |
| `hooks/useXxx.ts` | Hooks de dados (React Query no Soil; `useFetch` próprio no Fly) |
| `logic/*.ts` | Funções puras de regra/cálculo + `*.test.ts` |
| `pages/*.tsx` | Telas (cada uma embrulha seu conteúdo em `<XxxShell crumbs=[...]>`) |
| `componentes/` | Componentes reutilizáveis do módulo |
| `xxx-theme.css` | Tema escopado pela classe raiz do módulo |

Registro de módulo: **uma linha** em `core/moduleRegistry.ts` + rotas em `App.tsx` + tipo em `ModuloKey`.

```ts
export const MODULE_REGISTRY: ModuleDefinition[] = [
  { key: 'cadastros', nome: 'Cadastros', codigo: 'CA', descricao: '...', rota: '/cadastros', disponivel: true },
  { key: 'solos', nome: 'Locks Soil', codigo: 'SO', ..., rota: '/solos', disponivel: true },
  ...
]
export function moduloDaRota(pathname: string) {   // compara por SEGMENTO, não por prefixo solto
  return MODULE_REGISTRY.find((m) => pathname === m.rota || pathname.startsWith(`${m.rota}/`)) ?? null
}
```

### 11.2 Roteamento e rotas protegidas

```tsx
function AreaAutenticada() {           // rota de layout sem path
  return (
    <RequireAuth>
      <Outlet />
      <BarraUnidade />                 // filtro global montado UMA vez para toda a área autenticada
    </RequireAuth>
  )
}

<AuthProvider><Router><EscopoUnidadeProvider><Routes>
  <Route path="/login" element={<LoginPage />} />
  <Route element={<AreaAutenticada />}>
    <Route path="/" element={<HubPage />} />
    <Route path="/cadastros" element={<CadastrosModule />}>
      <Route index element={<Navigate to="fazendas" replace />} />
      <Route path="fazendas" element={<FazendasPage />} /> ...
    </Route>
    <Route path="/solos" element={<LocksSoilModule />}> ... </Route>
    ...
  </Route>
  <Route path="*" element={<Navigate to="/" replace />} />
</Routes></EscopoUnidadeProvider></Router></AuthProvider>
```

`RequireAuth`: `if (carregando) return null; if (!usuario) return <Navigate to="/login" replace />`. URLs em kebab-case pt-BR (`/locks-tracker/mapa-ao-vivo`, `/solos/fertilidade/mapas`), exceto o Fly (inglês: `/locks-fly/service-orders`). Sem lazy loading / code splitting (todas as páginas importadas estaticamente em `App.tsx`).

### 11.3 Camada de API, token e tenant

- `core/api/sessao.ts` — fonte única do token: `tokenDaPlataforma()` (localStorage `agro_token`; em DEV, `VITE_DEV_TOKEN` se ninguém logou), `guardarToken`, `limparToken`, `sessaoExpirou()` que dispara `window` `CustomEvent('locks:sessao-expirada')`; `AuthProvider` escuta e derruba a sessão.
- `core/api/agroApi.ts` — wrapper `fetch` em `/api/v1`, header `Authorization: Bearer`, converte `detail` do FastAPI em `AgroApiError(status, mensagem)`, 401 → `sessaoExpirou()` (exceto no próprio login). Métodos `get/post/put/del`.
- `core/api/flyApi.ts` — escolhe backend **por lista de prefixos** (`CAMINHOS_NOVOS = ['/service-orders', '/applications', '/imports', '/dashboard', ...]` → `/api/v1/fly`, resto → `/fly-api` legado), suporta `FormData`, `raw` e `download()` via `content-disposition`; `qs()` monta query string (arrays como CSV).
- `modules/locksSoil/soilApi.ts` — terceiro wrapper (`/soil-api`) com `postForm` e `qs`.
- **Tenant**: o front **não envia tenant**; ele vem do JWT. O que o front seleciona é a **unidade** (escopo), traduzida para lista de `fazendaIds` enviada em path/query (`/solos/balanco/{fazendaId}`, `?propertyIds=a,b`).
- Contrato divergente detectado: o front espera `POST /auth/auth → {token, user}` e `GET /auth/me`, e chama endpoints Fly (`/dashboard`, `/plots`, `/periodos`, `/restricted-zones`, `/export`) que não existem no backend clonado — o front está à frente desse snapshot do backend.

### 11.4 Hooks, contexts e stores

- **Auth**: `authContextObject.ts` (só `createContext` — separado para não quebrar o Fast Refresh), `AuthProvider.tsx` (estado `usuario`, `papel`, `carregando`, `erro`, `login`, `logout`; reconstrói sessão com `/auth/me` no F5), `useAuth.ts` (lança erro fora do provider). Papel resolvido a partir do `mockDb` (`papeisAcesso`) por `papel_id` ou por `role` (`papelFallbackPorRole`).
- **Escopo global**: `EscopoUnidadeProvider` / `useEscopoUnidade()` (detalhes em §12).
- **Dados**: React Query no Soil (`useQuery`, `useQueries`, `useMutation` + `invalidateQueries`); `useFetch(path|null, deps)` caseiro no Fly (ticket contra resposta velha, `reload`); `useDebounced`; contextos dedicados no Tracker (toasts, filtro de veículo, Local↔Fazenda).
- **CRUD genérico**: `EntityConfig<T>` (colunas com `render`, campos com tipo `text|number|date|select|checkbox|checkbox-group`, `ref` para outra coleção, `filterRef`, `escopo: 'unidade'|'unidades'|'fazenda'|'misto'|'grupo'`) + `EntityCrudPage` (953 linhas: tabela, busca, formulário em drawer, filtro pelo escopo) + `CrudApi<K>` (`listAll/create/update/remove`) injetável. As páginas de Cadastros são uma linha cada:

```tsx
export const FazendasPage = () => <EntityCrudPage config={fazendasConfig} api={plataformaApi} />
```

### 11.5 Layout/shell

- **Hub** (`/`): cards dos módulos filtrados por `papel.modulos_permitidos`.
- **Shell por módulo**: rail verde recolhível (estado em localStorage via `useRailRecolhido(chave)`), topbar com breadcrumb e `TopbarControles`, busca global com atalho (`BuscaGlobal`, índice montado por módulo), drawer no mobile.
- **Barra do rodapé** (`BarraUnidade`): faixa fina fixa com "Módulo" (`SeletorModulo`) e "Unidade" (`SeletorUnidade`) — o **único lugar** dos seletores globais; recua a largura do rail (`useRecuoDoRail`).
- **Transição de tela**: `<TransicaoDeTela>` com `key={pathname}` e `display: contents`.

### 11.6 Tema e i18n

- **Tema**: CSS puro. `index.css` define tokens no `:root` (cores da marca com referência Pantone: `--verde #00594f`, `--ambar #db8a06`…; neutros quentes; texto `--tinta*`; escala tipográfica `--t-*`; raios `--r-*`; sombras; **movimento** `--mov-rapida/media/lenta` + curvas, com teste que confere o uso). Cada módulo tem `xxx-theme.css` escopado pela classe raiz. **Só modo claro** (`color-scheme: light`, sem `prefers-color-scheme`). Responsivo via `responsivo.css` + `useMediaQuery`.
- **i18n**: inexistente; todos os textos em pt-BR hard-coded; formatação com `toLocaleString('pt-BR', ...)`.

---

## 12. Dashboards, gráficos e filtros

### 12.1 Filtro global: Unidade (→ lista de fazendas)

- `EscopoUnidadeProvider` (montado acima das rotas) busca em paralelo `GET /unidades/` e `GET /fazendas/fazendas/`, monta `Map<fazendaId, unidadeId|null>` e expõe:
  `unidades`, `unidadeId`, `unidade`, `definirUnidade(id)`, **`fazendasDaUnidade: string[]`**, `fazendasSemUnidade`, `todasAsFazendas`, `carregando`, `recarregar()`, `semUnidades`, `unidadeSemFazendas`, `erroCarregamento`.
- Persistência: `localStorage['locks.unidade-escopo']` (+ nome em `...nome` para sobreviver a falha de rede); migração da chave antiga por fazenda.
- Invariantes: sempre exatamente uma unidade ativa; se a salva sumiu, assume a primeira; refaz a busca quando muda o usuário logado; 401/403 não marca "servidor indisponível".
- **Não há filtro global de safra ou período**: safra/período/profundidade são filtros **locais da página** (`useState` + `<select>`/pills), e o Painel do Fly usa um único estado composto `"CULTURA|ANO"` para não disparar duas buscas. Período de datas (Tracker) via `PeriodoPicker` com atalhos (`Hoje`, `Ontem`, `7 dias`, `30 dias`, `Este mês`, `Tudo`, `Personalizado`) e estado do atalho guardado na página.
- Para gravar em **uma** fazenda dentro de uma unidade com várias: `useFazendaEscolhidaDaUnidade()` obriga escolha explícita (nunca grava "na primeira" em silêncio).

### 12.2 Hooks de leque por fazenda com falha parcial (padrão-chave)

```ts
// modules/locksSoil/hooks/useBalanco.ts
export function useBalancoDaUnidade(fazendaIds: string[]) {
  const resultados = useQueries({
    queries: fazendaIds.map((fazendaId) => ({
      queryKey: ["balanco-solo", fazendaId],
      queryFn: async () => agrupar(await agroApi.get<BalancoRowApi[]>(`/solos/balanco/${fazendaId}`)),
      enabled: Boolean(fazendaId),
    })),
  })
  return mesclarPorFazenda(fazendaIds, resultados)   // { data, isLoading, isError, fazendasComErro, tentarNovamente }
}
```

`mesclarPorFazenda`: `isLoading` se alguma pendente; `isError` só se **todas** falharam; senão devolve a união dos dados que chegaram + `fazendasComErro` → a tela mostra `<AvisoDadosParciais nomes=... aoTentarNovamente=.../>` ("os números abaixo estão incompletos"). Regra do projeto: *dado parcial nunca é apresentado como completo, e nada some em silêncio*.

### 12.3 Exemplo representativo — Painel do Locks Fly (Recharts)

```tsx
// modules/locksFly/pages/PainelPage.tsx (trechos)
const EIXO_X = { dataKey: 'mes', tick: { fontSize: 11, fill: 'var(--ink-4)' }, tickLine: false,
                 axisLine: { stroke: 'var(--line)' } } as const          // eixo compartilhado entre gráficos
const TOOLTIP = { contentStyle: { fontSize: 12, borderRadius: 8, border: '1px solid var(--line)' } } as const

export default function PainelPage() {
  const { units: system, fazendaIds, semFazendas, unidadeSemFazendas, carregandoEscopo, erroEscopo, recarregarEscopo } = useFly()
  const [chavePeriodo, setChavePeriodo] = useState('')                    // "" = todo o histórico (sem filtro implícito)
  const [cultura, safraAno] = chavePeriodo ? chavePeriodo.split('|') : ['', '']
  const { data, loading } = useFetch<DadosPainel>(
    fazendaIds.length ? `/dashboard${qs({ cultura, safraAno, propertyIds: fazendaIds })}` : null, [chavePeriodo])

  const serieArea = useMemo(() => {                                       // conversão de unidade NO DADO, não no tooltip
    const un = makeUnits(system)
    return (data?.timeline ?? []).map((t) => ({ mes: monthLabel(t.month),
      sobrevoada: un.areaValue(t.sobrevoadaHa), aplicada: un.areaValue(t.aplicadaHa) }))
  }, [data, system])

  return (
    <FlyShell crumbs={[{ label: 'Painel' }]}>
      {semFazendas ? <Empty title="Nenhuma fazenda cadastrada." />
       : carregandoEscopo ? <Loading />
       : erroEscopo ? <Empty title="Não foi possível confirmar as fazendas desta unidade." action={<button onClick={recarregarEscopo}>Tentar novamente</button>} />
       : unidadeSemFazendas ? <Empty title="Esta unidade ainda não tem fazendas." />
       : loading && !data ? <Loading />
       : !data ? <Empty title="Nao foi possivel carregar o painel." />
       : (/* KPIs (Stat/Gauge) + gráficos */
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={serieArea} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid vertical={false} stroke="var(--line)" strokeDasharray="3 3" />
              <XAxis {...EIXO_X} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--ink-4)' }} width={58} tickLine={false} axisLine={false} unit={` ${u.labels.area}`} />
              <Tooltip {...TOOLTIP} formatter={(v, nome) => [`${num(Number(v), 1)} ${u.labels.area}`, String(nome)]} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line type="monotone" dataKey="sobrevoada" name="Sobrevoada" stroke="var(--overlap)" strokeWidth={2} isAnimationActive={false} />
              <Line type="monotone" dataKey="aplicada"   name="Aplicada"   stroke="var(--applied)" strokeWidth={2} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>)}
    </FlyShell>
  )
}
```

Padrões visíveis: (1) **cascata explícita de estados vazios/erro** antes do conteúdo, cada um com texto distinto; (2) o backend entrega o agregado pronto (`/dashboard` com `totals`, `indices`, `timeline`, `worstPlots`, `alerts`), o front só formata; (3) cores do gráfico vêm de **tokens CSS** (`var(--applied)`); (4) `isAnimationActive={false}`; (5) cor da barra codifica diagnóstico (`corDaBarra(aplicacoes)`); (6) KPIs como cartões (`Stat`, `Gauge`, `.kpi-card`), tabelas `.tbl` com `tfoot` de totais (Soil Balanço).

---

## 13. Env, build, lint, testes e deploy (front)

- **Env** (`.env.example`; real em `.env.local`, ignorado por `*.local`): `VITE_LOCKS_TRACKER_WS_URL` (WebSocket com token na query), `VITE_DEV_TOKEN` (atalho de login só em `import.meta.env.DEV`; o ramo some do bundle de produção). Proxies leem `process.env.AGRO_API`, `LOCKSFLY_API`, `LOCKSSOIL_API` (com defaults localhost).
- **Dev server**: Vite na porta fixa 5190 (`strictPort`), `host: true` para acesso pela LAN; proxies:
  - `/api` → backend FastAPI `:8000` (sem rewrite — o FastAPI já tem `/api/v1`);
  - `/fly-api` → servidor Node legado `:4000` (rewrite para `/api`);
  - `/soil-api` → servidor Python do Soil (rewrite removendo o prefixo).
- **Build**: `tsc -b && vite build` (project references; `noUnusedLocals/Parameters`, `erasableSyntaxOnly`, `verbatimModuleSyntax`; **sem `"strict": true`** explícito).
- **Lint**: `oxlint` (react, typescript, oxc; `rules-of-hooks: error`, `only-export-components: warn`). Sem Prettier.
- **Testes**: Vitest + jsdom + Testing Library; `vi.mock('../../core/api/flyApi', ...)` para simular backend; `QueryClient({ defaultOptions: { queries: { retry: false } } })` nos testes; testes de tela focados em regressões de escopo/falha parcial; `logic/*.test.ts` para funções puras.
- **Deploy**: não há. O "ambiente" é `scripts/subir-tudo.ps1` (Windows) subindo Fly `:4000`, Soil `:8000` e o front com `vite dev` exposto na rede. Nenhum Dockerfile, nginx, CI ou build publicado.
- **Processo**: OpenSpec (`openspec/changes/<mudanca>/{proposal,design,tasks}.md`, artefatos em pt-BR, keywords SHALL/MUST em inglês) + design docs datados em `docs/superpowers/`.

---

# 14. Convenções a replicar no novo projeto

### 14.1 Layout de pastas proposto (espelhando a referência, já corrigido)

**Backend (Python)**

```
backend/
├── pyproject.toml / requirements.txt      # TODAS as dependências pinadas (boto3, geoalchemy2, httpx, openpyxl, pandas…)
├── alembic.ini + alembic/                 # um banco só (evitar o 2º banco do Fly); URL vinda de settings
├── Dockerfile                             # api e worker (mesma imagem, comandos diferentes)
├── tests/                                 # pytest: unit (adapters/services) + integração com Postgres real (inclui testes de RLS)
└── app/
    ├── main.py                            # FastAPI, include_router(prefix="/api/v1"), /health, CORS, handlers de erro, logging
    ├── api/v1/router.py                   # include_router(<recurso>.router, prefix="/<recurso>", tags=[...]) — rotas do endpoint SEM repetir o prefixo
    ├── api/v1/endpoints/<recurso>.py      # finos: validam, chamam service, devolvem schema
    ├── api/deps.py                        # get_db_autenticado (JWT → contexto RLS na sessão), exige_papel(...)
    ├── core/config.py                     # Settings (pydantic-settings) + .env.example
    ├── core/security.py                   # hash (bcrypt/argon2) + JWT
    ├── core/logging.py
    ├── db/session.py                      # engine, SessionLocal, listener after_begin com set_config(..., true)
    ├── db/base.py                         # Base(DeclarativeBase) + mixins (TenantMixin, TimestampMixin)
    ├── models/<entidade>.py               # SQLAlchemy 2.0 Mapped/mapped_column, um arquivo por tabela
    ├── schemas/<entidade>.py              # XxxCreate / XxxUpdate / XxxResponse (+ CAMEL_CONFIG se a API for camelCase)
    ├── repositories/<entidade>.py         # queries (ORM/Core), sem regra de negócio
    ├── services/<dominio>.py              # regra de negócio, transações
    ├── etl/
    │   ├── adapters/base.py               # Protocol SourceAdapter: identificar/extrair/normalizar → modelo canônico
    │   ├── adapters/metryx.py             # REST (httpx), paginação, retry
    │   ├── adapters/excel.py              # openpyxl/pandas + _ALIASES de cabeçalho + preview/mapeamento
    │   ├── mapping.py                     # de-para de entidades externas → ids internos (nunca casar só por nome cru)
    │   └── loaders.py                     # upsert em lote (INSERT ... ON CONFLICT DO UPDATE / COPY)
    ├── tasks/celery_app.py + tasks/etl_tasks.py
    └── storage.py                         # S3/MinIO
```

**Frontend (React + TS + Vite)**

```
src/
├── main.tsx / App.tsx / index.css (tokens)
├── pages/ (LoginPage, HubPage)
├── core/
│   ├── moduleRegistry.ts, types.ts
│   ├── api/ (sessao.ts, http.ts — UM cliente fetch com erro/401 —, <dominio>Api.ts)
│   ├── auth/ (AuthProvider, authContextObject, useAuth, RequireAuth)
│   ├── escopo/ (EscopoProvider: fazenda(s) + safra/período globais)
│   ├── relatorio/ (planilha.ts com ExcelJS)
│   └── ui/ (EntityCrudPage + entityCrud.types, Shell, BarraEscopo, primitives, hooks)
└── modules/<modulo>/ (XxxModule.tsx, XxxShell.tsx, XxxContexto.tsx, api.ts, hooks/, logic/, pages/, componentes/, xxx-theme.css)
```

### 14.2 Checklist — COPIAR

**Backend**
- [ ] `app/api/v1/endpoints` + `router.py` agregador com `prefix` e `tags`; prefixo global `/api/v1`; `GET /health`.
- [ ] `Settings` via pydantic-settings com propriedade `database_url`; Alembic pega a URL do settings (`sqlalchemy.url` vazio no ini) e importa `app.models`; `include_object` para ignorar tabelas do PostGIS.
- [ ] Models SQLAlchemy 2.0 tipados; PK `uuid` (`gen_random_uuid()`), `tenant_id NOT NULL FK ... ON DELETE CASCADE` em toda tabela de negócio; `ativo`; `criado_em`/`atualizado_em timestamptz`; `UniqueConstraint` nomeado `uq_<tabela>_<...>` começando por `tenant_id`; índices nomeados.
- [ ] Schemas `XxxCreate/XxxUpdate/XxxResponse` com `from_attributes`; um único padrão de nomes na API (escolher snake_case ou `CAMEL_CONFIG` e usar em tudo).
- [ ] Migração `create_<tabela>` seguida de `rls_<tabela>` (ENABLE + FORCE + políticas + downgrade simétrico); migração de índices declarativa e comentada por consulta atendida; *backfill* junto da coluna derivada.
- [ ] GUC de contexto lido com `current_setting('app.<chave>', true)` (missing_ok) e guard de vazio.
- [ ] Tabela de job com `tipo_origem`, `tipo_destino`, `status`, `total_processado`, `erro`/`detail jsonb`, timestamps; endpoint `POST` cria job e retorna `201 {job_id, status, mensagem}`; `GET /status/{job_id}` com mapa de mensagens; task `pending → processing → done/error`.
- [ ] Upload → objeto no S3/MinIO com chave `{tenant_id}/...` → job → **preview de colunas** → **confirmação do mapeamento** → task (para o Excel).
- [ ] Adaptadores no estilo do decoder: `identificar()` → `parse_<fonte>()` → **modelo canônico** → carga; `_ALIASES` de cabeçalho normalizado (sem acento/caixa) com 2 passadas (igualdade, prefixo); avisos explícitos em vez de inventar dado.
- [ ] Upsert idempotente `INSERT ... ON CONFLICT (chave natural com tenant) DO UPDATE`; "erros brandos" contabilizados (`sem match: [...]`) mesmo com sucesso.
- [ ] `pg_advisory_xact_lock(hashtext('<job>:<tenant>:<chave>'))` para serializar imports da mesma entidade; SHA-256 para deduplicar arquivo; identidade de reimportação (substitui em vez de duplicar); gravação em transação única e status de erro em conexão nova.
- [ ] Celery beat com *fan-out* por tenant (um job por tenant ativo).
- [ ] Listagem paginada com `pageSize` limitado, ordenação por **whitelist** (`ORDENACOES`), filtros em lista via `= ANY(CAST(:ids AS uuid[]))`, contagem/funil numa query só, consultas em lote para evitar N+1, métricas de dashboard **persistidas na carga**.

**Frontend**
- [ ] `core/` × `modules/<modulo>/` × `pages/`; `moduleRegistry.ts` com um card por linha; contrato de módulo (`XxxModule` com Providers + `<Outlet/>`, `XxxShell` com `crumbs`, `XxxContexto`, `api`, `hooks`, `logic` puro testado, `pages`, `componentes`, tema escopado).
- [ ] Rota de layout `AreaAutenticada` (`RequireAuth` + `<Outlet/>` + barra de escopo global montada uma vez); login fora dela; `*` → `/`.
- [ ] `sessao.ts` como fonte única do token + evento de sessão expirada escutado pelo `AuthProvider`; atalho `VITE_DEV_TOKEN` só em DEV; contexto em arquivo separado do Provider (Fast Refresh).
- [ ] Provider de escopo global persistido em `localStorage`, expondo listas de ids e estados distintos (`carregando`, `semX`, `escopoSemFazendas`, `erroCarregamento`) + cascata de estados vazios/erro nas telas.
- [ ] Hooks `useXxxDoEscopo(fazendaIds)` com React Query e tratamento de **falha parcial** (`mesclarPorFazenda` + `AvisoDadosParciais`) — ou, melhor, um endpoint que aceite a lista de fazendas.
- [ ] CRUD por configuração (`EntityConfig` + `EntityCrudPage` + `CrudApi`).
- [ ] Recharts com constantes de eixo/tooltip compartilhadas, cores por token CSS, séries em `useMemo`, conversão de unidade no dado, `isAnimationActive={false}`.
- [ ] Tokens de design no `:root` (cores, tipografia, raios, sombras, movimento) e tema por módulo escopado por classe.
- [ ] Exportação Excel com ExcelJS (bloco de identificação, cabeçalho na cor da marca, painel congelado, autofiltro, largura automática).
- [ ] Wizard de importação em passos (Upload → Pré-visualização → Mapear colunas → Vínculo → Revisão) — mesma UX para o Excel.
- [ ] Vitest + jsdom + Testing Library com testes colocados (`*.test.ts(x)`), `vi.mock` dos clientes de API; oxlint; `tsc -b && vite build`; proxy `/api` no Vite em dev.
- [ ] Specs/design docs datados (`docs/specs/AAAA-MM-DD-tema-design.md`) e esquema-alvo documentado (SQL + tipos TS + models) com convenções de tipo (`numeric`→string no TS, `| null` e não `?`, `timestamptz`, SRID 4326).

### 14.3 NÃO copiar (fraquezas da referência)

**Segurança / multi-tenancy**
- [ ] ✗ `SET app.current_tenant_id = '{f-string}'` repetido em cada endpoint/task → usar `set_config(..., true)` (**local à transação**) aplicado **num único lugar** (listener `after_begin` ou dependency), nunca de sessão com pool.
- [ ] ✗ Rodar API/worker/migrações com o **superusuário** do container → papéis separados (`app_owner` dono, `app_user` `NOSUPERUSER NOBYPASSRLS`), com GRANTs na migração inicial.
- [ ] ✗ Políticas só `FOR SELECT` + `INSERT WITH CHECK (true)` → `FOR ALL USING (...) WITH CHECK (...)` (ou uma por comando), incluindo UPDATE/DELETE; toda tabela de negócio com RLS (a referência esqueceu `importacao_mapa`/`limite_talhao`).
- [ ] ✗ Escopo de fazenda/unidade aplicado só no navegador → `usuario_fazenda` no banco + política por usuário; o front apenas reflete.
- [ ] ✗ Rotas públicas de criação de tenant/usuário; `role` nunca checado; papéis guardados em mock/localStorage → `exige_papel()` no servidor e papéis no banco.
- [ ] ✗ Login que busca e-mail em todos os tenants, ignora `ativo`, e diferencia "não encontrado" de "senha errada"; algoritmo JWT fixo no encode e configurável no decode; sem `/auth/me`; `datetime.utcnow()`.
- [ ] ✗ Segredos no repositório (credenciais MinIO no compose, chave de API em `schemas/testeevogo.py`), token de dev usado em chamada serviço→serviço, ausência de `.env.example` no backend.
- [ ] ✗ Token no `localStorage` sem estratégia de expiração/refresh (avaliar cookie httpOnly ou ao menos refresh token + expiração curta).

**Estrutura / código**
- [ ] ✗ SQL cru em todo endpoint, `row._asdict()` + renomeação manual de campos (`d["municipio"] = d.pop("cidade")`), models sem `relationship` → repositórios + schemas com alias.
- [ ] ✗ Regras de negócio enormes dentro de SQL no endpoint (classificação de fertilidade em `CASE` de centenas de linhas) e queries de 1.000+ linhas embutidas em `etl_tasks.py` → arquivos `.sql` versionados ou tabela de faixas/regras; service testável.
- [ ] ✗ Prefixo duplicado de rota (`/fazendas/fazendas/`), barras finais inconsistentes, mistura pt/en em tabelas e status, tabelas ora no plural ora no singular → escolher **uma** convenção (sugestão: tabelas no singular em pt-BR, como o esquema-alvo).
- [ ] ✗ Dois bancos (principal + Fly) com "join" em Python e chamada HTTP da API para ela mesma → um banco, schemas Postgres se precisar separar.
- [ ] ✗ Casar entidades externas por **nome** (`fazendas.nome = UNIDADE` do datalake) → tabela de de-para (`fonte`, `id_externo`, `entidade_id`) por adaptador.
- [ ] ✗ Celery: `create_engine` por task, `iterrows` + SELECT por linha, sem retry/time limit/acks_late, task que ignora parâmetro, `except` sem commit, beat "diário" a cada 10 min, caminho Windows fixo em `subprocess`, temporários não apagados.
- [ ] ✗ Alembic autogenerate aceito sem revisão (migração de cultura removeu índices alheios), migração vazia duplicada, revisão com id textual.
- [ ] ✗ Dependências fora do requirements, `print` no lugar de logging, zero testes no backend, sem Dockerfile/compose da app, sem CORS, `.idea/` versionado, scripts ad-hoc na raiz.

**Frontend**
- [ ] ✗ Três clientes HTTP diferentes (agroApi/flyApi/soilApi) com tratamento de erro duplicado e roteamento por lista de prefixos → um `http.ts`.
- [ ] ✗ React Query só num módulo e `useFetch` caseiro nos outros → um `QueryClientProvider` global, query keys padronizadas (`[recurso, escopo, filtros]`).
- [ ] ✗ Sem validação de formulário/contrato (zod ou equivalente) e contrato front×back divergente (`/auth/auth` com `{token,user}`, `/auth/me`, `/dashboard` inexistentes no backend) → tipos gerados do OpenAPI do FastAPI (ex.: `openapi-typescript`).
- [ ] ✗ Filtros de safra/período locais e reimplementados por página → colocar safra/período no provider de escopo global (o novo produto pede filtros globais).
- [ ] ✗ Comentários-narrativa gigantes contando histórico de bugs/revisões dentro do código ("fix round 1", "achado I2") → mover para docs/PR; comentário só explica o *porquê* atual.
- [ ] ✗ CSS por módulo com milhares de linhas sem biblioteca de componentes; somente tema claro; sem i18n; sem code splitting (todas as páginas importadas no `App.tsx`).
- [ ] ✗ "Produção" = `vite dev` exposto na LAN com proxies → build estático servido por nginx/CDN + API atrás de reverse proxy com HTTPS.
- [ ] ✗ `tsconfig` sem `"strict": true`.

---

### Apêndice A — Modelo de job a reutilizar (sugestão derivada da referência)

```sql
CREATE TABLE etl_job (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id        uuid NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
  usuario_id       uuid REFERENCES usuario(id) ON DELETE SET NULL,     -- quem disparou (RLS por usuário no worker)
  fonte            text NOT NULL CHECK (fonte IN ('metryx', 'excel')), -- = tipo_origem
  destino          text NOT NULL,                                       -- = tipo_destino
  status           text NOT NULL DEFAULT 'pendente'
                   CHECK (status IN ('pendente','processando','concluido','concluido_com_avisos','erro')),
  arquivo_chave    text,                -- chave S3/MinIO (Excel)
  arquivo_sha256   text,                -- deduplicação
  mapeamento       jsonb,               -- colunas confirmadas no preview (Excel)
  parametros       jsonb,               -- janela/cursor da API (Metryx)
  total_lido       integer, total_gravado integer, total_ignorado integer,
  detalhe          jsonb,               -- { alertas: [{nivel, titulo, detalhe}], sem_match: [...] }
  criado_em        timestamptz NOT NULL DEFAULT now(),
  iniciado_em      timestamptz,
  finalizado_em    timestamptz,
  atualizado_em    timestamptz NOT NULL DEFAULT now()
);
```

### Apêndice B — Mapeamento de conceitos referência → novo projeto

| Referência (agricultura) | Novo projeto (pecuária) — sugestão |
|---|---|
| `tenants` / `organizacao` | tenant / organização (raiz do RLS) |
| `unidade` (agrupa fazendas, escopo global no rodapé) | unidade/grupo (opcional) |
| `fazendas` | fazenda |
| `talhao` | pasto/piquete/curral (geometria 4326 opcional) |
| `safras` / `periodo_safra` | período/estação/ano pecuário (filtro global) |
| `analise_*` (fatos carregados pelo ETL, upsert por chave natural) | fatos de pesagem, nascimento, sanidade, abate etc. |
| Athena (`core/athena.py`, queries embutidas) | `etl/adapters/metryx.py` (REST) |
| Upload SHP com preview/confirm de colunas | `etl/adapters/excel.py` com preview/confirm de colunas |
| `fly_decoder.identificar()` + `_ALIASES` | detecção de layout de planilha + apelidos de cabeçalho |
| `EscopoUnidadeProvider` + `BarraUnidade` | provider de escopo (fazenda(s) + período) + barra de filtros global |
| `mesclarPorFazenda` / `AvisoDadosParciais` | mesma semântica de falha parcial (ou endpoint que aceite lista) |
| Painel do Fly (Recharts + KPIs prontos do backend) | dashboards com agregados persistidos/materializados no banco |
