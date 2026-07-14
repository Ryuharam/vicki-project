from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver

from app.services.tools import search_convention
from app.services.prompts import SYSTEM_PROMPT
from app.schemas.response import ReviewComments


def get_review_agent():
    model = ChatOllama(model="gemma4:e2b-mlx")

    agent = create_agent(
        model=model,
        tools=[search_convention],
        checkpointer=InMemorySaver(),
        system_prompt=SYSTEM_PROMPT,
        response_format=ReviewComments,
    )
    return agent
