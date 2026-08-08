from typing import Literal

from app.schemas.state import ReviewBotState


def check_diff_is_exist(state: ReviewBotState) -> Literal["EXIST", "MISSING"]:
    """state의 has_diff에 따라 분기하는 조건부 엣지"""

    return state["has_diff"]


def route_review(state: ReviewBotState) -> Literal["REVIEW", "SKIP"]:
    """state의 review_decision에 따라 분기하는 조건부 엣지"""

    return state["review_decision"]
