# LangGraph의 State 정의
from typing import TypedDict, List, Annotated, Any, Literal
from langgraph.graph.message import add_messages

from app.schemas.response import GitHubFileItem


class ReviewBotState(TypedDict):
    payload: dict
    installation_id: str
    access_token: str
    owner: str
    repo_id: int
    repo: str
    pull_number: int
    pr_files: List[GitHubFileItem]
    messages: Annotated[list, add_messages]
    pr_title: str
    pr_body: str
    review_result: str
    diff_summary: str
    verdict: Literal["APPROVE", "REQUEST_CHANGES", "COMMENT"]


class ReviewBotContext(TypedDict):
    """그래프 실행에 주입되는 의존성. 요청마다 container에서 채웁니다."""

    review_agent: Any
    github: Any
