"""
Testy dla agentów (src/agents/).
Testują logikę agentów z mockowanym LLM.
"""

import pytest
from unittest.mock import patch, AsyncMock
import json


class TestResearchAgent:
    """Testy dla Research Agent."""
    
    @pytest.mark.asyncio
    async def test_research_agent_returns_research_notes(self, mock_get_completion):
        """Test że research_agent zwraca ResearchNotes."""
        from src.agents.research_agent import research_agent
        from src.schemas import ResearchNotes
        
        with patch("src.agents.research_agent.get_completion", mock_get_completion):
            result = await research_agent("Test topic")
        
        assert isinstance(result, ResearchNotes)
        assert result.topic == "Test Topic"
        assert len(result.sources) > 0
    
    @pytest.mark.asyncio
    async def test_research_agent_has_key_facts(self, mock_get_completion):
        """Test że research_agent zwraca key_facts."""
        from src.agents.research_agent import research_agent
        
        with patch("src.agents.research_agent.get_completion", mock_get_completion):
            result = await research_agent("AI in healthcare")
        
        assert len(result.key_facts) > 0
        assert isinstance(result.key_facts[0], str)
    
    @pytest.mark.asyncio
    async def test_research_agent_has_suggested_angle(self, mock_get_completion):
        """Test że research_agent zwraca suggested_angle."""
        from src.agents.research_agent import research_agent
        
        with patch("src.agents.research_agent.get_completion", mock_get_completion):
            result = await research_agent("Technology trends")
        
        assert result.suggested_angle is not None
        assert len(result.suggested_angle) > 0


class TestWriterAgent:
    """Testy dla Writer Agent."""
    
    @pytest.mark.asyncio
    async def test_writer_agent_returns_article_draft(self, sample_research_notes):
        """Test że writer_agent zwraca ArticleDraft."""
        from src.agents.writer_agent import writer_agent
        from src.schemas import ArticleDraft
        from unittest.mock import patch
        
        # Mock odpowiedzi LLM - body musi mieć min 100 znaków
        mock_response = '''{
            "title": "Test Article Title About AI Technology",
            "lead": "This is a comprehensive test lead paragraph for the article about modern technology.",
            "body": "This is the main body of the test article with detailed content about artificial intelligence and its applications. The article explores various aspects of AI including machine learning, deep learning, and neural networks. These technologies are transforming industries.",
            "tags": ["test", "article", "AI"],
            "word_count": 150
        }'''
        
        async def mock_completion(*args, **kwargs):
            return mock_response
        
        with patch("src.agents.writer_agent.get_completion", mock_completion):
            result = await writer_agent(sample_research_notes)
        
        assert isinstance(result, ArticleDraft)
        assert result.title == "Test Article Title About AI Technology"
        assert len(result.body) >= 100
    
    @pytest.mark.asyncio
    async def test_writer_agent_with_feedback(self, sample_research_notes, sample_review_feedback):
        """Test writer_agent z feedbackiem od editora."""
        from src.agents.writer_agent import writer_agent
        from src.schemas import ArticleDraft, ReviewDecision
        from unittest.mock import patch
        
        # Zmień decyzję na REVISE
        sample_review_feedback.decision = ReviewDecision.REVISE
        
        mock_response = '''{
            "title": "Revised Article Title About Technology",
            "lead": "This is a revised lead paragraph with improvements based on editor feedback.",
            "body": "This is the revised body with improvements and additional content. The article has been enhanced to include more details about the topic, better structure, and clearer explanations of complex concepts. The improvements address all editor suggestions.",
            "tags": ["test", "revised", "improved"],
            "word_count": 160
        }'''
        
        async def mock_completion(*args, **kwargs):
            return mock_response
        
        with patch("src.agents.writer_agent.get_completion", mock_completion):
            result = await writer_agent(sample_research_notes, feedback=sample_review_feedback)
        
        assert result is not None
        assert result.title == "Revised Article Title About Technology"
        assert result.version == 2  # Wersja powinna być zwiększona
    
    @pytest.mark.asyncio
    async def test_writer_agent_generates_tags(self, sample_research_notes):
        """Test że writer_agent generuje tagi."""
        from src.agents.writer_agent import writer_agent
        from unittest.mock import patch
        
        mock_response = '''{
            "title": "Article With Tags About Innovation",
            "lead": "Lead paragraph about technological innovation and its impact on society.",
            "body": "Body content here with enough characters to pass validation. This article discusses various aspects of AI and technology. It covers important topics like machine learning, automation, and digital transformation in modern enterprises.",
            "tags": ["AI", "technology", "innovation"],
            "word_count": 100
        }'''
        
        async def mock_completion(*args, **kwargs):
            return mock_response
        
        with patch("src.agents.writer_agent.get_completion", mock_completion):
            result = await writer_agent(sample_research_notes)
        
        assert isinstance(result.tags, list)
        assert len(result.tags) == 3
        assert "AI" in result.tags


