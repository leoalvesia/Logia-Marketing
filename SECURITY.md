# Security — Logia Marketing Platform

Auditoria de segurança baseada no OWASP Top 10 (2021).
**Revisão final pré-lançamento público: 2026-03-07**

---

## OWASP Top 10 — Status Final

### A01 — Broken Access Control ✅

| Controle | Status | Arquivo |
|----------|:------:|---------|
| JWT `get_current_user` em todos os endpoints protegidos | ✅ | `app/auth.py` |
| Ownership por JOIN (não por query param) | ✅ | `app/routers/library.py`, `pipeline.py` |
| Soft delete filtra `status != 'deleted'` | ✅ | `app/routers/library.py` |
| `/admin/*` protegido por `X-Admin-Key` separado do JWT | ✅ | `app/routers/invites.py`, `costs.py`, `feedback.py` |
| `GET /account/export` retorna apenas dados do usuário autenticado | ✅ | `app/routers/account.py` |
| `DELETE /account` valida `current_user` antes de anonimizar | ✅ | `app/routers/account.py` |
| Perfis monitorados isolados por `user_id` | ✅ | `app/routers/settings.py` |

**Risco residual:** nenhum crítico identificado.

---

### A02 — Cryptographic Failures ✅

| Controle | Status | Arquivo |
|----------|:------:|---------|
| Senhas com bcrypt rounds=12 | ✅ | `app/auth.py` |
| JWT HS256 + `SECRET_KEY` mínimo 32 bytes | ✅ | `app/auth.py` (expiração 24h) |
| Tokens OAuth criptografados com Fernet (AES-128-CBC + HMAC-SHA256) | ✅ | `app/crypto.py` |
| `ENCRYPTION_KEY` obrigatória em produção (exit(1) se ausente) | ✅ | `app/config.py` |
| HTTPS obrigatório com HSTS (max-age=31536000) via Caddy | ✅ | `config/Caddyfile` |
| Secrets exclusivamente em variáveis de ambiente | ✅ | `.env.example` / CI secrets |

---

### A03 — Injection ✅

| Controle | Status | Arquivo |
|----------|:------:|---------|
| SQLAlchemy ORM com parâmetros vinculados (sem SQL raw) | ✅ | Todos os routers |
| Validação de entrada com Pydantic em todos os endpoints | ✅ | Schemas em todos os routers |
| HTML de email sanitizado com `_escape()` | ✅ | `app/publishers/email.py` |
| Screenshot de bug report truncada em 1.4 MB | ✅ | `app/routers/feedback.py:161` |
| Sem `eval()` / `exec()` com input de usuário | ✅ | Revisão manual |
| Prompt injection: estrutura fixa, dados do usuário como variáveis | ✅ | `app/agents/copy/` |

---

### A04 — Insecure Design ✅

| Controle | Status | Arquivo |
|----------|:------:|---------|
| Rate limiting em todos os endpoints críticos | ✅ | `app/middleware/rate_limit.py` |
| Bloqueio de IP após 100 falhas de login (TTL 24h) | ✅ | `app/middleware/rate_limit.py` |
| Pipeline state machine com transições validadas | ✅ | `app/pipeline_state_machine.py` |
| Backup diário automatizado (retenção 30 dias) | ✅ | `scripts/backup.sh` |
| Validação de config obrigatória no startup | ✅ | `app/config.py` |
| Soft delete LGPD + hard delete automatizado (30 dias) | ✅ | `app/routers/account.py`, `app/tasks/account_tasks.py` |

---

### A05 — Security Misconfiguration ✅

| Controle | Status | Arquivo |
|----------|:------:|---------|
| Headers de segurança HTTP (HSTS, CSP, X-Frame-Options) | ✅ | `app/middleware/security.py` |
| CORS restritivo (apenas origem do frontend) | ✅ | `app/main.py` |
| `DEBUG=False` em produção | ✅ | `app/config.py` |
| OpenAPI/Swagger desabilitado em produção | ✅ | `app/main.py` |
| Redis e PostgreSQL sem portas expostas ao host | ✅ | `docker-compose.prod.yml` |
| Containers rodando como usuário não-root (`USER logia`) | ✅ | `backend/Dockerfile` |

---

### A06 — Vulnerable and Outdated Components ✅

| Controle | Status | Arquivo |
|----------|:------:|---------|
| `safety check` (dependências Python) | ✅ | `scripts/security_audit.sh` |
| `bandit -ll` (código Python HIGH/MEDIUM) | ✅ | `scripts/security_audit.sh`, `.github/workflows/ci.yml` |
| `npm audit --audit-level=high` | ✅ | `.github/workflows/ci.yml` |
| `retire.js` (bibliotecas JS com CVEs) | ✅ | `scripts/security_audit.sh` |
| Script de auditoria bloqueia deploy em HIGH/CRITICAL (exit 1) | ✅ | `scripts/security_audit.sh` |

**Ação pendente:** configurar Dependabot (`.github/dependabot.yml`).

---

### A07 — Identification and Authentication Failures ✅

| Controle | Status | Arquivo |
|----------|:------:|---------|
| Rate limit login: 5 req/min por IP | ✅ | `app/middleware/rate_limit.py` |
| Rate limit register: 3 req/hora por IP | ✅ | `app/middleware/rate_limit.py` |
| IP block após 100 falhas/hora (TTL 24h) | ✅ | `app/middleware/rate_limit.py` |
| `track_login_failure()` chamado em todos os 401 | ✅ | `app/routers/auth.py` |
| JWT expira em 24h | ✅ | `app/auth.py` |
| Conta anonimizada em DELETE /account (is_active=False bloqueia login) | ✅ | `app/routers/account.py` |
| Convite obrigatório para registro (beta gate) | ✅ | `app/routers/auth.py` |
| Aceite de termos registrado com timestamp (`accepted_terms_at`) | ✅ | `app/models/user.py` |

