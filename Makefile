# Makefile for the project
# Provides standardized commands for common development tasks

# Default target when running 'make' without arguments
.PHONY: help
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@echo ""
	@echo "Setup:"
	@echo "  install         Install project dependencies using Poetry"
	@echo "  install-dev     Install development dependencies using Poetry"
	@echo ""
	@echo "Execution:"
	@echo "  run             Run the main application"
	@echo "  run-api         Start the API server"
	@echo ""
	@echo "Utility:"
	@echo "  clean           Remove temporary files and caches"
	@echo "  check-prereqs   Check if all prerequisites are installed"
	@echo ""

# Check if Poetry is installed
check-poetry:
	@command -v poetry >/dev/null 2>&1 || { echo "Error: Poetry is not installed. Please install it first: https://python-poetry.org/docs/#installation"; exit 1; }

# Install project dependencies
.PHONY: install
install: check-poetry
	@echo "Installing project dependencies..."
	@poetry install --no-dev
	@echo "Dependencies installed successfully."

# Install development dependencies
.PHONY: install-dev
install-dev: check-poetry
	@echo "Installing project dependencies with development packages..."
	@poetry install
	@echo "Development dependencies installed successfully."

# Run the main application
.PHONY: run
run: check-poetry
	@echo "Starting the main application..."
	@poetry run python src/main.py

# Run the API server
.PHONY: run-api
run-api: check-poetry
	@echo "Starting the API server..."
	@poetry run kb_api

# Clean temporary files and caches
.PHONY: clean
clean:
	@echo "Cleaning temporary files and caches..."
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type d -name .pytest_cache -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@find . -type f -name ".coverage" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type d -name "*.egg" -exec rm -rf {} +
	@find . -type d -name ".eggs" -exec rm -rf {} +
	@echo "Cleaned successfully."

# Check prerequisites
.PHONY: check-prereqs
check-prereqs:
	@echo "Checking prerequisites..."
	@command -v poetry >/dev/null 2>&1 || echo "Warning: Poetry is not installed. Install it from https://python-poetry.org/docs/#installation"
	@echo "Prerequisites check completed."