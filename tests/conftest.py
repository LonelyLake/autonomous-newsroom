"""
Konfiguracja pytest dla Autonomous Newsroom.
Zawiera fixtures i mocki używane w testach.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest


# === Konfiguracja async ===
@pytest.fixture(scope="session")
def event_loop():
    """Tworzy event loop dla testów async."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# === Mock LLM Client ===
@pytest.fixture
def mock_llm_response():
    """Zwraca przykładową odpowiedź LLM."""
    return {
        "research": '''{
            "topic": "Test Topic",
            "sources": [
                {"title": "Source 1", "url": "https://example.com", "summary": "Summary 1", "relevance_score": 0.9}
            ],
            "key_facts": ["Fact 1", "Fact 2"],
            "suggested_angle": "Test angle"
        }''',
        "writer": '''{
            "title": "Test Article Title",
            "lead": "This is a test lead paragraph for the article.",
            "body": "This is the main body of the test article. It contains multiple paragraphs and detailed information about the topic.",
            "tags": ["test", "article"],
            "word_count": 150
        }''',
        "editor": '''{
            "decision": "approve",
            "overall_score": 8.5,
            "strengths": ["Good structure", "Clear writing"],
            "weaknesses": ["Could use more examples"],
            "specific_suggestions": ["Add more data"],
            "fact_check_notes": null,
            "tone_appropriate": true,
            "clickbait_assessment": "OK"
        }'''
    }


@pytest.fixture
def mock_get_completion(mock_llm_response):
    """Mock dla get_completion - zwraca różne odpowiedzi w zależności od prompta."""
    async def _mock_completion(user_prompt: str, system_prompt: str = "", model: str = "gpt-4o-mini"):
        # Sprawdź system_prompt pod kątem słów kluczowych dla każdego agenta
        system_lower = system_prompt.lower()
        user_lower = user_prompt.lower()
        
        # Research Agent - szuka faktów i źródeł
        if "research" in system_lower or "fakty" in system_lower or "źródeł" in system_lower:
            return mock_llm_response["research"]
        # Writer Agent - dziennikarz, pisze artykuły
        elif "dziennikarz" in system_lower or "journalist" in system_lower or "artykuł" in system_lower:
            return mock_llm_response["writer"]
        # Editor Agent - redaktor, ocenia artykuły
        elif "redaktor" in system_lower or "editor" in system_lower or "ocen" in system_lower:
            return mock_llm_response["editor"]
        return '{"error": "Unknown prompt type"}'
    
    return _mock_completion


# === Przykładowe dane testowe ===
@pytest.fixture
def sample_research_notes():
    """Przykładowe notatki badawcze."""
    from src.schemas import ResearchNotes, SourceInfo
    
    return ResearchNotes(
        topic="AI w medycynie",
        sources=[
            SourceInfo(
                title="AI Healthcare Report 2024",
                url="https://example.com/report",
                summary="Raport o zastosowaniu AI w diagnostyce",
                relevance_score=0.95
            ),
            SourceInfo(
                title="Machine Learning in Radiology",
                url="https://example.com/ml-radiology",
                summary="Przegląd zastosowań ML w radiologii",
                relevance_score=0.88
            ),
        ],
        key_facts=[
            "AI zwiększa dokładność diagnostyki o 15%",
            "70% szpitali planuje wdrożenie AI do 2025",
        ],
        suggested_angle="Wpływ AI na przyszłość diagnostyki medycznej"
    )


@pytest.fixture
def sample_article_draft():
    """Przykładowy szkic artykułu."""
    from src.schemas import ArticleDraft, ArticleStatus
    
    return ArticleDraft(
        title="Jak AI rewolucjonizuje diagnostykę medyczną",
        lead="Sztuczna inteligencja zmienia oblicze współczesnej medycyny, oferując narzędzia zwiększające precyzję diagnoz.",
        body="""## Wprowadzenie

Sztuczna inteligencja (AI) staje się nieodłącznym elementem nowoczesnej medycyny. 
Algorytmy uczenia maszynowego są w stanie analizować obrazy medyczne z dokładnością 
przewyższającą ludzkich ekspertów.

## Zastosowania

- Diagnostyka obrazowa (RTG, MRI, CT)
- Analiza wyników laboratoryjnych
- Prognozowanie przebiegu chorób

## Podsumowanie

AI to przyszłość medycyny, która już dziś zmienia życie pacjentów na lepsze.""",
        tags=["AI", "medycyna", "diagnostyka", "technologia"],
        word_count=85,
        status=ArticleStatus.DRAFT,
        version=1
    )


@pytest.fixture
def sample_review_feedback():
    """Przykładowy feedback od editora."""
    from src.schemas import ReviewFeedback, ReviewDecision
    
    return ReviewFeedback(
        decision=ReviewDecision.APPROVE,
        overall_score=8.5,
        strengths=["Dobrze zorganizowana struktura", "Konkretne dane"],
        weaknesses=["Brak więcej przykładów"],
        specific_suggestions=["Dodać case study szpitala"],
        fact_check_notes=None
    )


# === FastAPI Test Client ===
@pytest.fixture
def test_client():
    """Klient testowy FastAPI."""
    from fastapi.testclient import TestClient
    from src.main import app
    
    return TestClient(app)
