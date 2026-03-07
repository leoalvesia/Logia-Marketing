# Production Readiness Checklist — Logia Marketing Platform

Execute cada item em ordem. Marque [x] ao confirmar.

---

## 1. Docker — Todos os containers saudáveis

### 1.1 Pré-deploy: variáveis obrigatórias

```bash
# No VPS como deploy
cd /opt/logia/app

# Verificar que .env existe e tem as variáveis críticas
grep -E "^(SECRET_KEY|DATABASE_URL|ENCRYPTION_KEY|SENTRY_DSN|ANTHROPIC_API_KEY)=" .env
# Esperado: 5 linhas com valores reais (não PLACEHOLDER_*)
```

- [ ] Todas as 5 variáveis têm valores reais

### 1.2 Subir os serviços

```bash
docker compose -f docker-compose.prod.yml up -d
```

Aguardar ~60 segundos para health checks completarem.

### 1.3 Verificar status

```bash
docker compose -f docker-compose.prod.yml ps
```

Saída esperada (todos `healthy`):
```
NAME                STATUS              PORTS
logia-backend       running (healthy)   8000/tcp
logia-worker        running             -
logia-beat          running             -
logia-frontend      running (healthy)   80/tcp
logia-redis         running (healthy)   -
logia-postgres      running (healthy)   -
```

- [ ] Todos os containers no status `running`
- [ ] backend, frontend, redis, postgres mostram `(healthy)`

### 1.4 Health check via HTTP local

```bash
# Via Caddy (porta 80)
curl -s http://localhost/health | python3 -m json.tool
```

Saída esperada:
```json
{
  "status": "healthy",
  "version": "abc1234",
  "uptime_seconds": 42,
  "database": {
    "status": "ok",
    "pool_size": 5,
    "checked_out": 1,
    "overflow": 0,
    "query_time_ms": 2.1
  },
  "redis": {
    "status": "ok",
    "memory_mb": 4.2
  },
  "celery": {
    "status": "ok",
    "workers_online": 1,
    "queue_copy": 0,
    "queue_art": 0,
    "queue_research": 0
  },
  "last_deploy": "2026-03-07T10:00:00Z"
}
```

- [ ] `status: healthy`
- [ ] `database.status: ok`
- [ ] `redis.status: ok`
- [ ] `celery.workers_online >= 1`

### 1.5 Verificar logs de startup

```bash
docker compose -f docker-compose.prod.yml logs backend --tail=20
```

Deve conter (JSON em produção):
```json
{"event": "startup", "version": "abc1234", "environment": "production", ...}
```

- [ ] Nenhum `ERROR` ou `CRITICAL` nos logs
- [ ] Log `startup` presente com `environment: production`

---

## 2. SSL — HTTPS funcionando (após DNS propagado)

### 2.1 Verificar propagação DNS

```bash
dig app.logia.com.br +short
# Deve retornar o IP do VPS
```

- [ ] DNS propagado — IP correto retornado

### 2.2 Health check via HTTPS

```bash
curl -s https://app.logia.com.br/health | python3 -m json.tool
```

- [ ] Resposta 200 via HTTPS sem erro de certificado

### 2.3 Verificar certificado

```bash
# Validade do certificado
echo | openssl s_client -connect app.logia.com.br:443 2>/dev/null \
  | openssl x509 -noout -issuer -dates

# Esperado: issuer = Let's Encrypt, notAfter = ~90 dias no futuro
```

- [ ] Emissor: Let's Encrypt
- [ ] Validade: > 60 dias

### 2.4 Verificar headers de segurança

```bash
curl -si https://app.logia.com.br/health | grep -E "(Strict-Transport|X-Frame|X-Content|Content-Security)"
```

Saída esperada:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Content-Security-Policy: default-src 'none'; ...
```

- [ ] HSTS presente
- [ ] X-Frame-Options: DENY
- [ ] X-Content-Type-Options: nosniff

### 2.5 SSL Labs (opcional mas recomendado)

Acessar: `https://www.ssllabs.com/ssltest/analyze.html?d=app.logia.com.br`

- [ ] Grade A (ou A+)

---

## 3. CI/CD — Deploy automático funcionando

