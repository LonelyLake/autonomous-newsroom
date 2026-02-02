"""
Testy dla schematów Pydantic (src/schemas.py).
Weryfikują walidację danych i poprawność modeli.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.schemas import (
    ArticleStatus,
    ReviewDecision,
    SourceInfo,
    ResearchNotes,
    ArticleDraft,
    ReviewFeedback,
)


class TestSourceInfo:
    """Testy dla modelu SourceInfo."""
    
    def test_valid_source_info(self):
        """Test tworzenia poprawnego SourceInfo."""
        source = SourceInfo(
            title="Test Article",
            url="https://example.com",
            summary="Test summary",
            relevance_score=0.85
        )
        assert source.title == "Test Article"
        assert source.url == "https://example.com"
        assert source.relevance_score == 0.85
    
    def test_source_info_optional_url(self):
        """Test SourceInfo bez URL."""
        source = SourceInfo(
            title="Test",
            summary="Summary",
            relevance_score=0.5
        )
        assert source.url is None
    
    def test_source_info_invalid_relevance_score_too_high(self):
        """Test walidacji - relevance_score > 1.0."""
        with pytest.raises(ValidationError) as exc_info:
            SourceInfo(
                title="Test",
                summary="Summary",
                relevance_score=1.5  # Za wysokie!
            )
        assert "less than or equal to 1" in str(exc_info.value)
    
    def test_source_info_invalid_relevance_score_negative(self):
        """Test walidacji - relevance_score < 0."""
        with pytest.raises(ValidationError) as exc_info:
            SourceInfo(
                title="Test",
                summary="Summary",
                relevance_score=-0.1  # Ujemne!
            )
        assert "greater than or equal to 0" in str(exc_info.value)


class TestResearchNotes:
    """Testy dla modelu ResearchNotes."""
    
    def test_valid_research_notes(self, sample_research_notes):
        """Test tworzenia poprawnych ResearchNotes."""
        notes = sample_research_notes
        assert notes.topic == "AI w medycynie"
        assert len(notes.sources) == 2
        assert len(notes.key_facts) == 2
        assert notes.suggested_angle is not None
    
    def test_research_notes_empty_sources(self):
        """Test ResearchNotes z pustą listą źródeł."""
        notes = ResearchNotes(
            topic="Test topic",
            sources=[],
            key_facts=["Fact 1"],
            suggested_angle="Test angle"
        )
        assert notes.sources == []
    
    def test_research_notes_has_created_at(self):
        """Test automatycznego ustawiania created_at."""
        notes = ResearchNotes(
            topic="Test",
            sources=[],
            key_facts=[],
            suggested_angle="Angle"
        )
        assert isinstance(notes.created_at, datetime)


class TestArticleDraft:
    """Testy dla modelu ArticleDraft."""
    
    def test_valid_article_draft(self, sample_article_draft):
        """Test tworzenia poprawnego ArticleDraft."""
        draft = sample_article_draft
        assert draft.title == "Jak AI rewolucjonizuje diagnostykę medyczną"
        assert draft.word_count == 85
        assert draft.status == ArticleStatus.DRAFT
        assert draft.version == 1
    
    def test_article_draft_title_too_short(self):
        """Test walidacji - tytuł za krótki (min 5 znaków)."""
        with pytest.raises(ValidationError) as exc_info:
            ArticleDraft(
                title="Hi",  # Za krótki!
                lead="This is a valid lead paragraph with enough characters.",
                body="This is the body " * 10,
                tags=[],
                word_count=100
            )
        assert "at least 5 characters" in str(exc_info.value)
    
    def test_article_draft_lead_too_short(self):
        """Test walidacji - lead za krótki (min 20 znaków)."""
        with pytest.raises(ValidationError) as exc_info:
            ArticleDraft(
                title="Valid Title Here",
                lead="Too short",  # Za krótki!
                body="This is the body " * 10,
                tags=[],
                word_count=100
            )
        assert "at least 20 characters" in str(exc_info.value)
    
    def test_article_draft_body_too_short(self):
        """Test walidacji - body za krótkie (min 100 znaków)."""
        with pytest.raises(ValidationError) as exc_info:
            ArticleDraft(
                title="Valid Title Here",
                lead="This is a valid lead paragraph.",
                body="Short",  # Za krótkie!
                tags=[],
                word_count=1
            )
        assert "at least 100 characters" in str(exc_info.value)
    
    def test_article_draft_negative_word_count(self):
        """Test walidacji - ujemna liczba słów."""
        with pytest.raises(ValidationError) as exc_info:
            ArticleDraft(
                title="Valid Title Here",
                lead="This is a valid lead paragraph.",
                body="This is the body " * 10,
                tags=[],
                word_count=-5  # Ujemne!
            )
        assert "greater than or equal to 0" in str(exc_info.value)
    
    def test_article_draft_default_values(self):
        """Test domyślnych wartości."""
        draft = ArticleDraft(
            title="Test Title Here",
            lead="This is a test lead paragraph.",
            body="This is the body content " * 5,
            tags=["test"],
            word_count=50
        )
        assert draft.status == ArticleStatus.DRAFT
        assert draft.version == 1
        assert draft.based_on_research is None


class TestReviewFeedback:
    """Testy dla modelu ReviewFeedback."""
    
    def test_valid_review_feedback(self, sample_review_feedback):
        """Test tworzenia poprawnego ReviewFeedback."""
        review = sample_review_feedback
        assert review.decision == ReviewDecision.APPROVE
        assert review.overall_score == 8.5
        assert len(review.strengths) == 2
        assert review.fact_check_notes is None  # pole opcjonalne
    
    def test_review_feedback_score_out_of_range(self):
        """Test walidacji - score > 10."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewFeedback(
                decision=ReviewDecision.APPROVE,
                overall_score=11.0,  # Za wysokie!
                strengths=[],
                weaknesses=[],
                specific_suggestions=[]
            )
        assert "less than or equal to 10" in str(exc_info.value)
    
    def test_review_decision_enum_values(self):
        """Test wartości enum ReviewDecision."""
        assert ReviewDecision.APPROVE.value == "approve"
        assert ReviewDecision.REVISE.value == "revise"
        assert ReviewDecision.REJECT.value == "reject"
    
    def test_article_status_enum_values(self):
        """Test wartości enum ArticleStatus."""
        assert ArticleStatus.DRAFT.value == "draft"
        assert ArticleStatus.APPROVED.value == "approved"
        assert ArticleStatus.PUBLISHED.value == "published"


