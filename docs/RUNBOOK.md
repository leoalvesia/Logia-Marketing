# RUNBOOK — Logia Marketing Platform

Guia de resposta a incidentes. Cada seção descreve diagnóstico e correção passo a passo.

> **Severidades**
> - P1 — Produção fora do ar (todo o sistema inoperante)
> - P2 — Feature crítica falhando (publicação, pipeline IA)
> - P3 — Degradação de performance / funcionalidade secundária

---

## Incidente 1 — Backend não responde (HTTP 502 / 503)

**Severidade:** P1
**Sintoma:** Usuários vêem "502 Bad Gateway" ou o frontend não carrega dados.

### Diagnóstico

```bash
# 1. Acessar o servidor
ssh deploy@$VPS_IP

# 2. Verificar estado dos containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
# Esperado: logia-backend Up X minutes

# 3. Ver últimos erros do backend
docker logs logia-backend --tail=50 2>&1 | grep -E "ERROR|CRITICAL|Exception"

# 4. Verificar uso de recursos
docker stats --no-stream logia-backend logia-worker

# 5. Testar health check interno (na rede Docker)
docker exec logia-backend curl -sf http://localhost:8000/health | python3 -m json.tool
```

### Correção

**Se o container está `Exited` (crash):**
```bash
# Ver motivo do crash
docker logs logia-backend --tail=100

# Reiniciar
cd /opt/logia/app
docker compose -f docker-compose.prod.yml restart backend

# Confirmar recuperação
curl -sf https://app.logia.com.br/health | python3 -m json.tool
```

**Se o container está `Up` mas não responde:**
```bash
# Força reinício
docker compose -f docker-compose.prod.yml stop backend
docker compose -f docker-compose.prod.yml up -d backend

# Aguardar 10s e testar
sleep 10 && curl -sf https://app.logia.com.br/health
```

**Se o problema persistir — rollback:**
```bash
# Disparar workflow de rollback no GitHub Actions
# (gh CLI ou Interface Web: Actions → Rollback → Run workflow)
gh workflow run rollback.yml
```

### Prevenção
- `restart: always` já configurado no `docker-compose.prod.yml`
- Health check no nginx detecta falha e para de rotear após 3 falhas consecutivas

---

## Incidente 2 — Publicação no Instagram falhando

**Severidade:** P2
**Sintoma:** Posts não são publicados; worker loga erro `190` (token inválido) ou `200` (permissão).

### Diagnóstico

```bash
# 1. Ver erros do worker com filtro instagram
ssh deploy@$VPS_IP
docker logs logia-worker --tail=100 2>&1 | grep -i instagram

# Mensagens comuns:
#   "Error code: 190" → token expirado
#   "Error code: 200" → permissão insuficiente
#   "Error code: 32"  → token de página inválido

# 2. Verificar validade do token atual via Graph API
curl -s "https://graph.facebook.com/me?access_token=${META_ACCESS_TOKEN}" | python3 -m json.tool
# Se retornar "error" → token expirado
```

### Correção

**Token expirado (código 190):**
```bash
# 1. Gerar novo Long-Lived Token (90 dias) no Meta Developer Console:
#    https://developers.facebook.com/tools/explorer/
#    Permissões: instagram_basic, instagram_content_publish, pages_read_engagement

# 2. Atualizar o .env de produção no servidor
ssh deploy@$VPS_IP
cd /opt/logia/app
nano .env.production
# Atualizar: META_ACCESS_TOKEN=novo_token_aqui

# 3. Reiniciar apenas backend e worker (sem rebuild)
docker compose -f docker-compose.prod.yml up -d --no-deps --no-build backend worker

# 4. Confirmar que worker reconectou
docker logs logia-worker --tail=20
```

**Limite de rate da API do Instagram atingido:**
```bash
# Aguardar 1h (limite é por hora) e tentar novamente
# As tasks ficam na fila — não é necessário resubmeter manualmente
docker exec logia-redis redis-cli llen copy  # checar fila
```

### Prevenção
- Configurar alerta no Meta Developer Console para expiração de token (60 dias antes)
- Adicionar job Celery mensal para verificar validade do token

---

## Incidente 3 — Celery queue acumulando (> 50 tasks pendentes)

**Severidade:** P2
**Sintoma:** Pipeline de IA demora minutos para responder; fila cresce indefinidamente.

### Diagnóstico

```bash
ssh deploy@$VPS_IP

# 1. Checar tamanho das filas
docker exec logia-redis redis-cli llen copy      # tasks de copy (IA)
docker exec logia-redis redis-cli llen art       # tasks de arte
docker exec logia-redis redis-cli llen research  # tasks de pesquisa
docker exec logia-redis redis-cli llen celery    # fila padrão

# 2. Verificar workers ativos
docker exec logia-worker celery -A app.celery_app inspect active

# 3. Ver se workers estão travados
docker stats --no-stream logia-worker
docker logs logia-worker --tail=50
```

### Correção

**Workers lentos — escalar horizontalmente:**
```bash
cd /opt/logia/app

# Escalar para 3 workers (ajustar conforme CPU disponível)
docker compose -f docker-compose.prod.yml \
  up -d --no-deps --scale worker=3 worker

# Verificar
docker compose -f docker-compose.prod.yml ps worker
```

**Worker travado em uma task (sem progresso por > 5 min):**
```bash
# Ver task travada
docker exec logia-worker celery -A app.celery_app inspect active

# Revogar task específica (substituir TASK_ID)
docker exec logia-worker celery -A app.celery_app control revoke TASK_ID --terminate

# Reiniciar worker
docker compose -f docker-compose.prod.yml restart worker
```

