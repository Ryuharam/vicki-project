# import pytest
# from langchain_core.documents import Document

# from app.core.config import AppSettings
# from app.core.container import Container
# from app.services.github_service import GitHubClient


# @pytest.fixture
# def settings() -> AppSettings:
#     """실제 .env를 무시하고 테스트용 설정을 만듭니다.

#     _env_file=None 이 없으면 개발자 로컬의 .env가 섞여 들어와
#     테스트 결과가 사람마다 달라집니다.
#     """
#     return AppSettings(
#         _env_file=None,
#         WEBHOOK_SECRET="test-secret",
#         GITHUB_CLIENT_ID="test-client-id",
#         GITHUB_KEY_FILE_PATH="/nonexistent/key.pem",
#         LLM_PRIMARY="anthropic:claude-haiku-4-5-20251001",
#         LLM_FALLBACKS="google_genai:gemini-2.5-flash",
#         ANTHROPIC_API_KEY="test-anthropic-key",
#         GOOGLE_API_KEY="test-google-key",
#         EMBED_MODEL="test-embed-model",
#         VECTOR_DB_HOST="localhost",
#         VECTOR_DB_PORT=8000,
#     )


# class FakeRepository:
#     """ConventionRepository 대역. Chroma 없이 동작합니다."""

#     def __init__(self, existing_hashes: set[str] | None = None):
#         self.existing_hashes = existing_hashes or set()
#         self.added: list[Document] = []
#         self.search_results: list[Document] = []

#     def exists_by_hash(self, repo_id: int, filehash: str) -> bool:
#         return filehash in self.existing_hashes

#     def add_documents(self, documents: list[Document]) -> None:
#         self.added.extend(documents)

#     def similarity_search(self, query: str) -> list[Document]:
#         return self.search_results

#     def get_all_documents(self) -> set[str]:
#         return {d.metadata["filename"] for d in self.added}


# @pytest.fixture
# def repository() -> FakeRepository:
#     return FakeRepository()


# @pytest.fixture
# def container(settings: AppSettings, repository: FakeRepository) -> Container:
#     """네트워크가 필요한 부품은 넣지 않은 container.

#     frozen dataclass라 이렇게 직접 조립할 수 있습니다.
#     테스트가 필요로 하는 부품만 진짜를 넣으면 됩니다.
#     """
#     return Container(
#         settings=settings,
#         llm=None,
#         vectorstore=None,
#         repository=repository,
#         github=GitHubClient(settings),
#         review_agent=None,
#         graph=None,
#     )
