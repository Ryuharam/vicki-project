import chromadb
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from app.core.config import AppSettings

COLLECTION_NAME = "conventions"


def build_vectorstore(settings: AppSettings, embeddings: Embeddings) -> Chroma:
    """Chroma Vector DB에 연결합니다."""
    client = chromadb.HttpClient(
        host=settings.VECTOR_DB_HOST,
        port=settings.VECTOR_DB_PORT,
    )

    return Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )
