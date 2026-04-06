"""
Supervisor Agent — координатор мультиагентної дослідницької системи.

Оркеструє цикл: Plan → Research → Critique → save_report (HITL) 
використовуючи патерн Agent-as-a-Tool (Orchestrator-Worker).
"""

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import HumanInTheLoopMiddleware

from config import settings, llm, SUPERVISOR_PROMPT
from tools import save_report

from agents.planner import plan
from agents.research import research
from agents.critic import critique

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
