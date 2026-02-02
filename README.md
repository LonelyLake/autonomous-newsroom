# 📰 The Autonomous Newsroom

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Package Manager: uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Tool: just](https://img.shields.io/badge/tool-just-orange.svg)](https://github.com/casey/just)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Symulacja autonomicznej redakcji technologicznej opartej na współpracy agentów AI, realizowana w ramach **GitHub Education Pack**. Projekt łączy nowoczesne podejście LLM (Agentic Workflow) z klasycznym uczeniem maszynowym w celach weryfikacji danych.

---

## 🎯 Cel Projektu

Stworzenie skalowalnego systemu multi-agentowego typu "Editorial Pipeline", w którym:
* **Researcher**: Eksploruje sieć w poszukiwaniu trendów technologicznych.
* **Writer**: Generuje drafty artykułów w oparciu o zebrane dane.
* **Fact-Checker**: Hybrydowa weryfikacja treści (LLM + klasyczny ML/Scikit-learn).
* **Editor**: Krytyczna analiza i finalne zatwierdzenie publikacji.

---

## 🏗️ Architektura i Stack Technologiczny (MLOps)

Projekt bazuje na rygorystycznych standardach inżynieryjnych:

* **Backend:** FastAPI (Asynchroniczna orkiestracja zadań).
* **Agent Core:** GitHub Models (Llama 3.1 / GPT-4o).
* **Package Management:** [uv](https://github.com/astral-sh/uv) (Błyskawiczna instalacja i izolowane `.venv`).
* **Task Runner:** `just` (Automatyzacja workflow).
* **Classic ML:** Scikit-learn (Wykorzystywany przez Fact-Checkera do analizy sentymentu i detekcji anomalii).
* **Environment:** WSL2 (Ubuntu 24.04).



---

## 🚀 Jak zacząć (Dla Developerów)

### Wymagania wstępne
* Python 3.12+
* Narzędzie `uv` (`pip install uv` lub przez skrypt instalacyjny)
* Narzędzie `just` (`uv tool install just`)
* Docker Engine (opcjonalnie, zalecane zarządzanie przez `sudo service docker start`)

### Szybki Start (Lokalnie)

1.  **Klonowanie repozytorium:**
    ```bash
    git clone [https://github.com/TWOJE_USER_NAME/autonomous-newsroom.git](https://github.com/TWOJE_USER_NAME/autonomous-newsroom.git)
    cd autonomous-newsroom
    ```

2.  **Konfiguracja środowiska:**
    ```bash
    cp .env.example .env
    # Uzupełnij GITHUB_TOKEN w pliku .env
    ```

3.  **Inicjalizacja i uruchomienie:**
    Wykorzystujemy `just` do uproszczenia workflow:
    ```bash
    just setup    # Tworzy venv przez uv i instaluje zależności
    just run      # Uruchamia serwer FastAPI na porcie 8000
    ```

4.  **Testowanie:**
    Wejdź na: `http://localhost:8000/docs`, aby uzyskać dostęp do interaktywnej dokumentacji Swagger UI.

### Uruchomienie przez Docker
Dla zachowania czystości systemu (4GB RAM optimization):
```bash
docker-compose up --build

```

---

## 📁 Struktura Projektu

```text
├── config/             # Prompty systemowe i konfiguracja YAML
├── src/
│   ├── agents/         # Logika agentów (Researcher, Writer, Editor)
│   ├── api/            # Endpointy FastAPI i schematy Pydantic
│   ├── core/           # Konfiguracja, asynchroniczne loggery, utils
│   ├── ml/             # Klasyczne modele weryfikacyjne (Scikit-learn)
│   └── main.py         # Entrypoint aplikacji
├── tests/              # Testy jednostkowe i integracyjne (pytest)
├── Dockerfile          # Multi-stage build
├── Justfile            # Definicje zadań (setup, run, lint, test)
└── pyproject.toml      # Konfiguracja uv i ruff

```

---

## 🤝 Zespół i Role

| Rola | Odpowiedzialność | Stack |
| --- | --- | --- |
| **Engineer 1** | MLOps, Infrastructure, Classic ML | Docker, Scikit-learn, FastAPI |
| **Engineer 2** | AI Logic, Agent Design, Prompt Engineering | GitHub Models, LangChain/CrewAI |

---

## 🛠️ Rozwój (Development)

W projekcie wymuszane są standardy jakości kodu:

* **Linter/Formatter**: `ruff` (Konfiguracja w `pyproject.toml`).
* **Type Checking**: `mypy`.
* **Git Flow**: Zmiany wprowadzane przez Pull Requesty.

```bash
just lint    # Sprawdzenie czystości kodu
just test    # Uruchomienie testów pytest

```