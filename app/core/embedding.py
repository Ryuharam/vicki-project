from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import AppSettings


def build_embeddings(settings: AppSettings) -> Embeddings:
    """임베딩 모델을 생성합니다."""
    if not settings.GOOGLE_API_KEY:
        raise ValueError(f"임베딩({settings.EMBED_MODEL})을 쓰려면 GOOGLE_API_KEY가 필요합니다.")

    return GoogleGenerativeAIEmbeddings(
        model=settings.EMBED_MODEL,
        api_key=settings.GOOGLE_API_KEY,
    )
