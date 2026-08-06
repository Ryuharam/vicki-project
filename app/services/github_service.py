import hashlib
import hmac
import base64
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

    def __init__(self, settings: AppSettings, client: httpx.AsyncClient):
        self._webhook_secret = settings.WEBHOOK_SECRET
        self._client_id = settings.GITHUB_CLIENT_ID
        self._key_file_path = settings.GITHUB_KEY_FILE_PATH
        self._client = client

    async def aclose(self):
        await self._client.aclose()

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

    async def request_access_token(self, installation_id: str) -> str:
        """JWT를 사용하여 깃허브 Access Token을 요청합니다."""
        logger.info("Request installation access token")

        url = (
            f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        )
        headers = get_github_headers(self.generate_jwt())

        response = await self._client.post(url=url, headers=headers)
        response.raise_for_status()
        response_data = response.json()

        # TODO: response_data.get("expires_at") 캐싱
        access_token = response_data.get("token")
        expires_at = response_data.get("expires_at")

        return access_token

    async def get_pr_files(
        self, owner: str, repo: str, pull_number: int, token: str
    ) -> List[GitHubFileItem]:
        """PR에서 변경된 파일 목록 및 변경 사항을 조회합니다."""
        logger.info("Request PR Files")

        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/files"
        headers = get_github_headers(token)

        response = await self._client.get(url=url, headers=headers)
        response.raise_for_status()

        adapter = TypeAdapter(List[GitHubFileItem])
        return adapter.validate_python(response.json())

    async def create_review(
        self, owner: str, repo: str, pull_number: int, token: str, event: str, body: str
    ) -> None:
        """event에 따라 다른 로직 수행.
        event: APPROVE, REQUEST_CHANGES, COMMENT"""
        logger.info("Create comment")

        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews"
        headers = get_github_headers(token=token)

        response = await self._client.post(
            url=url, headers=headers, json={"body": body, "event": event}
        )
        response.raise_for_status()

    async def create_comment(
        self, owner: str, repo: str, pull_number: int, token: str, body: str
    ) -> None:
        """event에 따라 다른 로직 수행.
        event: APPROVE, REQUEST_CHANGES, COMMENT"""
        logger.info("Create comment")

        url = (
            f"https://api.github.com/repos/{owner}/{repo}/issues/{pull_number}/comments"
        )
        headers = get_github_headers(token=token)

        response = await self._client.post(
            url=url, headers=headers, json={"body": body}
        )
        response.raise_for_status()

    async def get_reviews(
        self, owner: str, repo: str, pull_number: int, token: str
    ) -> str:
        """PR에 달린 review 조회"""
        logger.info("Review 조회")

        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews"
        header = get_github_headers(token=token)

        response = await self._client.get(url=url, headers=header)
        response.raise_for_status()

        review_data = response.json()
        reviews = [review["body"] for review in review_data if review.get("body")]

        return reviews

    async def get_comments(
        self, owner: str, repo: str, pull_number: int, token: str
    ) -> list:
        """PR에 달린 comment 조회"""
        logger.info("Comment 조회")

        url = (
            f"https://api.github.com/repos/{owner}/{repo}/issues/{pull_number}/comments"
        )
        header = get_github_headers(token=token)

        logger.info(f"url: {url}")

        response = await self._client.get(url=url, headers=header)
        response.raise_for_status()

        comment_data = response.json()
        comments = [comment["body"] for comment in comment_data if comment.get("body")]

        return comments

    async def get_convention_files(
        self, owner: str, repo: str, dirpath: str, token: str
    ):
        """main 브랜치의 dirpath 아래의 파일들을 읽어온다"""
        logger.info(f"{dirpath} 안의 파일들 정보 읽어오기")

        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{dirpath}?ref=main"
        header = get_github_headers(token=token)

        response = await self._client.get(url=url, headers=header)

        if response.status_code == 404:
            logger.info(f"main 브랜치에 {dirpath} 디렉토리가 없습니다.")
            return []

        response.raise_for_status()

        file_data = response.json()
        file_list = [
            {"name": file["name"], "filepath": file["path"]}
            for file in file_data
            if file.get("name") and file.get("path")
        ]

        return file_list

    async def get_convention_file(
        self,
        owner: str,
        repo: str,
        filepath: str,
        token: str,
    ):
        """filepath 로 파일 내용을 읽어온다"""
        logger.info(f"{filepath} 읽어오기")

        url = (
            f"https://api.github.com/repos/{owner}/{repo}/contents/{filepath}?ref=main"
        )
        header = get_github_headers(token=token)

        response = await self._client.get(url=url, headers=header)
        response.raise_for_status()

        file_data = response.json()
        encoded_content = file_data.get("content", "").replace("\n", "")
        content_bytes = base64.b64decode(encoded_content)
        content = content_bytes.decode("utf-8")

        return content
