#!/bin/bash
# release.sh — versionamento semântico automatizado
#
# Uso: ./scripts/release.sh patch|minor|major [--dry-run]
#
# O que faz:
#   1. Lê versão atual de backend/app/version.py
#   2. Incrementa conforme tipo (patch/minor/major)
#   3. Atualiza backend/app/version.py
#   4. Gera entrada no CHANGELOG.md com commits desde a última tag
#   5. Cria commit de release + tag v{VERSAO}
#   6. Push da tag → CI/CD dispara deploy com tag no nome da imagem

set -euo pipefail

RELEASE_TYPE="${1:-}"
DRY_RUN="${2:-}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION_FILE="${REPO_ROOT}/backend/app/version.py"
CHANGELOG="${REPO_ROOT}/CHANGELOG.md"

# ── Validações ────────────────────────────────────────────────────────────────

if [[ ! "$RELEASE_TYPE" =~ ^(patch|minor|major)$ ]]; then
  echo "Uso: $0 patch|minor|major [--dry-run]"
  echo ""
  echo "  patch  → 1.0.0 → 1.0.1  (bug fixes)"
  echo "  minor  → 1.0.0 → 1.1.0  (novas funcionalidades)"
  echo "  major  → 1.0.0 → 2.0.0  (breaking changes)"
  exit 1
fi

if [ ! -f "$VERSION_FILE" ]; then
  echo "ERRO: $VERSION_FILE não encontrado"
  exit 1
fi

# Verificar que o working tree está limpo
if [ -n "$(git -C "$REPO_ROOT" status --porcelain)" ]; then
  echo "ERRO: working tree com mudanças não commitadas."
  echo "Faça commit ou stash antes de criar um release."
  git -C "$REPO_ROOT" status --short
  exit 1
fi

# ── Ler versão atual ──────────────────────────────────────────────────────────

CURRENT_VERSION=$(grep -oP '(?<=__version__ = ")[^"]+' "$VERSION_FILE")
if [ -z "$CURRENT_VERSION" ]; then
  echo "ERRO: não foi possível ler __version__ em $VERSION_FILE"
  exit 1
fi

IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

# ── Calcular nova versão ──────────────────────────────────────────────────────

case "$RELEASE_TYPE" in
  major)
    NEW_MAJOR=$((MAJOR + 1))
    NEW_MINOR=0
    NEW_PATCH=0
    ;;
  minor)
    NEW_MAJOR=$MAJOR
    NEW_MINOR=$((MINOR + 1))
    NEW_PATCH=0
    ;;
  patch)
    NEW_MAJOR=$MAJOR
    NEW_MINOR=$MINOR
    NEW_PATCH=$((PATCH + 1))
    ;;
esac

NEW_VERSION="${NEW_MAJOR}.${NEW_MINOR}.${NEW_PATCH}"
TAG="v${NEW_VERSION}"

echo "================================================================"
echo " Release: ${CURRENT_VERSION} → ${NEW_VERSION} (${RELEASE_TYPE})"
echo " Tag: ${TAG}"
[ "$DRY_RUN" = "--dry-run" ] && echo " MODO DRY-RUN — nenhuma alteração será feita"
echo "================================================================"
echo ""

# ── Coletar commits desde a última tag ────────────────────────────────────────

LAST_TAG=$(git -C "$REPO_ROOT" describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LAST_TAG" ]; then
  echo "Commits desde ${LAST_TAG}:"
  COMMITS=$(git -C "$REPO_ROOT" log "${LAST_TAG}..HEAD" \
    --pretty=format:"- %s (%h)" \
    --no-merges \
    | grep -v "^$" || echo "- Sem commits novos")
else
  echo "Sem tag anterior — incluindo últimos 20 commits:"
  COMMITS=$(git -C "$REPO_ROOT" log -20 \
    --pretty=format:"- %s (%h)" \
    --no-merges)
fi

echo "$COMMITS"
echo ""

if [ "$DRY_RUN" = "--dry-run" ]; then
  echo "DRY-RUN: saindo sem fazer alterações."
  exit 0
fi

# ── Atualizar version.py ──────────────────────────────────────────────────────

sed -i "s/__version__ = \"${CURRENT_VERSION}\"/__version__ = \"${NEW_VERSION}\"/" \
  "$VERSION_FILE"
echo "✓ Atualizado: $VERSION_FILE → ${NEW_VERSION}"

# ── Atualizar CHANGELOG.md ────────────────────────────────────────────────────

RELEASE_DATE=$(date -u '+%Y-%m-%d')

CHANGELOG_ENTRY="## [${NEW_VERSION}] — ${RELEASE_DATE}

### Tipo: ${RELEASE_TYPE}

${COMMITS}

"

if [ -f "$CHANGELOG" ]; then
  # Inserir antes do primeiro ## (primeira entrada)
  TMP=$(mktemp)
  HEADER=$(head -5 "$CHANGELOG")
  REST=$(tail -n +6 "$CHANGELOG")
  printf '%s\n\n%s\n%s' "$HEADER" "$CHANGELOG_ENTRY" "$REST" > "$TMP"
  mv "$TMP" "$CHANGELOG"
else
  # Criar CHANGELOG.md
  cat > "$CHANGELOG" << EOF
# Changelog — Logia Marketing Platform

Todas as mudanças notáveis são documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com).

${CHANGELOG_ENTRY}
EOF
fi

echo "✓ CHANGELOG.md atualizado"

# ── Commit + Tag ──────────────────────────────────────────────────────────────

cd "$REPO_ROOT"

git add backend/app/version.py CHANGELOG.md

git commit -m "chore: release ${NEW_VERSION}

Co-Authored-By: release-script <noreply@logia.com.br>"

git tag -a "$TAG" -m "Release ${NEW_VERSION} (${RELEASE_TYPE})"

echo "✓ Commit e tag ${TAG} criados"

# ── Push ─────────────────────────────────────────────────────────────────────

echo ""
read -r -p "Push ${TAG} para origin? (y/N) " CONFIRM
if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
  git push origin HEAD
  git push origin "$TAG"
  echo ""
  echo "✅ Release ${TAG} publicado!"
  echo "   → CI/CD irá construir imagem: backend:${TAG}"
  echo "   → Acompanhe: $(git remote get-url origin)/actions"
else
  echo ""
  echo "Tag criada localmente. Para publicar:"
  echo "  git push origin HEAD && git push origin ${TAG}"
fi

echo "================================================================"
