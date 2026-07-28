import hashlib
import hmac
import logging
import time
from typing import List

import httpx
import jwt
from pydantic import TypeAdapter

from app.core.config import AppSettings
from app.schemas.response import GitHubFileItem

logger = logging.getLogger("uvicorn.error")

API_VERSION = "2026-03-10"


def get_github_headers(token: str) -> dict:
    """Github API 요청 헤더를 생성합니다."""
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": API_VERSION,
    }


class GitHubClient:
    """GitHub App 자격증명을 들고 API를 호출합니다."""

    def __init__(self, settings: AppSettings):
        self._webhook_secret = settings.WEBHOOK_SECRET
        self._client_id = settings.GITHUB_CLIENT_ID
        self._key_file_path = settings.GITHUB_KEY_FILE_PATH

    def is_valid_webhook(self, payload_body: bytes, signature_header: str) -> bool:
        """깃허브 웹훅 요청을 검증합니다."""
        hash_object = hmac.new(
            self._webhook_secret.encode("utf-8"),
            msg=payload_body,
            digestmod=hashlib.sha256,
        )

        expect_signature = "sha256=" + hash_object.hexdigest()

        return hmac.compare_digest(signature_header, expect_signature)

    def generate_jwt(self) -> str:
        """깃허브 앱 인증을 위한 JWT를 생성합니다."""
        with open(self._key_file_path, "rb") as pem_file:
            signing_key = pem_file.read()

        payload = {
            "iat": int(time.time()),
            "exp": int(time.time()) + 600,
            "iss": self._client_id,
        }

        return jwt.encode(payload=payload, key=signing_key, algorithm="RS256")

    def request_access_token(self, installation_id: str) -> str:
        """JWT를 사용하여 깃허브 Access Token을 요청합니다."""
        logger.info("Request installation access token")

        url = (
            f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        )
        headers = get_github_headers(self.generate_jwt())

        response = httpx.post(url=url, headers=headers)
        response_data = response.json()

        return response_data.get("token")

    async def get_pr_files(
        self, owner: str, repo: str, pull_number: int, token: str
    ) -> List[GitHubFileItem]:
        """PR에서 변경된 파일 목록 및 변경 사항을 조회합니다."""
        logger.info("Request PR Files")

        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/files"
        headers = get_github_headers(token)

        async with httpx.AsyncClient() as client:
            response = await client.get(url=url, headers=headers)
            response.raise_for_status()

            adapter = TypeAdapter(List[GitHubFileItem])
            return adapter.validate_python(response.json())

    async def create_review(
        self, owner: str, repo: str, pull_number: int, token: str, event: str, body: str
    ) -> None:
        """event에 따라 다른 로직 수행.
        event: APPROVE, REQUEST_CHANGES, COMMENT"""
        logger.info("Create review")

        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews"
        headers = get_github_headers(token=token)

        logger.info(f"리뷰 작성 요청 전송 : event - {event}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=url, headers=headers, json={"body": body, "event": event}
            )
            response.raise_for_status()
