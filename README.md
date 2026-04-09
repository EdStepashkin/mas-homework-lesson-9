# Мультиагентна дослідницька система 🤖🔬

Мультиагентна AI-система, побудована на базі **LangChain** та **LangGraph**, яка координує трьох спеціалізованих суб-агентів за патерном **Plan → Research → Critique**.

Supervisor оркеструє ітеративний цикл дослідження: Planner декомпозує запит, Researcher виконує глибокий аналіз, а Critic верифікує результати і може повернути на доопрацювання. Збереження звіту захищене через **Human-in-the-Loop (HITL)** — користувач затверджує, редагує або відхиляє фінальний документ.

> Розширення Research Agent із homework-lesson-5 до мультиагентної архітектури (homework-lesson-8).

---

## 🏗 Архітектура

```
User (REPL)
  │
  ▼
Supervisor Agent
  │
  ├── 1. plan(request)       → Planner Agent      → structured ResearchPlan
  │
  ├── 2. research(plan)      → Research Agent      → findings (web + knowledge base)
  │
  ├── 3. critique(findings)  → Critic Agent        → structured CritiqueResult
  │       │
  │       ├── verdict: "APPROVE"  → step 4
  │       └── verdict: "REVISE"   → back to step 2 with feedback (max 2 rounds)
  │
  └── 4. save_report(...)    → HITL gated          → approve / edit / reject
```

### Суб-агенти

| Агент | Роль | Інструменти | Structured Output |
|-------|------|-------------|-------------------|
| **Planner** | Декомпозиція запиту у план дослідження | `web_search`, `knowledge_search` | `ResearchPlan` |
| **Researcher** | Глибоке дослідження за планом | `web_search`, `read_url`, `knowledge_search` | — |
| **Critic** | Верифікація якості (freshness, completeness, structure) | `web_search`, `read_url`, `knowledge_search` | `CritiqueResult` |
| **Supervisor** | Оркестрація циклу Plan→Research→Critique→Save | `plan`, `research`, `critique`, `save_report` | — |

---

## 🌟 Ключові можливості

- **Мультиагентна оркестрація**: Supervisor координує 3 спеціалізованих агенти через `create_agent` з `langchain.agents`
- **Structured Output**: Planner і Critic повертають валідовані Pydantic-моделі (`ResearchPlan`, `CritiqueResult`) через `response_format`
- **Ітеративне дослідження**: Critic може повернути Researcher на доопрацювання з конкретним зворотним зв'язком (evaluator-optimizer патерн)
- **HITL (Human-in-the-Loop)**: `HumanInTheLoopMiddleware` перехоплює `save_report` — користувач затверджує, редагує або відхиляє звіт
- **RAG з гібридним пошуком**: FAISS (семантичний) + BM25 (лексичний) + CrossEncoder реранкінг
- **Стрімування**: Реальний час виводу через `stream_mode=["updates", "messages"]` з `version="v2"`

---

## 🛠 Технологічний стек

- **LLM**: Google Gemini (`gemini-2.5-flash`) через `ChatGoogleGenerativeAI`
- **Агентний фреймворк**: `langchain.agents.create_agent` + `langchain.agents.middleware.HumanInTheLoopMiddleware`
- **Персистентність**: `langgraph.checkpoint.memory.InMemorySaver`
- **RAG-пайплайн**: `FAISS`, `OpenAIEmbeddings` (`text-embedding-3-small`), `BM25Retriever`, `HuggingFaceCrossEncoder` (`BAAI/bge-reranker-base`), `EnsembleRetriever`
- **Structured Output**: Pydantic `BaseModel` через `response_format` параметр `create_agent`
- **Інструменти**:
  - `knowledge_search` — пошук у локальній базі знань (RAG)
  - `web_search` — пошук в інтернеті (DuckDuckGo)
  - `read_url` — витягування тексту веб-сторінки (trafilatura)
  - `save_report` — збереження звіту (HITL-захищений)
- **Конфігурація**: Pydantic `BaseSettings` + `.env`

---

## 🚀 Встановлення та запуск

### 1. Клонування репозиторію
```bash
git clone https://github.com/EdStepashkin/mas-homework-lesson-9.git
cd homework-lesson-9
```

