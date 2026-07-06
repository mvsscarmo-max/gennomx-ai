# GennomX AI — Makefile
# Comandos de desenvolvimento, testes, lint e deploy

.PHONY: help up down reset prod-up prod-down prod-logs install-backend install-frontend dev-backend dev-frontend dev test lint typecheck migrate dev-beat handshake handshake-llm release-check

BACKEND_DIR := backend
FRONTEND_DIR := frontend
COMPOSE := docker compose -f infra/docker-compose.yml
COMPOSE_PROD := docker compose -f infra/docker-compose.prod.yml

# ─── Help ──────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "GennomX AI — Comandos disponíveis"
	@echo "─────────────────────────────────────────────────────────────"
	@echo "  make up              Sobe Postgres + Redis (infra local)"
	@echo "  make up-dev          Sobe infra + pgAdmin + Redis Commander"
	@echo "  make down            Derruba infra local"
	@echo "  make reset           Derruba e apaga volumes (DESTRUTIVO)"
	@echo "  make prod-up         Sobe API + worker + beat + Redis TLS + Caddy"
	@echo "  make prod-down       Derruba stack produtiva"
	@echo ""
	@echo "  make install         Instala dependências backend + frontend"
	@echo "  make install-backend Instala dependências Python"
	@echo "  make install-frontend Instala dependências Node"
	@echo ""
	@echo "  make dev-backend     Inicia FastAPI em modo desenvolvimento"
	@echo "  make dev-worker      Inicia Celery worker"
	@echo "  make dev-beat        Inicia Celery beat (gatilhos agendados / VLAEG fase G)"
	@echo "  make dev-frontend    Inicia Next.js em modo desenvolvimento"
	@echo ""
	@echo "  make handshake       Valida conectividade das fontes (VLAEG fase L)"
	@echo ""
	@echo "  make migrate         Executa migrações Alembic"
	@echo "  make migrate-down    Reverte última migração"
	@echo ""
	@echo "  make test            Executa todos os testes"
	@echo "  make test-unit       Apenas testes unitários"
	@echo "  make test-int        Apenas testes de integração"
	@echo "  make test-e2e        Apenas testes end-to-end (Playwright)"
	@echo ""
	@echo "  make lint            Lint backend (ruff) + frontend (eslint)"
	@echo "  make typecheck       Type check backend (mypy) + frontend (tsc)"
	@echo "  make format          Formata código (ruff format + prettier)"
	@echo "  make release-check   Executa gates locais antes de deploy"
	@echo "─────────────────────────────────────────────────────────────"
	@echo ""

# ─── Infraestrutura ────────────────────────────────────────────────────────
up:
	$(COMPOSE) up -d postgres redis

up-dev:
	$(COMPOSE) --profile dev up -d

down:
	$(COMPOSE) down

prod-up:
	@if [ "$$ACKNOWLEDGE_LEGACY_TOPOLOGY" != "yes" ]; then \
		echo "ERRO: infra/docker-compose.prod.yml é topologia LEGADA (Caddy publicando 80:80/443:443, domínio api.gennomx.ai)."; \
		echo "A topologia atual (raiz do workspace, D-011) coloca o GennomX AI sob gennomx.com:"; \
		echo "  hub admin.gennomx.com/ai · API admin.gennomx.com/api/ai · MCP em mcp.gennomx.com,"; \
		echo "atrás do Traefik já compartilhado com outro projeto na VPS (ver F-006 no project_state/ da raiz)."; \
		echo "Este compose disputaria as portas 80/443 do Traefik e não deve subir nessa VPS/domínio."; \
		echo "Ver cabeçalho de infra/docker-compose.prod.yml e docs/09_DEPLOY_E_OPERACAO.md."; \
		echo ""; \
		echo "Se este ambiente é isolado (sem Traefik/gennomx.com compartilhado) e você sabe o que está fazendo, rode:"; \
		echo "  ACKNOWLEDGE_LEGACY_TOPOLOGY=yes make prod-up"; \
		exit 1; \
	fi
	$(COMPOSE_PROD) up -d --build

prod-down:
	$(COMPOSE_PROD) down

prod-logs:
	$(COMPOSE_PROD) logs -f --tail=200

reset:
	$(COMPOSE) down -v
	@echo "⚠  Volumes apagados. Execute 'make up' para recriar."

# ─── Instalação ────────────────────────────────────────────────────────────
install: install-backend install-frontend

install-backend:
	cd $(BACKEND_DIR) && pip install -e ".[dev]"

install-frontend:
	cd $(FRONTEND_DIR) && npm install

# ─── Desenvolvimento ───────────────────────────────────────────────────────
dev-backend:
	cd $(BACKEND_DIR) && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-worker:
	cd $(BACKEND_DIR) && celery -A workers.celery_app worker --loglevel=info -Q ingest,process,ai

dev-beat:
	cd $(BACKEND_DIR) && celery -A workers.celery_app beat --loglevel=info

dev-frontend:
	cd $(FRONTEND_DIR) && npm run dev

# ─── VLAEG fase L (Link) ───────────────────────────────────────────────────
handshake:
	python tools/handshake.py

handshake-llm:
	python tools/handshake_llm.py

# ─── Migrações ─────────────────────────────────────────────────────────────
migrate:
	cd $(BACKEND_DIR) && python -m alembic -c migrations/alembic.ini upgrade head

migrate-down:
	cd $(BACKEND_DIR) && python -m alembic -c migrations/alembic.ini downgrade -1

migrate-create:
	@read -p "Nome da migração: " name; \
	cd $(BACKEND_DIR) && python -m alembic -c migrations/alembic.ini revision --autogenerate -m "$$name"

# ─── Testes ────────────────────────────────────────────────────────────────
test:
	cd $(BACKEND_DIR) && pytest tests/ -v --tb=short
	cd $(FRONTEND_DIR) && npm run lint
	cd $(FRONTEND_DIR) && npm run typecheck

test-unit:
	cd $(BACKEND_DIR) && pytest tests/unit/ -v --tb=short

test-int:
	cd $(BACKEND_DIR) && pytest tests/integration/ -v --tb=short

test-e2e:
	cd $(FRONTEND_DIR) && npm run test:e2e

test-mcp:
	cd $(BACKEND_DIR) && pytest tests/mcp/ -v --tb=short

test-connectors:
	cd $(BACKEND_DIR) && pytest tests/connectors/ -v --tb=short

# ─── Qualidade ─────────────────────────────────────────────────────────────
lint:
	cd $(BACKEND_DIR) && ruff check .
	cd $(FRONTEND_DIR) && npm run lint

typecheck:
	cd $(BACKEND_DIR) && mypy app workers
	cd $(FRONTEND_DIR) && npx tsc --noEmit

format:
	cd $(BACKEND_DIR) && ruff format .
	cd $(FRONTEND_DIR) && npx prettier --write "src/**/*.{ts,tsx,css}"

security-scan:
	cd $(BACKEND_DIR) && pip-audit
	cd $(BACKEND_DIR) && bandit -r app workers -ll -s B608

release-check: lint typecheck test test-e2e security-scan build-frontend
	@echo "Release gates completed. Run make handshake with network access before production deploy."

# ─── Build ─────────────────────────────────────────────────────────────────
build-frontend:
	cd $(FRONTEND_DIR) && npm run build
