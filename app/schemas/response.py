# API 응답 형식 데이터 검증 (Pydantic)
from typing import Optional, Literal, ClassVar
from pydantic import BaseModel, Field


class GitHubFileItem(BaseModel):
    """PR 변경 파일 목록 API의 개별 파일 항목 모델"""

    sha: str
    filename: str = Field(description="변경된 파일의 이름")
    status: str = Field(description="변경 유형 added, modified, deleted 등")
    additions: int
    deletions: int
    changes: int
    patch: Optional[str] = Field(None, description="변경된 코드의 Diff 내용")
    raw_url: str


class ReviewCommentItem(BaseModel):
    title: str = Field(
        description="한 줄로 요약한 리뷰 제목. 예: '네이밍 규칙 위반', 'SRP 위반', '파일 리소스 관리'"
    )
    severity: Literal["high", "medium", "low"] = Field(
        description="리뷰의 중요도. "
        "high=기능 오류·버그·보안 문제, "
        "medium=설계·성능·유지보수성 문제, "
        "low=컨벤션·스타일 개선 사항."
    )

    _SEVERITY_ORDER: ClassVar[dict] = {"high": 1, "medium": 2, "low": 3}

    def __lt__(self, other: "ReviewCommentItem") -> bool:
        self_order = self._SEVERITY_ORDER.get(self.severity, 99)
        other_order = self._SEVERITY_ORDER.get(other.severity, 99)
        return self_order < other_order

    category: Literal["design", "convention", "performance", "bug", "security"] = Field(
        description="리뷰의 분류. 가장 적합한 하나만 선택한다."
    )
    issue: str = Field(
        description="문제가 되는 코드와 이유를 설명한다. "
        "구체적으로 무엇이 문제인지 작성하고, 같은 내용을 반복하지 않는다."
    )
    suggestion: str = Field(
        description="문제를 해결하기 위한 구체적인 개선 방법을 작성한다. "
        "실행 가능한 제안을 작성하며, 추상적인 표현은 피한다."
    )


class ReviewComments(BaseModel):
    """pull request에 대한 최종 comment"""

    summary: str = Field(
        description="PR 전체를 2~3문장으로 요약한다. "
        "전반적인 코드 품질과 주요 개선 사항을 간결하게 설명한다."
    )
    comments: list[ReviewCommentItem] = Field(
        description="발견한 리뷰 목록이다. "
        "중복된 리뷰는 하나로 합치고, 중요도가 높은 순서대로 정렬한다."
    )
