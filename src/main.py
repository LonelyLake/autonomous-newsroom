import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/newsroom.log"), logging.StreamHandler()],
)
logger = logging.getLogger("NewsroomOrchestrator")


class NewsRequest(BaseModel):
    topic: str
    max_iterations: int = 3


async def run_newsroom_cycle(topic: str):
    """This is a function to be filled in by Blajost in the future."""
    logger.info(f"Rozpoczynam cykl newsowy dla tematu: {topic}")

    # Symulacja opóźnienia (Research)
    await asyncio.sleep(2)
    logger.info("[Researcher] Znalazłem 3 artykuły.")
    # Symulacja opóźnienia (Writing)
    await asyncio.sleep(2)
    logger.info("[Writer] Draft gotowy.")

    logger.info("Cykl zakończony. Artykuł gotowy.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("System Newsroom uruchomiony.")
    yield
    logger.info("System Newsroom zatrzymany.")


app = FastAPI(title="Autonomous Newsroom API", lifespan=lifespan)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Autonomous Newsroom API. Go to /docs for API explorer."
    }


@app.get("/health")
async def health_check():
    return {"status": "active", "system": "Newsroom v1.0"}


@app.post("/start-cycle")
async def start_cycle(request: NewsRequest, background_tasks: BackgroundTasks):
    """
    Endpoint asynchroniczny - tylko przyjmuje zlecenie.
    Praca agentów dzieje się w tle (BackgroundTasks).
    """
    logger.info(f"Otrzymano zlecenie: {request.topic}")

    background_tasks.add_task(run_newsroom_cycle, request.topic)

    return {
        "message": "Zlecenie przyjęte. Agenty rozpoczynają pracę.",
        "topic": request.topic,
        "status": "processing",
    }
