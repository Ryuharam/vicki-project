import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.runtime import Runtime

from app.schemas.response import ReviewComments, ReviewRouterItem
from app.schemas.state import (
    BaseState,
    ReviewBotContext,
    ReviewBotState,
    QuestionBotState,
    QuestionBotContext,
)
from app.graph.prompts import REVIEW_DECISION_PROMPT

logger = logging.getLogger("uvicorn.error")

CONVENTION_PATH = "./convention"


async def request_token_node(
    state: BaseState, runtime: Runtime[ReviewBotContext]
) -> dict:
    """Github API를 호출하여 access-token을 발급받는 전처리 노드"""
    github = runtime.context["github"]

    payload = state["payload"]

    installation = payload.get("installation", {})
    if not installation:
        logger.error("Installaion information missing in payload")
        return {}

    installation_id = installation.get("id")
    access_token = await github.request_access_token(installation_id=installation_id)

    return {"installation_id": installation_id, "access_token": access_token}


def review_preprocess_node(
    state: ReviewBotState, runtime: Runtime[ReviewBotContext]
) -> dict:
    """추후 Github API를 호출할때 쓰이는 parameter 채우는 노드"""
    payload = state["payload"]

    repository = payload.get("repository", {})
    owner = repository.get("owner", {}).get("login")
    repo = repository.get("name")
    repo_id = repository.get("id")

    pull_request = payload.get("pull_request", {})
    pull_number = pull_request.get("number")
    pr_title = pull_request.get("title")
    pr_body = pull_request.get("body")

    return {
        "owner": owner,
        "repo": repo,
        "repo_id": repo_id,
        "pull_number": pull_number,
        "pr_title": pr_title,
        "pr_body": pr_body,
    }


def question_preprocess_node(
    state: QuestionBotState, runtime: Runtime[QuestionBotState]
) -> dict:
    payload = state["payload"]

    repository = payload.get("repository", {})
    owner = repository.get("owner", {}).get("login")
    repo = repository.get("name")
    repo_id = repository.get("id")

    issue = payload.get("issue", {})
    issue_number = issue.get("number", {})

    comment = payload.get("comment", {})
    question = comment.get("body", {})

    return {
        "owner": owner,
        "repo": repo,
        "repo_id": repo_id,
        "pull_number": issue_number,
        "question": question,
    }


async def request_diff_node(
    state: ReviewBotState, runtime: Runtime[ReviewBotContext]
) -> dict:
    """Github API를 호출하여 PR의 diff 목록을 가져오는 노드"""
    github = runtime.context["github"]

    diff_files = await github.get_pr_files(
        owner=state["owner"],
        repo=state["repo"],
        pull_number=state["pull_number"],
        token=state["access_token"],
    )

    diff_summary = "리뷰할 PR의 변경점(Diff) 목록입니다. :\n"
    for file in diff_files:
        if file.filename.startswith(".convention/"):
            logger.info(f"{file.filename} 은 컨벤션이라 제외")
            continue
        diff_summary += (
            f"\n파일명: {file.filename}\n\n{file.patch or "변경 내용 없음"}\n\n"
        )

    return {"diff_summary": diff_summary}


async def router_node(state: ReviewBotState, runtime: Runtime[ReviewBotContext]):
    logger.info("[START] router node 시작")
    llm = runtime.context["lite_llm"]

    structured_llm = llm.with_structured_output(ReviewRouterItem, method="json_schema")

    system = SystemMessage(content=REVIEW_DECISION_PROMPT)
    human = HumanMessage(content=f"PR 내용 :\n\n{state["diff_summary"]}")

    result = await structured_llm.ainvoke([system, human])

    return {
        "review_decision": result.review_decision,
        "reject_reason": result.skip_reason,
    }


async def post_skip_reason_node(
    state: ReviewBotState, runtime: Runtime[ReviewBotContext]
):
    """리뷰를 진행하지 않은 이유를 게시합니다."""
    github = runtime.context["github"]

    await github.create_review(
        owner=state["owner"],
        repo=state["repo"],
        pull_number=state["pull_number"],
        token=state["access_token"],
        event="COMMENT",
        body=state["reject_reason"],
    )


