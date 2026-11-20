# =============================================================================
# Asistente Carvajal — automatización de tareas
# =============================================================================

SHELL := /bin/bash

# Puerto del chat; se puede sobreescribir: make run PORT=8020
PORT ?= 8010

.DEFAULT_GOAL := help
.PHONY: help install dev pre-commit-install pre-commit lint format format-check typecheck test check run index acceptance build clean

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Sincroniza el entorno virtual e instala dependencias
	uv sync

dev: install pre-commit-install ## Prepara el entorno de desarrollo (sync + hooks)

pre-commit-install: ## Instala los hooks de pre-commit en el repositorio local
	uv run pre-commit install

pre-commit: ## Ejecuta todos los hooks de pre-commit sobre el repositorio
	uv run pre-commit run --all-files

lint: ## Ejecuta Ruff (lint)
	uv run ruff check .

format: ## Formatea el código con Ruff
	uv run ruff format .

format-check: ## Verifica el formato sin modificarlo
	uv run ruff format --check .

typecheck: ## Verifica los tipos con ty (Astral)
	uv run ty check

test: ## Ejecuta las pruebas
	uv run pytest

run: ## Arranca el asistente web (PORT=8010 por defecto)
	uv run python main.py --port $(PORT)

index: ## Construye el índice Qdrant desde el corpus
	uv run python scripts/index_corpus.py --recreate

acceptance: ## Ejecuta el set de preguntas de aceptación
	uv run python scripts/run_acceptance.py

gt-propose: ## Propone el ground truth de evaluación para revisión humana
	uv run python scripts/propose_ground_truth.py \
		--output specs/002-evaluacion-recuperacion/evaluation/questions.candidate.json \
		--review specs/002-evaluacion-recuperacion/evaluation/review.md

eval: ## Matriz de recuperación (8 variantes, sin LLM)
	uv run python scripts/run_evaluation.py --mode retrieval --variants all \
		--json-out specs/002-evaluacion-recuperacion/reports/baseline.json \
		--markdown-out specs/002-evaluacion-recuperacion/reports/baseline.md

eval-e2e: ## Evaluación end-to-end de una variante (VARIANTS=<id>)
	uv run python scripts/run_evaluation.py --mode e2e --variants $(or $(VARIANTS),nomic-1000-hybrid) \
		--json-out specs/002-evaluacion-recuperacion/reports/ganadora.json \
		--markdown-out specs/002-evaluacion-recuperacion/reports/ganadora.md

check: lint format-check typecheck test ## Verificación completa (lint + formato + tipos + pruebas)

clean: ## Limpia cachés y artefactos
	rm -rf .pytest_cache .ruff_cache .mypy_cache dist build htmlcov .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
