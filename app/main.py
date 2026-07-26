from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import convention_router, webhook_router
from app.core.container import build_container


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = build_container()
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
