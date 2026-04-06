"""
Critic Agent — оцінює якість дослідження через незалежну верифікацію.

Перевіряє freshness, completeness, structure. Повертає CritiqueResult
з вердиктом APPROVE або REVISE.
"""

from langchain.agents import create_agent
from langchain_core.tools import tool

from config import settings, llm, CRITIC_PROMPT
from schemas import CritiqueResult
from tools import web_search, read_url, knowledge_search


# Створюємо Critic Agent з structured output
_critic_agent = create_agent(
    model=llm,
    tools=[web_search, read_url, knowledge_search],
    system_prompt=CRITIC_PROMPT,
    response_format=CritiqueResult,
)


@tool
def critique(findings: str) -> str:
    """
    Оцінює якість дослідження (findings) шляхом незалежної верифікації.
    Повертає структурований CritiqueResult як рядок, з вердиктом APPROVE або REVISE.
    """
    content_to_evaluate = f"Отримані знахідки для перевірки: {findings}"
        
    result = _critic_agent.invoke(
        {"messages": [{"role": "user", "content": content_to_evaluate}]}
    )

    structured = result.get("structured_response")
    critic_text = ""
    
    if structured:
        if isinstance(structured, CritiqueResult):
            critic_text = (
                f"📎 CritiqueResult:\n"
                f"  verdict: {structured.verdict}\n"
                f"  is_fresh: {structured.is_fresh}\n"
                f"  is_complete: {structured.is_complete}\n"
                f"  is_well_structured: {structured.is_well_structured}\n"
                f"  strengths: {structured.strengths}\n"
                f"  gaps: {structured.gaps}\n"
                f"  revision_requests: {structured.revision_requests}"
            )
        else:
            critic_text = f"📎 CritiqueResult: {structured}"
    else:
        out_msgs = result.get("messages", [])
        if out_msgs:
            content = out_msgs[-1].content
            if isinstance(content, list):
                critic_text = " ".join([str(c.get("text", "")) for c in content if isinstance(c, dict) and "text" in c])
            else:
                critic_text = str(content)
        else:
            critic_text = "Critic не зміг оцінити дослідження."

    # Додаємо маркер наступного кроку для Supervisor
    if "REVISE" in critic_text:
        critic_text += "\n\n⚠️ УВАГА SUPERVISOR: Verdict = REVISE. НАСТУПНИЙ КРОК — виклич research(revision_requests) ЗАРАЗ."
    else:
        critic_text += "\n\n⚠️ УВАГА SUPERVISOR: Verdict = APPROVE. НАСТУПНИЙ КРОК — склади Markdown-звіт і виклич save_report(filename, content) ЗАРАЗ."

    return critic_text
