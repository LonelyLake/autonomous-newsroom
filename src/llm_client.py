import os
import logging
from openai import AsyncOpenAI
from dotenv import load_dotenv

# 1. Ładowanie zmiennych środowiskowych (klucza API)
load_dotenv()

# Konfiguracja loggera, żeby widzieć co się dzieje w konsoli
logger = logging.getLogger("newsroom_llm")
logging.basicConfig(level=logging.INFO)

# 2. Lazy initialization - klient tworzony dopiero przy pierwszym użyciu
_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    """Zwraca klienta GitHub Models (lazy initialization)."""
    global _client
    if _client is None:
        api_key = os.environ.get("GITHUB_TOKEN")
        if not api_key:
            raise ValueError("Brak GITHUB_TOKEN w zmiennych środowiskowych! Sprawdź plik .env")
        _client = AsyncOpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=api_key,
        )
    return _client

async def get_completion(
    user_prompt: str, 
    system_prompt: str = "Jesteś pomocnym asystentem AI.", 
    model: str = "gpt-4o-mini"
) -> str:
    """
    Wysyła zapytanie do modelu LLM (GitHub Models) i zwraca treść odpowiedzi.
    
    Args:
        user_prompt (str): Treść zadania dla agenta.
        system_prompt (str): Rola agenta (np. "Jesteś surowym redaktorem").
        model (str): Nazwa modelu (domyślnie gpt-4o-mini lub Llama-3.1).
        
    Returns:
        str: Odpowiedź modelu.
    """
    try:
        logger.info(f"🤖 Wysyłanie zapytania do modelu: {model}...")
        
        response = await _get_client().chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7, # Kreatywność (0.0 = robot, 1.0 = artysta)
        )
        
        content = response.choices[0].message.content
        logger.info("✅ Otrzymano odpowiedź.")
        return content

    except Exception as e:
        logger.error(f"❌ Błąd podczas komunikacji z LLM: {e}")
        # W przypadku błędu zwracamy pusty string lub komunikat, 
        # żeby program się nie wywalił całkowicie (zgodnie z planem obsługi błędów).
        return f"ERROR: Nie udało się uzyskać odpowiedzi. Powód: {str(e)}"

# --- Sekcja testowa (uruchomi się tylko przy bezpośrednim wywołaniu pliku) ---
if __name__ == "__main__":
    import asyncio

    async def test_run():
        print("Testowanie połączenia z GitHub Models...")
        answer = await get_completion(
            user_prompt="Opowiedz krótki żart o programistach.",
            system_prompt="Jesteś komikiem."
        )
        print(f"\nOdpowiedź modelu:\n{answer}")

    asyncio.run(test_run())