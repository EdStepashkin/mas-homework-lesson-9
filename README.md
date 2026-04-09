# Мультиагентна дослідницька система з MCP/ACP архітектурою 🤖🔬

Мультиагентна AI-система, побудована на базі **LangChain**, яка координує трьох спеціалізованих суб-агентів за патерном **Plan → Research → Critique**.

У цьому оновленні здійснено **міграцію на розподілену архітектуру** з використанням протоколів **MCP** (Model Context Protocol) для керування інструментами та **ACP** (Agent Context Protocol) для агент-до-агент комунікації. Supervisor тепер діє як оркестратор, що делегує завдання віддаленим ACP-агентам, а самі інструменти винесені в окремі MCP-сервери. Збереження звіту захищене через **Human-in-the-Loop (HITL)** — користувач затверджує, редагує або відхиляє фінальний документ.

> Розширення мультиагентної архітектури (homework-lesson-8) до розподіленої MCP/ACP архітектури (homework-lesson-9).

---

## 🏗 Архітектура (MCP/ACP)

```
User (REPL)
  │
  ▼
Supervisor Agent (Local Orchestrator)
  │
  ├── 1. plan(request)       → ACP Client → Planner Agent (ACP Server 8903) 
  │
  ├── 2. research(plan)      → ACP Client → Research Agent (ACP Server 8903) 
  │                                           ↓ (fastmcp tools)
  ├── 3. critique(findings)  → ACP Client → Critic Agent (ACP Server 8903)
  │                                           ↓ (fastmcp tools)
  │                                     SearchMCP (8901): web search, knowledge base
  │
  └── 4. save_report(...)    → HITL gated → ReportMCP (8902): save_report
```

### Сервери (Нова інфраструктура)

| Компонент | Роль | Порт | Інструменти |
|-------|------|-------------|-------------------|
| **Search MCP** | Надає інформаційні інструменти | 8901 | `web_search`, `read_url`, `knowledge_search` |
| **Report MCP** | Відповідає за збереження даних | 8902 | `save_report` |
| **ACP Server** | Хостить агентів як незалежні сервіси | 8903 | — |
| **Supervisor** | Клієнтська програма-оркестратор | — | Виклик ACP та ReportMCP інструментів |

---

## 🌟 Ключові можливості

- **Розподілена архітектура**: Інструменти (MCP) та агенти (ACP) працюють як ізольовані мікросервіси.
- **Динамічна міграція інструментів**: Утиліта `mcp_tools_to_langchain` на льоту підключається до FastMCP та пакує ресурси у LangChain `@tool`.
- **Structured Output**: Агенти повертають `Message` (ACP SDK), а всередині використовують Pydantic для структурування кроків.
- **Eval-Optimizer Pipeline**: Ітеративний цикл дослідження та критики.
- **Безпечний HITL**: `HumanInTheLoopMiddleware` перехоплює виклик віддаленого `save_report`, дозволяючи користувачу внести зміни до Markdown-звіту у терміналі перед його відправкою на ReportMCP.
- **RAG з гібридним пошуком**: FAISS (семантичний) + BM25 (лексичний) + CrossEncoder реранкінг (інтегровано у SearchMCP).

---

## 🛠 Технологічний стек

- **MCP/ACP**: `fastmcp` (3.2.2+), `acp-sdk` (1.0.3+), `uvicorn`
- **LLM**: Google Gemini (`gemini-2.5-flash`)
- **Агентний фреймворк**: `langchain.agents`
- **Інструменти (SearchMCP)**:
  - `knowledge_search` — пошук у локальній базі знань (RAG)
  - `web_search` — пошук в інтернеті (DuckDuckGo)
  - `read_url` — витягування тексту веб-сторінки (trafilatura)
- **Інструменти (ReportMCP)**:
  - `save_report` — збереження звіту 

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
```

```bash
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

### 5. Індексація документів (Ingestion)
Помістіть PDF-документи у папку `data/` і запустіть:
```bash
python ingest.py
```
Скрипт поріже документи на чанки, згенерує вектори через `OpenAIEmbeddings` і збереже індекси FAISS та BM25 у папку `index/`.

### 6. Інструкція із запуску серверів
Оскільки архітектура стала розподіленою, необхідно запустити 3 сервери як фонові процеси (або у 3-х окремих терміналах):

**Термінал 1 (Search MCP):**
```bash
python mcp_servers/search_mcp.py
```

**Термінал 2 (Report MCP):**
```bash
python mcp_servers/report_mcp.py
```

**Термінал 3 (ACP Server):**
```bash
python acp_server.py
```

### 7. Запуск Supervisor-оркестратора
Коли всі 3 сервери запущено (порти 8901, 8902, 8903), в **окремому 4-му терміналі** запустіть головну програму REPL системи:
```bash
python main.py
```

---

## 📁 Структура проєкту

```
homework-lesson-9/
├── main.py              # Головна програма користувача (REPL)
├── supervisor.py        # Supervisor Agent + HITL, що викликає віддалені ACP
├── mcp_servers/         # MCP-Сервери
│   ├── search_mcp.py    # Сервер із web_search та RAG
│   └── report_mcp.py    # Сервер із інструментами логування і виводу
├── acp_server.py        # Основний сервер із агентами planner, researcher, critic
├── mcp_utils.py         # Утиліти конвертації MCP-langchain tools
├── agents/              # Шаблони агентів
│   ├── planner.py       
│   ├── research.py      
│   └── critic.py        
├── schemas.py           # Pydantic-моделі
├── tools.py             # Внутрішня реалізація інструментів (виклик з MCP)
├── retriever.py         # Hybrid search: FAISS + BM25 + CrossEncoder 
├── ingest.py            # Ingestion pipeline: PDF → FAISS index
├── config.py            # System prompts та Settings
├── tests_experiments/   # Папка з перевірочними/додатковими скриптами
└── data/, index/        # Згенеровані дані RAG 
```

---

## 🔄 Що змінилося порівняно з homework-8

| Було (hw8) | Стало (hw9) |
|------------|-------------|
| Всі інструменти імпортовані локально | Інструменти віддалені (`SearchMCP`, `ReportMCP`) |
| Всі агенти (`planner`, `researcher`, `critic`) локальні | Агенти виділені у незалежний віддалений сервіс `acp_server.py` |
| `Supervisor` створює агентів через LangGraph або LangChain напряму | `Supervisor` делегує задачі через протокол `ACP SDK` (по 8903 порту) |
| Інструменти працювали як синхронні | Повністю асинхронні `mcp_utils`, адаптовані під `fastmcp` клієнти |

---

*Оригінальне завдання доступне у файлі `ASSIGNMENT.md`.*