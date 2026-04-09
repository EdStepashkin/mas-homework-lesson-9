"""
Supervisor Agent — координатор мультиагентної дослідницької системи.

Оркеструє цикл: Plan → Research → Critique → save_report (HITL) 
використовуючи патерн Agent-as-a-Tool (Orchestrator-Worker).
"""

import asyncio
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.tools import tool

from config import settings, llm, SUPERVISOR_PROMPT
from acp_sdk.client import Client as ACPClient
from fastmcp import Client as FastClient

import httpx
http_client = httpx.AsyncClient(base_url="http://localhost:8903", headers={"Content-Type": "application/json"}, timeout=None)
acp_client = ACPClient(client=http_client)

@tool
def plan(request: str) -> str:
    """
    Декомпозує запит користувача у детальний план дослідження.
    Викликає Planner Agent через ACP.
    """
    try:
        try:
            run = asyncio.run(acp_client.run_sync(input=request, agent="planner"))
        except RuntimeError:
            import nest_asyncio
            nest_asyncio.apply()
            run = asyncio.get_event_loop().run_until_complete(acp_client.run_sync(input=request, agent="planner"))
        return "\n".join([" ".join([p.content for p in getattr(m, 'parts', []) if getattr(p, 'content_type', '').startswith("text")]) for m in run.output])
    except Exception as e:
        return f"Помилка ACP виклику planner: {str(e)}"

@tool
def research(plan: str) -> str:
    """
    Збирає факти за планом.
    Викликає Research Agent через ACP.
    """
    try:
        try:
            run = asyncio.run(acp_client.run_sync(input=plan, agent="researcher"))
        except RuntimeError:
            import nest_asyncio
            nest_asyncio.apply()
            run = asyncio.get_event_loop().run_until_complete(acp_client.run_sync(input=plan, agent="researcher"))
        return "\n".join([" ".join([p.content for p in getattr(m, 'parts', []) if getattr(p, 'content_type', '').startswith("text")]) for m in run.output])
    except Exception as e:
        return f"Помилка ACP виклику researcher: {str(e)}"

@tool
def critique(findings: str) -> str:
    """
    Оцінює знахідки.
    Викликає Critic Agent через ACP.
    """
    try:
        try:
            run = asyncio.run(acp_client.run_sync(input=findings, agent="critic"))
        except RuntimeError:
            import nest_asyncio
            nest_asyncio.apply()
            run = asyncio.get_event_loop().run_until_complete(acp_client.run_sync(input=findings, agent="critic"))
        return "\n".join([" ".join([p.content for p in getattr(m, 'parts', []) if getattr(p, 'content_type', '').startswith("text")]) for m in run.output])
    except Exception as e:
        return f"Помилка ACP виклику critic: {str(e)}"

@tool
def save_report(filename: str, content: str) -> str:
    """
    Зберігає фінальний Markdown-звіт у файл у директорії output/.
    Викликає інструмент збереження на ReportMCP.
    """
    try:
        async def call_mcp():
            async with FastClient("http://127.0.0.1:8902/sse") as client:
                res = await client.call_tool("save_report", {"filename": filename, "content": content})
                if hasattr(res, "content") and isinstance(res.content, list):
                    return " ".join([c.text for c in res.content if hasattr(c, "text")])
                return str(res)
        
        try:
            res = asyncio.run(call_mcp())
        except RuntimeError:
            import nest_asyncio
            nest_asyncio.apply()
            res = asyncio.get_event_loop().run_until_complete(call_mcp())
        return res
    except Exception as e:
        return f"Помилка виклику ReportMCP: {str(e)}"

# Створюємо Supervisor Agent, використовуючи create_agent та middleware
memory = InMemorySaver()

supervisor_graph = create_agent(
    model=llm,
    tools=[plan, research, critique, save_report],
    system_prompt=SUPERVISOR_PROMPT,
    middleware=[
        HumanInTheLoopMiddleware(interrupt_on={"save_report": True}),
    ],
    checkpointer=memory,
)

# Експортуємо supervisor_graph, щоб main.py та test_run.py могли його використовувати.
