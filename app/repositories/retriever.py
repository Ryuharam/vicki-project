# VectorDB에서 관련 문서 검색(Search/Retrieve)
from langchain_core.documents import Document

from app.core.vectordb import get_vectorstore

TOP_K = 3


def get_retriever():
    vectorstore = get_vectorstore()
    return vectorstore.as_retriever(search_kwargs={"k": TOP_K})


def search(query: str) -> list[Document]:
    """컨벤션 문서를 검색합니다."""

    retriever = get_retriever()

    return retriever.invoke(query)
