from pydantic import BaseModel

from selvage.src.utils.token.models import EstimatedCost, ReviewResponse


class ReviewResult(BaseModel):
    review_response: ReviewResponse
    estimated_cost: EstimatedCost

    @staticmethod
    def get_error_result(error: Exception, model: str = "unknown") -> "ReviewResult":
        return ReviewResult(
            review_response=ReviewResponse.get_error_response(error),
            estimated_cost=EstimatedCost.get_zero_cost(model),
        )

    @staticmethod
    def get_empty_result(model: str = "unknown") -> "ReviewResult":
        return ReviewResult(
            review_response=ReviewResponse.get_empty_response(),
            estimated_cost=EstimatedCost.get_zero_cost(model),
        )
