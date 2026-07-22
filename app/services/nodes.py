import logging

from langchain_core.messages import HumanMessage
from langgraph.runtime import Runtime

from app.schemas.response import ReviewComments
from app.schemas.state import ReviewBotState, ReviewBotContext
from app.services.github_service import (
    request_access_token,
    get_pr_files,
    post_pr_comment,
)

logger = logging.getLogger("uvicorn.error")


async def preprocess_node(state: ReviewBotState) -> dict:
    """GitHub API를 호출하여 토큰을 발급받고 변경된 파일(Diff) 목록을 가져와 상태를 업데이트하는 전처리 노드"""
    logger.info("[START] 전처리 노드 시작")

    payload = state["payload"]
    installation = payload.get("installation")
    if not installation:
        logger.error("Installation information missing in payload")
        return {}

    installation_id = installation.get("id")
    access_token = request_access_token(installation_id=installation_id)

    owner = payload.get("repository", {}).get("owner", {}).get("login")
    repo_id = payload.get("repository", {}).get("id")
    repo = payload.get("repository", {}).get("name")
    pull_request = payload.get("pull_request", {})
    pull_number = pull_request.get("number")
    pr_title = pull_request.get("title")
    pr_body = pull_request.get("body")

    validated_files = await get_pr_files(
        owner=owner, repo=repo, pull_number=pull_number, token=access_token
    )

    diff_summary = "리뷰할 PR의 변경점(Diff) 목록입니다.:\n"
    for file in validated_files:
        diff_summary += (
            f"\n파일명: {file.filename} \n{file.patch or "변경 내용 없음"}\n"
        )

    initial_messages = HumanMessage(
        content=f"우리 팀 컨벤션 가이드를 준수했는지 검사해 줘. \n Pull request title: {pr_title} \nPull request body: {pr_body} \n{diff_summary}"
    )

    return {
        "installation_id": installation_id,
        "owner": owner,
        "repo_id": repo_id,
        "repo": repo,
        "pull_number": pull_number,
        "access_token": access_token,
        "pr_files": validated_files,
        "messages": [initial_messages],
        "pr_title": pr_title,
        "pr_body": pr_body,
    }


async def review_node(state: ReviewBotState, runtime: Runtime[ReviewBotContext]):
    """컨벤션과 Diff를 참고해 PR comment를 생성합니다."""
    logger.info("[START] review node start")
    review_agent = runtime.context["review_agent"]

    result = await review_agent.ainvoke({"messages": state["messages"]})

    logger.info(f"result key 확인 : {result.keys()}")

    # structured output이 있으면 파싱 후 최종 리뷰 완성
    if "structured_response" in result:
        logger.info("structured_output 있음")
        structured = result["structured_response"]

        review = parsing_response(structured)
        return {"review_result": review}

    # 없으면 평문 그대로 반환
    last_message = result["messages"][-1].content

    return {"review_result": last_message}


def parsing_response(response: ReviewComments) -> str:
    """structurd_response를 최종 응답 형태로 바꿉니다."""
    if not response.comments:
        return (
            f"## Summary\n"
            f"{response.summary}\n\n"
            "## Comments\n\n"
            "리뷰할 사항이 없습니다."
        )

    lines = [
        "## Summary",
        response.summary,
        "",
        "## Comments",
        "",
    ]

    for i, comment in enumerate(sorted(response.comments), start=1):
        lines.extend(
            [
                f"### {i}. [{comment.severity}] {comment.title}",
                f"- category: {comment.category}",
                f"- issue: {comment.issue}",
                f"- suggestion: {comment.suggestion}",
                "",
            ]
        )

    return "\n".join(lines)


async def comment_node(state: ReviewBotState):
    """최종 PR comment를 게시합니다."""
    logger.info("[START ] comment node start")

    review = state["review_result"]

    logger.info(f"review: \n{review}")

    await post_pr_comment(
        owner=state["owner"],
        repo=state["repo"],
        pull_number=state["pull_number"],
        token=state["access_token"],
        body=state["review_result"],
    )

    return {}
