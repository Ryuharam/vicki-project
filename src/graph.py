from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import SystemMessage, HumanMessage

from src.tools import search_convention
from src.prompts import SYSTEM_PROMPT


class graph:
    def __init__(self):
        self.agent = self._build_graph()

    def _build_graph(self):
        model = ChatOllama(model="gemma4:e2b-mlx")

        agent = create_agent(
            model=model,
            tools=[search_convention],
            checkpointer=InMemorySaver(),
            system_prompt=SYSTEM_PROMPT,
        )
        return agent

    def ask(self, question: str, thread_id: str):
        config = {"configurable": {"thread_id": thread_id}}
        result = self.agent.invoke(
            {"messages": [HumanMessage(content=question)]}, config=config
        )
        response = result["messages"][-1].content
        return response
