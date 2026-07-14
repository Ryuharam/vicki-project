# Chroma 등 VectorDB 클라이언트 초기화
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHROMA_DIR = BASE_DIR / "chroma_db"

# _embeddings = OllamaEmbeddings(model="bge-m3")
_embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2-preview")


if not CHROMA_DIR.exists():
    raise FileNotFoundError("Vector DB not found.")

# PersistentClient 생성은 스레드 안전하지 않으므로 모듈 로드 시점에 한 번만 생성
_vectorstore = Chroma(persist_directory=str(CHROMA_DIR), embedding_function=_embeddings)


def get_vectorstore() -> Chroma:
    """Chroma Vector DB를 반환합니다."""

    return _vectorstore
