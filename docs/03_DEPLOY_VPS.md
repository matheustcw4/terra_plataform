# Deploy na VPS Linux e operação

> Como o Terra roda em produção: um `docker compose` numa VPS Linux, com as cargas agendadas pelo Celery, HTTPS
> automático e backup diário do banco. O desenvolvimento continua no Windows (README); este guia é o da VPS.
> Validado em 15/10/2026 subindo o `docker-compose.prod.yml` inteiro no Docker Desktop (seção 9).

## 1. O que sobe

| Serviço | Imagem | O que faz | Credencial |
|---|---|---|---|
| `db` | postgres:16 | o banco; escuta só em `127.0.0.1` da VPS (túnel SSH para manutenção) | superusuário (só ele) |
| `redis` | redis:7-alpine | a fila das cargas (nada em disco) | — |
| `migracao` | terra-backend | `alembic upgrade head` a cada subida, e sai; a API só sobe depois | superusuário |
| `api` | terra-backend | FastAPI (uvicorn, 2 processos) | `app_user` (RLS) |
| `worker` | terra-backend | executa as cargas, uma por vez (Celery) | `app_etl` |
| `beat` | terra-backend | dispara as cargas nos horários de `AGENDA_*` | — |
| `web` | terra-web (Caddy) | o painel (build do front) e `/api` no mesmo endereço, com HTTPS automático | — |
| `backup` | postgres:16 | `pg_dump` diário em `BACKUP_HOST_DIR`, guarda `DIAS_DE_BACKUP` dias | superusuário |

Só o `web` fica exposto na internet (portas 80 e 443). A documentação da API (`/docs`) não sai pelo Caddy.

### Cargas agendadas

| Carga | Agenda padrão | O que faz |
|---|---|---|
| Importações (`cargas.importacoes`) | `*/5 * * * *`: a cada 5 minutos | carrega as planilhas enviadas pela tela que ainda estão na fila (a API já avisa o worker a cada envio; a agenda é a rede de segurança) |
| Metryx (`cargas.metryx`) | vazia: **desligada** | sincroniza os clientes com credencial ativa; liga só com a autorização das chamadas à API real |
| Estoque (`cargas.estoque`) | `30 0 1 * *`: dia 1, 00:30 | estende o estoque de todas as fazendas até o mês novo (a carga só recalcula as fazendas que mudaram) |

As agendas são no formato do cron (minuto hora dia mês dia-da-semana), no horário de Cuiabá. Uma carga por vez:
se outra estiver rodando, a das importações e a do Metryx são puladas (a agenda tenta de novo depois); a do estoque
espera. O resultado de cada carga fica em `ingest.job` e os avisos aparecem na aba Pendências.

As fontes são duas: as planilhas, que chegam só pela tela **Importar planilhas**, e o Metryx, pela API (o Google
Drive deixou de ser fonte em 10/11/2026). Fora da agenda, o admin pode pedir a carga do Metryx pelo painel: o botão
**"Atualizar agora"** (o ↻ no topo) põe `cargas.atualizar_agora` na fila. Ele só aparece com `AGENDA_METRYX` ligada:
sem o Metryx não há o que puxar. Por isso a API recebe o `REDIS_URL` e o `AGENDA_METRYX`, e o worker, o
`AGENDA_METRYX` (já no `docker-compose.prod.yml`). Uma `AGENDA_PLANILHAS` que tenha ficado num `.env.producao` antigo
não faz nada. As tarefas usam a fila `terra`; ao
atualizar uma instalação antiga, suba o beat e o worker juntos (os dois passam a usar a fila nova).

## 2. Requisitos

- VPS com Ubuntu 24.04 LTS (ou Debian 12), 2 vCPU, 4 GB de RAM, 40 GB de disco (o banco de validação inteiro, com as
  230 planilhas e o Metryx, ocupa poucos GB; o resto é folga para backups e imagens);
