# Chroma 등 VectorDB 클라이언트 초기화
from pathlib import Path

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHROMA_DIR = BASE_DIR / "chroma_db"

_embeddings = OllamaEmbeddings(model="bge-m3")


def get_vectorstore() -> Chroma:
    """Chroma Vector DB를 반환합니다."""

    if not CHROMA_DIR.exists():
        raise FileNotFoundError("Vector DB not found.")

    return Chroma(persist_directory=str(CHROMA_DIR), embedding_function=_embeddings)
