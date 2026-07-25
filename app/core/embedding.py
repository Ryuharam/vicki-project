from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings

_model = settings.EMBED_MODEL

_embeddings = GoogleGenerativeAIEmbeddings(model=_model)


def get_embeddings():
    """Embedding을 반환합니다."""
    return _embeddings
