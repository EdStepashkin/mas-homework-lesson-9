"""
Planner Agent — декомпозує запит користувача у структурований ResearchPlan.

Робить попередній пошук (web_search, knowledge_search), щоб зрозуміти домен,
і повертає структурований план дослідження.
"""

from langchain.agents import create_agent
from langchain_core.tools import tool

from config import settings, llm, PLANNER_PROMPT
from schemas import ResearchPlan
from tools import web_search, knowledge_search


# Створюємо Planner Agent з structured output
_planner_agent = create_agent(
    model=llm,
    tools=[web_search, knowledge_search],
    system_prompt=PLANNER_PROMPT,
    response_format=ResearchPlan,
)


@tool
def plan(request: str) -> str:
    """
    Декомпозує запит користувача у детальний план дослідження.
    Використовує пошук (web, knowledge), щоб зрозуміти домен.
    Повертає структурований ResearchPlan як рядок.
    """
    result = _planner_agent.invoke({"messages": [{"role": "user", "content": request}]})

    structured = result.get("structured_response")
    plan_text = ""
    if structured:
        if isinstance(structured, ResearchPlan):
            plan_text = (
                f"📎 ResearchPlan:\n"
                f"  goal: {structured.goal}\n"
                f"  search_queries: {structured.search_queries}\n"
                f"  sources_to_check: {structured.sources_to_check}\n"
                f"  output_format: {structured.output_format}"
            )
        else:
            plan_text = f"📎 ResearchPlan: {structured}"
    else:
        out_msgs = result.get("messages", [])
        if out_msgs:
            content = out_msgs[-1].content
            if isinstance(content, list):
                plan_text = " ".join([str(c.get("text", "")) for c in content if isinstance(c, dict) and "text" in c])
            else:
                plan_text = str(content)
        else:
            plan_text = "Planner не зміг створити план."

    return plan_text + "\n\n⚠️ УВАГА SUPERVISOR: План готовий. НАСТУПНИЙ КРОК — виклич research(plan) ЗАРАЗ."
