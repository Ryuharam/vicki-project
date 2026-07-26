import logging
from dataclasses import dataclass
from typing import Any

from langchain_chroma import Chroma
from langchain_core.language_models import BaseChatModel

from app.core.config import AppSettings
from app.core.embedding import build_embeddings
from app.core.llm import build_llm_chain
from app.core.vectordb import build_vectorstore
from app.repositories.vector_repository import ConventionRepository
from app.services.agents import build_review_agent
from app.services.builder import build_graph
from app.services.github_service import GitHubClient
from app.services.tools import make_search_convention

logger = logging.getLogger("uvicorn.error")


@dataclass(frozen=True)
class Container:
    """애플리케이션이 사용하는 의존성 묶음. 부팅 시 한 번 조립됩니다."""

    settings: AppSettings
    llm: BaseChatModel
    vectorstore: Chroma
    repository: ConventionRepository
    github: GitHubClient
    review_agent: Any
    graph: Any


def build_container(settings: AppSettings | None = None) -> Container:
    """의존성을 조립합니다. 이 프로젝트의 유일한 조립 지점입니다.

    여기서 실패하면 트래픽을 받기 전에 프로세스가 죽습니다(fail fast).
    """
    settings = settings or AppSettings()
    logger.info(f"[container] env={settings.APP_ENV} llm={settings.LLM_PRIMARY}")

    llm = build_llm_chain(settings)
    embeddings = build_embeddings(settings)
    vectorstore = build_vectorstore(settings, embeddings)

    repository = ConventionRepository(vectorstore)
    github = GitHubClient(settings)

    review_agent = build_review_agent(
        model=llm,
        tools=[make_search_convention(repository)],
    )

    logger.info("[container] 조립 완료")

    return Container(
        settings=settings,
        llm=llm,
        vectorstore=vectorstore,
        repository=repository,
        github=github,
        review_agent=review_agent,
        graph=build_graph(),
    )
