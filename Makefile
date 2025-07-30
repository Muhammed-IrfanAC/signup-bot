.PHONY: install test lint format clean run run-api docker-build docker-up docker-down

# Variables
PYTHON = python3
PIP = pip3
VENV = venv
PYTHON_VENV = $(VENV)/bin/python
PIP_VENV = $(VENV)/bin/pip
FLAKE8 = $(VENV)/bin/flake8
BLACK = $(VENV)/bin/black
ISORT = $(VENV)/bin/isort

# Default target
all: install

# Create virtual environment
venv:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	$(PIP_VENV) install --upgrade pip

# Install dependencies
install: venv
	@echo "Installing dependencies..."
	$(PIP_VENV) install -r requirements.txt
	$(PIP_VENV) install -e .

# Install development dependencies
dev: install
	@echo "Installing development dependencies..."
	$(PIP_VENV) install -r requirements-dev.txt

# Run tests
test:
	@echo "Running tests..."
	$(PYTHON_VENV) -m pytest tests/ -v

# Lint code
lint:
	@echo "Linting code..."
	$(FLAKE8 signup_bot tests

# Format code
format:
	@echo "Formatting code..."
	$(BLACK) signup_bot tests
	$(ISORT) signup_bot tests

# Clean up
clean:
	@echo "Cleaning up..."
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +

# Run the bot
run:
	@echo "Starting bot..."
	$(PYTHON_VENV) run.py

# Run the API server
run-api:
	@echo "Starting API server..."
	$(PYTHON_VENV) run_api.py

# Build Docker images
docker-build:
	@echo "Building Docker images..."
	docker-compose build

# Start containers
docker-up:
	@echo "Starting containers..."
	docker-compose up -d

# Stop containers
docker-down:
	@echo "Stopping containers..."
	docker-compose down

# Show logs
docker-logs:
	docker-compose logs -f

# Help
help:
	@echo "Available targets:"
	@echo "  install     Install dependencies"
	@echo "  dev         Install development dependencies"
	@echo "  test        Run tests"
	@echo "  lint        Check code style"
	@echo "  format      Format code"
	@echo "  clean       Clean up"
	@echo "  run         Run the bot"
	@echo "  run-api     Run the API server"
	@echo "  docker-build  Build Docker images"
	@echo "  docker-up   Start containers"
	@echo "  docker-down Stop containers"
	@echo "  docker-logs Show container logs"
