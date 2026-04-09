import os
import sys

# Додаємо батьківську директорію до sys.path для імпорту config і tools
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastmcp import FastMCP
from config import settings
from tools import web_search, read_url, knowledge_search

# Створюємо сервер
mcp = FastMCP("SearchMCP")

@mcp.tool(name="web_search")
def do_web_search(query: str) -> str:
    """Виконує пошук в інтернеті за запитом."""
    # викликаємо оригінальну функцію з tools.py
    return web_search.invoke({"query": query})

@mcp.tool(name="read_url")
def do_read_url(url: str) -> str:
    """Завантажує та витягує повний текст веб-сторінки за вказаним URL."""
    return read_url.invoke({"url": url})

@mcp.tool(name="knowledge_search")
def do_knowledge_search(query: str) -> str:
    """Search the local knowledge base. Use for questions about ingested documents."""
    return knowledge_search.invoke({"query": query})

@mcp.resource("resource://knowledge-base-stats")
def get_knowledge_base_stats() -> str:
    """Статистика бази знань (кількість документів, дата)"""
    try:
        count = len(os.listdir(settings.data_dir)) if os.path.exists(settings.data_dir) else 0
        return f"Кількість документів у базі знань ({settings.data_dir}): {count}"
    except Exception as e:
        return f"Помилка отримання статистики: {str(e)}"

if __name__ == "__main__":
    print("Starting SearchMCP on port 8901...")
    mcp.run(transport="sse", port=8901)