### 3.1 Push de mudança de teste

Na sua máquina local:
```bash
cd /caminho/para/logia-marketing
echo "# deploy test $(date)" >> README.md
git add README.md
git commit -m "chore: production readiness test deploy"
git push origin main
```

### 3.2 Acompanhar CI no GitHub Actions

- Acessar: `https://github.com/SEU_ORG/logia-marketing/actions`
- Aguardar workflow **CI** completar (jobs em paralelo: lint, test-backend, test-frontend, security)

- [ ] Job `lint` verde
- [ ] Job `test-backend` verde (cobertura >= 70%)
- [ ] Job `test-frontend` verde (build OK, bundle < 250 KB)
- [ ] Job `security` verde (bandit + npm audit OK)

### 3.3 Acompanhar CD no GitHub Actions

Após CI verde, workflow **Deploy** dispara automaticamente:
- Build imagens Docker → push para GHCR
- Deploy via SSH no VPS
- Health check pós-deploy

- [ ] Workflow `Deploy` completo com sucesso
- [ ] Step `Health check` retornou status `ok`

### 3.4 Verificar nova versão no servidor

```bash
curl -s https://app.logia.com.br/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['version'])"
# Deve retornar o SHA do commit recém-deployado (primeiros 7 chars)
```

- [ ] SHA do health check bate com o `git rev-parse --short HEAD` do commit

### 3.5 Verificar last_deploy

```bash
curl -s https://app.logia.com.br/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['last_deploy'])"
# Deve ser o timestamp do deploy recém-executado (UTC, dentro dos últimos 10 min)
```

- [ ] `last_deploy` atualizado corretamente

---

## 4. Monitoramento — Sentry funcionando

### 4.1 Verificar integração (erro intencional via endpoint de debug)

> Atenção: este endpoint só existe em desenvolvimento. Em produção, `/docs` está desabilitado.
> Para testar em produção, temporariamente adicionar o endpoint, deployar, testar, remover.

Alternativa segura — provocar erro via log direto:
```bash
# No VPS — forçar exceção no worker para ver no Sentry
docker compose -f docker-compose.prod.yml exec backend \
  python3 -c "
import sentry_sdk
sentry_sdk.init(dsn='$(grep SENTRY_DSN .env | cut -d= -f2)')
sentry_sdk.capture_message('Production readiness test', level='info')
print('Mensagem enviada ao Sentry')
"
```

- [ ] Mensagem aparece no Sentry em < 60 segundos

### 4.2 Verificar logs estruturados JSON

```bash
# No VPS
docker compose -f docker-compose.prod.yml logs backend --tail=5 \
  | python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if line.startswith('{'):
        d = json.loads(line)
        print(json.dumps(d, indent=2, ensure_ascii=False))
        break
"
```

Saída esperada (campos obrigatórios presentes):
```json
{
  "event": "...",
  "level": "info",
  "service": "logia-backend",
  "environment": "production",
  "timestamp": "2026-03-07T10:00:00.000000Z",
  "request_id": "uuid-aqui"
}
```

- [ ] Logs em formato JSON
- [ ] Campo `service: logia-backend` presente
- [ ] Campo `environment: production` presente
- [ ] Campo `request_id` presente

### 4.3 Verificar X-Request-ID nas respostas

```bash
curl -si https://app.logia.com.br/health | grep X-Request-ID
# X-Request-ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

- [ ] Header `X-Request-ID` presente em todas as respostas

### 4.4 Verificar alertas configurados no Sentry

Acessar Sentry → Alerts → verificar que existem regras para:

- [ ] Error rate > 5% em 5 minutos → email
- [ ] P95 > 2s em 10 minutos → email
- [ ] Issue criada automaticamente em falha de deploy (via GitHub Script)

---

## 5. Backup — Funcionando e testado

### 5.1 Executar backup manualmente

```bash
# No VPS como deploy
bash /opt/logia/app/scripts/backup.sh
```

Saída esperada:
```
[2026-03-07T03:00:00Z] ==> Iniciando backup 20260307_030000
[2026-03-07T03:00:01Z] Fazendo dump do PostgreSQL...
[2026-03-07T03:00:05Z] Dump OK: /home/deploy/backups/db_20260307_030000.sql.gz (1.2M)
[2026-03-07T03:00:05Z] Fazendo backup de configurações...
[2026-03-07T03:00:05Z] Config backup OK: /home/deploy/backups/config_20260307_030000.tar.gz
[2026-03-07T03:00:06Z] Verificando integridade do dump...
[2026-03-07T03:00:06Z] Integridade OK
[2026-03-07T03:00:06Z] ==> Backup concluido: 1 backups locais, 1.5M total
```

- [ ] Script executa sem erros
- [ ] Arquivo `.sql.gz` gerado em `/home/deploy/backups/`
- [ ] `gzip -t` passa (integridade OK)

### 5.2 Simular restore (teste de recuperação)

```bash
# No VPS — restaurar para banco de teste
BACKUP_FILE=$(ls /home/deploy/backups/db_*.sql.gz | tail -1)

