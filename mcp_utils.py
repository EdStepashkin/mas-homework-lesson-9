import asyncio
from langchain_core.tools import tool

async def mcp_tools_to_langchain(client):
    """
    Отримує список інструментів з fastmcp.Client та обгортає їх як LangChain інструменти.
    Повертає асинхронні інструменти для LangChain.
    """
    tools = await client.list_tools()
        
    langchain_tools = []
    for t in tools:
        t_name = t.name
        t_desc = t.description
        
        # Створюємо унікальну функцію для кожного інструменту за допомогою замикання (closure),
        # яка може приймати будь-які типові аргументи інструментів (query, url).
        def create_wrapper(name, desc):
            @tool(name, description=desc)
            async def tool_wrapper(query: str = "", url: str = "", filename: str = "", content: str = "") -> str:
                kwargs = {}
                if query: kwargs["query"] = query
                if url: kwargs["url"] = url
                if filename: kwargs["filename"] = filename
                if content: kwargs["content"] = content
                
                res = await client.call_tool(name, kwargs)
                    
                if hasattr(res, "content") and isinstance(res.content, list):
                    return " ".join([c.text for c in res.content if hasattr(c, "text")])
                return str(res)
            
            return tool_wrapper
            
        langchain_tools.append(create_wrapper(t_name, t_desc))
        
    return langchain_tools
