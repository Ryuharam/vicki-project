# LangGraph의 State 정의
from typing import TypedDict, List, Annotated, Any, Literal
from langgraph.graph.message import add_messages, BaseMessage

from app.schemas.response import GitHubFileItem


class BaseState(TypedDict):
    payload: dict
    installation_id: str
    access_token: str
    owner: str
    repo: str  # repo 이름
    repo_id: int
    pull_number: int
    messages: Annotated[list[BaseMessage], add_messages]


class ReviewBotState(BaseState):
    pr_files: List[GitHubFileItem]
    review_decision: Literal["REVIEW", "SKIP"]
    reject_reason: str
    pr_title: str
    pr_body: str
    has_convention: bool
    llm_result: str
    review_result: str
    diff_summary: str
    verdict: Literal["APPROVE", "REQUEST_CHANGES", "COMMENT"]
    conventions: list


class ReviewBotContext(TypedDict):
    review_agent: Any
    github: Any
    lite_llm: Any


class QuestionBotState(BaseState):
    question: str
    reviews: list
    comments: list
    context: str
    answer: str


class QuestionBotContext(TypedDict):
    question_agent: Any
    github: Any
