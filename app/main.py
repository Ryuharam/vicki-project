from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api import webhook_router
from app.core.container import build_container
from app.exceptions.custom_exception import BaseAPIException
from app.exceptions.handler import (
    global_exception_handler,
    validation_exception_handler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = build_container()
    yield
    await app.state.container.github.aclose()


app = FastAPI(lifespan=lifespan)

app.add_exception_handler(BaseAPIException, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.include_router(webhook_router.router)


@app.get("/")
def root():
    return "Hello"


@app.get("/healthz")
def healthcheck():
    return {"status": "ok"}
