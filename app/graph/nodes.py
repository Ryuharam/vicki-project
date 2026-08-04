import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.runtime import Runtime

from app.schemas.response import ReviewComments, ReviewRouterItem
from app.schemas.state import (
    ReviewBotContext,
    ReviewBotState,
    QuestionBotState,
    QuestionBotContext,
)
from app.graph.prompts import REVIEW_DECISION_PROMPT

logger = logging.getLogger("uvicorn.error")


async def preprocess_node(
    state: ReviewBotState, runtime: Runtime[ReviewBotContext]
) -> dict:
    """GitHub API를 호출하여 토큰을 발급받고 변경된 파일(Diff) 목록을 가져와 상태를 업데이트하는 전처리 노드"""
    logger.info("[START] 전처리 노드 시작")

    github = runtime.context["github"]

    payload = state["payload"]
    installation = payload.get("installation")
    if not installation:
        logger.error("Installation information missing in payload")
        return {}

    installation_id = installation.get("id")
    access_token = github.request_access_token(installation_id=installation_id)

    owner = payload.get("repository", {}).get("owner", {}).get("login")
    repo = payload.get("repository", {}).get("name")
    repo_id = payload.get("repository", {}).get("id")
    pull_request = payload.get("pull_request", {})
    pull_number = pull_request.get("number")
    pr_title = pull_request.get("title")
    pr_body = pull_request.get("body")

    validated_files = await github.get_pr_files(
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
        "repo": repo,
        "repo_id": repo_id,
        "pull_number": pull_number,
        "access_token": access_token,
        "pr_files": validated_files,
        "messages": [initial_messages],
        "pr_title": pr_title,
        "pr_body": pr_body,
        "diff_summary": diff_summary,
    }


async def review_node(state: ReviewBotState, runtime: Runtime[ReviewBotContext]):
    """컨벤션과 Diff를 참고해 PR comment를 생성합니다."""
    logger.info("[START] review node start")
    review_agent = runtime.context["review_agent"]

    result = await review_agent.ainvoke({"messages": state["messages"]})

    if "structured_response" in result:
        logger.info("structured_output 있음")

        structured = result["structured_response"]

        if structured.verdict == "REQUEST_CHANGES":
            structured.summary += (
                "\n\n⚠️ severity가 high인 부분은 꼭 수정하시기 바랍니다!"
            )

        review = parsing_response(structured)

        return {"review_result": review, "verdict": structured.verdict}

    last_message = result["messages"][-1].content

    return {"review_result": last_message, "verdict": "COMMENT"}


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


async def comment_node(state: ReviewBotState, runtime: Runtime[ReviewBotContext]):
    """최종 PR comment를 게시합니다."""
    logger.info("[START] comment node start")

    github = runtime.context["github"]

    await github.create_review(
        owner=state["owner"],
        repo=state["repo"],
        pull_number=state["pull_number"],
        token=state["access_token"],
        event=state["verdict"],
        body=state["review_result"],
    )

    return {}


async def router_node(state: ReviewBotState, runtime: Runtime[ReviewBotContext]):
    logger.info("[START] router node 시작")
    llm = runtime.context["lite_llm"]

    structured_llm = llm.with_structured_output(ReviewRouterItem)

    system = SystemMessage(content=REVIEW_DECISION_PROMPT)
    human = HumanMessage(content=f"PR 내용 :\n\n{state["diff_summary"]}")

    result = await structured_llm.ainvoke([system, human])

    logger.info(f"리뷰가 필요하다고 생각한 근거는?\n{result.reason}")

    return {
        "review_decision": result.review_decision,
        "reject_reason": result.skip_reason,
    }


async def post_reject_node(state: ReviewBotState, runtime: Runtime[ReviewBotContext]):
    """리뷰를 거절합니다."""
    logger.info("[START] Post reject review")

    github = runtime.context["github"]

    await github.create_review(
        owner=state["owner"],
        repo=state["repo"],
        pull_number=state["pull_number"],
        token=state["access_token"],
        event="REQUEST_CHANGES",
        body=state["reject_reason"],
    )


async def question_preprocess_node(
    state: QuestionBotState, runtime: Runtime[QuestionBotContext]
):
    logger.info("[START] 질문 전처리 시작")

    github = runtime.context["github"]

    payload = state["payload"]
    installation_id = payload.get("installation", {}).get("id")
    access_token = github.request_access_token(installation_id=installation_id)

    repository = payload.get("repository")
    owner = repository.get("owner", {}).get("login")
    repo = repository.get("name")
    repo_id = repository.get("id")

    issue = payload.get("issue")
    pull_number = issue.get("number")
    comment = payload.get("comment", {}).get("body")

    return {
        "installation_id": installation_id,
        "access_token": access_token,
        "owner": owner,
        "repo": repo,
        "repo_id": repo_id,
        "pull_number": pull_number,
        "comment": comment,
    }


async def answer_node(state: QuestionBotState, runtime: Runtime[QuestionBotContext]):
    """사용자 질문에 답합니다."""
    logger.info("[START] answer node start")
    question_agent = runtime.context["question_agent"]

    thread_id = f"{state["repo_id"]}:{state["pull_number"]}"

    github = runtime.context["github"]
    review = await github.get_reviews(
        owner=state["owner"],
        repo=state["repo"],
        pull_number=state["pull_number"],
        token=state["access_token"],
    )

    initial_message = HumanMessage(
        content=f"PR 리뷰 내용:\n\n{review}\n\n사용자 질문: {state["comment"]}"
    )

    result = await question_agent.ainvoke(
        {"messages": [initial_message]},
        config={"configurable": {"thread_id": thread_id}},
    )

    structured = result.get("structured_response")

    answer = (
        f"## Summary\n\n {structured.summary}\n\n ## Answer\n\n {structured.answer}\n\n"
    )

    return {"answer": answer}


async def post_answer_node(
    state: QuestionBotState, runtime: Runtime[QuestionBotContext]
):
    """사용자 질문에 대한 답을 게시합니다."""
    logger.info("[START] answer node")

    github = runtime.context["github"]

    await github.create_comment(
        owner=state["owner"],
        repo=state["repo"],
        pull_number=state["pull_number"],
        token=state["access_token"],
        event="COMMENT",
        body=state["answer"],
    )
