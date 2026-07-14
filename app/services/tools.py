from langchain_core.tools import tool

from app.repositories.retriever import search


@tool
def search_convention(query: str) -> str:
    """팀과 협의한 컨벤션 노트를 확인합니다.

    Args:
        query: 컨벤션에서 확인할 검색어

    Returns:
        result: chromadb에서 검색한 결과(string)
    """
    docs = search(query=query)

    return "\n\n".join(doc.page_content for doc in docs)
