# Chroma 등 VectorDB 클라이언트 초기화
import os

from dotenv import load_dotenv
from langchain_chroma import Chroma
import chromadb

from app.core.embedding import get_embeddings

load_dotenv()

_host = os.getenv("VECTOR_DB_HOST")
_port = os.getenv("VECTOR_DB_PORT")

embeddings = get_embeddings()
_client = chromadb.HttpClient(host=_host, port=int(_port))
_vectorstore = Chroma(
    client=_client, collection_name="conventions", embedding_function=embeddings
)


def get_vectorstore() -> Chroma:
    """Chroma Vector DB를 반환합니다."""

    return _vectorstore
