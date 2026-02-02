set shell := ["zsh", "-c"]

default:
    @just --list

setup:
    @echo "Instalowanie środowiska..."
    uv sync

run:
    @echo "Startowanie serwera Newsroom..."
    uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

lint:
    @echo "Czyszczenie kodu..."
    uv run ruff check --fix .
    uv run ruff format .

test:
    @echo "Uruchamianie testów..."
    uv run pytest tests/ -v

clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type d -name ".pytest_cache" -exec rm -rf {} +