### 2. Створення віртуального середовища
```bash
python -m venv venv
source venv/bin/activate 

```

### 3. Встановлення залежностей
```bash
pip install -r requirements.txt
```

### 4. Налаштування змінних середовища (.env)
Створіть файл `.env` у кореневій директорії:
```env
GEMINI_API_KEY="AIzaSyYourApiKeyHere..."
OPENAI_API_KEY="sk-proj-YourOpenAiKey..."
```
*(`.env` додано до `.gitignore`).*

### 5. Індексація документів (Ingestion)
Помістіть PDF-документи у папку `data/` і запустіть:
```bash
python ingest.py
```
Скрипт поріже документи на чанки, згенерує вектори через `OpenAIEmbeddings` і збереже індекси FAISS та BM25 у папку `index/`.

### 6. Запуск системи
```bash
python main.py
```

---

## 💬 Приклад роботи

```
🔬 Multi-Agent Research System (type 'exit' to quit)
   Supervisor → Planner → Researcher → Critic → HITL
------------------------------------------------------------

You: Compare RAG approaches: naive, sentence-window, and parent-child. Write a report.

🔧 plan("Compare RAG approaches: naive, sentence-window, parent-child")
  📎 plan → ResearchPlan(goal="Compare three RAG retrieval strategies", ...)

🔧 research("Research these topics: 1) naive RAG approach 2) sentence-window ...")
  📎 research → [detailed findings with sources]

🔧 critique("Findings: ... [research results] ...")
  📎 critique → CritiqueResult(verdict="REVISE", gaps=["Outdated benchmarks", ...])

🔧 research("Find: 1) 2025-2026 benchmarks 2) parent-child details")
  📎 research → [updated findings]

🔧 critique("Updated findings: ...")
  📎 critique → CritiqueResult(verdict="APPROVE", strengths=["Up-to-date", ...])

🔧 save_report({"filename": "rag_comparison.md", "content": "# Comparison of RAG..."})

============================================================
⏸️  ACTION REQUIRES APPROVAL
============================================================
  Tool:  save_report
  File:  rag_comparison.md
  Content preview:
# Comparison of RAG Approaches...

👉 approve / edit / reject: approve

✅ Approved!

🤖 Supervisor: Звіт збережено у output/rag_comparison.md
```

---

## 📁 Структура проєкту

```
homework-lesson-8/
├── main.py              # REPL з HITL interrupt/resume loop
├── supervisor.py        # Supervisor Agent + HITL middleware
├── agents/
│   ├── __init__.py
│   ├── planner.py       # Planner Agent (response_format=ResearchPlan)
│   ├── research.py      # Research Agent (перевикористання hw5 tools)
│   └── critic.py        # Critic Agent (response_format=CritiqueResult)
├── schemas.py           # Pydantic-моделі: ResearchPlan, CritiqueResult
├── tools.py             # web_search, read_url, knowledge_search, save_report
├── retriever.py         # Hybrid search: FAISS + BM25 + CrossEncoder reranking
├── ingest.py            # Ingestion pipeline: PDF → chunks → FAISS index
├── config.py            # System prompts (4 агенти) + Settings
├── requirements.txt     # Залежності
├── data/                # Вхідні PDF-документи для RAG
├── index/               # Згенеровані індекси (не в Git)
├── output/              # Згенеровані звіти
└── .env                 # API-ключі (не в Git)
```

---

## 🔄 Що змінилося порівняно з homework-5

| Було (hw5) | Стало (hw8) |
|------------|-------------|
| Один Research Agent з 6 інструментами | Supervisor + 3 суб-агенти |
| `create_react_agent` (LangGraph prebuilt) | `create_agent` з `langchain.agents` |
| Агент робить усе одразу | Plan → Research → Critique цикл |
| Одноразове дослідження | Ітеративне: Critic може повернути на доопрацювання |
| Без потоку затвердження | HITL: save_report потребує approve/edit/reject |
| Лише вільний текст | Structured output через Pydantic (ResearchPlan, CritiqueResult) |

---

*Оригінальне завдання доступне у файлі `ASSIGNMENT.md`.*