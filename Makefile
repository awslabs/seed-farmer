.PHONY: help test validate format install clean

# Default target when just running 'make'
.DEFAULT_GOAL := help

.PHONY: install
install:  ## Install dependencies
	curl -Ls https://astral.sh/uv/install.sh | sh
	@echo "Setting up virtual environment..."
	uv venv -p3.11 .venv-uvtest
	@echo "Installing Dev dependencies..."
	. .venv-uvtest/bin/activate && \
	uv pip install -r requirements.txt && \
	uv pip install -r requirements-dev.txt && \
	uv pip install -e .

.PHONY: test
test:  ## Run unit tests
	@echo "Running unit tests..."
	. .venv-uvtest/bin/activate && ./test/pytest.sh

.PHONY: validate
validate:  ## Run linters and type checkers
	@echo "Running ruff and type checkers..."
	. .venv-uvtest/bin/activate && \
		pip install ruff mypy && \
		ruff format --check seedfarmer --quiet && \
		python3 -m ruff check --fix seedfarmer --quiet && \
		python3 -m mypy --pretty --ignore-missing-imports seedfarmer


.PHONY: format
format:  ## Format code with ruff and prettier
	@echo "Formatting code with ruff and prettier..."
	. .venv-uvtest/bin/activate && \
		python -m ruff format seedfarmer && \
		python -m ruff check --fix seedfarmer && \
		python -m ruff format test && \
		python -m ruff check --fix test && \
		python -m ruff format setup.py && \
		python -m ruff check --fix setup.py

.PHONY: help
help:  ## Show help for each of the Makefile recipes
	@grep -E '^[a-zA-Z0-9 -]+:.*##' Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

.PHONY: clean
clean:  ## Remove build artifacts and virtual environment
	@echo "Cleaning build artifacts and virtual environment..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .venv-uvtest/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
