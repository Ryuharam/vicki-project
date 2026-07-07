from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, field_validator

from src.graph import graph

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.graph = graph()
    yield


app = FastAPI(lifespan=lifespan)


class ChatRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def strip_and_check(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("question은 공백일 수 없습니다.")
        return v


class ChatResponse(BaseModel):
    answer: str


@app.get("/")
def root():
    return "Hello"


@app.post("/chat")
def answer(request: ChatRequest):
    graph = app.state.graph
    answer = graph.ask(request.question, thread_id="1111")
    return ChatResponse(answer=answer)
