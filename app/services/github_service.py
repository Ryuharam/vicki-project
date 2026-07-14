import os
import time
import hmac
import hashlib
import logging
from typing import List
from pydantic import TypeAdapter

import jwt
import httpx
from dotenv import load_dotenv

from app.schemas.response import GitHubFileItem

load_dotenv()
logger = logging.getLogger("uvicorn.error")


def is_valid_github_webhook(payload_body: bytes, signature_header: str) -> bool:
    """깃허브 웹훅 요청을 검증합니다."""

    webhook_secret = os.getenv("WEBHOOK_SECRET")

    hash_object = hmac.new(
        webhook_secret.encode("utf-8"), msg=payload_body, digestmod=hashlib.sha256
    )

    expect_signature = "sha256=" + hash_object.hexdigest()

    return hmac.compare_digest(signature_header, expect_signature)


def generate_jwt() -> str:
    """깃허브 앱 인증을 위한 JWT를 생성합니다."""

    client_id = os.getenv("GITHUB_CLIENT_ID")
    pem_file_path = os.getenv("GITHUB_KEY_FILE")

    with open(pem_file_path, "rb") as pem_file:
        signing_key = pem_file.read()

    payload = {"iat": int(time.time()), "exp": int(time.time()) + 600, "iss": client_id}

    encoded_jwt = jwt.encode(payload=payload, key=signing_key, algorithm="RS256")
    return encoded_jwt


def get_github_headers(token: str) -> dict:
    """Github API 요청 헤더를 생성합니다."""
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2026-03-10",
    }


def request_access_token(installation_id: str) -> str:
    """JWT를 사용하여 깃허브 Access Token을 요청합니다."""
    logger.info("Request installation access token")

    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    jwt_token = generate_jwt()

    headers = get_github_headers(jwt_token)

    response = httpx.post(url=url, headers=headers)
    response_data = response.json()

    return response_data.get("token")


async def get_pr_files(
    owner: str, repo: str, pull_number: int, token: str
) -> List[GitHubFileItem]:
    """PR에서 변경된 파일 목록 및 변경 사항을 조회합니다."""
    logger.info("Request PR Files")

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/files"
    headers = get_github_headers(token)

    async with httpx.AsyncClient() as client:
        response = await client.get(url=url, headers=headers)
        response.raise_for_status()

        adapter = TypeAdapter(List[GitHubFileItem])
        validated = adapter.validate_python(response.json())
        return validated


async def post_pr_comment(
    owner: str, repo: str, pull_number: int, token: str, body: str
) -> None:
    """생성해 낸 최종 Comment를 게시합니다."""
    logger.info("[Tool] Post Comment")

    if body is None:
        logger.warning("Comment body is empty. Skip posting comment.")
        return

    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pull_number}/comments"
    headers = get_github_headers(token=token)

    async with httpx.AsyncClient() as client:
        response = await client.post(url=url, headers=headers, json={"body": body})
        response.raise_for_status()
