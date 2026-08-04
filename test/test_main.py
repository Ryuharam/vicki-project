# import hashlib
# import hmac
# import json

# import pytest
# from fastapi.testclient import TestClient

# from app.api.deps import get_container
# from app.main import app, healthcheck


# def test_healthcheck():
#     assert healthcheck() == {"status": "ok"}


# @pytest.fixture
# def client(container):
#     """container를 가짜로 갈아끼운 TestClient.

#     lifespan을 실행하지 않으므로 Chroma도 API 키도 필요 없습니다.
#     """
#     app.dependency_overrides[get_container] = lambda: container
#     yield TestClient(app)
#     app.dependency_overrides.clear()


# def sign(secret: str, body: bytes) -> str:
#     digest = hmac.new(secret.encode(), msg=body, digestmod=hashlib.sha256).hexdigest()
#     return f"sha256={digest}"


# def test_webhook_rejects_missing_signature(client):
#     response = client.post("/webhook", json={"action": "opened"})

#     assert response.status_code == 403


# def test_webhook_rejects_bad_signature(client):
#     response = client.post(
#         "/webhook",
#         json={"action": "opened"},
#         headers={"x-hub-signature-256": "sha256=deadbeef"},
#     )

#     assert response.status_code == 403


# def test_webhook_ignores_event_without_action(client):
#     """서명은 맞지만 action이 없으면 그래프를 실행하지 않습니다."""
#     body = json.dumps({"zen": "ping"}).encode()

#     response = client.request(
#         "POST",
#         "/webhook",
#         content=body,
#         headers={"x-hub-signature-256": sign("test-secret", body)},
#     )

#     assert response.status_code == 200
#     assert response.json() == {}


# def test_convention_list_uses_injected_repository(client, repository):
#     """라우터가 container의 repository를 그대로 사용합니다."""
#     assert client.get("/convention").json() == []

#     repository.added.append(
#         type("Doc", (), {"metadata": {"filename": "convention.md"}})()
#     )

#     assert client.get("/convention").json() == ["convention.md"]
