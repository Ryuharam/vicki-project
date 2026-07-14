# LangGraph의 State 정의
from typing import TypedDict, List, Annotated, Any
from langgraph.graph.message import add_messages

from app.schemas.response import GitHubFileItem


class ReviewBotState(TypedDict):
    payload: dict
    installation_id: str
    access_token: str
    owner: str
    repo: str
    pull_number: int
    pr_files: List[GitHubFileItem]
    messages: Annotated[list, add_messages]
    pr_title: str
    pr_body: str
    review_result: str


class ReviewBotContext(TypedDict):
    review_agent: Any
