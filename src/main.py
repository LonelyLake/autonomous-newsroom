import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel

# --- KONFIGURACJA LOGOWANIA ---
logger = logging.getLogger("autonomous-newsroom")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Wyjście na konsolę (widoczne w docker logs)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Wyjście do pliku (dla trwałości logów)
file_handler = logging.FileHandler("newsroom.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# --- MODELE DANYCH (Tymczasowe, dopóki Blazejost nie stworzy schemas.py) ---
class NewsRequest(BaseModel):
    topic: str
    max_iterations: int = 3


# --- LOGIKA TŁA (Miejsce na AI Logic) ---
async def run_newsroom_cycle(topic: str):
    """
    Funkcja wykonywana asynchronicznie w tle.
    Tutaj Blazejost zaimplementuje agentów.
    """
    logger.info(f"PROCES TŁA: Rozpoczynam cykl dla tematu: {topic}")

    # Symulacja kroków inżynierskich
    await asyncio.sleep(1)
    logger.info(f"[Zadanie: Research] Przeszukiwanie źródeł dla: {topic}...")

    await asyncio.sleep(2)
    logger.info("[Zadanie: Writing] Generowanie szkicu artykułu...")

    await asyncio.sleep(1)
    logger.info("PROCES TŁA: Cykl zakończony sukcesem.")


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


# --- ENDPOINTY ---
@app.get("/")
async def root():
    return {"status": "ok", "message": "Newsroom Infrastructure is ready. Go to /docs"}


@app.post("/start-cycle")
async def start_cycle(request: NewsRequest, background_tasks: BackgroundTasks):
    """
    Główny endpoint startujący pracę agentów.
    Zwraca natychmiastową odpowiedź, a praca trwa w tle.
    """
    logger.info(f"API: Otrzymano żądanie cyklu dla tematu: {request.topic}")

    # Przekazanie zadania do wykonania w tle
    background_tasks.add_task(run_newsroom_cycle, request.topic)

    return {
        "message": "Zlecenie przyjęte. Agenty pracują w tle.",
        "topic": request.topic,
        "status": "processing",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "autonomous-newsroom"}