- um domínio (ou subdomínio) com registro DNS `A` apontando para o IP da VPS, por exemplo `painel.terra.agr.br`;
- portas 80 e 443 abertas para a internet (o Caddy tira o certificado pela 80) e 22 para o SSH;
- Docker Engine com o plugin compose (instalação oficial: https://docs.docker.com/engine/install/ubuntu/).

## 3. Primeira instalação

```bash
# 1. pastas da VPS (fora do repositório): o código e os backups
sudo mkdir -p /srv/terra/{app,backups}
sudo chown -R $USER /srv/terra

# 2. o código (repositório privado)
git clone <url-do-repositorio> /srv/terra/app
cd /srv/terra/app

# 3. a configuração: preencha senhas, chaves, domínio e e-mail (ver os comentários do arquivo)
cp .env.producao.example .env.producao
chmod 600 .env.producao
nano .env.producao

# 4. firewall
sudo ufw allow OpenSSH && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp && sudo ufw enable

# 5. subir tudo (a primeira vez constrói as imagens: alguns minutos)
docker compose -f docker-compose.prod.yml --env-file .env.producao up -d --build
docker compose -f docker-compose.prod.yml --env-file .env.producao ps
```

Para não repetir os dois `-f`/`--env-file` em todo comando, use um alias na VPS:

```bash
echo "alias terra='docker compose -f /srv/terra/app/docker-compose.prod.yml --env-file /srv/terra/app/.env.producao'" >> ~/.bashrc
source ~/.bashrc
terra ps
```

Os comandos abaixo usam esse alias.

### O primeiro admin

O container `migracao` tem a credencial de superusuário que o comando de usuários usa; sem `SENHA_NOVA`, a senha é
perguntada sem aparecer na tela:

```bash
terra run --rm -it migracao python -m app.comandos criar-usuario --email voce@terra.com --nome "Seu Nome" --admin
```

Os demais usuários e o acesso de cada um às fazendas ficam na tela **Administração → Usuários e acesso**. A equipe
da consultoria (técnicos e gerentes, com as fazendas de cada um) sai da planilha de levantamento. Rode depois que as
cargas tiverem trazido as fazendas, e de novo quando entrarem clientes novos do Metryx:

```bash
terra run --rm -v /caminho/da/planilha:/dados/equipe:ro migracao \
  python -m app.comandos importar-equipe "/dados/equipe/Levantamento Clientes para Power BI.xlsx" --aplicar
```

### As planilhas

As planilhas chegam pela tela **Importar planilhas** do painel (menu Dados; decisão D8, 09/11/2026), no lugar da
pasta sincronizada com o Google Drive. A pessoa envia o `RELATÓRIO - código - fazenda.xlsm`; a API guarda o arquivo
em `ingest.importacao` e avisa o worker, que carrega um por vez, pelo mesmo motor de antes (o nome do arquivo continua
sendo a chave dele: enviar de novo com o mesmo nome é uma versão nova). Cada técnico só importa as fazendas a que tem
acesso; a primeira planilha de uma fazenda nova é com o admin, que depois dá o acesso aos técnicos. O resultado de
cada envio aparece na própria tela, e os avisos, em Pendências. O arquivo sai do banco depois de carregado (o que foi
lido fica em `raw.payload`).

Para a primeira carga, com as 230 planilhas, há dois caminhos: restaurar o dump do banco de validação (seção 10) ou o
admin enviar todas pela tela (pode marcar várias de uma vez; o worker leva um ou dois minutos por planilha). Uma pasta
inteira também carrega pela linha de comando, por um túnel SSH, como o histórico abaixo:
`python -m app.etl planilhas --pasta <pasta>`.

### O histórico das planilhas (carga única, Q6)

O histórico de antes do período atual de cada planilha vem do datalake do BI (snapshot de ago/2026), que está na
máquina Windows. Rode **depois** da primeira carga das planilhas na VPS, da máquina Windows, por um túnel SSH até o
banco da VPS:

```bash
# na máquina Windows, num terminal: o banco da VPS aparece em 127.0.0.1:55433
ssh -N -L 55433:127.0.0.1:55432 usuario@ip-da-vps
```

```powershell
# noutro terminal, em backend/: aponta o ETL para o banco da VPS (senha do app_etl da produção) e o datalake local
$env:POSTGRES_HOST = "127.0.0.1"; $env:POSTGRES_PORT = "55433"; $env:APP_ETL_PASSWORD = "<senha do app_etl da VPS>"
.venv/Scripts/python -m app.etl planilhas-historico --ate 2026-06
```

### O Metryx (só com autorização)

As chamadas à API real do Metryx dependem de autorização explícita (CLAUDE.md, Segurança). Autorizado: cadastre o
token de cada cliente (cifrado no banco com `METRYX_CHAVE_CIFRA`), preencha `AGENDA_METRYX` (ex.: `0 3 * * *`) no
`.env.producao` e recrie o beat:

```bash
terra run --rm -it worker python -m app.etl metryx-credencial --cliente <idCustomer> --nome "Nome do cliente"
terra up -d beat
```

## 4. Atualizar a versão

```bash
cd /srv/terra/app
git pull
terra up -d --build      # a migração roda sozinha antes da API subir
terra ps
```

## 5. Operação do dia a dia

```bash
terra ps                                   # tudo de pé? (api "healthy")
terra logs -f worker                       # as cargas (resumo de cada uma)
terra logs --since 24h beat                # quando cada carga foi disparada

# rodar uma carga agora (pela fila: respeita a trava de uma carga por vez)
terra exec worker celery -A app.tasks.fila call cargas.importacoes   # a fila da tela de importação
terra exec worker celery -A app.tasks.fila call cargas.estoque

# as últimas cargas, pelo banco
terra exec db psql -U postgres -d terra -c \
  "SELECT fonte, status, iniciado_em, finalizado_em, unidades_total, unidades_carregadas, unidades_com_erro
   FROM ingest.job ORDER BY criado_em DESC LIMIT 10"

# as últimas planilhas enviadas pela tela
terra exec db psql -U postgres -d terra -c   "SELECT arquivo, enviado_por, enviado_em, status, mensagem FROM ingest.importacao ORDER BY enviado_em DESC LIMIT 10"
```

O que a carga deixou de fora ou marcou para conferir aparece na aba **Pendências** do painel; categorias e contas sem
de-para, em **Administração**.

## 6. Backup e restauração

O serviço `backup` grava um `pg_dump` por dia (`HORA_DO_BACKUP`, padrão 03:00) em `BACKUP_HOST_DIR`, mais um na subida,
e apaga os mais velhos que `DIAS_DE_BACKUP`. **Copie essa pasta para fora da VPS** (ex.: `rclone copy` para o Drive ou
um bucket): backup que fica só na VPS some junto com ela.

Restaurar (testado: a restauração traz os dados, a versão das migrações, o RLS e as políticas):

```bash
# 1. pare quem escreve no banco
terra stop api worker beat

# 2. restaure num banco novo e confira
terra exec -T db createdb -U postgres terra_restaurado
terra exec -T db pg_restore -U postgres -d terra_restaurado < /srv/terra/backups/terra-AAAAMMDD-HHMM.dump
terra exec db psql -U postgres -d terra_restaurado -c "SELECT version_num FROM alembic_version"

# 3. troque: renomeie os bancos e suba de novo
terra exec db psql -U postgres -c "ALTER DATABASE terra RENAME TO terra_antigo"
terra exec db psql -U postgres -c "ALTER DATABASE terra_restaurado RENAME TO terra"
terra up -d
```

Os papéis (`app_owner`, `app_user`, `app_etl`) são do servidor, não do dump: numa VPS nova, eles nascem na primeira
subida do volume do banco (`docker/postgres/init`), com as senhas do `.env.producao`; depois restaure como acima.

## 7. Segurança (lista de conferência)

- `.env.producao` com `chmod 600`, fora do git (o `.gitignore` já ignora); senhas e chaves aleatórias e diferentes;
- o Postgres não sai da VPS (só `127.0.0.1`); acesso de manutenção por túnel SSH;
- SSH só com chave (`PasswordAuthentication no`) e o `ufw` liberando 22, 80 e 443;
- a API conecta como `app_user` (RLS de verdade) e o worker como `app_etl`; o superusuário só na migração e no backup;
- as planilhas (dados de clientes) chegam pela tela, de quem está logado, e só para as fazendas a que a pessoa tem
  acesso (o worker confere com a mesma regra do RLS); o arquivo sai do banco depois de carregado;
- os backups copiados para fora da VPS, com acesso restrito.

## 8. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| o painel não abre em HTTPS | DNS ainda não aponta para a VPS, ou a porta 80 está fechada | `dig painel...`; `terra logs web` mostra a tentativa do certificado |
| a planilha enviada fica "Na fila" | o worker está parado, ou outra carga está rodando | `terra ps` e `terra logs worker`; com o worker de pé, a agenda das importações pega em até 5 min |
| a planilha enviada "Não carregou" | a mensagem diz o motivo (sem acesso à fazenda, fazenda nova, planilha com erro) | corrija e envie de novo; acesso, em Administração → Usuários e acesso |
| a carga devolve `ocupada` | outra carga estava rodando | normal: a próxima passada pega |
| a API não sobe | a migração falhou | `terra logs migracao` |

## 9. Testar a produção no Windows antes do deploy

O mesmo compose sobe no Docker Desktop, num projeto separado (não mexe no banco de desenvolvimento), sem domínio e
sem HTTPS. Num arquivo de ambiente de teste, use `DOMINIO=:80`, `PORTA_HTTP=8088`, `PORTA_HTTPS=8443`,
`POSTGRES_PORTA_LOCAL=55499`, uma pasta de backups temporária e, para ver o beat disparar logo,
`AGENDA_IMPORTACOES=* * * * *`:

```bash
docker compose -f docker-compose.prod.yml -p terra_prod_teste --env-file teste.env up -d --build
curl http://localhost:8088/api/v1/health
docker compose -p terra_prod_teste logs -f worker
docker compose -f docker-compose.prod.yml -p terra_prod_teste --env-file teste.env down -v   # apaga tudo do teste
```

No Git Bash, comandos `docker compose exec` com caminho do container (ex.: `/backups/...`) precisam de
`MSYS_NO_PATHCONV=1`, senão o Git Bash troca o caminho por um do Windows.

## 10. Servidor de teste na rede interna (cópia do banco atual)

Para a equipe testar o painel antes da produção (decidido em 27/10/2026): um servidor Linux da rede interna, acesso
só pelo IP (`http://IP`, sem HTTPS), com **uma cópia do banco de validação** e **nenhuma carga agendada** (ninguém
atualiza os dados nele). Os dados são reais: a porta do painel fica aberta só para a rede interna.

### O que levar da máquina Windows

Os dois arquivos ficam em `backups/servidor_teste/`, pasta que o git ignora (dados de clientes e senhas):

- `terra_validacao.dump`: o banco de validação inteiro (`pg_dump --format=custom`, testado com uma restauração);
- `.env.producao`: a configuração do teste, com senhas novas, `DOMINIO=:80` e as agendas vazias.

```powershell
# na máquina Windows, na raiz do repositório
scp backups/servidor_teste/terra_validacao.dump backups/servidor_teste/.env.producao usuario@IP-do-servidor:/tmp/
```

### No servidor

Precisa de Docker com o plugin compose (seção 2) e acesso à internet na primeira subida (as imagens e as
dependências do Python e do Node são baixadas para montar as imagens).

```bash
# 1. pastas e o código (repositório privado: chave de deploy só leitura, abaixo)
sudo mkdir -p /srv/terra/backups && sudo chown -R $USER /srv/terra
git clone git@github.com:<organizacao>/<repositorio>.git /srv/terra/app
cd /srv/terra/app
mv /tmp/.env.producao .env.producao && chmod 600 .env.producao
echo "alias terra='docker compose -f /srv/terra/app/docker-compose.prod.yml --env-file /srv/terra/app/.env.producao'" >> ~/.bashrc
source ~/.bashrc

# 2. só o banco: na primeira subida ele cria os papéis app_owner, app_user e app_etl
terra up -d db
terra ps        # espere o db ficar "healthy"

# 3. a cópia do banco atual
terra exec -T db pg_restore -U postgres -d terra --exit-on-error < /tmp/terra_validacao.dump
terra exec db psql -U postgres -d terra -c "SELECT version_num FROM alembic_version"
rm /tmp/terra_validacao.dump

# 4. o resto (a migração vê que o banco já está na versão do código e não muda nada)
terra up -d --build
terra ps        # api "healthy" e web de pé
```

O painel abre em `http://IP-do-servidor` (ou `http://IP:PORTA_HTTP`, se a 80 estiver ocupada e o `.env.producao`
usar outra porta). Os logins são os mesmos de hoje; quem vai testar ganha usuário na tela **Administração →
Usuários e acesso**.

### Chave de deploy (clonar o repositório privado)

```bash
ssh-keygen -t ed25519 -f ~/.ssh/terra_deploy -N "" -C "servidor-teste-terra"
cat ~/.ssh/terra_deploy.pub
# no GitHub: repositório → Settings → Deploy keys → Add deploy key (só leitura), cole a chave
printf 'Host github.com\n  IdentityFile ~/.ssh/terra_deploy\n' >> ~/.ssh/config
ssh -T git@github.com    # "successfully authenticated"
```

### Firewall

A porta do painel só para a rede interna (troque pela faixa da rede da empresa):

```bash
sudo ufw allow OpenSSH
sudo ufw allow from 192.168.0.0/16 to any port 80 proto tcp
sudo ufw enable
```

### Atualizar e desmontar

```bash
cd /srv/terra/app && git pull && terra up -d --build    # versão nova do código (os dados ficam)
terra down -v                                            # fim do teste: apaga tudo, inclusive o banco
```

Quando a versão nova muda os números (uma regra de carga nova, um cliente recarregado), o banco também precisa da
cópia nova. Gere o dump na máquina Windows, leve-o como na primeira vez e troque o banco inteiro:

```powershell
# na máquina Windows, na raiz do repositório
docker exec terra_db pg_dump -U postgres --format=custom -f /tmp/terra_validacao.dump terra_validacao
docker cp terra_db:/tmp/terra_validacao.dump backups/servidor_teste/terra_validacao.dump
scp backups/servidor_teste/terra_validacao.dump usuario@IP-do-servidor:/tmp/
```

```bash
# no servidor
cd /srv/terra/app
git pull
terra down                    # para tudo; o volume do banco fica (sem -v)
terra up -d db
terra ps                      # espere o db ficar "healthy"
terra exec db psql -U postgres -d postgres -c "DROP DATABASE terra WITH (FORCE)" -c "CREATE DATABASE terra OWNER app_owner"
terra exec -T db pg_restore -U postgres -d terra --exit-on-error < /tmp/terra_validacao.dump
terra exec db psql -U postgres -d terra -c "SELECT version_num FROM alembic_version"
rm /tmp/terra_validacao.dump
terra up -d --build
terra ps                      # api "healthy" e web de pé
```

Os usuários, as senhas e os acessos vêm junto com a cópia: o que foi criado só no servidor se perde na troca.

Sem o Metryx ligado no servidor, o botão **"Atualizar agora"** não aparece. A tela **Importar planilhas** funciona aqui (o worker sobe com o resto), o que serve para a equipe
testá-la; o que for importado no servidor também se perde na próxima troca do banco.

