import hashlib
import logging

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.repositories.vector_repository import add_documents, search_by_hash

logger = logging.getLogger("uvicorn.error")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
)


def calculate_hash(content: str) -> str:
    """문서 내용의 SHA256 해시를 계산합니다."""

    return hashlib.sha256(content.encode()).hexdigest()


def is_dupicate(repo_id: int, filehash: str) -> bool:
    """이미 동일한 문서가 존재하는지 확인합니다."""

    return bool(search_by_hash(repo_id, filehash))


def create_document(
    content: str, filename: str, repo_id: int, filehash: str
) -> Document:
    """Document와 metadata를 생성합니다."""

    return Document(
        page_content=content,
        metadata={"filename": filename, "repo_id": repo_id, "filehash": filehash},
    )


def split_documents(documents: list[Document]) -> list[Document]:
    """Document를 Chunk 단위로 분할합니다."""
    chunks = _splitter.split_documents(documents)

    logger.info(f"{len(chunks)} chunks 로 분할")

    return chunks


def upload_convention(content: str, filename: str, repo_id: int) -> None:
    """컨벤션 문서를 저장합니다."""

    filehash = calculate_hash(content=content)

    if is_dupicate(repo_id=repo_id, filehash=filehash):
        logger.info(f"이미 존재하는 파일 : {filename}")
        return

    document = create_document(content=content, filename=filename, repo_id=repo_id)

    chunks = split_documents([document])

    add_documents(chunks)

    logger.info("문서 저장 완료")
