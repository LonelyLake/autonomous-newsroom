"""
Research Agent - zbiera twarde fakty i źródła na dany temat.
Używa promptów z config/prompts.yaml.
"""

import asyncio
import json

from src.llm_client import get_completion
from src.schemas import ResearchNotes
from src.core.prompt_loader import get_agent_config


async def research_agent(topic: str) -> ResearchNotes:
    """
    Agent Research - zbiera informacje na temat.
    
    Args:
        topic: Temat do zbadania
        
    Returns:
        ResearchNotes: Ustrukturyzowane notatki badawcze
    """
    # 1. Ładujemy konfigurację z YAML
    config = get_agent_config("researcher")
    system_prompt = config["system_prompt"]
    user_prompt = config["user_prompt_template"].format(topic=topic)
    
    # 2. Wysyłamy prompt do GPT-4
    response = await get_completion(user_prompt, system_prompt)
    
    # 3. Parsujemy JSON (usuwamy ewentualne markdown code blocks)
    clean_response = response.strip()
    if clean_response.startswith("```"):
        clean_response = clean_response.split("```")[1]
        if clean_response.startswith("json"):
            clean_response = clean_response[4:]
    
    data = json.loads(clean_response)
    
    # 4. Walidacja przez Pydantic (schema)
    return ResearchNotes(**data)


# --- Test agenta ---
if __name__ == "__main__":
    async def main():
        print("🔍 Uruchamiam Research Agent...")
        print("-" * 50)
        
        notes = await research_agent("wykorzystanie AI w polskich mediach")
        
        print(f"\n📋 Temat: {notes.topic}")
        print(f"\n📰 Znalezione źródła ({len(notes.sources)}):")
        for src in notes.sources:
            print(f"   • {src.title} (trafność: {src.relevance_score})")
        
        print(f"\n✅ Kluczowe fakty:")
        for fact in notes.key_facts:
            print(f"   • {fact}")
        
        print(f"\n💡 Sugerowany kąt: {notes.suggested_angle}")

    asyncio.run(main())
