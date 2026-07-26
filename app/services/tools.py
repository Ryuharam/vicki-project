import logging

from langchain_core.tools import BaseTool, tool

from app.repositories.vector_repository import ConventionRepository

logger = logging.getLogger("uvicorn.error")


def make_search_convention(repository: ConventionRepository) -> BaseTool:
    """repository를 클로저로 묶어 convention 검색 tool을 만듭니다."""

    @tool
    def search_convention(query: str) -> str:
        """팀과 협의한 컨벤션 노트를 확인합니다.

        Args:
            query: 컨벤션에서 확인할 검색어

        Returns:
            result: chromadb에서 검색한 결과(string)
        """
        logger.info("[Tool] search convention")
        docs = repository.similarity_search(query=query)

        logger.info(f"검색 결과: {len(docs)}")
        return "\n\n".join(doc.page_content for doc in docs)

    return search_convention
