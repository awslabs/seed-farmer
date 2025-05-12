.PHONY: help test validate format install clean

# Default target when just running 'make'
.DEFAULT_GOAL := help

.PHONY: install
install:  ## Install dependencies
	@echo "Setting up virtual environment..."
	python3 -m venv .venv
	@echo "Installing Dev dependencies..."
	. .venv/bin/activate && \
	python -m pip install --upgrade pip && \
	pip install -r requirements.txt && \
	pip install -r requirements-dev.txt && \
	pip install -e .

.PHONY: test
test:  ## Run unit tests
	@echo "Running unit tests..."
	. .venv/bin/activate && ./test/pytest.sh

.PHONY: validate
validate:  ## Run linters and type checkers
	@echo "Running ruff and type checkers..."
	. .venv/bin/activate && \
		pip install ruff && \
		pip install mypy && \
		ruff format --check seedfarmer && \
		python3 -m ruff check --fix seedfarmer && \
		python3 -m mypy --ignore-missing-imports seedfarmer

.PHONY: format
format:  ## Format code with ruff and prettier
	@echo "Formatting code with ruff and prettier..."
	. .venv/bin/activate && \
		python -m ruff format seedfarmer && \
		python -m ruff check --fix seedfarmer && \
		python -m ruff format test && \
		python -m ruff check --fix test

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
