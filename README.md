# �️ Autonomous Newsroom

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

> **AI-powered multi-agent system for automated article generation with iterative feedback loop.**

System wieloagentowy wykorzystujący LLM (GPT-4o-mini via GitHub Models) do automatycznego generowania wysokiej jakości artykułów. Pipeline składa się z trzech wyspecjalizowanych agentów: **Researcher**, **Writer** i **Editor**, którzy współpracują w iteracyjnej pętli feedback aż do uzyskania artykułu spełniającego standardy redakcyjne.

---

## ✨ Kluczowe funkcje

| Funkcja | Opis |
|---------|------|
| 🔍 **Research Agent** | Zbiera twarde fakty i wiarygodne źródła na dany temat |
| ✍️ **Writer Agent** | Generuje angażujące artykuły w formacie Markdown |
| 📋 **Editor Agent** | Krytycznie ocenia i decyduje: APPROVE / REVISE / REJECT |
| 🔄 **Feedback Loop** | Iteracyjne dopracowywanie artykułu na podstawie uwag redaktora |
| 🤖 **Clickbait Detector** | Wykrywa nagłówki typu clickbait (heurystyczny + ML-ready) |
| 🌐 **Web UI** | Intuicyjny interfejs z logami na żywo |
| 🐳 **Docker Ready** | Gotowy do wdrożenia w kontenerze |

---

## 🏗️ Architektura

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AUTONOMOUS NEWSROOM                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│   │  👤 User │───▶│ 🔍Research│───▶│ ✍️ Writer │───▶│ 📋 Editor│     │
│   │  (topic) │    │   Agent  │    │   Agent  │    │   Agent  │     │
│   └──────────┘    └──────────┘    └──────────┘    └────┬─────┘     │
│                                         ▲              │            │
│                                         │   REVISE     │            │
│                                         └──────────────┘            │
│                                                │                     │
│                                         APPROVE│REJECT               │
│                                                ▼                     │
│                                   ┌────────────────────┐            │
│                                   │   📰 Final Article │            │
│                                   └────────────────────┘            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Przepływ danych

| Krok | Agent | Input | Output | Opis |
|------|-------|-------|--------|------|
| 1 | Research Agent | `topic: str` | `ResearchNotes` | Zbiera 3-5 źródeł i kluczowe fakty |
| 2 | Writer Agent | `ResearchNotes` + `feedback?` | `ArticleDraft` | Pisze artykuł Markdown |
| 3 | ML Module | `title: str` | `clickbait_score` | Ocena 0.0-1.0 |
| 4 | Editor Agent | `ArticleDraft` + `score` | `ReviewFeedback` | Decyzja redakcyjna |

---

## 🚀 Szybki start

### Wymagania

