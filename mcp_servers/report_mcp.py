import os
import sys

# Додаємо батьківську директорію до sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastmcp import FastMCP
from config import settings
from tools import save_report

mcp = FastMCP("ReportMCP")

@mcp.tool(name="save_report")
def do_save_report(filename: str, content: str) -> str:
    """
    Зберігає фінальний Markdown-звіт у файл у директорії output/.
    Приймає назву файлу та повний текст звіту.
    """
    return save_report.invoke({"filename": filename, "content": content})

@mcp.resource("resource://output-dir")
def get_output_dir_stats() -> str:
    """Повертає шлях до директорії та список збережених звітів."""
    try:
        out_dir = settings.output_dir
        if not os.path.exists(out_dir):
            return f"Директорія {out_dir} порожня або не існує."
        files = os.listdir(out_dir)
        return f"Директорія: {out_dir}. Файли: {', '.join(files) if files else 'немає'}"
    except Exception as e:
        return f"Помилка отримання статистики: {str(e)}"

if __name__ == "__main__":
    print("Starting ReportMCP on port 8902...")
    mcp.run(transport="sse", port=8902)
