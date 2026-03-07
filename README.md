# Logia Marketing Platform

[![CI](https://github.com/leoal/logia-marketing/actions/workflows/ci.yml/badge.svg)](https://github.com/leoal/logia-marketing/actions/workflows/ci.yml)

Plataforma de criação e distribuição de conteúdo com IA para consultores e pequenas empresas brasileiras.

Automatiza o ciclo completo: **pesquisa → copy → arte → publicação**.

## Stack

- **Backend**: FastAPI + Celery + Redis
- **Frontend**: React 18 + Vite + Tailwind + shadcn/ui
- **Banco**: SQLite (dev) / PostgreSQL (prod)
- **IA**: Claude Sonnet + GPT-4o via LangChain

## Início rápido

```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Acesse a API em `http://localhost:8000/docs`.
