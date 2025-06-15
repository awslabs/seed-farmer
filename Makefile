.PHONY: help test validate format install clean

# Default target when just running 'make'
.DEFAULT_GOAL := help

.PHONY: install
install:  ## Install dependencies
	curl -Ls https://astral.sh/uv/install.sh | sh
	@echo "Setting up virtual environment..."
	uv venv -p3.11 .venv
	@echo "Installing Dev dependencies..."
	. .venv/bin/activate && \
	uv sync --frozen

.PHONY: test
test:  ## Run unit tests
	@echo "Running unit tests..."
	. .venv/bin/activate && ./test/pytest.sh

.PHONY: build
build:  ## Run build
	@echo "Running build..."
	. .venv/bin/activate && uv build --wheel

.PHONY: validate
validate:  ## Run linters and type checkers
	@echo "Running ruff and type checkers..."
	. .venv/bin/activate && \
		uv sync --frozen --inexact --no-install-project --only-dev
		uv run ruff format --check seedfarmer --quiet && \
		uv run ruff check seedfarmer --quiet && \
		uv run mypy --pretty --ignore-missing-imports seedfarmer

.PHONY: format
format:  ## Format code with ruff and prettier
	@echo "Formatting code with ruff and prettier..."
	. .venv/bin/activate && \
		uv run ruff format seedfarmer && \
		uv run ruff check --fix seedfarmer && \
		uv run ruff format test && \
		uv run ruff check --fix test

.PHONY: help
help:  ## Show help for each of the Makefile recipes
	@grep -E '^[a-zA-Z0-9 -]+:.*##' Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

.PHONY: clean
clean:  ## Remove build artifacts and virtual environment
	@echo "Cleaning build artifacts and virtual environment..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .venv/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
