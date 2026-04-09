import asyncio
from acp_sdk.server import Server
from acp_sdk import Message, MessagePart
from fastmcp import Client as FastClient
from langchain.agents import create_agent
from pydantic import BaseModel
import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import llm, PLANNER_PROMPT, RESEARCHER_PROMPT, CRITIC_PROMPT
from mcp_utils import mcp_tools_to_langchain
from schemas import ResearchPlan, CritiqueResult

app_server = Server()

async def get_search_tools():
    """Підключаємося до SearchMCP та створюємо LangChain інструменти."""
    client = FastClient("sse", "http://localhost:8901")
    # Actually wait we might need to initialize it async then wrap it
    # Client is an async context manager normally, or initialize via .connect()
    # `fastmcp.Client("...", "...")` has no initialize probably. It usually has `await client.__aenter__()`
    # Let's hope client wrapper inside mcp_tools_to_langchain handles it,
    # or let's connect first. But mcp_utils uses list_tools async.
    return client

@app_server.agent(name="planner", description="Planner Agent (Plan)", input_content_types=["text/plain"])
async def planner_agent(messages: list[Message]) -> Message:
    print("▶️ [ACP] Planner agent started...")
    async with FastClient("http://127.0.0.1:8901/sse") as client:
        print("  → Connected to FastMCP.")
        tools = await mcp_tools_to_langchain(client)
        
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=PLANNER_PROMPT,
            response_format=ResearchPlan,
        )
        
        request_text = " ".join([p.content for p in getattr(messages[-1], "parts", []) if getattr(p, "content_type", "").startswith("text")]) if messages else ""
        print(f"  → Invoking LangChain agent for Planner (Length: {len(request_text)})...")
        
        result = await agent.ainvoke({"messages": [{"role": "user", "content": request_text}]})
        
        structured = result.get("structured_response")
        if structured and isinstance(structured, BaseModel):
            content = f"📎 ResearchPlan:\n  goal: {structured.goal}\n  search_queries: {structured.search_queries}\n  sources_to_check: {structured.sources_to_check}\n  output_format: {structured.output_format}"
            content += "\n\n⚠️ УВАГА SUPERVISOR: План готовий. НАСТУПНИЙ КРОК — виклич research(plan) ЗАРАЗ."
        else:
            out_msgs = result.get("messages", [])
            content = str(out_msgs[-1].content) if out_msgs else "Planner не зміг створити план."
            content += "\n\n⚠️ УВАГА SUPERVISOR: План готовий. НАСТУПНИЙ КРОК — виклич research(plan) ЗАРАЗ."
            
        print("✅ [ACP] Planner success.")
        return Message(role="agent", parts=[MessagePart(content_type="text/plain", content=content)])

@app_server.agent(name="researcher", description="Research Agent", input_content_types=["text/plain"])
async def research_agent(messages: list[Message]) -> Message:
    print("▶️ [ACP] Researcher agent started...")
    async with FastClient("http://127.0.0.1:8901/sse") as client:
        print("  → Connected to FastMCP.")
        tools = await mcp_tools_to_langchain(client)
        
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=RESEARCHER_PROMPT,
        )
        
        request_text = " ".join([p.content for p in getattr(messages[-1], "parts", []) if getattr(p, "content_type", "").startswith("text")]) if messages else ""
        print(f"  → Invoking LangChain agent for Researcher (Length: {len(request_text)})... [This might take 30-60s]")
        
        result = await agent.ainvoke({"messages": [{"role": "user", "content": request_text}]})
        
        out_msgs = result.get("messages", [])
        content = str(out_msgs[-1].content) if out_msgs else "Failed"
            
        print("✅ [ACP] Researcher success.")
        return Message(role="agent", parts=[MessagePart(content_type="text/plain", content=content)])

@app_server.agent(name="critic", description="Critic Agent", input_content_types=["text/plain"])
async def critic_agent(messages: list[Message]) -> Message:
    print("▶️ [ACP] Critic agent started...")
    async with FastClient("http://127.0.0.1:8901/sse") as client:
        print("  → Connected to FastMCP.")
        tools = await mcp_tools_to_langchain(client)
        
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=CRITIC_PROMPT,
            response_format=CritiqueResult,
        )
        
        request_text = " ".join([p.content for p in getattr(messages[-1], "parts", []) if getattr(p, "content_type", "").startswith("text")]) if messages else ""
        print(f"  → Invoking LangChain agent for Critic (Length: {len(request_text)})... [This might take 30-60s]")
        
        result = await agent.ainvoke({"messages": [{"role": "user", "content": request_text}]})
        
        structured = result.get("structured_response")
        if structured and isinstance(structured, BaseModel):
            content = f"📎 CritiqueResult:\n  verdict: {structured.verdict}\n  gap: {getattr(structured, 'gaps', '')}\n  feedback: {getattr(structured, 'feedback', getattr(structured, 'revision_requests', ''))}"
            if getattr(structured, "verdict", "REVISE") == "APPROVE":
                content += "\n\n⚠️ УВАГА SUPERVISOR: Вердикт APPROVE. НАСТУПНИЙ КРОК — виклич save_report(filename, report)"
        else:
            out_msgs = result.get("messages", [])
            content = str(out_msgs[-1].content) if out_msgs else "Failed"
            
        print("✅ [ACP] Critic success.")
        return Message(role="agent", parts=[MessagePart(content_type="text/plain", content=content)])

if __name__ == "__main__":
    print("Starting ACP Server on port 8903...")
    import uvicorn
    original_init = uvicorn.Config.__init__
    def patched_init(self, *args, **kwargs):
        # acp-sdk has a bug due to Uvicorn position arguments shifting.
        # We override __init__ to only pass safe basic params.
        app = args[0] if args else kwargs.get("app")
        host = args[1] if len(args) > 1 else kwargs.get("host", "127.0.0.1")
        port = args[2] if len(args) > 2 else kwargs.get("port", 8903)
        original_init(self, app=app, host=host, port=port)
    uvicorn.Config.__init__ = patched_init
    
    app_server.run(host="127.0.0.1", port=8903)
