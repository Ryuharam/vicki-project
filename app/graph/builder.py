from langgraph.graph import StateGraph, START, END

from app.schemas.state import (
    ReviewBotState,
    ReviewBotContext,
    QuestionBotState,
    QuestionBotContext,
)
from app.graph.nodes import (
    request_token_node,
    review_preprocess_node,
    question_preprocess_node,
    request_diff_node,
    generate_no_diff_response_node,
    router_node,
    post_skip_reason_node,
    request_convention_node,
    review_node,
    parsing_output_node,
    post_review_node,
    request_reviews_node,
    request_comments_node,
    context_builder_node,
    answer_node,
    post_answer_node,
)
from app.graph.edges import route_review, check_diff_is_exist


def build_review_graph():
    """PR 리뷰 그래프를 조립해 컴파일합니다.

    토큰 발급 → 전처리 → diff 조회 → 리뷰 여부 판단 순으로 진행하고,
    판단 결과에 따라 생략 사유 게시(SKIP) 또는 컨벤션 조회 후 리뷰(REVIEW)로 분기합니다.
    """
    builder = StateGraph(state_schema=ReviewBotState, context_schema=ReviewBotContext)

    builder.add_node("request_token", request_token_node)
    builder.add_node("preprocess", review_preprocess_node)
    builder.add_node("request_diff", request_diff_node)
    builder.add_node("no_diff", generate_no_diff_response_node)
    builder.add_node("router", router_node)
    builder.add_node("skip", post_skip_reason_node)
    builder.add_node("request_convention", request_convention_node)
    builder.add_node("review", review_node)
    builder.add_node("parsing", parsing_output_node)
    builder.add_node("post_review", post_review_node)

    builder.add_edge(START, "request_token")
    builder.add_edge("request_token", "preprocess")
    builder.add_edge("preprocess", "request_diff")
    builder.add_conditional_edges(
        "request_diff",
        check_diff_is_exist,
        {"EXIST": "router", "MISSING": "no_diff"},
    )
    builder.add_conditional_edges(
        "router", route_review, {"SKIP": "skip", "REVIEW": "request_convention"}
    )
    builder.add_edge("skip", END)
    builder.add_edge("request_convention", "review")
    builder.add_edge("review", "parsing")
    builder.add_edge("parsing", "post_review")
    builder.add_edge("post_review", END)

    return builder.compile()


def build_question_graph():
    """`/prism` 질문 응답 그래프를 조립해 컴파일합니다.

    토큰 발급 → 전처리 후 review/comment 조회를 병렬로 수행하고,
    둘을 합친 컨텍스트로 답변을 생성해 PR에 게시합니다.
    """
    builder = StateGraph(
        state_schema=QuestionBotState, context_schema=QuestionBotContext
    )

    builder.add_node("request_token", request_token_node)
    builder.add_node("preprocess", question_preprocess_node)
    builder.add_node("request_reviews", request_reviews_node)
    builder.add_node("request_comments", request_comments_node)
    builder.add_node("context_build", context_builder_node)
    builder.add_node("answer", answer_node)
    builder.add_node("post_answer", post_answer_node)

    builder.add_edge(START, "request_token")
    builder.add_edge("request_token", "preprocess")
    builder.add_edge("preprocess", "request_reviews")
    builder.add_edge("preprocess", "request_comments")
    builder.add_edge("request_reviews", "context_build")
    builder.add_edge("request_comments", "context_build")
    builder.add_edge("context_build", "answer")
    builder.add_edge("answer", "post_answer")
    builder.add_edge("post_answer", END)

    return builder.compile()
