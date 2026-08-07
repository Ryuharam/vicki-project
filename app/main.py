import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from app.logging_config import setup_logging
from app.api import webhook_router
from app.core.container import build_container
from app.exceptions.custom_exception import BaseAPIException
from app.exceptions.handler import (
    global_exception_handler,
    validation_exception_handler,
)

setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """부팅 시 의존성 container를 조립하고, 종료 시 github 클라이언트를 정리합니다."""
    app.state.container = build_container()
    yield
    await app.state.container.github.aclose()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

@app.middleware("http")
async def log_request_duration(request: Request, call_next):
    """요청 처리 시간을 로그로 남깁니다.

    응답을 돌려주기까지의 시간만 재며, BackgroundTasks로 넘긴 작업 시간은 포함되지 않습니다.
    """
    started_at = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        logger.exception(
            f"[request] {request.method} {request.url.path} 처리 중 예외 ({elapsed_ms:.0f}ms)"
        )
        raise

    elapsed_ms = (time.perf_counter() - started_at) * 1000
    logger.info(
        f"[request] {request.method} {request.url.path} "
        f"-> {response.status_code} ({elapsed_ms:.0f}ms)"
    )

    return response


app.add_exception_handler(BaseAPIException, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.include_router(webhook_router.router)


@app.get("/")
def root():
    """루트 응답."""
    return "Hello"


@app.get("/healthz")
def healthcheck():
    """헬스체크 엔드포인트."""
    return {"status": "ok"}
