from typing import Literal

from app.schemas.state import ReviewBotState


# TODO : 판단 기준 더 명확하게 수정
def route_review(state: ReviewBotState) -> Literal["review", "reject"]:
    """PR diff_summary를 확인하고 너무 짧으면 거절하는 조건부 엣지"""
    if len(state["diff_summary"]) < 500:
        return "reject"
    return "review"
