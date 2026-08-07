import re
import json
import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks

from app.api.deps import ContainerDep

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])

PRISM_COMMAND_PATTERN = re.compile(r"^\s*/prism(?:\s|$)", re.IGNORECASE)


async def run_graph(name: str, graph: Any, payload: dict, context: dict) -> None:
    """백그라운드에서 그래프를 실행하고 소요 시간을 로그로 남깁니다.

    이미 200을 응답한 뒤 실행되므로, 예외는 밖으로 던지지 않고 여기서 기록만 합니다.
    """
    started_at = time.perf_counter()

    try:
        await graph.ainvoke({"payload": payload}, context=context)
    except Exception:
        logger.exception(f"[{name}] 실행 실패 ({time.perf_counter() - started_at:.1f}s)")
        return

    logger.info(f"[{name}] 실행 완료 ({time.perf_counter() - started_at:.1f}s)")


@router.post("")
async def github_webhook(
    request: Request,
    container: ContainerDep,
    background_tasks: BackgroundTasks,
):
    """GitHub 웹훅 이벤트를 검증하고 이벤트 종류에 맞는 그래프를 실행합니다.

    서명을 검증한 뒤 이벤트를 분기합니다.
    - pull_request(opened/synchronize): 리뷰 그래프를 백그라운드로 실행
    - issue_comment(created)에 `/prism` 명령: 질문 그래프를 백그라운드로 실행

    그 외 이벤트는 무시하고 바로 200을 반환합니다.

    Args:
        - request (Request): GitHub가 보낸 raw request 객체.
            `x-hub-signature-256` 헤더를 반드시 포함해야 합니다.

    Raises:
        - HTTPException:
            - 403 : Signature 헤더가 누락되었거나 검증에 실패하는 경우

    Returns:
        dict: 빈 딕셔너리 (HTTP 200 OK)
    """
    payload_body = await request.body()
    signature_header = request.headers.get("x-hub-signature-256")

    if not signature_header:
        logger.error("[webhook] `x-hub-signature-256` 헤더가 없습니다.")
        raise HTTPException(
            status_code=403, detail="x-hub-signature-256 header is missing!"
        )

    if not container.github.is_valid_webhook(payload_body, signature_header):
        logger.error("[webhook] 서명 검증에 실패했습니다.")
        raise HTTPException(status_code=403, detail="Request signatures didn't match!")

    event_header = request.headers.get("X-Github-Event")
    delivery_header = request.headers.get("X-Github-Delivery")

    payload = json.loads(payload_body)
    action = payload.get("action")

    logger.info(
        f"[webhook] 이벤트 수신: event={event_header} action={action} delivery={delivery_header}"
    )

    if not action:
        logger.info("[webhook] action 필드가 없어 무시합니다.")
        return {}

    if event_header == "pull_request":
        if action in ["opened", "synchronize"]:
            logger.info(f"[webhook] 리뷰 그래프 실행: action={action}")

            background_tasks.add_task(
                run_graph,
                "review_graph",
                container.review_graph,
                payload,
                {
                    "review_agent": container.review_agent,
                    "github": container.github,
                    "lite_llm": container.lite_llm,
                },
            )
    elif event_header == "issue_comment":
        if not payload.get("issue", {}).get("pull_request", {}):
            logger.info("[webhook] PR이 아닌 issue의 comment라 무시합니다.")
            return {}

        if action == "created":
            if payload.get("comment", {}).get("user", {}).get("type") == "Bot":
                logger.info("[webhook] Bot이 작성한 comment라 무시합니다.")
                return {}

            body = payload.get("comment", {}).get("body", "")

            if not PRISM_COMMAND_PATTERN.match(body):
                logger.info("[webhook] /prism 명령이 아니라 무시합니다.")
                return {}

            logger.info("[webhook] 질문 그래프 실행")

            background_tasks.add_task(
                run_graph,
                "question_graph",
                container.question_graph,
                payload,
                {
                    "question_agent": container.question_agent,
                    "github": container.github,
                },
            )
    return {}
