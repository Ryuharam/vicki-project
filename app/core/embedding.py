# 임베딩 모델 로딩
import os

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

_model = os.getenv("EMBED_MODEL")

_embeddings = GoogleGenerativeAIEmbeddings(model=_model)


def get_embeddings():
    """Embedding을 반환합니다."""
    return _embeddings
