#!/bin/bash
# security_audit.sh — auditoria de segurança automatizada pre-deploy
#
# Uso: bash scripts/security_audit.sh
#   ./scripts/security_audit.sh --ci   (modo CI: falha no primeiro HIGH/CRITICAL)
#
# Saida: scripts/security_report.txt
# Exit code: 0 = nenhuma vulnerabilidade HIGH/CRITICAL
#            1 = encontradas vulnerabilidades HIGH/CRITICAL (bloqueia deploy)

set -euo pipefail

REPORT="$(dirname "$0")/security_report.txt"
CI_MODE="${1:-}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAIL=0

# Cores para terminal (sem cor em CI)
if [ -t 1 ] && [ -z "${CI:-}" ]; then
  RED="\033[0;31m"; GREEN="\033[0;32m"; YELLOW="\033[1;33m"; RESET="\033[0m"
else
  RED=""; GREEN=""; YELLOW=""; RESET=""
fi

log_ok()   { echo -e "${GREEN}[OK]${RESET}    $*"; echo "[OK]    $*" >> "$REPORT"; }
log_warn() { echo -e "${YELLOW}[WARN]${RESET}  $*"; echo "[WARN]  $*" >> "$REPORT"; }
log_fail() { echo -e "${RED}[FAIL]${RESET}  $*"; echo "[FAIL]  $*" >> "$REPORT"; FAIL=1; }
log_info() { echo "        $*"; echo "        $*" >> "$REPORT"; }
log_sep()  { echo ""; echo ""; echo "---" >> "$REPORT"; echo "" >> "$REPORT"; }

# Inicializar relatório
mkdir -p "$(dirname "$REPORT")"
cat > "$REPORT" <<EOF
================================================================
 LOGIA — RELATÓRIO DE AUDITORIA DE SEGURANÇA
 $(date -u '+%Y-%m-%dT%H:%M:%SZ')
================================================================

EOF

echo "================================================================"
echo " LOGIA — Auditoria de Segurança"
echo " $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "================================================================"
echo ""

# ── 1. PYTHON: vulnerabilidades em dependências (safety) ──────────────────────
log_sep
echo "=== [1/5] Python Dependencies (safety) ===" | tee -a "$REPORT"
echo ""

if ! command -v safety &>/dev/null; then
  log_warn "safety não encontrado — instalando..."
  pip install safety -q
fi

SAFETY_OUT=$(mktemp)
if safety check -r "$REPO_ROOT/backend/requirements.txt" \
    --output text 2>&1 > "$SAFETY_OUT"; then
  log_ok "Nenhuma vulnerabilidade conhecida em requirements.txt"
else
  EXIT_CODE=$?
  # safety exit 64 = vulnerabilidades encontradas, 1 = outros erros
  if grep -qiE "CRITICAL|HIGH" "$SAFETY_OUT" 2>/dev/null; then
    log_fail "Vulnerabilidades HIGH/CRITICAL em dependências Python!"
    grep -E "CRITICAL|HIGH|->|Vuln" "$SAFETY_OUT" | head -20 | tee -a "$REPORT"
  else
    log_warn "Vulnerabilidades LOW/MEDIUM em dependências Python (não bloqueiam)"
    cat "$SAFETY_OUT" | head -20 | tee -a "$REPORT"
  fi
fi
rm -f "$SAFETY_OUT"

# ── 2. PYTHON: código inseguro (bandit) ──────────────────────────────────────
log_sep
echo "=== [2/5] Python Code Security (bandit -ll) ===" | tee -a "$REPORT"
echo ""

if ! command -v bandit &>/dev/null; then
  log_warn "bandit não encontrado — instalando..."
  pip install bandit -q
fi

BANDIT_OUT=$(mktemp)
# -ll = apenas MEDIUM e HIGH; -x = excluir tests
if bandit -r "$REPO_ROOT/backend/app/" \
    -ll \
    -x "$REPO_ROOT/backend/app/tests" \
    --format text \
    -o "$BANDIT_OUT" 2>&1; then
  log_ok "Nenhum problema MEDIUM/HIGH encontrado pelo bandit"