# Criar banco de teste
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U logia -c "CREATE DATABASE logia_restore_test;"

# Restaurar
gunzip -c "$BACKUP_FILE" | \
  docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U logia -d logia_restore_test

# Verificar tabelas restauradas
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U logia -d logia_restore_test -c "\dt"

# Limpar banco de teste
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U logia -c "DROP DATABASE logia_restore_test;"
```

- [ ] Restore sem erros
- [ ] Tabelas listadas (`\dt`) batem com o banco de produção
- [ ] Banco de teste removido após verificação

### 5.3 Configurar cron automático

```bash
# No VPS como deploy
crontab -e
```

Adicionar:
```cron
# Backup diário às 3h UTC
0 3 * * * /opt/logia/app/scripts/backup.sh >> /var/log/logia-backup.log 2>&1
```

```bash
# Verificar que o cron está registrado
crontab -l | grep backup
```

- [ ] Cron configurado e visível em `crontab -l`

### 5.4 Verificar log de backup após primeiro cron

```bash
# Após a primeira execução automática (verificar no dia seguinte)
cat /var/log/logia-backup.log | tail -20
```

- [ ] Log presente sem erros após primeira execução automática

---

## 6. Rate Limiting — Verificar proteções ativas

### 6.1 Teste de brute-force no login

```bash
# 6 tentativas em sequência devem retornar 429 na 6ª
for i in $(seq 1 7); do
  STATUS=$(curl -so /dev/null -w "%{http_code}" \
    -X POST https://app.logia.com.br/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}')
  echo "Tentativa $i: HTTP $STATUS"
  sleep 1
done
```

Saída esperada:
```
Tentativa 1: HTTP 401
Tentativa 2: HTTP 401
Tentativa 3: HTTP 401
Tentativa 4: HTTP 401
Tentativa 5: HTTP 401
Tentativa 6: HTTP 429   ← rate limit ativado
Tentativa 7: HTTP 429
```

- [ ] 429 ativo após 5 tentativas por minuto
- [ ] Header `Retry-After` presente na resposta 429

---

## Resultado Final

Após todos os itens marcados:

```
[x] 1. Docker — todos os containers healthy
[x] 2. SSL — HTTPS com grade A + headers de segurança
[x] 3. CI/CD — deploy automático e verificação de versão OK
[x] 4. Monitoramento — Sentry recebendo eventos, logs JSON OK
[x] 5. Backup — executado, restaurado, cron configurado
[x] 6. Rate limiting — brute-force protegido
```

**STATUS: PRODUCTION READY**

---

## Quick Reference — Comandos de emergência

```bash
# Ver status geral
docker compose -f docker-compose.prod.yml ps

# Logs em tempo real
docker compose -f docker-compose.prod.yml logs -f backend

# Reiniciar serviço específico
docker compose -f docker-compose.prod.yml restart backend

# Rollback imediato (via GitHub Actions — recomendado)
# Actions → Rollback → workflow_dispatch → informar SHA + motivo

# Rollback manual de emergência
cd /opt/logia/app
IMAGE_TAG=SHA_ANTIGO docker compose -f docker-compose.prod.yml up -d --no-build

# Health check completo
curl -s https://app.logia.com.br/health | python3 -m json.tool

# Backup imediato
bash /opt/logia/app/scripts/backup.sh
```
