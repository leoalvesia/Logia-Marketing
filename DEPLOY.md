# Guia de Deploy — Logia Marketing Platform

Do zero ao servidor funcionando em produção.

---

## Índice

1. [Pré-requisitos](#1-pré-requisitos)
2. [Configurar o VPS](#2-configurar-o-vps)
3. [Configurar DNS](#3-configurar-dns)
4. [Preparar variáveis de ambiente](#4-preparar-variáveis-de-ambiente)
5. [Configurar GitHub Secrets](#5-configurar-github-secrets)
6. [Deploy manual (primeira vez)](#6-deploy-manual-primeira-vez)
7. [Deploy automático (CI/CD)](#7-deploy-automático-cicd)
8. [Verificar saúde do sistema](#8-verificar-saúde-do-sistema)
9. [Operações de manutenção](#9-operações-de-manutenção)
10. [Rollback](#10-rollback)
11. [Troubleshooting](#11-troubleshooting)
12. [Monitoramento e Alertas (Sentry)](#12-monitoramento-e-alertas-sentry)

---

## 1. Pré-requisitos

### O que você precisa antes de começar

| Item | Onde obter |
|------|-----------|
| VPS Ubuntu 22.04 com acesso root | Hetzner / DigitalOcean / Vultr (mínimo 2 vCPU, 4 GB RAM) |
| Domínio registrado | Registro.br / Cloudflare |
| Conta no GitHub com o repositório | github.com |
| Par de chaves SSH (local + servidor) | `ssh-keygen -t ed25519 -C "deploy@logia"` |
| Todas as chaves de API do `.env.production` | Ver seção 4 |

### Gerar par de chaves SSH para o deploy

```bash
# Na sua máquina local
ssh-keygen -t ed25519 -C "deploy@logia-ci" -f ~/.ssh/logia_deploy

# Exibir chave pública (vai para o servidor)
cat ~/.ssh/logia_deploy.pub

# Exibir chave privada (vai para o GitHub Secrets)
cat ~/.ssh/logia_deploy
```

---

## 2. Configurar o VPS

### 2.1 Executar o script de setup

```bash
# Conectar ao servidor como root
ssh root@SEU_IP_VPS

# Baixar e executar o script (ou copiar o conteúdo de scripts/setup-server.sh)
curl -fsSL https://raw.githubusercontent.com/SEU_ORG/logia-marketing/main/scripts/setup-server.sh | bash
```

O script automatiza:
- Atualização do sistema
- Instalação do Docker + Docker Compose Plugin
- Instalação do Caddy (proxy reverso com SSL automático)
- Configuração do firewall UFW (portas 22, 80, 443)
- Configuração do Fail2ban (proteção SSH)
- Criação do usuário `deploy` sem root
- Criação de 2 GB de swap
- Ajuste de limites de sistema para containers

### 2.2 Adicionar chave SSH do deploy

```bash
# Ainda como root no servidor
echo "CONTEUDO_DA_CHAVE_PUBLICA_logia_deploy.pub" >> /home/deploy/.ssh/authorized_keys

# Verificar
cat /home/deploy/.ssh/authorized_keys
```

### 2.3 Testar acesso com usuário deploy

```bash
# Na sua máquina local
ssh -i ~/.ssh/logia_deploy deploy@SEU_IP_VPS

# Deve logar sem senha
```

---

## 3. Configurar DNS

### 3.1 Registros necessários

| Tipo | Nome | Valor | TTL |
|------|------|-------|-----|
| A | `app` | `SEU_IP_VPS` | 300 |
| A | `www` | `SEU_IP_VPS` | 300 |

TTL 300 = 5 minutos. Após confirmar propagação, aumentar para 3600.

### 3.2 Verificar propagação

```bash
# Aguardar propagação (pode levar até 5 minutos com TTL=300)
dig app.logia.com.br +short
# Deve retornar o IP do VPS

# Verificar de múltiplas regiões
curl -s "https://dns.google/resolve?name=app.logia.com.br&type=A" | jq .
```

### 3.3 SSL automático pelo Caddy

O Caddy obtém o certificado Let's Encrypt automaticamente quando:
1. O DNS propaga (registro A apontando para o VPS)
2. A porta 80 está acessível
3. O Caddy está rodando

Não é necessário nenhum passo manual para o SSL.

---

## 4. Preparar variáveis de ambiente

### 4.1 Copiar e preencher o template

```bash
# Na sua máquina local
cp .env.production .env.production.local
# Editar com seus valores reais
nano .env.production.local
```

### 4.2 Referência das chaves

| Variável | Como obter |
|----------|-----------|
| `SECRET_KEY` | `openssl rand -hex 32` |
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys |
| `OPENAI_API_KEY` | platform.openai.com → API Keys |
| `META_ACCESS_TOKEN` | developers.facebook.com → Graph API Explorer |
| `META_INSTAGRAM_ACCOUNT_ID` | ID numérico — obter via `GET /me/accounts` |
| `TWITTER_CONSUMER_KEY/SECRET` | developer.twitter.com → Apps → Keys and Tokens |
| `TWITTER_ACCESS_TOKEN/SECRET` | developer.twitter.com → Apps → Keys and Tokens |
| `LINKEDIN_ACCESS_TOKEN` | linkedin.com/developers → Auth → Token Inspector |
| `LINKEDIN_PERSON_ID` | `GET https://api.linkedin.com/v2/me` → `id` |
| `RESEND_API_KEY` | resend.com → API Keys |
| `APIFY_TOKEN` | console.apify.com → Settings → Integrations |
| `YOUTUBE_API_KEY` | console.cloud.google.com → APIs → YouTube Data API v3 |
| `RAPIDAPI_KEY` | rapidapi.com → Apps → Security |
| `GOOGLE_DRIVE_FOLDER_ID` | ID na URL da pasta: `drive.google.com/drive/folders/ID_AQUI` |

### 4.3 Google Service Account (para Drive + YouTube)

```bash
# 1. Criar Service Account no Google Cloud Console
#    IAM & Admin → Service Accounts → Create
#    Função: Editor (apenas para o Drive)

# 2. Criar chave JSON
#    Service Account → Keys → Add Key → Create new key → JSON

# 3. Copiar para o servidor
scp -i ~/.ssh/logia_deploy google-sa.json \
  deploy@SEU_IP_VPS:/opt/logia/shared/credentials/google-sa.json

# 4. Compartilhar a pasta do Google Drive com o e-mail da Service Account
#    (encontrado no JSON como "client_email")
```

### 4.4 Copiar .env para o servidor

```bash
scp -i ~/.ssh/logia_deploy .env.production.local \
  deploy@SEU_IP_VPS:/opt/logia/.env
```

---

## 5. Configurar GitHub Secrets

Acesse: **GitHub → Repositório → Settings → Secrets and variables → Actions → New repository secret**

### 5.1 Secrets obrigatórios

| Secret | Valor |
|--------|-------|
| `SSH_PRIVATE_KEY` | Conteúdo de `~/.ssh/logia_deploy` (chave privada completa, incluindo `-----BEGIN...`) |
| `VPS_HOST` | IP do servidor (ex: `123.456.789.0`) |
| `VPS_USER` | `deploy` |
| `ANTHROPIC_API_KEY` | `sk-ant-...` |
| `OPENAI_API_KEY` | `sk-...` |
| `SECRET_KEY` | Resultado de `openssl rand -hex 32` |
| `DATABASE_URL` | `postgresql+asyncpg://logia:SENHA@postgres:5432/logia_prod` |
| `META_ACCESS_TOKEN` | Token da Meta Graph API |
| `META_INSTAGRAM_ACCOUNT_ID` | ID numérico da conta |
| `TWITTER_CONSUMER_KEY` | — |
| `TWITTER_CONSUMER_SECRET` | — |
| `TWITTER_ACCESS_TOKEN` | — |
| `TWITTER_ACCESS_TOKEN_SECRET` | — |
| `LINKEDIN_ACCESS_TOKEN` | — |
| `LINKEDIN_PERSON_ID` | `urn:li:person:XXXXXXXX` |
| `RESEND_API_KEY` | `re_...` |
| `APIFY_TOKEN` | — |
| `YOUTUBE_API_KEY` | — |
| `RAPIDAPI_KEY` | — |
| `GOOGLE_DRIVE_FOLDER_ID` | ID da pasta |
| `STABILITY_AI_KEY` | Opcional — apenas se usar Stability AI |

### 5.2 Adicionar via GitHub CLI (alternativa)

```bash
gh secret set SSH_PRIVATE_KEY < ~/.ssh/logia_deploy
gh secret set VPS_HOST --body "SEU_IP"
gh secret set VPS_USER --body "deploy"
# ... repetir para cada secret
```

---

## 6. Deploy manual (primeira vez)

```bash
# Conectar como deploy
ssh -i ~/.ssh/logia_deploy deploy@SEU_IP_VPS

# Clonar o repositório
git clone https://github.com/SEU_ORG/logia-marketing.git /opt/logia/app
cd /opt/logia/app

# Copiar o Caddyfile para o local esperado
cp config/Caddyfile /opt/logia/Caddyfile

# Verificar se o .env está em /opt/logia/.env
ls -la /opt/logia/.env

# Subir todos os serviços
docker compose -f docker-compose.prod.yml --env-file /opt/logia/.env up -d

# Verificar logs de inicialização
docker compose -f docker-compose.prod.yml logs -f --tail=50

# Executar migrations do banco
docker compose -f docker-compose.prod.yml exec backend \
  alembic upgrade head

# Configurar Caddy para usar nosso Caddyfile
sudo cp /opt/logia/Caddyfile /etc/caddy/Caddyfile
sudo systemctl reload caddy

# Verificar status do Caddy
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl status caddy
```

### 6.1 Verificar se subiu corretamente

```bash
# Health check da API
curl https://app.logia.com.br/health

# Deve retornar:
# {"status":"ok","db":"ok","redis":"ok","celery":"ok"}
```

---

## 7. Deploy automático (CI/CD)

O arquivo `.github/workflows/deploy.yml` automatiza o deploy a cada push na branch `main`.

### Fluxo do CI/CD

```
Push → main
  └── Testes (pytest)
  └── Build das imagens Docker
  └── Push para GitHub Container Registry (ghcr.io)
  └── SSH no VPS como deploy
      └── docker compose pull
      └── docker compose up -d --no-deps --build
      └── alembic upgrade head
      └── caddy reload
```

### Estrutura do workflow (criar em `.github/workflows/deploy.yml`)

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r backend/requirements.txt
      - run: cd backend && pytest --tb=short

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy no VPS
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/logia/app
            git pull origin main
            docker compose -f docker-compose.prod.yml pull
            docker compose -f docker-compose.prod.yml up -d --remove-orphans
            docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
            docker image prune -f
```

---

## 8. Verificar saúde do sistema

```bash
# Todos os containers rodando
docker compose -f docker-compose.prod.yml ps

# Health check completo
curl https://app.logia.com.br/health | jq .

# Logs em tempo real
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f worker

# Uso de recursos
docker stats --no-stream

# SSL — verificar validade do certificado
echo | openssl s_client -connect app.logia.com.br:443 2>/dev/null | openssl x509 -noout -dates

# Logs do Caddy
sudo tail -f /var/log/caddy/access.log | jq .
```

---

## 9. Operações de manutenção

### Atualizar variáveis de ambiente

```bash
# Editar no servidor
nano /opt/logia/.env

# Reiniciar serviços afetados
docker compose -f docker-compose.prod.yml up -d backend worker beat
```

### Backup do banco de dados

```bash
# Dump completo
docker compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U logia logia_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar
docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U logia logia_prod < backup_20260307_120000.sql
```

### Limpar espaço em disco

```bash
# Imagens Docker não utilizadas
docker image prune -f

# Volumes e containers parados
docker system prune -f

# Logs antigos do Caddy (já configurado para rotacionar automaticamente)
ls -lh /var/log/caddy/
```

### Verificar uso de disco

```bash
df -h
du -sh /opt/logia/*
docker system df
```

---

## 10. Rollback

### Rollback rápido (voltar para o commit anterior)

```bash
cd /opt/logia/app
git log --oneline -5   # identificar o commit alvo
git checkout HASH_DO_COMMIT

docker compose -f docker-compose.prod.yml up -d --build
```

### Rollback do banco de dados

```bash
# Listar migrations aplicadas
docker compose -f docker-compose.prod.yml exec backend \
  alembic history --verbose

# Reverter uma migration
docker compose -f docker-compose.prod.yml exec backend \
  alembic downgrade -1

# Reverter para revision específica
docker compose -f docker-compose.prod.yml exec backend \
  alembic downgrade REVISION_ID
```

---

## 11. Troubleshooting

### Caddy não obtém certificado SSL

```bash
# Verificar se porta 80 está acessível externamente
curl http://app.logia.com.br

# Verificar logs do Caddy
sudo journalctl -u caddy -n 50 --no-pager

# Testar configuração
sudo caddy validate --config /etc/caddy/Caddyfile

# Forçar renovação (use com cautela — limite de 5 falhas/hora no Let's Encrypt)
sudo caddy reload --config /etc/caddy/Caddyfile
```

### Container backend não sobe

```bash
docker compose -f docker-compose.prod.yml logs backend

# Erros comuns:
# "password authentication failed" → checar DATABASE_URL no .env
# "Connection refused redis" → verificar se redis está healthy
# "Module not found" → rebuild da imagem necessário
docker compose -f docker-compose.prod.yml up -d --build backend
```

### WebSocket desconectando

```bash
# Verificar se o header Upgrade está sendo passado pelo Caddy
curl -v --http1.1 \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  https://app.logia.com.br/ws/test

# O Caddyfile já configura os headers Upgrade/Connection corretamente
```

### Banco de dados cheio

```bash
# Verificar tamanho das tabelas
docker compose -f docker-compose.prod.yml exec postgres psql -U logia logia_prod -c "
  SELECT schemaname, tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
  FROM pg_tables
  WHERE schemaname = 'public'
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

### Memória esgotando

```bash
# Verificar uso por container
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Checar se swap está sendo usado
free -h
swapon --show

# Reiniciar worker se vazar memória
docker compose -f docker-compose.prod.yml restart worker
```

---

## 12. Monitoramento e Alertas (Sentry)

### 12.1 Criar projetos no Sentry

1. Acesse [sentry.io](https://sentry.io) → New Project
2. Criar **dois** projetos separados:
   - `logia-backend` → plataforma **FastAPI**
   - `logia-frontend` → plataforma **React**
3. Copiar o DSN de cada projeto para os respectivos secrets no GitHub e no `.env.production`

| Secret | Projeto Sentry |
|--------|---------------|
| `SENTRY_DSN` | logia-backend |
| `VITE_SENTRY_DSN` | logia-frontend |

### 12.2 Configurar alertas (Sentry → Alerts → Create Alert)

#### Error Rate > 5% em 5 minutos
```
Tipo:        Error
Condição:    Percentage of sessions with errors > 5%
Janela:      5 minutos
Destino:     Email do time + Slack (se configurado)
```

#### P95 Response Time > 2s
```
Tipo:        Performance
Métrica:     p95(transaction.duration)
Condição:    > 2000 ms
Janela:      10 minutos
Filtro:      transaction não contém "/health"
Destino:     Email do time
```

#### Celery queue > 100 tasks pendentes
```
Tipo:        Metric Alert
Métrica:     Custom — via Sentry Crons ou via /health endpoint monitorado externamente
Alternativa: Configurar UptimeRobot para alertar se /health retornar
             celery.queue_copy > 100 ou celery.queue_art > 100
Nota:        Sentry não monitora métricas custom diretamente sem SDK de métricas.
             Para monitoramento de filas, usar Grafana + Prometheus (ver seção 12.4)
             ou alert via script cron que lê o /health endpoint.
```

#### Publicação falhou 3x seguidas
```
Tipo:        Error
Filtro:      tags[publisher.error] exists
Condição:    count() > 3 em 1 hora
Destino:     Email do time
Nota:        Requer instrumentação nos publishers (ver 12.3)
```

### 12.3 Instrumentar publishers com Sentry

Adicionar nos publishers (`email.py`, `instagram.py`, etc.) quando ocorrer falha:

```python
import sentry_sdk

def publish_post(post_id: str, channel: str) -> None:
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("publisher.channel", channel)
        scope.set_context("post", {"id": post_id})
        try:
            # ... lógica de publicação
            pass
        except Exception as exc:
            scope.set_tag("publisher.error", "true")
            sentry_sdk.capture_exception(exc)
            raise
```

### 12.4 Testar integração (disparo intencional)

```bash
# Backend — disparar erro de teste via endpoint temporário
# Adicionar em app/main.py APENAS em dev, remover antes de commitar:
@app.get("/sentry-debug")
async def sentry_debug():
    1 / 0  # ZeroDivisionError — aparece no Sentry em ~30s

# Chamar:
curl http://localhost:8000/sentry-debug

# Frontend — disparar erro de teste no console:
# Sentry.captureMessage("Teste de integração frontend", "info")
```

```bash
# Verificar logs estruturados JSON (produção)
docker compose -f docker-compose.prod.yml logs backend | head -20 | python3 -m json.tool

# Verificar health expandido
curl -s https://app.logia.com.br/health | python3 -m json.tool
```

### 12.5 GitHub Secret adicional para Sentry

| Secret | Valor |
|--------|-------|
| `SENTRY_DSN` | DSN do projeto logia-backend |
| `VITE_SENTRY_DSN` | DSN do projeto logia-frontend |

Adicionar também no workflow de deploy o `VITE_BUILD_SHA` como build-arg do frontend:
```yaml
# Em deploy.yml — build frontend
build-args: |
  VITE_API_URL=https://app.logia.com.br
  VITE_WS_URL=wss://app.logia.com.br
  VITE_BUILD_SHA=${{ github.event.workflow_run.head_sha }}
  VITE_ENVIRONMENT=production
  VITE_SENTRY_DSN=${{ secrets.VITE_SENTRY_DSN }}
```

### 12.6 Gravar timestamp de cada deploy no VPS

O endpoint `/health` retorna `last_deploy` lido de `/app/.deploy_ts`.
O script SSH do deploy.yml deve gravar esse arquivo:

```bash
# Adicionar no bloco SSH do deploy.yml, antes do docker image prune:
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" | \
  docker compose -f docker-compose.prod.yml exec -T backend \
  tee /app/.deploy_ts
```
