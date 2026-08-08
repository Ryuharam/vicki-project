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

logger = logging.getLogger(__name__)

API_VERSION = "2026-03-10"


async def _on_request(request: httpx.Request) -> None:
    """요청 시작 시각을 남겨 응답 훅에서 소요 시간을 계산할 수 있게 합니다."""
    request.extensions["started_at"] = time.perf_counter()


async def _on_response(response: httpx.Response) -> None:
    """Github API 호출의 상태 코드와 소요 시간을 남깁니다.

    `response.elapsed` 는 본문을 읽기 전이라 이 시점에 접근할 수 없어 직접 잽니다.
    """
    request = response.request
    started_at = request.extensions.get("started_at")
    elapsed_ms = (time.perf_counter() - started_at) * 1000 if started_at else -1

    level = logging.WARNING if response.status_code >= 400 else logging.INFO
    logger.log(
        level,
        f"[github] {request.method} {request.url.path} "
        f"-> {response.status_code} ({elapsed_ms:.0f}ms)",
    )


def build_http_client() -> httpx.AsyncClient:
    """Github API 호출 로깅 훅이 달린 httpx 클라이언트를 만듭니다."""
    return httpx.AsyncClient(
        event_hooks={"request": [_on_request], "response": [_on_response]}
    )


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

    async def aclose(self) -> None:
        """내부 httpx 클라이언트를 닫습니다. 앱 종료 시 호출합니다."""
        await self._client.aclose()

    def is_valid_webhook(self, payload_body: bytes, signature_header: str) -> bool:
        """webhook secret으로 서명을 계산해 요청이 깃허브에서 왔는지 검증합니다."""
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
        """JWT로 인증해 해당 installation의 access token을 발급받습니다."""
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
        """PR에서 변경된 파일 목록과 patch 내용을 조회합니다."""
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/files"
        headers = get_github_headers(token)

        response = await self._client.get(url=url, headers=headers)
        response.raise_for_status()

        adapter = TypeAdapter(List[GitHubFileItem])
        return adapter.validate_python(response.json())

    async def create_review(
        self, owner: str, repo: str, pull_number: int, token: str, event: str, body: str
    ) -> None:
        """PR에 review를 생성합니다.

        Args:
            event: APPROVE, REQUEST_CHANGES, COMMENT 중 하나
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews"
        headers = get_github_headers(token=token)

        response = await self._client.post(
            url=url, headers=headers, json={"body": body, "event": event}
        )
        response.raise_for_status()

    async def create_comment(
        self, owner: str, repo: str, pull_number: int, token: str, body: str
    ) -> None:
        """PR에 일반 comment를 생성합니다."""
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
    ) -> List[str]:
        """PR에 달린 review 중 본문이 있는 것들의 body만 모아서 반환합니다."""
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews"
        header = get_github_headers(token=token)

        response = await self._client.get(url=url, headers=header)
        response.raise_for_status()

        review_data = response.json()
        reviews = [review["body"] for review in review_data if review.get("body")]

        return reviews

    async def get_comments(
        self, owner: str, repo: str, pull_number: int, token: str
    ) -> List[str]:
        """PR에 달린 comment 중 본문이 있는 것들의 body만 모아서 반환합니다."""
        url = (
            f"https://api.github.com/repos/{owner}/{repo}/issues/{pull_number}/comments"
        )
        header = get_github_headers(token=token)

        response = await self._client.get(url=url, headers=header)
        response.raise_for_status()

        comment_data = response.json()
        comments = [comment["body"] for comment in comment_data if comment.get("body")]

        return comments

    async def get_convention_files(
        self, owner: str, repo: str, dirpath: str, token: str
    ) -> List[dict]:
        """main 브랜치의 dirpath 아래 파일 목록을 조회합니다.

        디렉토리가 없으면(404) 빈 리스트를 반환합니다.
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{dirpath}?ref=main"
        header = get_github_headers(token=token)

        response = await self._client.get(url=url, headers=header)

        if response.status_code == 404:
            logger.info(f"[github] main 브랜치에 {dirpath} 디렉토리가 없습니다.")
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
    ) -> str:
        """main 브랜치의 filepath 파일 내용을 base64 디코딩해서 반환합니다.
        바이너리 파일인 경우 content에 빈 문자열을 반환합니다."""
        BINARY_EXTENSIONS = (
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".pdf",
            ".zip",
            ".tar",
            ".gz",
            ".exe",
            ".dll",
        )

        if filepath.lower().endswith(BINARY_EXTENSIONS):
            return "None"

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
