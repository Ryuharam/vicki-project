import json
import logging
from fastapi import APIRouter, Request, HTTPException

from app.services.github_service import is_valid_github_webhook

router = APIRouter(prefix="/webhook", tags=["webhook"])
logger = logging.getLogger("uvicorn.error")


@router.post("")
async def github_webhook(request: Request):
    """
    GitHub Pull Request 웹훅 이벤트를 처리하는 핸들러

    GitHub에서 발송한 PR Webhook payload를 수신하고, 검증 후
    PR의 상태(열림, 닫힘, 머지)에 따라 후속 로직을 실행합니다.

    Args:
        - request (Request): GitHub가 보낸 raw request 객체.
            `x-hub-signature-256` 헤더를 반드시 포함해야 합니다.

    Raises:
        - HTTPException:
            - 403 : Signature 헤더가 누락되었거나 검증에 실패하는 경우

    Returns:
        dict: 빈 딕셔너리 (HTTP 200 OK)
    """
    logger.info("PR Webhook 도착")

    payload_body = await request.body()
    signature_header = request.headers.get("x-hub-signature-256")

    if not signature_header:
        logger.error("header 없음")
        raise HTTPException(
            status_code=403, detail="x-hub-signature-256 header is missing!"
        )

    if not is_valid_github_webhook(payload_body, signature_header):
        logger.error("검증 실패")
        raise HTTPException(status_code=403, detail="Request signatures didn't match!")

    payload = json.loads(payload_body)

    action = payload.get("action")
    if not action:
        logger.info("This event doesn't have an action field")
        return {}

    if action in ["opened", "synchronize"]:
        logger.info(f"PR - action : {action}")

        graph = request.app.state.graph

        await graph.ainvoke(
            {"payload": payload},
            context={"review_agent": request.app.state.review_agent},
        )

    elif action == "closed":
        logger.info("PR closed")
        if payload.get("pull_request", {}).get("merged"):
            logger.info("PR merged")
        else:
            logger.info("PR not merged")
    return {}
