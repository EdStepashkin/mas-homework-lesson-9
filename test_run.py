from supervisor import supervisor_graph as supervisor
from config import settings
from langgraph.types import Command

config = {
    "configurable": {"thread_id": "test_1"},
    "recursion_limit": settings.max_iterations,
}
print("Starting stream...")
for chunk in supervisor.stream(
    {"messages": [{"role": "user", "content": "Compare RAG approaches: naive, sentence-window. Just short plan and research."}]},
    config=config,
    stream_mode=["updates", "messages"],
    version="v2",
):
    print("CHUNK TYPE:", chunk["type"])
    if chunk["type"] == "messages":
        token, meta = chunk["data"]
        print("MSG:", type(token), repr(token.content))
    elif chunk["type"] == "updates":
        print("UPDATE:", chunk["data"].keys())
