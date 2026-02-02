"""
Orchestrator - główna pętla agentowa Autonomous Newsroom.

Implementuje przepływ: Research → Writer → Editor z możliwością rewizji.
Writer otrzymuje feedback od Editora przy kolejnych iteracjach.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.agents.research_agent import research_agent
from src.agents.writer_agent import writer_agent
from src.agents.editor_agent import editor_agent
from src.schemas import ResearchNotes, ArticleDraft, ReviewFeedback, ReviewDecision

logger = logging.getLogger("autonomous-newsroom")


class CycleStatus(str, Enum):
    """Status cyklu generowania artykułu."""
    SUCCESS = "success"           # Artykuł zaakceptowany
    MAX_ITERATIONS = "max_iterations"  # Przekroczono limit
    REJECTED = "rejected"         # Odrzucony bez szans poprawy
    ERROR = "error"               # Błąd w pipeline


@dataclass
class CycleResult:
    """Wynik pełnego cyklu generowania artykułu."""
    status: CycleStatus
    topic: str
    iterations: int
    final_draft: ArticleDraft | None = None
    final_review: ReviewFeedback | None = None
    research_notes: ResearchNotes | None = None
    error_message: str | None = None
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: datetime | None = None
    
    def to_dict(self) -> dict:
        """Konwersja do słownika (dla API response)."""
        result = {
            "status": self.status.value,
            "topic": self.topic,
            "iterations": self.iterations,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }
        if self.final_draft:
            result["article"] = {
                "title": self.final_draft.title,
                "lead": self.final_draft.lead,
                "body": self.final_draft.body[:500] + "..." if len(self.final_draft.body) > 500 else self.final_draft.body,
                "tags": self.final_draft.tags,
                "word_count": self.final_draft.word_count,
            }
        if self.final_review:
            result["review"] = {
                "decision": self.final_review.decision.value,
                "score": self.final_review.overall_score,
                "strengths": self.final_review.strengths,
                "weaknesses": self.final_review.weaknesses,
            }
        if self.error_message:
            result["error"] = self.error_message
        return result


def detect_clickbait(title: str) -> float:
    """
    Prosty detektor clickbaitu (moduł ML).
    
    W przyszłości: zastąpić prawdziwym modelem ML od Inżyniera 1.
    
    Returns:
        float: Score 0.0 (OK) do 1.0 (clickbait)
    """
    clickbait_words = [
        "szok", "nie uwierzysz", "tego nie wiedziałeś", "sekret", 
        "zdradza", "musisz zobaczyć", "niewiarygodne", "hit",
        "sensacja", "pilne", "breaking", "exclusive"
    ]
    title_lower = title.lower()
    
    score = sum(1 for word in clickbait_words if word in title_lower)
    score += title.count("!") * 0.5
    score += title.count("?") * 0.25
    
    # Caps lock = clickbait
    caps_ratio = sum(1 for c in title if c.isupper()) / max(len(title), 1)
    if caps_ratio > 0.3:
        score += 0.5
    
    return min(score * 0.2, 1.0)


async def orchestrate_newsroom_cycle(
    topic: str,
    max_iterations: int = 2
) -> CycleResult:
    """
    Główna pętla agentowa (Orchestrator).
    
    Przepływ:
    1. Research Agent → zbiera fakty
    2. Writer Agent → pisze draft (z opcjonalnym feedbackem)
    3. ML → sprawdza clickbait score
    4. Editor Agent → ocenia i decyduje
    5. Jeśli REVISE → wróć do kroku 2 z feedbackem
    6. Jeśli REJECT lub max_iterations → zakończ
    
    Args:
        topic: Temat artykułu
        max_iterations: Maksymalna liczba prób (domyślnie 2)
        
    Returns:
        CycleResult: Pełny wynik cyklu
    """
    logger.info("=" * 60)
    logger.info(f"ORCHESTRATOR START: '{topic}'")
    logger.info(f"Max iterations: {max_iterations}")
    logger.info("=" * 60)
    
    result = CycleResult(
        status=CycleStatus.ERROR,
        topic=topic,
        iterations=0
    )
    
    try:
        # =====================================================================
        # KROK 1: RESEARCH - zbieranie faktów (wykonywane raz)
        # =====================================================================
        logger.info("\n[STEP 1/4] RESEARCH AGENT")
        logger.info("-" * 40)
        
        research_notes = await research_agent(topic)
        result.research_notes = research_notes
        
        logger.info(f"  Temat: {research_notes.topic}")
        logger.info(f"  Zrodla: {len(research_notes.sources)}")
        logger.info(f"  Fakty: {len(research_notes.key_facts)}")
        logger.info(f"  Sugerowany kat: {research_notes.suggested_angle}")
        
        # Zmienne do przekazywania feedbacku między iteracjami
        previous_feedback: ReviewFeedback | None = None
        article_draft: ArticleDraft | None = None
        review: ReviewFeedback | None = None
        
        # =====================================================================
        # PĘTLA AGENTOWA: Writer → ML → Editor → (feedback) → Writer...
        # =====================================================================
        for iteration in range(1, max_iterations + 1):
            result.iterations = iteration
            
            logger.info(f"\n{'='*60}")
            logger.info(f"ITERATION {iteration}/{max_iterations}")
            logger.info(f"{'='*60}")
            
            # =================================================================
            # KROK 2: WRITER - pisanie/przepisywanie artykułu
            # =================================================================
            logger.info("\n[STEP 2/4] WRITER AGENT")
            logger.info("-" * 40)
            
            if previous_feedback:
                logger.info("  [!] Otrzymano feedback od Editora:")
                for suggestion in previous_feedback.specific_suggestions[:3]:
                    logger.info(f"      - {suggestion}")
            
            # Wywołanie Writer z opcjonalnym feedbackem
            article_draft = await writer_agent(
                research=research_notes,
                feedback=previous_feedback
            )
            result.final_draft = article_draft
            
            logger.info(f"  Tytul: {article_draft.title}")
            logger.info(f"  Slow: {article_draft.word_count}")
            logger.info(f"  Wersja: {article_draft.version}")
            
            # =================================================================
            # KROK 3: ML CLICKBAIT DETECTOR
            # =================================================================
            logger.info("\n[STEP 3/4] ML CLICKBAIT DETECTOR")
            logger.info("-" * 40)
            
            clickbait_score = detect_clickbait(article_draft.title)
            
            if clickbait_score < 0.3:
                cb_status = "OK"
            elif clickbait_score < 0.6:
                cb_status = "WARNING"
            else:
                cb_status = "CLICKBAIT!"
            
            logger.info(f"  Score: {clickbait_score:.2f} [{cb_status}]")
            
            # =================================================================
            # KROK 4: EDITOR - ocena i decyzja
            # =================================================================
            logger.info("\n[STEP 4/4] EDITOR AGENT")
            logger.info("-" * 40)
            
            review = await editor_agent(article_draft, clickbait_score)
            result.final_review = review
            
            logger.info(f"  Decyzja: {review.decision.value.upper()}")
            logger.info(f"  Ocena: {review.overall_score}/10")
            logger.info(f"  Mocne strony: {review.strengths}")
            logger.info(f"  Slabosci: {review.weaknesses}")
            
            # =================================================================
            # LOGIKA DECYZJI
            # =================================================================
            if review.decision == ReviewDecision.APPROVE:
                # SUKCES - artykuł zaakceptowany
                logger.info("\n" + "=" * 60)
                logger.info(">>> ARTICLE APPROVED! <<<")
                logger.info("=" * 60)
                logger.info(f"  Final title: {article_draft.title}")
                logger.info(f"  Iterations: {iteration}")
                logger.info(f"  Final score: {review.overall_score}/10")
                
                result.status = CycleStatus.SUCCESS
                result.finished_at = datetime.now()
                return result
            
            elif review.decision == ReviewDecision.REJECT:
                # ODRZUCONY - zbyt słaby do poprawy
                logger.warning("\n" + "=" * 60)
                logger.warning(">>> ARTICLE REJECTED <<<")
                logger.warning("=" * 60)
                logger.warning(f"  Powod: {review.weaknesses}")
                
                # Przy REJECT próbujemy jeszcze raz (jeśli zostały iteracje)
                if iteration < max_iterations:
                    logger.info("  Probuje ponownie z uwzglednieniem uwag...")
                    previous_feedback = review
                    continue
                else:
                    result.status = CycleStatus.REJECTED
                    result.finished_at = datetime.now()
                    return result
            
            else:  # REVISE
                # WYMAGA POPRAWEK - przekaż feedback do Writera
                logger.info("\n[REVISION REQUIRED]")
                logger.info(f"  Sugestie do poprawy:")
                for i, suggestion in enumerate(review.specific_suggestions, 1):
                    logger.info(f"    {i}. {suggestion}")
                
                if iteration < max_iterations:
                    logger.info(f"  -> Przekazuje feedback do Writer (iteracja {iteration + 1})")
                    previous_feedback = review
                    # Kontynuuj pętlę
                else:
                    logger.warning("  -> Brak pozostalych iteracji")
        
        # Przekroczono max iteracji - artykuł gotowy, ale nie perfekcyjny
        logger.warning("\n" + "=" * 60)
        logger.warning(f"MAX ITERATIONS ({max_iterations}) REACHED")
        logger.warning("=" * 60)
        logger.warning(f"  Ostatni draft: {article_draft.title if article_draft else 'brak'}")
        logger.warning(f"  Ostatnia ocena: {review.overall_score if review else 'brak'}/10")
        logger.info(">>> CYKL ZAKONCZONY - Artykul gotowy (limit iteracji)")
        
        result.status = CycleStatus.MAX_ITERATIONS
        result.finished_at = datetime.now()
        return result
        
    except Exception as e:
        logger.error(f"\n!!! ORCHESTRATOR ERROR: {e}")
        logger.exception("Szczegoly bledu:")
        
        result.status = CycleStatus.ERROR
        result.error_message = str(e)
        result.finished_at = datetime.now()
        return result


# --- Test orchestratora ---
if __name__ == "__main__":
    import asyncio
    
    async def test_orchestrator():
        print("\n" + "=" * 70)
        print("TEST ORCHESTRATOR - Pelny cykl agentowy")
        print("=" * 70)
        
        result = await orchestrate_newsroom_cycle(
            topic="przyszlosc pracy zdalnej w branzy IT",
            max_iterations=2
        )
        
        print("\n" + "=" * 70)
        print("WYNIK KONCOWY")
        print("=" * 70)
        print(f"Status: {result.status.value}")
        print(f"Iteracje: {result.iterations}")
        if result.final_draft:
            print(f"Tytul: {result.final_draft.title}")
        if result.final_review:
            print(f"Ocena: {result.final_review.overall_score}/10")
    
    asyncio.run(test_orchestrator())
