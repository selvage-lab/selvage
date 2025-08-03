from enum import Enum

from pydantic import BaseModel, Field

from selvage.src.diff_parser.models.diff_result import DiffResult
from selvage.src.utils.base_console import console


# Structured Outputs용 스키마 클래스 (기본값 없음)
class IssueSeverityEnum(str, Enum):
    """이슈 심각도 열거형"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class StructuredReviewIssue(BaseModel):
    """Structured Outputs용 코드 리뷰 이슈 모델"""

    type: str
    line_number: int | None
    file: str | None
    description: str
    suggestion: str | None
    severity: IssueSeverityEnum
    target_code: str | None  # 리뷰 대상 코드
    suggested_code: str | None  # 개선된 코드


class StructuredReviewResponse(BaseModel):
    """Structured Outputs용 코드 리뷰 응답 모델"""

    issues: list[StructuredReviewIssue]
    summary: str
    score: float | None
    recommendations: list[str]


class ReviewRequest(BaseModel):
    """코드 리뷰 요청 모델"""

    diff_content: str
    processed_diff: DiffResult
    file_paths: list[str] = Field(default_factory=list)
    model: str
    repo_path: str = "."

    def is_include_entirely_new_content(self) -> bool:
        """전체 새로운 내용을 포함하는 파일이 있는지 확인합니다."""
        return self.processed_diff.is_include_entirely_new_content()


class ReviewIssue(BaseModel):
    """코드 리뷰 이슈 모델"""

    type: str
    line_number: int | None = None
    file: str | None = None
    description: str
    suggestion: str | None = None
    severity: str = "info"  # info, warning, error
    target_code: str | None = None  # 리뷰 대상 코드
    suggested_code: str | None = None  # 개선된 코드

    @staticmethod
    def from_structured_issue(
        issue: StructuredReviewIssue, index: int = 0
    ) -> "ReviewIssue":
        """구조화된 이슈 객체에서 ReviewIssue 인스턴스를 생성합니다.

        Args:
            issue: 구조화된 이슈 객체
            index: 디버깅을 위한 이슈 인덱스

        Returns:
            ReviewIssue: 변환된 이슈 객체

        Raises:
            Exception: 변환 중 오류 발생 시
        """
        try:
            # severity 처리 (모든 게이트웨이에서 동일하게 처리)
            severity_value = issue.severity.value

            return ReviewIssue(
                type=issue.type,
                line_number=issue.line_number,
                file=issue.file,
                description=issue.description,
                suggestion=issue.suggestion,
                severity=severity_value,
                target_code=issue.target_code,
                suggested_code=issue.suggested_code,
            )
        except Exception as e:
            console.error(f"이슈 #{index + 1} 변환 중 오류: {str(e)}", exception=e)
            raise


class ReviewResponse(BaseModel):
    """코드 리뷰 응답 모델"""

    issues: list[ReviewIssue] = Field(default_factory=list)
    summary: str
    score: float | None = None
    recommendations: list[str] = Field(default_factory=list)

    @staticmethod
    def from_structured_response(
        structured_response: StructuredReviewResponse,
    ) -> "ReviewResponse":
        """구조화된 응답 객체에서 ReviewResponse 인스턴스를 생성합니다.

        Args:
            structured_response: 구조화된 응답 객체

        Returns:
            ReviewResponse: 변환된 응답 객체
        """
        issues = []

        # 이슈 변환
        for i, issue in enumerate(structured_response.issues):
            try:
                issues.append(ReviewIssue.from_structured_issue(issue, i))
            except (ValueError, TypeError, AttributeError):
                # 개별 이슈 변환 실패는 무시하고 계속 진행
                continue

        # 옵셔널 필드 안전하게 처리
        return ReviewResponse(
            issues=issues,
            summary=structured_response.summary,
            score=structured_response.score,
            recommendations=structured_response.recommendations,
        )

    @staticmethod
    def get_empty_response() -> "ReviewResponse":
        """비어있는 응답 객체를 생성합니다.

        Returns:
            ReviewResponse: 에러 메시지가 포함된 빈 리뷰 응답
        """
        console.warning("응답이 비어있습니다")
        return ReviewResponse(
            issues=[],
            summary="LLM 응답이 비어있거나 불완전합니다.",
            recommendations=["다른 프롬프트나 모델을 사용해보세요."],
        )

    @staticmethod
    def get_error_response(error: Exception) -> "ReviewResponse":
        """API 오류에 대한 응답 객체를 생성합니다.

        Args:
            error: 발생한 예외

        Returns:
            ReviewResponse: 에러 정보가 포함된 리뷰 응답

        Raises:
            Exception: 요청 또는 네트워크 오류인 경우 재발생
        """

        import requests

        console.error(f"API 처리 중 오류 발생: {str(error)}", exception=error)

        # 요청 또는 네트워크 오류인 경우
        if isinstance(error, requests.RequestException):
            raise Exception(f"API 호출 중 오류 발생: {str(error)}") from error

        # 기타 예외 처리 (토큰 제한, 파싱 오류 등)
        return ReviewResponse(
            issues=[],
            summary=f"LLM API 처리 중 오류 발생: {str(error)}",
            recommendations=["요청 내용을 줄이거나 다른 모델을 사용해보세요."],
        )


class EstimatedCost(BaseModel):
    """API 응답의 usage 정보를 이용한 비용 추정 결과 모델"""

    model: str
    input_tokens: int
    input_cost_usd: float
    output_tokens: int
    output_cost_usd: float
    total_cost_usd: float
    within_context_limit: bool = (
        True  # API 응답이 성공했다면 컨텍스트 제한 내에서 처리된 것으로 간주
    )

    @staticmethod
    def get_zero_cost(model: str) -> "EstimatedCost":
        return EstimatedCost(
            model=model,
            input_tokens=0,
            input_cost_usd=0,
            output_tokens=0,
            output_cost_usd=0,
            total_cost_usd=0,
        )
