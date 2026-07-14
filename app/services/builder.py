from langgraph.graph import StateGraph, START, END

from app.schemas.state import ReviewBotState, ReviewBotContext
from app.services.nodes import preprocess_node, comment_node, review_node


def build_graph():
    builder = StateGraph(state_schema=ReviewBotState, context_schema=ReviewBotContext)

    builder.add_node("preprocess", preprocess_node)
    builder.add_node("review", review_node)
    builder.add_node("comment", comment_node)

    builder.add_edge(START, "preprocess")
    builder.add_edge("preprocess", "review")
    builder.add_edge("review", "comment")
    builder.add_edge("comment", END)

    return builder.compile()
