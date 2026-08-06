from typing import Sequence

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver

from app.schemas.response import ReviewComments, QuestionComment
from app.graph.prompts import REVIEW_SYSTEM_PROMPT, QUESTION_PROMPT


def build_review_agent(model: BaseChatModel):
    """리뷰 agent를 조립합니다. 모델은 주입받습니다."""
    return create_agent(
        model=model,
        system_prompt=REVIEW_SYSTEM_PROMPT,
        response_format=ReviewComments,
    )


def build_question_agent(model: BaseChatModel):
    """단어 질문 agent를 조립합니다. 모델은 주입받습니다."""
    return create_agent(
        model=model,
        checkpointer=InMemorySaver(),
        system_prompt=QUESTION_PROMPT,
        response_format=QuestionComment,
    )
