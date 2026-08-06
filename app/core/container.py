import logging
import httpx
from dataclasses import dataclass
from typing import Any

from langchain_core.language_models import BaseChatModel

from app.core.config import AppSettings
from app.core.llm import build_llm_chain, build_lite_llm
from app.graph.agents import build_review_agent, build_question_agent
from app.graph.builder import build_review_graph, build_question_graph
from app.services.github_service import GitHubClient

logger = logging.getLogger("uvicorn.error")


@dataclass(frozen=True)
class Container:
    """애플리케이션이 사용하는 의존성 묶음. 부팅 시 한 번 조립됩니다."""

    settings: AppSettings
    llm: BaseChatModel
    lite_llm: BaseChatModel
    github: GitHubClient
    review_agent: Any
    question_agent: Any
    review_graph: Any
    question_graph: Any


def build_container(settings: AppSettings | None = None) -> Container:
    """의존성을 조립합니다. 이 프로젝트의 유일한 조립 지점입니다.

    여기서 실패하면 트래픽을 받기 전에 프로세스가 죽습니다(fail fast).
    """
    settings = settings or AppSettings()
    logger.info(f"[container] env={settings.APP_ENV} llm={settings.LLM_PRIMARY}")

    llm = build_llm_chain(settings)
    lite_llm = build_lite_llm(settings)

    github = GitHubClient(settings, httpx.AsyncClient())

    review_agent = build_review_agent(
        model=llm,
        #        tools=[make_search_convention(session_factory=rdb.session_maker)],
    )

    question_agent = build_question_agent(model=llm)

    logger.info("[container] 조립 완료")

    return Container(
        settings=settings,
        llm=llm,
        lite_llm=lite_llm,
        github=github,
        review_agent=review_agent,
        question_agent=question_agent,
        review_graph=build_review_graph(),
        question_graph=build_question_graph(),
    )