**Acao pendente:** JWT blacklist Redis para logout explícito (pós-lançamento).

---

### A08 — Software and Data Integrity Failures ✅

| Controle | Status | Arquivo |
|----------|:------:|---------|
| Imagens Docker assinadas via GHCR | ✅ | `.github/workflows/deploy.yml` |
| `npm ci` usa `package-lock.json` (build reprodutível) | ✅ | `.github/workflows/ci.yml` |
| CI obrigatório antes do deploy normal | ✅ | `.github/workflows/deploy.yml` |
| Hotfix: lint + testes unitários + integração obrigatórios | ✅ | `.github/workflows/hotfix.yml` |
| `before_send` Sentry sanitiza campos sensíveis | ✅ | `app/main.py` |

---

### A09 — Security Logging and Monitoring Failures ✅

| Controle | Status | Arquivo |
|----------|:------:|---------|
| Logging estruturado JSON com structlog | ✅ | `app/logger.py` |
| `X-Request-ID` em todas as respostas | ✅ | `app/middleware/request_id.py` |
| Sentry captura exceções + bug reports | ✅ | `app/main.py`, `app/routers/feedback.py` |
| Rate limit exceeded e IP block logados | ✅ | `app/middleware/rate_limit.py` |
| Export e soft delete de conta logados | ✅ | `app/routers/account.py` |
| Dashboard de bugs (novo/em análise/resolvido) | ✅ | `/admin/feedback` |
| Script de diagnóstico rápido | ✅ | `scripts/diagnose.sh` |
| Runbook de incidentes (5 tipos, P1/P2/P3) | ✅ | `docs/RUNBOOK.md` |

---

### A10 — Server-Side Request Forgery (SSRF) ✅

| Controle | Status | Arquivo |
|----------|:------:|---------|
| URLs de coleta vêm de config, não de input de usuário | ✅ | `app/agents/research/` |
| Google Drive: path validado pelo SDK | ✅ | `app/storage/google_drive.py` |
| Nenhum endpoint aceita URL arbitrária do usuário | ✅ | Revisão manual |

---

## Rate Limiting — Tabela Final

| Endpoint | Limite | Janela | Chave |
|----------|--------|--------|-------|
| `POST /auth/login` | 5 req | 1 min | IP |
| `POST /auth/register` | 3 req | 1 hora | IP |
| `POST /api/pipeline/start` | 20 req | 1 hora | Usuário |
| `POST /api/pipeline/*/select-topic` | 100 req | 1 hora | Usuário |
| `POST /api/pipeline/*/approve-copy` | 100 req | 1 hora | Usuário |
| `POST /api/pipeline/*/approve-art` | 20 req | 1 hora | Usuário |
| `POST /feedback/*` | 10 req | 1 dia | Usuário |
| Bloqueio IP (falhas login) | 100 falhas/hora | bloqueio 24h | IP |

Todos os 429 retornam `Retry-After: <segundos>`.

---

## LGPD / GDPR — Endpoints de Compliance

| Endpoint | Descricao | Base legal |
|----------|-----------|------------|
| `GET /account/export` | Portabilidade — JSON com todos os dados | LGPD Art. 18, VI |
| `DELETE /account` | Exclusão — soft delete imediato + hard delete em 30 dias | LGPD Art. 18, VI |
| `GET /terms` | Termos de Uso (frontend) | — |
| `GET /privacy` | Política de Privacidade | LGPD Art. 9 |
| `accepted_terms_at` (User model) | Registro de aceite com timestamp | LGPD Art. 7, I |
| Beat `hard_delete_expired_accounts` (3h UTC) | Hard delete automático | LGPD Art. 16 |

---

## Celery Beat — Tasks de Segurança e Compliance

| Task | Horário | Finalidade |
|------|---------|------------|
| `hard_delete_expired_accounts` | 3h UTC diário | LGPD: apaga contas deletadas há > 30 dias |
| `daily_cost_report` | 8h UTC diário | Alerta se custo IA > $10/dia |
| `daily_nps_summary` | 9h UTC diário | Resumo NPS + detratores |
| `run_daily_research` | 6h BRT diário | Pesquisa de tendências |

---

## Geração de Chaves Seguras

```bash
# ENCRYPTION_KEY (Fernet)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# SECRET_KEY (JWT — min 32 bytes)
openssl rand -hex 32

# ADMIN_KEY
openssl rand -hex 24
```

```bash
# GitHub Secrets
gh secret set ENCRYPTION_KEY --body "$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
gh secret set SECRET_KEY     --body "$(openssl rand -hex 32)"
gh secret set ADMIN_KEY      --body "$(openssl rand -hex 24)"
```

---

## Auditoria Automatizada

```bash
# Executar (bloqueia em HIGH/CRITICAL)
bash scripts/security_audit.sh

# Modo CI (sem cores)
CI=true bash scripts/security_audit.sh

# Ver relatório gerado
cat scripts/security_report.txt
```

---

## Backlog de Segurança (pós-lançamento)

| # | Item | Esforço |
|---|------|---------|
| 1 | JWT blacklist Redis para logout explícito | 2h |
| 2 | Configurar Dependabot (`.github/dependabot.yml`) | 15 min |
| 3 | Política de senha mínima (8 chars + 1 número) | 30 min |
| 4 | `pip-compile --generate-hashes` (pinagem determinística) | 1h |
| 5 | CAPTCHA após 10 falhas de login | 3h |
| 6 | Alertas Sentry configurados (ver `DEPLOY.md` seção 12.2) | 30 min |
