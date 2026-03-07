#!/bin/bash
# diagnose.sh — snapshot do estado do sistema Logia em producao
# Uso: bash /opt/logia/app/scripts/diagnose.sh
# Saida: texto formatado para copiar em relatório de incidente

set -euo pipefail

HEALTH_URL="${HEALTH_URL:-https://app.logia.com.br/health}"
REDIS_CONTAINER="${REDIS_CONTAINER:-logia-redis}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-logia-postgres}"
BACKEND_CONTAINER="${BACKEND_CONTAINER:-logia-backend}"
WORKER_CONTAINER="${WORKER_CONTAINER:-logia-worker}"

echo "================================================================"
echo " LOGIA — DIAGNOSTICO DO SISTEMA"
echo " $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "================================================================"
echo ""

# ── Containers ───────────────────────────────────────────────────
echo "=== CONTAINERS ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.RunningFor}}\t{{.Ports}}" 2>/dev/null || \
  echo "ERRO: docker nao acessivel"
echo ""

# ── Health Check ─────────────────────────────────────────────────
echo "=== HEALTH CHECK ==="
if curl -sf --max-time 10 "${HEALTH_URL}" -o /tmp/health.json 2>/dev/null; then
  python3 -m json.tool /tmp/health.json
else
  echo "FALHA: ${HEALTH_URL} nao respondeu"
fi
echo ""

# ── Celery Queues ────────────────────────────────────────────────
echo "=== CELERY QUEUES ==="
for queue in copy art research celery; do
  count=$(docker exec "${REDIS_CONTAINER}" redis-cli llen "${queue}" 2>/dev/null || echo "ERR")
  echo "  ${queue}: ${count} tasks"
done
echo ""

# ── Uso de Memória por Container ─────────────────────────────────
echo "=== MEMORIA POR CONTAINER ==="
docker stats --no-stream --format \
  "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.CPUPerc}}" 2>/dev/null || \
  echo "ERRO ao obter stats"
echo ""

# ── Disco ────────────────────────────────────────────────────────
echo "=== DISCO ==="
df -h | grep -E "Filesystem|/$|/opt|/var|/home" || df -h
echo ""

# Tamanho dos volumes Docker
echo "--- Volumes Docker ---"
docker system df 2>/dev/null || echo "N/A"
echo ""

# ── Últimos Erros do Backend ─────────────────────────────────────
echo "=== ULTIMOS 10 ERROS — BACKEND ==="
docker logs "${BACKEND_CONTAINER}" --tail=200 2>&1 | \
  grep -E "ERROR|CRITICAL|Exception|Traceback" | \
  tail -10 || echo "(nenhum erro recente)"
echo ""

# ── Últimos Erros do Worker ──────────────────────────────────────
echo "=== ULTIMOS 10 ERROS — WORKER ==="
docker logs "${WORKER_CONTAINER}" --tail=200 2>&1 | \
  grep -E "ERROR|CRITICAL|Exception|Traceback" | \
  tail -10 || echo "(nenhum erro recente)"
echo ""

# ── PostgreSQL ───────────────────────────────────────────────────
echo "=== DB — CONEXOES ATIVAS ==="
docker exec "${POSTGRES_CONTAINER}" psql -U logia -logia -c \
  "SELECT state, count(*) FROM pg_stat_activity GROUP BY state ORDER BY count DESC;" \
  2>/dev/null || echo "ERRO ao conectar no postgres"
echo ""

echo "=== DB — QUERIES LONGAS (> 10s) ==="
docker exec "${POSTGRES_CONTAINER}" psql -U logia -logia -c \
  "SELECT pid,
          round(extract(epoch from now() - query_start)) AS seconds,
          left(query, 80) AS query_preview
   FROM pg_stat_activity
   WHERE state = 'active'
     AND now() - query_start > interval '10 seconds'
   ORDER BY seconds DESC
   LIMIT 5;" \
  2>/dev/null || echo "ERRO ou nenhuma query longa"
echo ""

# ── Redis ────────────────────────────────────────────────────────
echo "=== REDIS — MEMORIA ==="
docker exec "${REDIS_CONTAINER}" redis-cli info memory 2>/dev/null | \
  grep -E "used_memory_human|maxmemory_human|mem_fragmentation_ratio" || \
  echo "ERRO ao conectar no redis"
echo ""

# ── OOM / Kernel ─────────────────────────────────────────────────
echo "=== OOM KILLS (ultimas 24h) ==="
dmesg --ctime 2>/dev/null | grep -i "oom\|killed" | tail -10 || \
  journalctl -k --since "24 hours ago" 2>/dev/null | grep -i "oom\|killed" | tail -10 || \
  echo "(nao disponivel ou sem eventos)"
echo ""

# ── Swap ─────────────────────────────────────────────────────────
echo "=== SWAP ==="
free -h
swapon --show 2>/dev/null || echo "(swap nao configurado)"
echo ""

echo "================================================================"
echo " FIM DO DIAGNOSTICO — $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "================================================================"
