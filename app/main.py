from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api import webhook_router, convention_router
from app.services.agents import get_review_agent
from app.services.builder import build_graph

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.review_agent = get_review_agent()
    app.state.graph = build_graph()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(webhook_router.router)
app.include_router(convention_router.router)


@app.get("/")
def root():
    return "Hello"


@app.get("/healthz")
def healthcheck():
    return {"status": "ok"}
