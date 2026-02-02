"""
Editor Agent - krytycznie ocenia artykuły i podejmuje decyzje redakcyjne.
Używa promptów z config/prompts.yaml.
Uwzględnia Clickbait Score z modułu ML.
"""

import asyncio
import json

from src.llm_client import get_completion
from src.schemas import ArticleDraft, ReviewFeedback, ReviewDecision
from src.core.prompt_loader import get_agent_config


async def editor_agent(
    draft: ArticleDraft, 
    clickbait_score: float = 0.0
) -> ReviewFeedback:
    """
    Agent Editor - ocenia artykuł i podejmuje decyzję redakcyjną.
    
    Args:
        draft: Szkic artykułu od Writer Agent
        clickbait_score: Wynik z modułu ML (0.0 = OK, 1.0 = clickbait)
        
    Returns:
        ReviewFeedback: Ocena i decyzja (ACCEPT/REVISE/REJECT)
    """
    # 1. Ładujemy konfigurację z YAML
    config = get_agent_config("editor")
    system_prompt = config["system_prompt"]
    
    # 2. Wypełniamy szablon prompta
    user_prompt = config["user_prompt_template"].format(
        title=draft.title,
        lead=draft.lead,
        body=draft.body,
        tags=", ".join(draft.tags),
        word_count=draft.word_count,
        clickbait_score=f"{clickbait_score:.2f}"
    )
    
    # 3. Wysyłamy prompt do GPT-4
    response = await get_completion(user_prompt, system_prompt)
    
    # 4. Parsujemy JSON
    clean_response = response.strip()
    if clean_response.startswith("```"):
        clean_response = clean_response.split("```")[1]
        if clean_response.startswith("json"):
            clean_response = clean_response[4:]
    
    data = json.loads(clean_response)
    
    # 5. Mapowanie decision string na enum
    decision_map = {
        "approve": ReviewDecision.APPROVE,
        "revise": ReviewDecision.REVISE,
        "reject": ReviewDecision.REJECT,
    }
    data["decision"] = decision_map.get(data["decision"].lower(), ReviewDecision.REVISE)
    
    # 6. Walidacja przez Pydantic
    return ReviewFeedback(**data)


# --- Test pełnego pipeline ---
if __name__ == "__main__":
    from src.agents.research_agent import research_agent
    from src.agents.writer_agent import writer_agent
    
    # Symulacja modułu ML (w przyszłości zastąpiony prawdziwym modelem)
    def mock_clickbait_detector(title: str) -> float:
        """
        Tymczasowy detektor clickbaitu.
        W przyszłości: model ML od Inżyniera 1.
        """
        clickbait_words = [
            "szok", "nie uwierzysz", "tego nie wiedziałeś",
            "sekret", "zdradza", "!", "?"
        ]
        title_lower = title.lower()
        score = sum(1 for word in clickbait_words if word in title_lower)
        return min(score * 0.25, 1.0)  # Max 1.0
    
    async def main():
        print("🔄 PEŁNY PIPELINE: Research → Writer → Editor")
        print("=" * 60)
        
        # === KROK 1: RESEARCH ===
        print("\n🔍 [1/3] Research Agent...")
        notes = await research_agent("przyszłość pracy zdalnej w IT")
        print(f"   ✅ Źródła: {len(notes.sources)}, Fakty: {len(notes.key_facts)}")
        
        # === KROK 2: WRITER ===
        print("\n✍️ [2/3] Writer Agent...")
        draft = await writer_agent(notes)
        print(f"   ✅ Artykuł: '{draft.title}' ({draft.word_count} słów)")
        
        # === KROK 3: ML CLICKBAIT DETECTION ===
        clickbait_score = mock_clickbait_detector(draft.title)
        print(f"\n🤖 [ML] Clickbait Score: {clickbait_score:.2f}")
        
        # === KROK 4: EDITOR ===
        print("\n📋 [3/3] Editor Agent...")
        review = await editor_agent(draft, clickbait_score)
        
        # === WYNIK ===
        print(f"\n{'=' * 60}")
        print(f"📊 DECYZJA REDAKCYJNA")
        print(f"{'=' * 60}")
        
        decision_emoji = {
            ReviewDecision.APPROVE: "✅ ACCEPT",
            ReviewDecision.REVISE: "🔄 REVISE",
            ReviewDecision.REJECT: "❌ REJECT",
        }
        
        print(f"\n{decision_emoji[review.decision]} (Ocena: {review.overall_score}/10)")
        
        print(f"\n💪 Mocne strony:")
        for s in review.strengths:
            print(f"   • {s}")
        
        print(f"\n⚠️ Do poprawy:")
        for w in review.weaknesses:
            print(f"   • {w}")
        
        print(f"\n💡 Sugestie:")
        for s in review.specific_suggestions:
            print(f"   • {s}")
        
        if review.fact_check_notes:
            print(f"\n🔎 Fact-check: {review.fact_check_notes}")

    asyncio.run(main())
