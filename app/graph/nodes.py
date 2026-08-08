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

logger = logging.getLogger(__name__)

CONVENTION_PATH = "./convention"


async def request_token_node(
    state: BaseState, runtime: Runtime[ReviewBotContext]
) -> dict:
    """payload의 installation 정보로 Github access token을 발급받습니다."""
    github = runtime.context["github"]

    payload = state["payload"]

    installation = payload.get("installation", {})
    if not installation:
        logger.error("[request_token] payload에 installation 정보가 없습니다.")
        return {}

    installation_id = installation.get("id")
    access_token = await github.request_access_token(installation_id=installation_id)

    return {"installation_id": installation_id, "access_token": access_token}


def review_preprocess_node(
    state: ReviewBotState, runtime: Runtime[ReviewBotContext]
) -> dict:
    """리뷰 흐름에서 Github API 호출에 쓰일 PR 정보를 payload에서 꺼내 state에 채웁니다."""
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
    """질문 흐름에서 Github API 호출에 쓰일 PR 정보와 질문 본문을 payload에서 꺼내 state에 채웁니다."""
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
    """PR의 diff 목록을 가져와 리뷰용 텍스트로 합칩니다. 컨벤션 문서 변경분은 제외합니다."""
    github = runtime.context["github"]

    diff_data = await github.get_pr_files(
        owner=state["owner"],
        repo=state["repo"],
        pull_number=state["pull_number"],
        token=state["access_token"],
    )

    diff_files = []
    for file in diff_data:
        if file.filename.startswith(".convention/"):
            logger.info(f"[request_diff] 컨벤션 문서라 제외: {file.filename}")
            continue
        diff_files.append(
            {"filename": file.filename, "status": file.status, "patch": file.patch}
        )

    if not diff_files:
        return {"diff_files": [], "has_diff": "MISSING"}

    return {"diff_files": diff_files, "has_diff": "EXIST"}


async def generate_no_diff_response_node(
    state: ReviewBotState, runtime: Runtime[ReviewBotContext]
):
    """check_diff_is_exist 조건부 엣지로 'MISSING' 분기한 결과 게시"""
    logger.info("[no diff] diff가 없어 리뷰 진행하지 않음을 게시")

    github = runtime.context["github"]

    await github.create_comment(
        owner=state["owner"],
        repo=state["repo"],
        pull_number=state["pull_number"],
        token=state["access_token"],
        body="변경된 파일이 없거나 컨벤션 문서만 변경되어 리뷰를 진행하지 않습니다.",
    )


async def router_node(state: ReviewBotState, runtime: Runtime[ReviewBotContext]):
    """경량 모델로 diff를 훑어 리뷰를 진행할지(REVIEW/SKIP) 판단합니다."""
    llm = runtime.context["lite_llm"]

    structured_llm = llm.with_structured_output(ReviewRouterItem, method="json_schema")

    system = SystemMessage(content=REVIEW_DECISION_PROMPT)
    human = HumanMessage(content=f"PR 내용 :\n\n{state["diff_files"]}")

    result = await structured_llm.ainvoke([system, human])

    logger.info(f"[router] 리뷰 판단: {result.review_decision}")

    return {
        "review_decision": result.review_decision,
        "reject_reason": result.skip_reason,
    }


async def post_skip_reason_node(
    state: ReviewBotState, runtime: Runtime[ReviewBotContext]
):
    """리뷰를 건너뛴 이유를 PR에 COMMENT로 게시합니다."""
    logger.info("[skip] 리뷰 생략 사유 게시")

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
    """main 브랜치의 `.convention` 디렉토리에서 컨벤션 문서를 읽어옵니다.

    문서가 없으면 has_convention=False로 두고 리뷰는 그대로 진행합니다.
    """
    github = runtime.context["github"]

    file_list = await github.get_convention_files(
        owner=state["owner"],
        repo=state["repo"],
        dirpath=".convention",
        token=state["access_token"],
    )

    if not file_list:
        logger.info("[request_convention] 컨벤션 문서 없이 리뷰를 진행합니다.")
        return {"has_convention": False, "conventions": "컨벤션 문서가 없습니다."}

    file_contents = []
    not_md_convention = False
    for file in file_list:
        content = await github.get_convention_file(
            owner=state["owner"],
            repo=state["repo"],
            filepath=file["filepath"],
            token=state["access_token"],
        )

        if file.get("name", "") and not file.get("name").endswith(".md"):
            logger.info(f"[request_convention] {file.get("name")} 이 .md 파일이 아님")
            not_md_convention = True

        file_contents.append({"filename": file.get("name"), "content": content})

    logger.info(f"[request_convention] 컨벤션 문서 {len(file_contents)}건 로드")

    return {
        "conventions": file_contents,
        "has_convention": True,
        "not_md_convention": not_md_convention,
    }