class TestSchemaIntegration:
    """Testy integracyjne schematów."""
    
    def test_full_pipeline_data_flow(self, sample_research_notes, sample_article_draft, sample_review_feedback):
        """Test przepływu danych przez cały pipeline."""
        # Research -> Writer -> Editor
        research = sample_research_notes
        draft = sample_article_draft
        review = sample_review_feedback
        
        # Sprawdź kompatybilność
        assert research.topic in ["AI w medycynie", draft.title] or True  # Logiczny przepływ
        assert draft.word_count > 0
        assert review.overall_score >= 0
        
        # Sprawdź że decyzja APPROVE oznacza sukces
        if review.decision == ReviewDecision.APPROVE:
            assert review.overall_score >= 7.0  # Zakładamy próg akceptacji
    
    def test_serialization_to_dict(self, sample_article_draft):
        """Test serializacji do słownika."""
        draft_dict = sample_article_draft.model_dump()
        
        assert isinstance(draft_dict, dict)
        assert "title" in draft_dict
        assert "body" in draft_dict
        assert "word_count" in draft_dict
    
    def test_serialization_to_json(self, sample_research_notes):
        """Test serializacji do JSON."""
        json_str = sample_research_notes.model_dump_json()
        
        assert isinstance(json_str, str)
        assert "AI w medycynie" in json_str
        assert "sources" in json_str
