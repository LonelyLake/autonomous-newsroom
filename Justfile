# Justfile dla projektu Autonomous Newsroom
set shell := ["zsh", "-c"]

# Definicje kolorów przy użyciu printf dla kompatybilności z just
green  := `printf "\033[0;32m"`
red    := `printf "\033[0;31m"`
yellow := `printf "\033[0;33m"`
reset  := `printf "\033[0m"`

# Domyślne: lista dostępnych komend
default:
    @just --list

# --- INSTALACJA I KONFIGURACJA ---

# Inicjalizacja projektu i venv przez uv
setup:
    @echo "{{green}}Instalowanie środowiska...{{reset}}"
    uv sync
    @if [ ! -f .env ]; then \
        if [ -f .env.example ]; then \
            cp .env.example .env && echo "{{yellow}}Utworzono .env z .env.example{{reset}}"; \
        else \
            touch .env && echo "{{yellow}}Utworzono pusty plik .env{{reset}}"; \
        fi \
    fi

# --- ROZWÓJ I JAKOŚĆ KODU ---

# Startowanie serwera Newsroom (Uvicorn)
run:
    @echo "{{green}}Startowanie serwera Newsroom...{{reset}}"
    uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Pełny linting: Ruff + MyPy
lint:
    @echo "{{green}}Formatowanie i sprawdzanie kodu (Ruff)...{{reset}}"
    uv run ruff check --fix .
    uv run ruff format .
    @echo "{{green}}Sprawdzanie typów (MyPy)...{{reset}}"
    uv run mypy .

# Uruchamianie testów
test:
    @echo "{{green}}Uruchamianie testów z pytest...{{reset}}"
    uv run pytest tests/ -v

# --- DOCKER I DEPLOYMENT ---

# Budowanie obrazu kontenera
docker-build:
    @echo "{{green}}Budowanie obrazu Docker...{{reset}}"
    docker build -t newsroom-app:latest .

# Uruchomienie kontenera lokalnie (z limitami RAM dla 8GB hosta)
docker-run:
    @echo "{{yellow}}Uruchamianie kontenera (limit 1GB RAM)...{{reset}}"
    docker run --rm -p 8000:8000 --memory="1g" --name newsroom-container newsroom-app:latest

# --- SPRZĄTANIE I KONSERWACJA ---

# Usuwanie wszystkich śmieci (cache, venv, temporary files)
clean:
    @echo "{{red}}Czyszczenie cache i plików tymczasowych...{{reset}}"
    rm -rf .venv
    rm -rf .pytest_cache
    rm -rf .ruff_cache
    rm -rf .mypy_cache
    rm -rf .coverage
    rm -rf htmlcov
    rm -rf dist
    rm -rf build
    find . -type d -name "__pycache__" -exec rm -rf {} +
    @echo "{{green}}Sprzątanie zakończone.{{reset}}"

# --- WERYFIKACJA ---

# Pełna weryfikacja: od czystego stanu do gotowego obrazu
verify: clean setup lint test docker-build
    @echo "{{green}}Weryfikacja zakończona sukcesem! System gotowy do prezentacji.{{reset}}"