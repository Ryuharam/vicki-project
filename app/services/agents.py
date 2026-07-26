from typing import Sequence

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver

from app.schemas.response import ReviewComments
from app.services.prompts import SYSTEM_PROMPT


def build_review_agent(model: BaseChatModel, tools: Sequence[BaseTool]):
    """리뷰 agent를 조립합니다. 모델과 tool은 주입받습니다."""
    return create_agent(
        model=model,
        tools=list(tools),
        checkpointer=InMemorySaver(),
        system_prompt=SYSTEM_PROMPT,
        response_format=ReviewComments,
    )
