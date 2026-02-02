"""
Loader promptów z pliku YAML.
Centralne miejsce do ładowania konfiguracji agentów.
"""

import os
from pathlib import Path
from typing import Any

import yaml


def get_config_path() -> Path:
    """Zwraca ścieżkę do folderu config/."""
    # Szukamy config/ względem głównego katalogu projektu
    current = Path(__file__).parent.parent.parent  # src/core -> src -> project root
    return current / "config"


def load_prompts() -> dict[str, Any]:
    """
    Ładuje prompty z config/prompts.yaml.
    
    Returns:
        dict: Słownik z konfiguracją wszystkich agentów
    """
    config_path = get_config_path() / "prompts.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Brak pliku prompts.yaml w: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_agent_config(agent_name: str) -> dict[str, Any]:
    """
    Pobiera konfigurację konkretnego agenta.
    
    Args:
        agent_name: Nazwa agenta (researcher, writer, editor)
        
    Returns:
        dict: Konfiguracja agenta z system_prompt i user_prompt_template
    """
    prompts = load_prompts()
    
    if agent_name not in prompts:
        raise KeyError(f"Nieznany agent: {agent_name}. Dostępne: {list(prompts.keys())}")
    
    return prompts[agent_name]


# --- Test ---
if __name__ == "__main__":
    print("Testowanie loadera promptów...")
    
    for agent in ["researcher", "writer", "editor"]:
        config = get_agent_config(agent)
        print(f"\n✅ {config['name']}")
        print(f"   Opis: {config['description']}")
        print(f"   Prompt length: {len(config['system_prompt'])} znaków")
