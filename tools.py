import os
from langchain_core.tools import tool
from ddgs import DDGS
import trafilatura

# Імпортуємо наші налаштування
from config import settings


@tool
def web_search(query: str) -> str:
    """
    Виконує пошук в інтернеті за запитом.
    Повертає список знайдених сторінок із заголовком (title), посиланням (href) та коротким описом (body).
    Використовуй це для знаходження актуальної інформації.
    """
    try:
        # DDGS().text повертає генератор словників
        results = list(DDGS().text(query, max_results=settings.max_search_results))
        res_str = str(results)

        # Context Engineering: обрізаємо текст, щоб не переповнити пам'ять агента
        if len(res_str) > settings.max_url_content_length:
            return res_str[:settings.max_url_content_length] + "\n... [ТЕКСТ ОБРІЗАНО ЧЕРЕЗ ЛІМІТ]"

        return res_str
    except Exception as e:
        # Повертаємо помилку текстом, щоб агент не впав і міг змінити стратегію
        return f"Помилка пошуку: {str(e)}"


@tool
def read_url(url: str) -> str:
    """
    Завантажує та витягує повний текст веб-сторінки за вказаним URL.
    Використовуй цей інструмент, щоб детально прочитати статтю, знайдену через web_search.
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return f"Помилка: не вдалося завантажити сторінку {url}"

        # Витягуємо основний текст, ігноруючи меню та рекламу
        text = trafilatura.extract(downloaded)
        if not text:
            return f"Помилка: не вдалося витягнути текст зі сторінки {url}"

        # Context Engineering: обрізаємо текст, щоб не переповнити пам'ять агента
        if len(text) > settings.max_url_content_length:
            return text[:settings.max_url_content_length] + "\n... [ТЕКСТ ОБРІЗАНО ЧЕРЕЗ ЛІМІТ]"

        return text
    except Exception as e:
        return f"Помилка читання URL: {str(e)}"


@tool
def save_report(filename: str, content: str) -> str:
    """
    Зберігає фінальний Markdown-звіт у файл у директорії output/.
    Приймає назву файлу (наприклад, rag_comparison.md) та повний текст звіту.
    Ця операція потребує затвердження користувача (HITL).
    """
    try:
        # Створюємо директорію, якщо її ще немає
        os.makedirs(settings.output_dir, exist_ok=True)
        filepath = os.path.join(settings.output_dir, filename)

        # Зберігаємо файл
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return f"✅ Звіт успішно збережено: {filepath}"
    except Exception as e:
        return f"Помилка збереження файлу: {str(e)}"


# Глобальний кеш для рітрівера, щоб не завантажувати модель та базу щоразу
_GLOBAL_RETRIEVER = None

def _get_cached_retriever():
    global _GLOBAL_RETRIEVER
    if _GLOBAL_RETRIEVER is None:
        from retriever import get_retriever
        _GLOBAL_RETRIEVER = get_retriever()
    return _GLOBAL_RETRIEVER

@tool
def knowledge_search(query: str) -> str:
    """
    Search the local knowledge base. Use for questions about ingested documents.
    """
    try:
        retriever = _get_cached_retriever()

        # Retrieve documents
        docs = retriever.invoke(query)

        if not docs:
            return "Не знайдено релевантної інформації у базі знань."

        result = f"[{len(docs)} documents found]\n"
        for i, doc in enumerate(docs):
            source = doc.metadata.get('source', 'Unknown')
            page = doc.metadata.get('page', 'Unknown')
            # Extract filename from path if possible
            filename = os.path.basename(source) if '/' in source or '\\' in source else source
            result += f"- [Page {page} of {filename}] {doc.page_content}\n\n"

        # Context Engineering
        if len(result) > settings.max_url_content_length:
            return result[:settings.max_url_content_length] + "\n... [ТЕКСТ ОБРІЗАНО ЧЕРЕЗ ЛІМІТ]"

        return result
    except Exception as e:
        return f"Помилка пошуку в базі знань: {str(e)}"