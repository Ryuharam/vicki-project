# LangGraph의 State 정의
from typing import TypedDict, List, Annotated, Any, Literal
from langgraph.graph.message import add_messages, BaseMessage

from app.schemas.response import GitHubFileItem


class BaseState(TypedDict):
    """두 그래프가 공통으로 쓰는 state. webhook payload와 Github 호출용 정보를 담습니다."""

    payload: dict
    installation_id: str
    access_token: str
    owner: str
    repo: str  # repo 이름
    repo_id: int
    pull_number: int
    messages: Annotated[list[BaseMessage], add_messages]


class ReviewBotState(BaseState):
    """리뷰 그래프의 state. diff 수집부터 최종 리뷰 본문까지의 중간 결과를 담습니다."""

    pr_files: List[GitHubFileItem]
    review_decision: Literal["REVIEW", "SKIP"]
    reject_reason: str
    pr_title: str
    pr_body: str
    has_diff: Literal["EXIST", "MISSING"]
    not_md_convention: bool
    has_convention: bool
    llm_result: str
    review_result: str
    diff_files: list
    verdict: Literal["APPROVE", "REQUEST_CHANGES", "COMMENT"]
    conventions: list


class ReviewBotContext(TypedDict):
    """리뷰 그래프 실행 시 주입되는 의존성."""

    review_agent: Any
    github: Any
    lite_llm: Any


class QuestionBotState(BaseState):
    """질문 그래프의 state. 질문과 조회한 review/comment, 생성된 답변을 담습니다."""

    question: str
    reviews: list
    comments: list
    context: str
    answer: str


class QuestionBotContext(TypedDict):
    """질문 그래프 실행 시 주입되는 의존성."""

    question_agent: Any
    github: Any
