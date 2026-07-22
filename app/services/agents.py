import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from app.services.tools import search_convention
from app.services.prompts import SYSTEM_PROMPT
from app.schemas.response import ReviewComments
from app.core.llm import get_model

load_dotenv()


def get_review_agent():

    model = get_model()

    agent = create_agent(
        model=model,
        tools=[search_convention],
        checkpointer=InMemorySaver(),
        system_prompt=SYSTEM_PROMPT,
        response_format=ReviewComments,
    )
    return agent
