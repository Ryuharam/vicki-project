from typing import Literal

from app.schemas.state import ReviewBotState


def route_review(state: ReviewBotState) -> Literal["REVIEW", "SKIP"]:
    """state의 review_decision에 따라 분기하는 조건부 엣지"""

    return state["review_decision"]
