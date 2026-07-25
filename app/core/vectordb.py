from langchain_chroma import Chroma
import chromadb

from app.core.embedding import get_embeddings
from app.core.config import settings

_host = settings.VECTOR_DB_HOST
_port = settings.VECTOR_DB_PORT

embeddings = get_embeddings()

_client = chromadb.HttpClient(host=_host, port=_port)

_vectorstore = Chroma(
    client=_client, collection_name="conventions", embedding_function=embeddings
)


def get_vectorstore() -> Chroma:
    """Chroma Vector DB를 반환합니다."""

    return _vectorstore
