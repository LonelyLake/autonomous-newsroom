import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import orchestratora
from src.core.orchestrator import orchestrate_newsroom_cycle, CycleStatus

# --- KONFIGURACJA ŚCIEŻEK ---
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = Path(__file__).parent
TEMPLATES_DIR = SRC_DIR / "templates"
STATIC_DIR = SRC_DIR / "static"
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "newsroom.log"

# Konfiguracja loggera
logger = logging.getLogger("autonomous-newsroom")
logger.setLevel(logging.INFO)
logger.handlers.clear()  # Czyścimy poprzednie handlery

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Handler do pliku (UTF-8)
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8", mode="a")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

# Handler do konsoli
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

# Zapobiegamy propagacji do root loggera
logger.propagate = False


# --- MODELE DANYCH ---
class NewsRequest(BaseModel):
    topic: str
    max_iterations: int = 2  # Domyślnie 2 pętle (zgodnie z instrukcją)


# --- PRZECHOWYWANIE OSTATNIEGO WYNIKU ---
# Przechowujemy pełny wynik ostatniego cyklu (z pełnym artykułem)
_last_result: dict | None = None


# --- WRAPPER DLA ORCHESTRATORA ---
async def run_newsroom_cycle(topic: str, max_iterations: int = 2) -> dict:
    """
    Wrapper wywołujący orchestrator z pętlą feedback.
    Orchestrator realizuje: Research → Writer → Editor (z przekazywaniem uwag)
    """
    global _last_result
    logger.info(f">>> START CYKLU: '{topic}'")
    
    try:
        result = await orchestrate_newsroom_cycle(topic, max_iterations)
        
        # Zapisz pełny wynik (z pełnym artykułem) do zmiennej globalnej
        _last_result = _build_full_result(result)
        
        # Logujemy wynik końcowy
        if result.status == CycleStatus.SUCCESS:
            logger.info(">>> ARTYKUL ZAAKCEPTOWANY!")
            if result.final_draft:
                logger.info(f"TYTUL: {result.final_draft.title}")
                logger.info(f"LEAD: {result.final_draft.lead}")
        elif result.status == CycleStatus.REJECTED:
            logger.warning(f"XXX ARTYKUL ODRZUCONY: {result.error_message}")
        elif result.status == CycleStatus.MAX_ITERATIONS:
            logger.warning(f"!!! Przekroczono limit {max_iterations} iteracji")
        else:
            logger.error(f"XXX BLAD: {result.error_message}")
        
        return result.to_dict()
        
    except Exception as e:
        logger.error(f"XXX BLAD W PIPELINE: {e}")
        _last_result = {"status": "error", "message": str(e)}
        return _last_result


def _build_full_result(result) -> dict:
    """Buduje pełny słownik wyniku z CAŁYM artykułem (nie skróconym)."""
    data = {
        "status": result.status.value,
        "topic": result.topic,
        "iterations": result.iterations,
    }
    
    if result.final_draft:
        data["article"] = {
            "title": result.final_draft.title,
            "lead": result.final_draft.lead,
            "body": result.final_draft.body,  # PEŁNY artykuł!
            "tags": result.final_draft.tags,
            "word_count": result.final_draft.word_count,
            "version": result.final_draft.version,
        }
    
    if result.final_review:
        data["review"] = {
            "decision": result.final_review.decision.value,
            "score": result.final_review.overall_score,
            "strengths": result.final_review.strengths,
            "weaknesses": result.final_review.weaknesses,
            "suggestions": result.final_review.specific_suggestions,
        }
    
    if result.error_message:
        data["error"] = result.error_message
    
    return data


# --- CYKL ŻYCIA APLIKACJI ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SYSTEM: Newsroom API uruchomione.")
    yield
    logger.info("SYSTEM: Newsroom API zatrzymane.")


app = FastAPI(
    title="Autonomous Newsroom API",
    description="Infrastruktura przygotowana przez Engineer 1",
    lifespan=lifespan,
)

# --- MONTOWANIE PLIKÓW STATYCZNYCH ---
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# --- ENDPOINTY ---
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serwuje główny interfejs graficzny."""
    html_file = TEMPLATES_DIR / "index.html"
    if html_file.exists():
        return html_file.read_text(encoding="utf-8")
    return HTMLResponse("<h1>Brak pliku index.html</h1>", status_code=404)


@app.get("/api")
async def api_info():
    """Informacje o API."""
    return {"status": "ok", "message": "Newsroom API is ready. Go to /docs"}


@app.post("/start-cycle")
async def start_cycle(request: NewsRequest, background_tasks: BackgroundTasks):
    """
    Główny endpoint startujący pracę agentów.
    Zwraca natychmiastową odpowiedź, a praca trwa w tle.
    """
    global _last_result
    
    # Wyczyść poprzednie logi i wynik - nowy cykl = czysty start
    if LOG_FILE.exists():
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("")  # Wyczyść plik
    _last_result = None
    
    logger.info(f"API: Otrzymano żądanie cyklu dla tematu: {request.topic}")

    # Przekazanie zadania do wykonania w tle
    background_tasks.add_task(run_newsroom_cycle, request.topic, request.max_iterations)

    return {
        "message": "Zlecenie przyjęte. Agenty pracują w tle.",
        "topic": request.topic,
        "max_iterations": request.max_iterations,
        "status": "processing",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "autonomous-newsroom"}


@app.get("/last-result")
async def get_last_result():
    """
    Zwraca pełny wynik ostatniego cyklu (z całym artykułem).
    Używane przez frontend do wyświetlania artykułu.
    """
    if _last_result is None:
        return {"status": "no_result", "message": "Brak wyników. Uruchom cykl."}
    return _last_result


@app.get("/logs", response_class=PlainTextResponse)
async def get_logs(lines: int = 50):
    """
    Pobiera ostatnie linie z pliku logów.
    Użycie: GET /logs?lines=100
    """
    if not LOG_FILE.exists():
        return "Brak pliku logów."
    
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
    
    # Zwróć ostatnie N linii
    last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
    return "".join(last_lines)


@app.delete("/logs")
async def clear_logs():
    """Czyści plik logów."""
    if LOG_FILE.exists():
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("")
        logger.info("Logi wyczyszczone przez API.")
        return {"message": "Logi wyczyszczone."}
    return {"message": "Brak pliku logów do wyczyszczenia."}