async def review_node(
    state: ReviewBotState, runtime: Runtime[ReviewBotContext]
) -> dict:
    """PR 내용, diff, 컨벤션 문서를 review agent에 넘겨 리뷰를 생성합니다."""
    logger.info("[review] 리뷰 생성 시작")

    review_agent = runtime.context["review_agent"]

    content = f"Pull request 내용과 Diff 내용, 컨벤션 문서 내용을 바탕으로 코드 리뷰 해줘.\n\n Pull request:\n - title: \n{state["pr_title"]}\n - body: \n{state["pr_body"]}\n\nPR Diff: \n{state["diff_files"]}\n\n Convention docs: \n{state["conventions"]}"

    result = await review_agent.ainvoke({"messages": [HumanMessage(content=content)]})

    return {"llm_result": result}


def parsing_output_node(
    state: ReviewBotState, runtime: Runtime[ReviewBotContext]
) -> dict:
    """llm이 생성한 리뷰를 PR에 게시할 최종 응답 형태로 바꿉니다.

    structured_response가 없으면 마지막 메시지를 그대로 COMMENT로 내보냅니다.
    """
    result = state["llm_result"]

    if "structured_response" in result:
        structured = result["structured_response"]

        if structured.verdict == "REQUEST_CHANGES":
            structured.summary += (
                "\n\n - ⚠️ severity가 **high**인 부분은 꼭 수정하시기 바랍니다!"
            )

        if state["not_md_convention"]:
            structured.summary += "\n - 참고 사항: 현재 컨벤션 분석 기능은 Markdown(.md) 파일만 지원하고 있습니다. 이에 따라 다른 형식의 컨벤션 문서는 이번 요약에 포함되지 않았습니다."

        if not state["has_convention"]:
            structured.summary += "\n - 참고 사항: main 브랜치 루트에 .convention 디렉토리의 컨벤션 파일이 감지되지 않았습니다. 이에 따라 별도의 컨벤션 문서 적용 없이 리뷰가 완료되었습니다."

        review = parsing_response(structured)

        return {"review_result": review, "verdict": structured.verdict}

    logger.warning("[parsing] structured_response가 없어 마지막 메시지를 사용합니다.")

    last_message = result["messages"][-1].content

    return {"review_result": last_message, "verdict": "COMMENT"}


def parsing_response(response: ReviewComments) -> str:
    """structured_response를 마크다운 형식의 리뷰 본문으로 변환합니다."""
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
                f"- source: {comment.source_filename}" "",
            ]
        )

    return "\n".join(lines)


async def post_review_node(state: ReviewBotState, runtime: Runtime[ReviewBotContext]):
    """생성된 리뷰를 verdict에 맞춰 PR review로 게시합니다."""
    logger.info(f"[post_review] 리뷰 게시: verdict={state['verdict']}")

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
    """답변 컨텍스트로 쓸 PR review 목록을 조회합니다."""
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
    """답변 컨텍스트로 쓸 PR comment 목록을 조회합니다."""
    github = runtime.context["github"]

    comments = await github.get_comments(
        owner=state["owner"],
        repo=state["repo"],
        pull_number=state["pull_number"],
        token=state["access_token"],
    )
    return {"comments": comments}


def context_builder_node(state: QuestionBotState) -> dict:
    """조회한 review/comment와 사용자 질문을 하나의 프롬프트 컨텍스트로 합칩니다."""
    reviews = state["reviews"]
    comments = state["comments"]

    context = f"PR review 내용과 전의 comment들의 내용을 참고하여 사용자 질문에 답하시오.\n사용자 질문: {state["question"]}\n\nPR 리뷰 내용들:\n{reviews}\n\nComments:\n{comments}"
    return {"context": context}


async def answer_node(
    state: QuestionBotState, runtime: Runtime[QuestionBotContext]
) -> dict:
    """question agent를 호출해 사용자 질문에 대한 답변을 생성합니다."""
    logger.info("[answer] 답변 생성 시작")

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
    """생성된 답변을 PR comment로 게시합니다."""
    logger.info("[post_answer] 답변 게시")

    github = runtime.context["github"]

    await github.create_comment(
        owner=state["owner"],
        repo=state["repo"],
        pull_number=state["pull_number"],
        token=state["access_token"],
        body=state["answer"],
    )
