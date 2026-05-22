.PHONY: help install install-dev install-python install-frontend frontend-build dev run run-prod stop stop-vite restart clean test backup-db dicionario

PORT ?= 8000
VITE_PORT ?= 5173
VENV := .venv
PYTHON := $(CURDIR)/$(VENV)/bin/python3
PIP := $(CURDIR)/$(VENV)/bin/pip
SRC := src
FRONTEND := frontend

help:
	@echo "Comandos:"
	@echo "  make install        — Python (venv) + npm (frontend)"
	@echo "  make install-dev    — install + dependências de testes/dicionário"
	@echo "  make dev            — API :$(PORT) + Vite :$(VITE_PORT) (abra a UI no :$(VITE_PORT))"
	@echo "  make run            — build Vue + só :$(PORT) (produção local)"
	@echo "  make stop           — libera portas $(PORT) e $(VITE_PORT)"
	@echo "  make frontend-build — gera src/static/dist/"
	@echo "  make test           — pytest"
	@echo "  make backup-db      — cópia de data/termo.db"
	@echo "  make dicionario     — regenera dicionário (dicionario/dicionario.db)"

# --- Instalação ---

install: install-python install-frontend
	@echo ""
	@echo "Pronto."
	@echo "  Desenvolvimento: make dev  →  UI http://localhost:$(VITE_PORT)"
	@echo "  Produção local:  make run  →  http://localhost:$(PORT)"

install-python:
	@test -f requirements.txt || (echo "requirements.txt não encontrado." && exit 1)
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

install-dev: install
	$(PIP) install -r requirements-dev.txt

install-frontend:
	@test -f $(FRONTEND)/package.json || (echo "Erro: $(FRONTEND)/package.json não encontrado." && exit 1)
	cd $(FRONTEND) && npm install

frontend-build: install-frontend
	cd $(FRONTEND) && npm run build

# --- Execução ---

stop-vite:
	@echo "Liberando porta $(VITE_PORT)..."
	@-fuser -k $(VITE_PORT)/tcp 2>/dev/null || true
	@-lsof -ti:$(VITE_PORT) | xargs -r kill -9 2>/dev/null || true

stop: stop-vite
	@echo "Liberando porta $(PORT)..."
	@-fuser -k $(PORT)/tcp 2>/dev/null || true
	@-lsof -ti:$(PORT) | xargs -r kill -9 2>/dev/null || true
	@sleep 0.3
	@echo "Portas livres."

# Desenvolvimento: backend + Vite em paralelo
dev: stop install-frontend
	@test -x $(PYTHON) || (echo "Ambiente Python não encontrado. Rode: make install" && exit 1)
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  API  →  http://localhost:$(PORT)"
	@echo "  UI   →  http://localhost:$(VITE_PORT)   ← abra no navegador"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@trap '$(MAKE) stop 2>/dev/null; exit 0' INT TERM; \
		(cd $(SRC) && PORT=$(PORT) $(PYTHON) main.py) & \
		pid_api=$$!; \
		(cd $(FRONTEND) && npm run dev -- --port $(VITE_PORT) --host 127.0.0.1) & \
		pid_vite=$$!; \
		wait $$pid_api $$pid_vite

# Produção local: Vue buildado servido na porta 8000
run: frontend-build stop
	@test -x $(PYTHON) || (echo "Ambiente Python não encontrado. Rode: make install" && exit 1)
	@test -f $(SRC)/static/dist/index.html || (echo "Build Vue falhou (dist/ ausente)." && exit 1)
	@echo "Termo (Vue) em http://localhost:$(PORT)"
	cd $(SRC) && PORT=$(PORT) $(PYTHON) main.py

run-prod: run

restart: stop run

clean:
	find $(SRC) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find $(SRC) -name '*.pyc' -delete 2>/dev/null || true

test:
	@test -x $(PYTHON) || (echo "Rode: make install-dev" && exit 1)
	$(PYTHON) -m pytest tests/ -q

backup-db:
	@mkdir -p data/backups
	@test -f data/termo.db || (echo "data/termo.db não existe." && exit 1)
	cp data/termo.db "data/backups/termo-$$(date +%Y%m%d-%H%M%S).db"
	@echo "Backup em data/backups/"

dicionario:
	@test -x $(PYTHON) || (echo "Rode: make install-dev" && exit 1)
	@test -f dicionario/dicionario.db || (echo "Coloque dicionario.db em dicionario/" && exit 1)
	$(PYTHON) scripts/gerar_dicionario_db.py
