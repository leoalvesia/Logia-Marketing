#!/usr/bin/env bash
# tests/run_all.sh — Roda toda a suite de testes com relatório de cobertura
#
# Uso:
#   chmod +x tests/run_all.sh
#   ./tests/run_all.sh
#
# Pré-requisitos: pytest, pytest-cov, pytest-asyncio instalados (ver requirements.txt)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

echo "============================================================"
echo "  Logia Marketing — Suite de Testes"
echo "============================================================"
echo ""

cd "$BACKEND_DIR"

pytest tests/ \
    -v \
    --cov=app \
    --cov-report=html \
    --cov-report=term-missing \
    --tb=short \
    -p no:warnings

echo ""
echo "============================================================"
echo "  Cobertura gerada em htmlcov/index.html"
echo "  Abra no browser: open htmlcov/index.html"
echo "============================================================"
