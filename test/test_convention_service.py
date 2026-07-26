from langchain_core.documents import Document

from app.services.convention_service import calculate_hash, upload_convention
from app.services.tools import make_search_convention


def test_upload_convention_stores_chunks(repository):
    """새 문서는 청크로 분할되어 저장됩니다."""
    upload_convention(
        repository=repository,
        content="컨벤션 문서 내용",
        filename="convention.md",
        repo_id=1,
    )

    assert len(repository.added) == 1
    assert repository.added[0].metadata["filename"] == "convention.md"
    assert repository.added[0].metadata["repo_id"] == 1


def test_upload_convention_skips_duplicate(repository):
    """같은 내용이 이미 있으면 저장하지 않습니다."""
    content = "컨벤션 문서 내용"
    repository.existing_hashes.add(calculate_hash(content))

    upload_convention(
        repository=repository, content=content, filename="convention.md", repo_id=1
    )

    assert repository.added == []


def test_search_convention_tool_joins_documents(repository):
    """tool은 주입받은 repository로 검색해 본문을 이어붙입니다."""
    repository.search_results = [
        Document(page_content="첫번째", metadata={"filename": "a.md"}),
        Document(page_content="두번째", metadata={"filename": "b.md"}),
    ]

    search_convention = make_search_convention(repository)
    result = search_convention.invoke({"query": "네이밍 규칙"})

    assert result == "첫번째\n\n두번째"