class TestEditorAgent:
    """Testy dla Editor Agent."""
    
    @pytest.mark.asyncio
    async def test_editor_agent_returns_review_feedback(self, sample_article_draft):
        """Test że editor_agent zwraca ReviewFeedback."""
        from src.agents.editor_agent import editor_agent
        from src.schemas import ReviewFeedback
        from unittest.mock import patch
        
        mock_response = '''{
            "decision": "approve",
            "overall_score": 8.5,
            "strengths": ["Good structure", "Clear writing"],
            "weaknesses": ["Could use more examples"],
            "specific_suggestions": ["Add more data"],
            "fact_check_notes": null
        }'''
        
        async def mock_completion(*args, **kwargs):
            return mock_response
        
        with patch("src.agents.editor_agent.get_completion", mock_completion):
            result = await editor_agent(sample_article_draft, clickbait_score=0.1)
        
        assert isinstance(result, ReviewFeedback)
        assert result.decision is not None
    
    @pytest.mark.asyncio
    async def test_editor_agent_returns_score(self, sample_article_draft):
        """Test że editor_agent zwraca overall_score."""
        from src.agents.editor_agent import editor_agent
        from unittest.mock import patch
        
        mock_response = '''{
            "decision": "revise",
            "overall_score": 7.0,
            "strengths": ["Good introduction"],
            "weaknesses": ["Needs more depth"],
            "specific_suggestions": ["Expand section 2"],
            "fact_check_notes": "All facts verified"
        }'''
        
        async def mock_completion(*args, **kwargs):
            return mock_response
        
        with patch("src.agents.editor_agent.get_completion", mock_completion):
            result = await editor_agent(sample_article_draft, clickbait_score=0.0)
        
        assert 0 <= result.overall_score <= 10
        assert result.overall_score == 7.0
    
    @pytest.mark.asyncio
    async def test_editor_agent_with_high_clickbait_score(self, sample_article_draft):
        """Test editor_agent z wysokim clickbait score."""
        from src.agents.editor_agent import editor_agent
        from unittest.mock import patch
        
        mock_response = '''{
            "decision": "reject",
            "overall_score": 4.0,
            "strengths": ["Topic is interesting"],
            "weaknesses": ["Title is too clickbaity", "Misleading content"],
            "specific_suggestions": ["Rewrite title to be more informative"],
            "fact_check_notes": null
        }'''
        
        async def mock_completion(*args, **kwargs):
            return mock_response
        
        with patch("src.agents.editor_agent.get_completion", mock_completion):
            result = await editor_agent(sample_article_draft, clickbait_score=0.9)
        
        # Agent powinien zwrócić feedback niezależnie od clickbait score
        assert result is not None
        assert result.overall_score == 4.0


class TestClickbaitDetector:
    """Testy dla detektora clickbaitu."""
    
    def test_detect_clickbait_clean_title(self):
        """Test czystego tytułu (brak clickbaitu)."""
        from src.core.orchestrator import detect_clickbait
        
        score = detect_clickbait("Analiza wpływu AI na rynek pracy w 2024 roku")
        
        assert score < 0.3  # Niski score = dobry tytuł
    
    def test_detect_clickbait_obvious_clickbait(self):
        """Test oczywistego clickbaitu."""
        from src.core.orchestrator import detect_clickbait
        
        score = detect_clickbait("SZOK! Nie uwierzysz co się stało!")
        
        assert score > 0.3  # Wyższy score = clickbait
    
    def test_detect_clickbait_exclamation_marks(self):
        """Test wykrywania wykrzykników."""
        from src.core.orchestrator import detect_clickbait
        
        score_clean = detect_clickbait("Nowe badania o AI")
        score_exclaim = detect_clickbait("Nowe badania o AI!!!")
        
        assert score_exclaim > score_clean
    
    def test_detect_clickbait_question_marks(self):
        """Test wykrywania znaków zapytania."""
        from src.core.orchestrator import detect_clickbait
        
        score = detect_clickbait("Co będzie z rynkiem pracy???")
        
        assert score >= 0  # Powinien być jakiś score
    
    def test_detect_clickbait_returns_max_1(self):
        """Test że score nie przekracza 1.0."""
        from src.core.orchestrator import detect_clickbait
        
        # Tytuł z wieloma triggerami
        title = "SZOK! NIE UWIERZYSZ! SEKRET! SENSACJA!!!"
        score = detect_clickbait(title)
        
        assert score <= 1.0


class TestPromptLoader:
    """Testy dla loadera promptów."""
    
    def test_load_prompts(self):
        """Test ładowania promptów z YAML."""
        from src.core.prompt_loader import load_prompts
        
        prompts = load_prompts()
        
        assert isinstance(prompts, dict)
        assert "researcher" in prompts
        assert "writer" in prompts
        assert "editor" in prompts
    
    def test_get_agent_config_researcher(self):
        """Test pobierania konfiguracji Research Agent."""
        from src.core.prompt_loader import get_agent_config
        
        config = get_agent_config("researcher")
        
        assert "system_prompt" in config
        assert "user_prompt_template" in config
        assert "name" in config
    
    def test_get_agent_config_writer(self):
        """Test pobierania konfiguracji Writer Agent."""
        from src.core.prompt_loader import get_agent_config
        
        config = get_agent_config("writer")
        
        assert "system_prompt" in config
        assert len(config["system_prompt"]) > 100  # Prompt powinien być długi
    
    def test_get_agent_config_editor(self):
        """Test pobierania konfiguracji Editor Agent."""
        from src.core.prompt_loader import get_agent_config
        
        config = get_agent_config("editor")
        
        assert "system_prompt" in config
        assert "redaktor" in config["system_prompt"].lower() or "editor" in config["system_prompt"].lower()
    
    def test_get_agent_config_invalid_agent(self):
        """Test błędu dla nieistniejącego agenta."""
        from src.core.prompt_loader import get_agent_config
        
        with pytest.raises(KeyError):
            get_agent_config("nonexistent_agent")
