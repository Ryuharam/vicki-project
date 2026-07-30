# LangGraph의 State 정의
from typing import TypedDict, List, Annotated, Any, Literal
from langgraph.graph.message import add_messages

from app.schemas.response import GitHubFileItem


class ReviewBotState(TypedDict):
    payload: dict
    installation_id: str
    access_token: str
    owner: str
    repo: str
    repo_id: int
    pull_number: int
    pr_files: List[GitHubFileItem]
    review_decision: Literal["REVIEW", "SKIP"]
    reject_reason: str
    messages: Annotated[list, add_messages]
    pr_title: str
    pr_body: str
    review_result: str
    diff_summary: str
    verdict: Literal["APPROVE", "REQUEST_CHANGES", "COMMENT"]


class ReviewBotContext(TypedDict):
    review_agent: Any
    github: Any
    lite_llm: Any


class QuestionBotState(TypedDict):
    payload: dict
    installation_id: str
    access_token: str
    owner: str
    repo: str
    repo_id: int
    pull_number: int
    comment: str
    answer: str


class QuestionBotContext(TypedDict):
    question_agent: Any
    github: Any
