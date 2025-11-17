# Makefile per Poker Manager
# -----------------------------------------------------------------
# Gestisce sia i comandi Docker (per sviluppo e produzione)
# sia i comandi locali (per utility).
# -----------------------------------------------------------------

# Variabili
CONTAINER_NAME = pokerapp
COMPOSE_CMD = docker-compose

# --- Comandi Docker Principali ---

.PHONY: dev build up down restart logs migrate shell test-docker

dev: ## Avvia l'ambiente di sviluppo (App+DB+Redis) con hot-reload
	@echo "Avvio di Docker Compose (App, DB, Redis) in modalità sviluppo..."
	@$(COMPOSE_CMD) up

build: ## Costruisce o ricostruisce le immagini Docker
	@echo "Costruzione delle immagini Docker..."
	@$(COMPOSE_CMD) build

up: ## Avvia i container Docker in background (modalità produzione)
	@echo "Avvio dei container Docker in background (detached)..."
	@$(COMPOSE_CMD) up -d

down: ## Ferma e rimuove i container Docker
	@echo "Stop e rimozione dei container..."
	@$(COMPOSE_CMD) down

clean-db: ## Ferma i container E DISTRUGGE il volume del database
	@echo "ATTENZIONE: Eliminazione di tutti i container E del volume del database..."
	@$(COMPOSE_CMD) down -v

restart: down up ## Riavvia i container Docker (modalità produzione)
	@echo "Riavvio completato."

logs: ## Mostra i log del container dell'app in tempo reale
	@echo "Streaming dei log da $(CONTAINER_NAME)..."
	@$(COMPOSE_CMD) logs -f $(CONTAINER_NAME)

migrate: ## Esegue le migrazioni del database nel container
	@echo "Esecuzione di 'flask db upgrade' nel container..."
	@$(COMPOSE_CMD) run --rm migrate

shell: ## Apre una shell (sh) dentro il container dell'app
	@echo "Apertura shell in $(CONTAINER_NAME)..."
	@docker exec -it $(CONTAINER_NAME) sh

test-docker: ## Esegue i test (pytest) all'interno del container Docker
	@echo "Esecuzione di pytest nel container..."
	@docker exec -it $(CONTAINER_NAME) pytest

# --- Comandi Locali (Utility) ---

.PHONY: install run-local test-local lint clean-local

install: ## Installa le dipendenze Python locali (da requirements.txt)
	@echo "Installazione delle dipendenze in .venv..."
	pip install -r requirements.txt

run-local: ## Avvia il server locale (USA SQLITE, NON DOCKER)
	@echo "Avvio del server di sviluppo Flask locale (usa SQLite)..."
	@flask run

test-local: ## Esegue i test (pytest) localmente usando .venv
	@echo "Esecuzione di pytest localmente..."
	@pytest

lint: ## Esegue il controllo dello stile (flake8) localmente
	@echo "Controllo dello stile con flake8..."
	@flake8 app/

clean-local: ## Rimuove i file temporanei di Python (.pyc, cache)
	@echo "Pulizia dei file temporanei..."
	@find . -type f -name "*.py[co]" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@rm -f .coverage
	@rm -rf htmlcov/

# --- Comando di Aiuto ---

.PHONY: help
help: ## Mostra questo messaggio di aiuto
	@echo "Comandi disponibili per Poker App 5.0:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Target di default (se si esegue solo 'make')
.DEFAULT_GOAL := help