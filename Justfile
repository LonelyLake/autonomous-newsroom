# Justfile dla projektu Autonomous Newsroom
# Kompatybilny z Windows (PowerShell) i Linux/Mac (sh)

# Wykryj system - użyj PowerShell na Windows, sh na Linux/Mac
set windows-shell := ["powershell", "-NoLogo", "-Command"]
set shell := ["sh", "-c"]

# Domyślne: lista dostępnych komend
default:
    @just --list

# =============================================================================
# INSTALACJA I KONFIGURACJA
# =============================================================================

# Inicjalizacja projektu i venv przez uv
setup:
    uv sync
    @echo "Srodowisko zainstalowane."

# =============================================================================
# ROZWÓJ I URUCHAMIANIE
# =============================================================================

# Startowanie serwera Newsroom (Uvicorn)
run:
    uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Uruchomienie serwera w tle (Windows)
[windows]
run-bg:
    Start-Process -NoNewWindow -FilePath "uv" -ArgumentList "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"

# =============================================================================
# TESTOWANIE AGENTÓW
# =============================================================================

# Test Research Agent
test-research:
    uv run python -m src.agents.research_agent

# Test Writer Agent (Research → Writer)
test-writer:
    uv run python -m src.agents.writer_agent

# Test Editor Agent (pełny pipeline)
test-editor:
    uv run python -m src.agents.editor_agent

# Test LLM Client
test-llm:
    uv run python -m src.llm_client

# Test ładowania promptów
test-prompts:
    uv run python -m src.core.prompt_loader

# Test Orchestratora (pełna pętla z feedback)
test-orchestrator:
    uv run python -m src.core.orchestrator

# =============================================================================
# LOGI
# =============================================================================

# Pokaż ostatnie 30 linii logów
[windows]
logs:
    Get-Content logs/newsroom.log -Tail 30 -Encoding UTF8

[unix]
logs:
    tail -n 30 logs/newsroom.log

# Pokaż wszystkie logi
[windows]
logs-all:
    Get-Content logs/newsroom.log -Encoding UTF8

[unix]
logs-all:
    cat logs/newsroom.log

# Śledź logi na żywo (live)
[windows]
logs-follow:
    Get-Content logs/newsroom.log -Wait -Tail 20 -Encoding UTF8

[unix]
logs-follow:
    tail -f logs/newsroom.log

# Wyczyść logi
[windows]
logs-clear:
    Remove-Item logs/newsroom.log -ErrorAction SilentlyContinue; New-Item logs/newsroom.log -ItemType File | Out-Null; Write-Host "Logi wyczyszczone."

[unix]
logs-clear:
    > logs/newsroom.log && echo "Logi wyczyszczone."

# =============================================================================
# TESTY PYTEST
# =============================================================================

# Uruchom wszystkie testy
test:
    uv run pytest -v

# Uruchom testy z pokryciem kodu
test-cov:
    uv run pytest --cov=src --cov-report=term-missing -v

# Uruchom tylko testy schematów
test-schemas:
    uv run pytest tests/test_schemas.py -v

# Uruchom tylko testy API
test-api:
    uv run pytest tests/test_api.py -v

# Uruchom tylko testy agentów
test-agents:
    uv run pytest tests/test_agents.py -v

# =============================================================================
# JAKOŚĆ KODU
# =============================================================================

# Pełny linting: Ruff
lint:
    uv run ruff check --fix .
    uv run ruff format .

# =============================================================================
# TESTY API (curl/Invoke-RestMethod)
# =============================================================================

# Wyślij testowe zlecenie do API
[windows]
api-test topic="AI w dziennikarstwie":
    Invoke-RestMethod -Uri "http://127.0.0.1:8000/start-cycle" -Method POST -ContentType "application/json" -Body ('{"topic": "' + '{{topic}}' + '", "max_iterations": 2}') | ConvertTo-Json

[unix]
api-test topic="AI w dziennikarstwie":
    curl -X POST "http://127.0.0.1:8000/start-cycle" -H "Content-Type: application/json" -d '{"topic": "{{topic}}", "max_iterations": 2}'

# Pobierz logi przez API
[windows]
api-logs:
    Invoke-RestMethod -Uri "http://127.0.0.1:8000/logs?lines=50"

[unix]
api-logs:
    curl "http://127.0.0.1:8000/logs?lines=50"

# Sprawdź health
[windows]
api-health:
    Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" | ConvertTo-Json

[unix]
api-health:
    curl "http://127.0.0.1:8000/health"

# =============================================================================
# DOCKER
# =============================================================================

# Budowanie obrazu kontenera
docker-build:
    docker build -t newsroom-app:latest .

# Uruchomienie przez Docker Compose
docker-up:
    docker compose up -d

# Zatrzymanie Docker Compose
docker-down:
    docker compose down

# Logi z Dockera
docker-logs:
    docker compose logs -f newsroom-api

# =============================================================================
# SPRZĄTANIE
# =============================================================================

# Usuwanie wszystkich śmieci (cache, venv, temporary files)
[windows]
clean:
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue .venv, .pytest_cache, .ruff_cache, .mypy_cache, .coverage, htmlcov, dist, build
    Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
    Write-Host "Sprzatanie zakonczone."

[unix]
clean:
    rm -rf .venv .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov dist build
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    echo "Sprzątanie zakończone."