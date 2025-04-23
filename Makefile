.PHONY: setup run run-script clean test lint format

# Default Python interpreter
PYTHON = python3
VENV = venv
PIP = $(VENV)/bin/pip
PYTHON_VENV = $(VENV)/bin/python
UVICORN = $(VENV)/bin/uvicorn

# Application settings
APP_MODULE = app.main:app
HOST = 0.0.0.0
PORT = 8000

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run:
	$(UVICORN) $(APP_MODULE) --host $(HOST) --port $(PORT) --reload

run-script:
	$(PYTHON_VENV) run.py --reload

clean:
	rm -rf __pycache__
	rm -rf app/__pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

test:
	$(PYTHON_VENV) -m pytest

lint:
	$(PYTHON_VENV) -m flake8 app

format:
	$(PYTHON_VENV) -m black app

db-init:
	$(PYTHON_VENV) -m app.db.init_db

help:
	@echo "Available commands:"
	@echo "  make setup      - Create virtual environment and install dependencies"
	@echo "  make run        - Run the application with uvicorn directly"
	@echo "  make run-script - Run the application using run.py script"
	@echo "  make clean      - Remove Python cache files"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linter"
	@echo "  make format     - Format code with Black"
	@echo "  make db-init    - Initialize the database"