- **Python 3.12+**
- **[uv](https://github.com/astral-sh/uv)** - szybki menedżer pakietów
- **GitHub Token** z dostępem do [GitHub Models](https://github.com/marketplace/models)

### Instalacja

```bash
# 1. Klonowanie repozytorium
git clone https://github.com/your-username/autonomous-newsroom.git
cd autonomous-newsroom

# 2. Instalacja zależności
uv sync

# 3. Konfiguracja
cp .env.example .env
# Edytuj .env i dodaj swój GITHUB_TOKEN
```

### Uruchomienie

```bash
# Serwer deweloperski
just run

# lub bezpośrednio
uv run uvicorn src.main:app --reload --port 8000
```

🌐 Otwórz: **http://127.0.0.1:8000**

### Docker

```bash
docker-compose up -d
```

---

## 📖 Użycie

### Web UI

1. Otwórz http://127.0.0.1:8000
2. Wpisz temat artykułu (np. *"AI w medycynie"*)
3. Wybierz liczbę iteracji (2-5)
4. Kliknij **"Uruchom agentów"**
5. Obserwuj logi na żywo → artykuł pojawi się po prawej

### REST API

```bash
# Uruchom cykl generowania
curl -X POST http://127.0.0.1:8000/start-cycle \
  -H "Content-Type: application/json" \
  -d '{"topic": "przyszłość pracy zdalnej", "max_iterations": 3}'

# Pobierz wynik
curl http://127.0.0.1:8000/last-result

# Logi (ostatnie 50 linii)
curl http://127.0.0.1:8000/logs?lines=50

# Health check
curl http://127.0.0.1:8000/health
```

### CLI - Testowanie agentów

```bash
just test-research      # Test Research Agent
just test-writer        # Test Writer Agent  
just test-editor        # Test pełnego pipeline
just test-orchestrator  # Test Orchestratora z feedback loop
```

---

## 📁 Struktura projektu

```
autonomous-newsroom/
├── config/
│   └── prompts.yaml           # 🎯 Konfiguracja promptów (YAML)
├── src/
│   ├── agents/
│   │   ├── research_agent.py  # 🔍 Zbieranie faktów
│   │   ├── writer_agent.py    # ✍️ Generowanie artykułów
│   │   └── editor_agent.py    # 📋 Ocena redakcyjna
│   ├── core/
│   │   ├── orchestrator.py    # 🔄 Główna pętla agentowa
│   │   └── prompt_loader.py   # 📂 Loader YAML
│   ├── static/                # 🎨 CSS, JavaScript
│   ├── templates/             # 🖼️ HTML (Jinja2)
│   ├── llm_client.py          # 🤖 Klient GitHub Models
│   ├── schemas.py             # 📋 Modele Pydantic
│   └── main.py                # ⚡ FastAPI app
├── tests/                     # 🧪 Testy pytest
├── logs/                      # 📝 Logi aplikacji
├── docker-compose.yml
├── Dockerfile
├── Justfile                   # 🛠️ Komendy deweloperskie
└── pyproject.toml
```

---

## 🧪 Testy

```bash
# Wszystkie testy
just test
# lub
uv run pytest -v

# Z pokryciem kodu
uv run pytest --cov=src --cov-report=html

# Tylko testy schematów
uv run pytest tests/test_schemas.py -v
```

---

## ⚙️ Konfiguracja

### Zmienne środowiskowe (`.env`)

| Zmienna | Opis | Wymagana |
|---------|------|----------|
| `GITHUB_TOKEN` | Token GitHub Models API | ✅ Tak |
| `MODEL_NAME` | Nazwa modelu LLM | Nie (default: `gpt-4o-mini`) |

### Prompty agentów (`config/prompts.yaml`)

Prompty są w pełni konfigurowalne bez zmiany kodu:

```yaml
researcher:
  name: "Research Agent"
  system_prompt: |
    Jesteś doświadczonym research journalistem...
  user_prompt_template: "Zbierz fakty na temat: {topic}"
```

---

## 🛠️ Komendy deweloperskie

```bash
just run              # Uruchom serwer
just test             # Uruchom testy
just lint             # Linting + formatowanie (ruff)
just logs             # Pokaż ostatnie 30 linii logów
just logs-follow      # Śledź logi na żywo
just logs-clear       # Wyczyść logi
just clean            # Wyczyść cache
```

---

## 🔮 Roadmap

- [ ] 🧠 Prawdziwy model ML clickbait detector (TF-IDF + LogisticRegression)
- [ ] 💾 Persystencja artykułów (SQLite/PostgreSQL)
- [ ] 📤 Export do PDF/Markdown
- [ ] 📡 Streaming odpowiedzi (SSE zamiast polling)
- [ ] ✅ Fact-Checker Agent
- [ ] 🔍 SEO Optimizer Agent

---

## 🤝 Technologie

| Kategoria | Technologia |
|-----------|-------------|
| Backend | FastAPI, Uvicorn |
| LLM | GitHub Models (GPT-4o-mini) |
| Validation | Pydantic v2 |
| Frontend | Vanilla JS, CSS |
| Package Manager | uv |
| Task Runner | just |
| Containerization | Docker |
| Testing | pytest |
| Linting | ruff |

---

## 📄 Licencja

MIT License - zobacz [LICENSE](LICENSE)

---

<p align="center">
  <strong>Made with ❤️ and 🤖 AI Agents</strong>
</p>