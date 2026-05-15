COMPOSE_LOCAL := docker compose -f dc-plc-datalink-rfc1006-local.yml
COMPOSE_ACR   := docker compose -f dc-plc-datalink-rfc1006-acr.yml

.DEFAULT_GOAL := help

.PHONY: help build up down restart logs ps clean \
        build-acr up-acr down-acr \
        lint format

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?##/ {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

## --- Local stack (build from source) ---

build: ## Build all containers from source
	$(COMPOSE_LOCAL) build

up: ## Start the stack in the background (builds if needed)
	$(COMPOSE_LOCAL) up -d --build

down: ## Stop and remove containers (keeps volumes)
	$(COMPOSE_LOCAL) down

restart: down up ## Restart the local stack

logs: ## Tail logs from all local containers
	$(COMPOSE_LOCAL) logs -f

ps: ## Show running containers
	$(COMPOSE_LOCAL) ps

clean: ## Stop the stack and remove named volumes (DESTRUCTIVE)
	$(COMPOSE_LOCAL) down -v

## --- ACR stack (pull pre-built images) ---

build-acr: ## Pull pre-built images from ACR
	$(COMPOSE_ACR) pull

up-acr: ## Start the stack using ACR images
	$(COMPOSE_ACR) up -d

down-acr: ## Stop the ACR-based stack
	$(COMPOSE_ACR) down

## --- Backend dev tooling (Phase C — requires backend dev extras) ---

lint: ## Run ruff lint + format check on the backend
	cd backend && ruff check src test && ruff format --check src test

format: ## Auto-fix ruff lint issues and format the backend
	cd backend && ruff check --fix src test && ruff format src test
