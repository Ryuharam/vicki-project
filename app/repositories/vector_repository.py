import logging
from uuid import uuid4

from langchain_core.documents import Document

from app.core.vectordb import get_vectorstore

logger = logging.getLogger("uvicorn.error")

TOP_K = 3

vectorstore = get_vectorstore()


def add_documents(documents: list[Document]) -> None:
    """문서를 Vector DB에 저장합니다."""
    uuids = [str(uuid4()) for _ in range(len(documents))]

    vectorstore.add_documents(documents=documents, ids=uuids)


def get_all_documents():
    result = vectorstore.get()

    if not bool(result.get("documents")):
        return []

    filenames = set()

    for r in result.get("metadatas"):
        filenames.add(r.get("filename"))

    return filenames


def similarity_search(query: str) -> list[Document]:
    """유사한 문서를 검색합니다."""
    results = vectorstore.similarity_search(query=query, k=TOP_K)

    for r in results:
        logger.info(f"검색 결과 : {r.metadata['filename']}")

    return results


def search_by_hash(repo_id: int, filehash: str) -> dict:
    """ropo_id와 hash로 문서를 조회합니다."""

    result = vectorstore.get(
        where={
            "$and": [
                {"repo_id": repo_id},
                {"filehash": filehash},
            ]
        }
    )

    return bool(result.get("documents"))


def search_by_filename(repo_id: int, filename: str) -> dict:
    """repo_id와 파일명으로 문서를 조회합니다."""

    return vectorstore.get(
        where={
            "$and": [
                {"repo_id": repo_id},
                {"filename": filename},
            ]
        }
    )


def delete_documents(repo_id: int, filename: str) -> None:
    """문서를 삭제합니다."""

    pass