else
  if grep -qE "Severity: (High|Medium)" "$BANDIT_OUT" 2>/dev/null; then
    HIGH_COUNT=$(grep -c "Severity: High" "$BANDIT_OUT" 2>/dev/null || echo 0)
    MED_COUNT=$(grep -c "Severity: Medium" "$BANDIT_OUT" 2>/dev/null || echo 0)
    if [ "$HIGH_COUNT" -gt 0 ]; then
      log_fail "bandit encontrou $HIGH_COUNT issue(s) HIGH"
    else
      log_warn "bandit encontrou $MED_COUNT issue(s) MEDIUM (não bloqueia)"
    fi
    cat "$BANDIT_OUT" | head -40 | tee -a "$REPORT"
  else
    log_ok "Sem issues significativos (bandit)"
  fi
fi
rm -f "$BANDIT_OUT"

# ── 3. NODE: npm audit ────────────────────────────────────────────────────────
log_sep
echo "=== [3/5] Node.js Dependencies (npm audit) ===" | tee -a "$REPORT"
echo ""

NPM_OUT=$(mktemp)
(cd "$REPO_ROOT/frontend" && npm audit --audit-level=high --omit=dev 2>&1) > "$NPM_OUT" || NPM_RC=$?

if grep -qiE "found 0 vulnerabilities|0 vulnerabilities" "$NPM_OUT"; then
  log_ok "Nenhuma vulnerabilidade HIGH/CRITICAL no frontend (npm audit)"
elif grep -qiE "critical|high" "$NPM_OUT"; then
  log_fail "npm audit encontrou vulnerabilidades HIGH/CRITICAL!"
  grep -E "critical|high|severity" "$NPM_OUT" | head -20 | tee -a "$REPORT"
else
  log_warn "npm audit encontrou problemas LOW/MODERATE (não bloqueiam)"
  head -10 "$NPM_OUT" | tee -a "$REPORT"
fi
rm -f "$NPM_OUT"

# ── 4. NODE: retire.js ────────────────────────────────────────────────────────
log_sep
echo "=== [4/5] Node.js Known Vulnerabilities (retire.js) ===" | tee -a "$REPORT"
echo ""

if ! command -v retire &>/dev/null; then
  log_warn "retire não encontrado — instalando globalmente..."
  npm install -g retire -q
fi

RETIRE_OUT=$(mktemp)
if (cd "$REPO_ROOT/frontend" && retire --path . --outputformat text 2>&1) > "$RETIRE_OUT"; then
  log_ok "Nenhuma vulnerabilidade conhecida (retire.js)"
else
  if grep -qiE "CRITICAL|HIGH" "$RETIRE_OUT"; then
    log_fail "retire.js encontrou vulnerabilidades HIGH/CRITICAL!"
    grep -iE "CRITICAL|HIGH|severity" "$RETIRE_OUT" | head -20 | tee -a "$REPORT"
  else
    log_warn "retire.js encontrou problemas (severidade baixa)"
    head -10 "$RETIRE_OUT" | tee -a "$REPORT"
  fi
fi
rm -f "$RETIRE_OUT"

# ── 5. HEADERS DE SEGURANÇA (curl) ───────────────────────────────────────────
log_sep
echo "=== [5/5] Security Headers (producao) ===" | tee -a "$REPORT"
echo ""

PROD_URL="${PROD_URL:-https://app.logia.com.br}"
if curl -sf --max-time 10 -I "$PROD_URL" -o /dev/null 2>/dev/null; then
  HEADERS=$(curl -sf --max-time 10 -I "$PROD_URL" 2>/dev/null)
  for HEADER in "Strict-Transport-Security" "X-Content-Type-Options" "X-Frame-Options" "Content-Security-Policy"; do
    if echo "$HEADERS" | grep -qi "$HEADER"; then
      log_ok "Header presente: $HEADER"
    else
      log_warn "Header ausente: $HEADER"
    fi
  done
else
  log_info "Produção inacessível — pulando verificação de headers"
fi

# ── RESUMO ────────────────────────────────────────────────────────────────────
echo ""
echo "" >> "$REPORT"
echo "================================================================" | tee -a "$REPORT"

if [ "$FAIL" -eq 0 ]; then
  echo -e "${GREEN}RESULTADO: APROVADO — nenhuma vulnerabilidade HIGH/CRITICAL${RESET}" | tee -a "$REPORT"
  echo "Relatório: $REPORT"
  echo "================================================================"
  exit 0
else
  echo -e "${RED}RESULTADO: REPROVADO — vulnerabilidades HIGH/CRITICAL encontradas${RESET}" | tee -a "$REPORT"
  echo "Relatório completo: $REPORT"
  echo "DEPLOY BLOQUEADO — corrigir issues antes de prosseguir."
  echo "================================================================"
  exit 1
fi
