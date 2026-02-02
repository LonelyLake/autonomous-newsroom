# =============================================================================
# NEWSROOM - Skrypt pomocniczy dla Windows PowerShell
# Użycie: .\run.ps1 <komenda>
# =============================================================================

param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    
    [Parameter(Position=1)]
    [string]$Arg1 = ""
)

$ErrorActionPreference = "Stop"

function Show-Help {
    Write-Host @"

=== AUTONOMOUS NEWSROOM - Komendy ===

SERWER:
  .\run.ps1 start          - Uruchom serwer API
  .\run.ps1 stop           - Zatrzymaj serwer

TESTOWANIE AGENTOW:
  .\run.ps1 test-research  - Test Research Agent
  .\run.ps1 test-writer    - Test Writer Agent  
  .\run.ps1 test-editor    - Test pelny pipeline
  .\run.ps1 test-llm       - Test polaczenia z LLM

LOGI:
  .\run.ps1 logs           - Pokaz ostatnie 30 linii
  .\run.ps1 logs-all       - Pokaz wszystkie logi
  .\run.ps1 logs-follow    - Sledz logi na zywo
  .\run.ps1 logs-clear     - Wyczysc logi

API:
  .\run.ps1 api-test       - Wyslij testowe zlecenie
  .\run.ps1 api-test "temat" - Zlecenie z wlasnym tematem
  .\run.ps1 api-logs       - Pobierz logi przez API
  .\run.ps1 api-health     - Sprawdz status serwera

INNE:
  .\run.ps1 setup          - Instaluj zaleznosci
  .\run.ps1 lint           - Sprawdz jakosc kodu
  .\run.ps1 clean          - Wyczysc cache

"@
}

function Start-Server {
    Write-Host "Uruchamiam serwer na http://127.0.0.1:8000 ..." -ForegroundColor Green
    Write-Host "Swagger UI: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
    Write-Host "Zatrzymaj: Ctrl+C" -ForegroundColor Yellow
    uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
}

function Stop-Server {
    Write-Host "Zatrzymuje serwer..." -ForegroundColor Yellow
    Stop-Process -Name "python" -ErrorAction SilentlyContinue
    Write-Host "Serwer zatrzymany." -ForegroundColor Green
}

function Test-Research {
    Write-Host "=== TEST: Research Agent ===" -ForegroundColor Cyan
    uv run python -m src.agents.research_agent
}

function Test-Writer {
    Write-Host "=== TEST: Writer Agent (Research -> Writer) ===" -ForegroundColor Cyan
    uv run python -m src.agents.writer_agent
}

function Test-Editor {
    Write-Host "=== TEST: Editor Agent (pelny pipeline) ===" -ForegroundColor Cyan
    uv run python -m src.agents.editor_agent
}

function Test-LLM {
    Write-Host "=== TEST: LLM Client ===" -ForegroundColor Cyan
    uv run python -m src.llm_client
}

function Show-Logs {
    $logFile = "logs\newsroom.log"
    if (Test-Path $logFile) {
        Get-Content $logFile -Tail 30 -Encoding UTF8
    } else {
        Write-Host "Brak pliku logow: $logFile" -ForegroundColor Yellow
    }
}

function Show-AllLogs {
    $logFile = "logs\newsroom.log"
    if (Test-Path $logFile) {
        Get-Content $logFile -Encoding UTF8
    } else {
        Write-Host "Brak pliku logow: $logFile" -ForegroundColor Yellow
    }
}

function Follow-Logs {
    $logFile = "logs\newsroom.log"
    Write-Host "Sledzenie logow (Ctrl+C aby przerwac)..." -ForegroundColor Yellow
    if (Test-Path $logFile) {
        Get-Content $logFile -Wait -Tail 20 -Encoding UTF8
    } else {
        Write-Host "Brak pliku logow: $logFile" -ForegroundColor Yellow
    }
}

function Clear-Logs {
    $logFile = "logs\newsroom.log"
    if (Test-Path $logFile) {
        Set-Content $logFile -Value "" -Encoding UTF8
        Write-Host "Logi wyczyszczone." -ForegroundColor Green
    } else {
        New-Item -Path $logFile -ItemType File -Force | Out-Null
        Write-Host "Utworzono pusty plik logow." -ForegroundColor Green
    }
}

function Send-ApiTest {
    param([string]$Topic = "sztuczna inteligencja w Polsce 2026")
    
    Write-Host "Wysylam zlecenie: $Topic" -ForegroundColor Cyan
    $body = @{
        topic = $Topic
        max_iterations = 2
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/start-cycle" -Method POST -ContentType "application/json" -Body $body
        $response | ConvertTo-Json
        Write-Host "`nZlecenie wyslane! Sprawdz logi: .\run.ps1 logs-follow" -ForegroundColor Green
    } catch {
        Write-Host "Blad: Czy serwer jest uruchomiony? (.\run.ps1 start)" -ForegroundColor Red
    }
}

function Get-ApiLogs {
    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:8000/logs?lines=50"
    } catch {
        Write-Host "Blad: Czy serwer jest uruchomiony?" -ForegroundColor Red
    }
}

function Get-ApiHealth {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
        $response | ConvertTo-Json
    } catch {
        Write-Host "Serwer nie odpowiada." -ForegroundColor Red
    }
}

function Install-Setup {
    Write-Host "Instaluje zaleznosci..." -ForegroundColor Cyan
    uv sync
    Write-Host "Gotowe!" -ForegroundColor Green
}

function Run-Lint {
    Write-Host "Sprawdzam jakosc kodu..." -ForegroundColor Cyan
    uv run ruff check --fix .
    uv run ruff format .
    Write-Host "Linting zakonczony." -ForegroundColor Green
}

function Clear-Cache {
    Write-Host "Czyszcze cache..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue .pytest_cache, .ruff_cache, .mypy_cache, htmlcov, dist, build
    Get-ChildItem -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Cache wyczyszczony." -ForegroundColor Green
}

# === MAIN ===
switch ($Command.ToLower()) {
    "help"          { Show-Help }
    "start"         { Start-Server }
    "stop"          { Stop-Server }
    "test-research" { Test-Research }
    "test-writer"   { Test-Writer }
    "test-editor"   { Test-Editor }
    "test-llm"      { Test-LLM }
    "logs"          { Show-Logs }
    "logs-all"      { Show-AllLogs }
    "logs-follow"   { Follow-Logs }
    "logs-clear"    { Clear-Logs }
    "api-test"      { Send-ApiTest -Topic $(if ($Arg1) { $Arg1 } else { "sztuczna inteligencja w Polsce 2026" }) }
    "api-logs"      { Get-ApiLogs }
    "api-health"    { Get-ApiHealth }
    "setup"         { Install-Setup }
    "lint"          { Run-Lint }
    "clean"         { Clear-Cache }
    default         { Show-Help }
}
