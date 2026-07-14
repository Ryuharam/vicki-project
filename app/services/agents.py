import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver

from app.services.tools import search_convention
from app.services.prompts import SYSTEM_PROMPT
from app.schemas.response import ReviewComments

load_dotenv()


def get_review_agent():
    # model = ChatOllama(model="gemma4:e2b-mlx")
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

    agent = create_agent(
        model=model,
        tools=[search_convention],
        checkpointer=InMemorySaver(),
        system_prompt=SYSTEM_PROMPT,
        response_format=ReviewComments,
    )
    return agent
