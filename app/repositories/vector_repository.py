import logging
from uuid import uuid4

from langchain_chroma import Chroma
from langchain_core.documents import Document

logger = logging.getLogger("uvicorn.error")

TOP_K = 3


class ConventionRepository:
    """컨벤션 문서 저장소. vectorstore를 주입받아 사용합니다."""

    def __init__(self, vectorstore: Chroma):
        self._vectorstore = vectorstore

    def add_documents(self, documents: list[Document]) -> None:
        """문서를 Vector DB에 저장합니다."""
        uuids = [str(uuid4()) for _ in range(len(documents))]

        self._vectorstore.add_documents(documents=documents, ids=uuids)

    def get_all_documents(self) -> set[str]:
        """저장된 모든 문서의 파일명을 조회합니다."""
        result = self._vectorstore.get()

        if not result.get("documents"):
            return set()

        return {metadata.get("filename") for metadata in result.get("metadatas")}

    def similarity_search(self, query: str) -> list[Document]:
        """유사한 문서를 검색합니다."""
        results = self._vectorstore.similarity_search(query=query, k=TOP_K)

        for r in results:
            logger.info(f"검색 결과 : {r.metadata['filename']}")

        return results

    def exists_by_hash(self, repo_id: int, filehash: str) -> bool:
        """repo_id와 hash로 문서 존재 여부를 확인합니다."""
        result = self._vectorstore.get(
            where={
                "$and": [
                    {"repo_id": repo_id},
                    {"filehash": filehash},
                ]
            }
        )

        return bool(result.get("documents"))

    def search_by_filename(self, repo_id: int, filename: str) -> dict:
        """repo_id와 파일명으로 문서를 조회합니다."""
        return self._vectorstore.get(
            where={
                "$and": [
                    {"repo_id": repo_id},
                    {"filename": filename},
                ]
            }
        )

    def delete_documents(self, repo_id: int, filename: str) -> None:
        """문서를 삭제합니다."""
        pass