**Fila com lixo acumulado (ex: tasks de ambiente antigo):**
```bash
# CUIDADO: isso descarta todas as tasks pendentes
# Confirmar antes de executar
docker exec logia-redis redis-cli del copy art research celery
docker compose -f docker-compose.prod.yml restart worker
```

### Prevenção
- `CLAUDE.md` define `soft_time_limit=55s` para copy tasks — nunca travam indefinidamente
- Monitorar `GET /health` → campo `celery.queue_copy` para alertas automáticos

---

## Incidente 4 — Banco de dados lento ou disco cheio

**Severidade:** P1 (disco cheio) / P2 (queries lentas)
**Sintoma:** Requisições com timeout; erros `DiskFull` ou `too many connections`.

### Diagnóstico

```bash
ssh deploy@$VPS_IP

# 1. Checar uso de disco
df -h | grep -E "/$|/var|/opt"
du -sh /var/lib/docker/volumes/logia_postgres_data

# 2. Ver conexões ativas no PostgreSQL
docker exec logia-postgres psql -U logia -c \
  "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# 3. Queries lentas (rodando há mais de 30s)
docker exec logia-postgres psql -U logia -c \
  "SELECT pid, now() - query_start AS duration, query
   FROM pg_stat_activity
   WHERE state = 'active' AND now() - query_start > interval '30 seconds'
   ORDER BY duration DESC;"

# 4. Tamanho das tabelas
docker exec logia-postgres psql -U logia -logia -c \
  "SELECT relname AS table, pg_size_pretty(pg_total_relation_size(relid)) AS size
   FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 10;"
```

### Correção

**Disco cheio:**
```bash
# Limpar logs antigos do Docker (CUIDADO: remove logs de todos os containers)
docker system prune --volumes -f

# Limpar imagens antigas (mantém as em uso)
docker image prune -a -f

# Verificar espaço recuperado
df -h /
```

**Queries lentas / conexões acumuladas:**
```bash
# Matar queries travadas (substituir PID)
docker exec logia-postgres psql -U logia -c "SELECT pg_terminate_backend(PID);"

# Reiniciar conexões do pool (sem downtime)
docker compose -f docker-compose.prod.yml restart backend
```

**Crescimento anormal da tabela `bug_reports` (screenshots base64):**
```bash
# Limpar screenshots de bug reports resolvidos com mais de 30 dias
docker exec logia-postgres psql -U logia -logia -c \
  "UPDATE bug_reports SET screenshot_b64 = NULL
   WHERE status = 'resolved'
   AND created_at < now() - interval '30 days'
   AND screenshot_b64 IS NOT NULL;"
```

### Prevenção
- Backup automático configurado em `scripts/backup.sh` (cron diário)
- Screenshot de bug reports truncada em 1.4 MB no backend
- Monitorar disco com alerta em `/health` se < 10% livre

---

## Incidente 5 — VPS sem memória (OOM / processo morto pelo kernel)

**Severidade:** P1
**Sintoma:** Containers reiniciam sozinhos; `docker logs` mostra `Killed`; `dmesg` mostra `oom-kill`.

### Diagnóstico

```bash
ssh deploy@$VPS_IP

# 1. Confirmar OOM no histórico do kernel
dmesg | grep -i "oom\|killed" | tail -20

# 2. Uso atual de memória por container
docker stats --no-stream --format \
  "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"

# 3. Memória total do host
free -h

# 4. Swap disponível
swapon --show
```

### Correção

**Recuperação imediata:**
```bash
cd /opt/logia/app

# Reiniciar containers que caíram (restart:always já faz isso)
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml up -d

# Reduzir workers se estiver sobrecarregado
docker compose -f docker-compose.prod.yml \
  up -d --no-deps --scale worker=1 worker
```

**Se não houver swap configurado:**
```bash
# Criar swap de 2GB (operação segura, não requer reinício)
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# Persistir no fstab
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Confirmar
free -h
```

**Liberação de memória rápida:**
```bash
# Parar beat scheduler (usa ~128 MB e não é crítico por horas)
docker compose -f docker-compose.prod.yml stop beat

# Limpar cache do kernel (seguro — não perde dados)
sync && echo 3 > /proc/sys/vm/drop_caches
```

### Prevenção
- `docker-compose.prod.yml` define `mem_limit` por serviço (ver CLAUDE.md)
- Worker Celery tem `--max-tasks-per-child=50` para evitar memory leak
- Adicionar swap de 2GB na configuração inicial do servidor (`scripts/setup-server.sh`)

---

## Scripts Utilitários Rápidos

```bash
# Reiniciar tudo
cd /opt/logia/app && docker compose -f docker-compose.prod.yml restart

# Ver logs em tempo real (todos os serviços)
docker compose -f docker-compose.prod.yml logs -f --tail=50

# Só backend + worker
docker compose -f docker-compose.prod.yml logs -f --tail=50 backend worker

# Tamanho das filas (resumo)
for q in copy art research celery; do
  echo "${q}: $(docker exec logia-redis redis-cli llen $q) tasks"
done

# Snapshot completo do sistema
bash /opt/logia/app/scripts/diagnose.sh
```

---

## Contatos de Escalada

| Situação | Ação |
|----------|------|
| P1 sem resolução em 15 min | Acionar rollback via `rollback.yml` |
| Banco corrompido | Restaurar último backup (`scripts/backup.sh restore`) |
| Acesso SSH perdido | Acessar via console web do provedor de VPS |
| Meta API suspensa | Verificar status em `developers.facebook.com/status` |