async def request_convention_node(
    state: ReviewBotState, runtime: Runtime[ReviewBotContext]
) -> dict:
    github = runtime.context["github"]

    file_list = await github.get_convention_files(
        owner=state["owner"],
        repo=state["repo"],
        dirpath=".convention",
        token=state["access_token"],
    )

    if not file_list:
        return {"has_convention": False, "conventions": "컨벤션 문서가 없습니다."}

    file_contents = []
    for file in file_list:
        content = await github.get_convention_file(
            owner=state["owner"],
            repo=state["repo"],
            filepath=file["filepath"],
            token=state["access_token"],
        )

        file_contents.append({"filename": file.get("name"), "content": content})

    return {"conventions": file_contents, "has_convention": True}


async def review_node(
    state: ReviewBotState, runtime: Runtime[ReviewBotContext]
) -> dict:
    """review agent를 이용하여 리뷰를 생성합니다."""
    review_agent = runtime.context["review_agent"]

    content = f"Pull request 내용과 Diff 내용, 컨벤션 문서 내용을 바탕으로 코드 리뷰 해줘.\n\n Pull request:\n - title: \n{state["pr_title"]}\n - body: \n{state["pr_body"]}\n\nPR Diff: \n{state["diff_summary"]}\n\n Convention docs: \n{state["conventions"]}"

    result = await review_agent.ainvoke({"messages": [HumanMessage(content=content)]})

    return {"llm_result": result}


def parsing_output_node(
    state: ReviewBotState, runtime: Runtime[ReviewBotContext]
) -> dict:
    """llm이 생성한 리뷰를 최종 응답 형태로 바꿉니다."""
    result = state["llm_result"]

    if "structured_response" in result:
        logger.info("structured_output 있음")

        structured = result["structured_response"]

        if structured.verdict == "REQUEST_CHANGES":
            structured.summary += (
                "\n\n⚠️ severity가 high인 부분은 꼭 수정하시기 바랍니다!"
            )

        if not state["has_convention"]:
            structured.summary += "\nmain 브랜치의 루트에 `.convetnion` 디렉토리가 없어 컨벤션 문서 없이 리뷰를 진행했습니다."

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


async def post_review_node(state: ReviewBotState, runtime: Runtime[ReviewBotContext]):
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


async def request_reviews_node(
    state: QuestionBotState, runtime: Runtime[QuestionBotContext]
) -> dict:
    github = runtime.context["github"]

    reviews = await github.get_reviews(
        owner=state["owner"],
        repo=state["repo"],
        pull_number=state["pull_number"],
        token=state["access_token"],
    )

    return {"reviews": reviews}


async def request_comments_node(
    state: QuestionBotState, runtime: Runtime[QuestionBotContext]
) -> dict:
    github = runtime.context["github"]

    comments = await github.get_comments(
        owner=state["owner"],
        repo=state["repo"],
        pull_number=state["pull_number"],
        token=state["access_token"],
    )
    return {"comments": comments}


def context_builder_node(state: QuestionBotState) -> dict:
    reviews = state["reviews"]
    comments = state["comments"]

    context = f"PR review 내용과 전의 comment들의 내용을 참고하여 사용자 질문에 답하시오.\n사용자 질문: {state["question"]}\n\nPR 리뷰 내용들:\n{reviews}\n\nComments:\n{comments}"
    return {"context": context}


async def answer_node(
    state: QuestionBotState, runtime: Runtime[QuestionBotContext]
) -> dict:
    question_agent = runtime.context["question_agent"]
    content = state["context"]
    result = await question_agent.ainvoke({"messages": [HumanMessage(content=content)]})
    structured = result.get("structured_response")

    answer = (
        f"## Summary\n\n {structured.summary}\n\n ## Answer\n\n {structured.answer}\n\n"
    )
    return {"answer": answer}


async def post_answer_node(
    state: QuestionBotState, runtime: Runtime[QuestionBotContext]
):
    github = runtime.context["github"]

    await github.create_comment(
        owner=state["owner"],
        repo=state["repo"],
        pull_number=state["pull_number"],
        token=state["access_token"],
        body=state["answer"],
    )
