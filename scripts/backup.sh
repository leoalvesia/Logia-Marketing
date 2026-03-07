#!/bin/bash
# =============================================================================
# Logia Marketing Platform — Backup automático diário
# Executar como usuário deploy no VPS
# Cron: 0 3 * * * /opt/logia/app/scripts/backup.sh >> /var/log/logia-backup.log 2>&1
# =============================================================================
set -euo pipefail

# ── Configurações ─────────────────────────────────────────────────────────────
BACKUP_DIR="/home/deploy/backups"
APP_DIR="/opt/logia/app"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30
COMPOSE_FILE="$APP_DIR/docker-compose.prod.yml"

# Carregar variáveis de ambiente (para SLACK_WEBHOOK, se configurado)
# shellcheck source=/dev/null
[ -f "$APP_DIR/.env" ] && source <(grep -E '^(SLACK_WEBHOOK)=' "$APP_DIR/.env")
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"

# ── Helpers ───────────────────────────────────────────────────────────────────
log() { echo "[$(date '+%Y-%m-%dT%H:%M:%SZ')] $*"; }

notify_failure() {
    local msg="$1"
    log "ERRO: $msg"
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -sf -X POST "$SLACK_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"Backup Logia FALHOU: $msg — $(date '+%Y-%m-%d %H:%M UTC')\"}" \
            || true
    fi
}

# ── Setup ─────────────────────────────────────────────────────────────────────
mkdir -p "$BACKUP_DIR"
log "==> Iniciando backup $DATE"

# ── 1. Dump PostgreSQL ────────────────────────────────────────────────────────
DB_FILE="$BACKUP_DIR/db_${DATE}.sql.gz"
log "Fazendo dump do PostgreSQL..."

if ! docker compose -f "$COMPOSE_FILE" exec -T postgres \
        pg_dump -U logia logia_prod \
        | gzip > "$DB_FILE"; then
    notify_failure "pg_dump falhou"
    exit 1
fi

DB_SIZE=$(du -sh "$DB_FILE" | cut -f1)
log "Dump OK: $DB_FILE ($DB_SIZE)"

# ── 2. Backup dos arquivos de configuração (excl. segredos) ──────────────────
CONFIG_FILE="$BACKUP_DIR/config_${DATE}.tar.gz"
log "Fazendo backup de configurações..."
tar -czf "$CONFIG_FILE" \
    -C "$APP_DIR" \
    --exclude=".env" \
    --exclude="*.pyc" \
    --exclude="__pycache__" \
    --exclude="node_modules" \
    docker-compose.prod.yml \
    config/Caddyfile \
    backend/alembic/versions/ \
    2>/dev/null || true  # não falhar se algum arquivo não existir
log "Config backup OK: $CONFIG_FILE"

# ── 3. Upload para Google Drive (via rclone) ──────────────────────────────────
# Pré-requisito: instalar rclone e configurar remote "gdrive" apontando para
# a pasta de backup do Drive.
#   curl https://rclone.org/install.sh | sudo bash
#   rclone config  (criar remote "gdrive" do tipo "drive")
#
if command -v rclone &>/dev/null; then
    log "Enviando backup para Google Drive..."
    if rclone copy "$BACKUP_DIR" gdrive:logia-backups/ \
            --include "*.gz" \
            --min-age 0 \
            --log-level INFO \
            2>&1; then
        log "Upload Google Drive OK"
    else
        # Upload falhou — backup local ainda existe, não é crítico
        log "AVISO: upload para Google Drive falhou (backup local preservado)"
    fi
else
    log "AVISO: rclone não instalado — backup apenas local (ver README para configurar)"
fi

# ── 4. Limpeza: remover backups locais mais antigos que 30 dias ───────────────
log "Removendo backups com mais de $RETENTION_DAYS dias..."
DELETED=$(find "$BACKUP_DIR" -name "*.gz" -mtime "+$RETENTION_DAYS" -print -delete | wc -l)
log "Removidos: $DELETED arquivo(s)"

# ── 5. Verificar integridade do dump ─────────────────────────────────────────
log "Verificando integridade do dump..."
if ! gzip -t "$DB_FILE"; then
    notify_failure "dump corrompido: $DB_FILE"
    exit 1
fi
log "Integridade OK"

# ── 6. Relatório final ────────────────────────────────────────────────────────
TOTAL_BACKUPS=$(find "$BACKUP_DIR" -name "db_*.gz" | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "==> Backup concluido: $TOTAL_BACKUPS backups locais, $TOTAL_SIZE total"
