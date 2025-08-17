from pydantic import BaseModel

from selvage.src.models.error_response import ErrorResponse
from selvage.src.utils.token.models import EstimatedCost, ReviewResponse


class ReviewResult(BaseModel):
    review_response: ReviewResponse
    estimated_cost: EstimatedCost
    success: bool = True
    """리뷰 성공 여부. 기본값 True로 기존 호환성 유지"""

    error_response: ErrorResponse | None = None
    """에러 발생 시 구조화된 에러 정보"""

    @staticmethod
    def get_success_result(
        review_response: ReviewResponse, estimated_cost: EstimatedCost
    ) -> "ReviewResult":
        """성공적인 리뷰 결과를 생성합니다.

        Args:
            review_response: 리뷰 응답
            estimated_cost: 예상 비용

        Returns:
            ReviewResult: 성공 상태의 리뷰 결과
        """
        return ReviewResult(
            review_response=review_response, estimated_cost=estimated_cost, success=True
        )

    @staticmethod
    def get_error_result(
        error: Exception, model: str = "unknown", provider: str = "unknown"
    ) -> "ReviewResult":
        """에러 발생 시 리뷰 결과를 생성합니다.

        Args:
            error: 발생한 예외
            model: 모델 이름
            provider: Provider 이름

        Returns:
            ReviewResult: 실패 상태의 리뷰 결과
        """
        return ReviewResult(
            review_response=ReviewResponse.get_empty_response(),
            estimated_cost=EstimatedCost.get_zero_cost(model),
            success=False,
            error_response=ErrorResponse.from_exception(error, provider),
        )

    @staticmethod
    def get_empty_result(model: str = "unknown") -> "ReviewResult":
        """빈 리뷰 결과를 생성합니다.

        Args:
            model: 모델 이름

        Returns:
            ReviewResult: 빈 상태의 리뷰 결과
        """
        return ReviewResult(
            review_response=ReviewResponse.get_empty_response(),
            estimated_cost=EstimatedCost.get_zero_cost(model),
            success=True,
        )

    def is_context_limit_error(self) -> bool:
        """Context limit 에러인지 확인합니다.

        Returns:
            bool: Context limit 에러 여부
        """
        return (
            not self.success
            and self.error_response is not None
            and self.error_response.is_context_limit_error()
        )

    def should_retry_with_multiturn(self) -> bool:
        """Multiturn 리뷰로 재시도할 수 있는지 확인합니다.

        Returns:
            bool: Multiturn 재시도 가능 여부
        """
        return (
            not self.success
            and self.error_response is not None
            and self.error_response.should_retry_with_multiturn()
        )
