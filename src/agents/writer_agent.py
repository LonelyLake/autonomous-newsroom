"""
Writer Agent (Tech Journalist) - przekształca ResearchNotes w artykuł Markdown.
Używa promptów z config/prompts.yaml.
Obsługuje feedback od Editora przy rewizjach.
"""

import asyncio
import json

from src.llm_client import get_completion
from src.schemas import ResearchNotes, ArticleDraft, ReviewFeedback
from src.core.prompt_loader import get_agent_config


async def writer_agent(
    research: ResearchNotes,
    feedback: ReviewFeedback | None = None
) -> ArticleDraft:
    """
    Agent Writer - pisze artykuł na podstawie notatek badawczych.
    
    Args:
        research: Notatki z agenta Research
        feedback: Opcjonalny feedback od Editora (przy rewizji)
        
    Returns:
        ArticleDraft: Szkic artykułu w formacie Markdown
    """
    # 1. Ładujemy konfigurację z YAML
    config = get_agent_config("writer")
    system_prompt = config["system_prompt"]
    
    # 2. Formatujemy źródła do czytelnej formy
    sources_text = "\n".join([
        f"- {src.title} ({src.url or 'brak URL'}) - {src.summary}"
        for src in research.sources
    ])
    
    key_facts_text = "\n".join([f"- {fact}" for fact in research.key_facts])
    
    # 3. Wypełniamy szablon prompta
    user_prompt = config["user_prompt_template"].format(
        topic=research.topic,
        sources=sources_text,
        key_facts=key_facts_text,
        suggested_angle=research.suggested_angle
    )
    
    # 4. Jeśli jest feedback od Editora, dodaj go do prompta
    if feedback:
        feedback_section = f"""

=== FEEDBACK OD REDAKTORA (UWZGLĘDNIJ KONIECZNIE!) ===
Poprzednia ocena: {feedback.overall_score}/10
Decyzja: {feedback.decision.value.upper()}

SŁABE STRONY DO POPRAWY:
{chr(10).join(f'- {w}' for w in feedback.weaknesses)}

KONKRETNE SUGESTIE:
{chr(10).join(f'- {s}' for s in feedback.specific_suggestions)}

{f'UWAGI DO FAKTÓW: {feedback.fact_check_notes}' if feedback.fact_check_notes else ''}

WAŻNE: Napisz NOWĄ, ULEPSZONĄ wersję artykułu uwzględniając powyższe uwagi!
"""
        user_prompt += feedback_section
    
    # 5. Wysyłamy prompt do GPT-4
    response = await get_completion(user_prompt, system_prompt)
    
    # 6. Parsujemy JSON
    clean_response = response.strip()
    if clean_response.startswith("```"):
        clean_response = clean_response.split("```")[1]
        if clean_response.startswith("json"):
            clean_response = clean_response[4:]
    
    data = json.loads(clean_response)
    
    # 7. Ustaw wersję draftu
    if feedback:
        # Jeśli to rewizja, zwiększ numer wersji
        data["version"] = getattr(feedback, "_iteration", 1) + 1
    
    # 8. Walidacja przez Pydantic
    return ArticleDraft(**data)


# --- Test agenta ---
if __name__ == "__main__":
    from src.agents.research_agent import research_agent
    
    async def main():
        print("📝 Pipeline: Research → Writer")
        print("=" * 50)
        
        # Krok 1: Research
        print("\n🔍 [1/2] Uruchamiam Research Agent...")
        notes = await research_agent("wpływ AI na rynek pracy w Polsce 2025")
        print(f"   ✅ Zebrano {len(notes.sources)} źródeł, {len(notes.key_facts)} faktów")
        
        # Krok 2: Writer
        print("\n✍️ [2/2] Uruchamiam Writer Agent...")
        draft = await writer_agent(notes)
        
        print(f"\n{'=' * 50}")
        print(f"📰 ARTYKUŁ GOTOWY")
        print(f"{'=' * 50}")
        print(f"\n# {draft.title}\n")
        print(f"**Lead:** {draft.lead}\n")
        print(f"**Treść:**\n{draft.body[:500]}...")
        print(f"\n**Tagi:** {', '.join(draft.tags)}")
        print(f"**Słów:** {draft.word_count}")

    asyncio.run(main())
