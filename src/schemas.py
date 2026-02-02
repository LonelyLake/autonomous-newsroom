"""
Kontrakty danych (Schemas) dla Autonomous Newsroom.

Te klasy Pydantic definiują sztywny format JSON dla komunikacji między agentami.
Dzięki temu unikamy "luźnego tekstu" i mamy walidację danych.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ArticleStatus(str, Enum):
    """Status artykułu w pipeline."""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    NEEDS_REVISION = "needs_revision"
    APPROVED = "approved"
    PUBLISHED = "published"


class ReviewDecision(str, Enum):
    """Decyzja recenzenta."""
    APPROVE = "approve"
    REVISE = "revise"
    REJECT = "reject"


# --- Research Agent Output ---

class SourceInfo(BaseModel):
    """Informacja o pojedynczym źródle."""
    title: str = Field(..., description="Tytuł artykułu/źródła")
    url: str | None = Field(None, description="URL źródła (jeśli dostępny)")
    summary: str = Field(..., description="Krótkie podsumowanie treści")
    relevance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Ocena trafności (0.0-1.0)"
    )


class ResearchNotes(BaseModel):
    """
    Output agenta Research.
    Zawiera zebrane informacje i źródła na dany temat.
    """
    topic: str = Field(..., description="Temat badania")
    sources: list[SourceInfo] = Field(
        default_factory=list, description="Lista znalezionych źródeł"
    )
    key_facts: list[str] = Field(
        default_factory=list, description="Kluczowe fakty do wykorzystania"
    )
    suggested_angle: str = Field(
        ..., description="Sugerowany kąt/perspektywa artykułu"
    )
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "AI w dziennikarstwie",
                "sources": [
                    {
                        "title": "How AI is transforming newsrooms",
                        "url": "https://example.com/ai-news",
                        "summary": "Artykuł o automatyzacji w redakcjach",
                        "relevance_score": 0.85,
                    }
                ],
                "key_facts": [
                    "80% redakcji testuje narzędzia AI",
                    "Automatyzacja raportów sportowych i finansowych",
                ],
                "suggested_angle": "Wpływ AI na jakość dziennikarstwa śledczego",
            }
        }


# --- Writer Agent Output ---

class ArticleDraft(BaseModel):
    """
    Output agenta Writer.
    Szkic artykułu gotowy do recenzji.
    """
    title: str = Field(..., min_length=5, max_length=200, description="Tytuł artykułu")
    lead: str = Field(..., min_length=20, max_length=500, description="Lead/wprowadzenie")
    body: str = Field(..., min_length=100, description="Treść główna artykułu")
    tags: list[str] = Field(default_factory=list, description="Tagi/słowa kluczowe")
    word_count: int = Field(..., ge=0, description="Liczba słów")
    status: ArticleStatus = Field(default=ArticleStatus.DRAFT)
    based_on_research: str | None = Field(
        None, description="ID notatek badawczych (powiązanie)"
    )
    version: int = Field(default=1, ge=1, description="Numer wersji draftu")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Jak sztuczna inteligencja zmienia redakcje",
                "lead": "Automatyzacja wkracza do newsroomów. Sprawdzamy, co to oznacza dla dziennikarzy.",
                "body": "Treść artykułu o AI w dziennikarstwie...",
                "tags": ["AI", "dziennikarstwo", "technologia"],
                "word_count": 850,
                "status": "draft",
                "version": 1,
            }
        }


# --- Editor/Reviewer Agent Output ---

class ReviewFeedback(BaseModel):
    """
    Output agenta Editor/Reviewer.
    Feedback i ocena artykułu.
    """
    decision: ReviewDecision = Field(..., description="Decyzja: approve/revise/reject")
    overall_score: float = Field(
        ..., ge=0.0, le=10.0, description="Ogólna ocena (0-10)"
    )
    strengths: list[str] = Field(
        default_factory=list, description="Mocne strony artykułu"
    )
    weaknesses: list[str] = Field(
        default_factory=list, description="Słabe strony do poprawy"
    )
    specific_suggestions: list[str] = Field(
        default_factory=list, description="Konkretne sugestie zmian"
    )
    fact_check_notes: str | None = Field(
        None, description="Uwagi dotyczące weryfikacji faktów"
    )
    reviewed_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "decision": "revise",
                "overall_score": 7.5,
                "strengths": [
                    "Dobry lead przyciągający uwagę",
                    "Solidne źródła",
                ],
                "weaknesses": [
                    "Brak cytatu z ekspertem",
                    "Zbyt długie akapity",
                ],
                "specific_suggestions": [
                    "Dodaj wypowiedź dziennikarza pracującego z AI",
                    "Podziel akapit 3 na dwa mniejsze",
                ],
                "fact_check_notes": "Sprawdzić statystykę o 80% redakcji",
            }
        }


# --- Pipeline Communication ---

class AgentMessage(BaseModel):
    """
    Uniwersalny format wiadomości między agentami.
    Używany do orkiestracji w pipeline.
    """
    from_agent: str = Field(..., description="Nazwa agenta nadawcy")
    to_agent: str = Field(..., description="Nazwa agenta odbiorcy")
    message_type: str = Field(..., description="Typ wiadomości: research/draft/review")
    payload: ResearchNotes | ArticleDraft | ReviewFeedback = Field(
        ..., description="Dane wiadomości"
    )
    timestamp: datetime = Field(default_factory=datetime.now)
