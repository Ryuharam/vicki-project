from pathlib import Path

from langchain_core.tools import tool
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = BASE_DIR / "chroma_db"
TOP_K = 3


def build_retriever():
    embeddings = OllamaEmbeddings(model="bge-m3")

    if not CHROMA_DIR.exists:
        raise FileNotFoundError(f"Vector DB not found")

    vectorstore = Chroma(
        persist_directory=str(CHROMA_DIR), embedding_function=embeddings
    )

    return vectorstore.as_retriever(search_kwargs={"k": TOP_K})


@tool
def search_convention(query: str) -> str:
    """팀과 협의한 컨벤션 노트를 확인합니다.

    Args:
        query: 컨벤션에서 확인할 검색어

    Returns:
        result: chromadb에서 검색한 결과(string)
    """

    retriever = build_retriever()
    result = retriever.invoke(query)

    docs = "\n\n".join(doc.page_content for doc in result)

    return docs


@tool
def call_github_tool(file_name: str) -> str:
    """자세한 내용이 필요한 코드를 Github에서 확인합니다.

    Args:
        file_name: 원하는 파일 이름

    Returns:
        result: 원하는 파일 코드(string)
    """
    return ""


@tool
def write_comment():
    """코드 변경사항과 관련 코드를 보고 코드 리뷰를 작성합니다.

    Args:
        diff_file: 변경 파일 목록

    Returns:
        result: 개선 사항
    """

    return
