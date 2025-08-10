"""리뷰 결과 합성기"""

from selvage.src.models.review_result import ReviewResult
from selvage.src.utils.base_console import console
from selvage.src.utils.token.models import EstimatedCost, ReviewResponse


class ReviewSynthesizer:
    """여러 리뷰 결과를 LLM을 활용하여 지능적으로 합성하는 클래스"""

    def __init__(self, model_name: str) -> None:
        """
        Args:
            model_name: 사용할 모델명
        """
        self.model_name = model_name

    def synthesize_review_results(
        self, review_results: list[ReviewResult]
    ) -> ReviewResult:
        """
        여러 리뷰 결과를 합성하여 하나의 통합된 리뷰 결과를 생성

        Args:
            review_results: 합성할 리뷰 결과들

        Returns:
            ReviewResult: 합성된 최종 리뷰 결과
        """
        if not review_results:
            return ReviewResult.get_empty_result(self.model_name)

        # 성공한 결과들만 추출
        successful_results = [r for r in review_results if r.success]
        if not successful_results:
            return ReviewResult.get_empty_result(self.model_name)

        console.info("리뷰 결과 합성 시작")

        # 1. Issues는 단순 합산 (기존 방식 유지)
        all_issues = []
        for result in successful_results:
            all_issues.extend(result.review_response.issues)

        # 2. Summary와 Recommendations를 LLM으로 합성
        synthesized_summary, synthesized_recommendations = self._synthesize_with_llm(
            successful_results
        )

        # 3. 비용 합산
        total_cost = self._calculate_total_cost(successful_results)

        # 4. 최종 결과 생성
        synthesized_review_response = ReviewResponse(
            summary=synthesized_summary,
            recommendations=synthesized_recommendations,
            issues=all_issues,
            score=successful_results[
                0
            ].review_response.score,  # 첫 번째 결과의 점수 사용
        )

        console.info("리뷰 결과 합성 완료")
        return ReviewResult.get_success_result(
            review_response=synthesized_review_response, estimated_cost=total_cost
        )

    def _synthesize_with_llm(
        self, successful_results: list[ReviewResult]
    ) -> tuple[str, list[str]]:
        """
        LLM을 사용하여 Summary와 Recommendations를 합성

        Args:
            successful_results: 성공한 리뷰 결과들

        Returns:
            tuple[str, list[str]]: (합성된 summary, 합성된 recommendations)
        """
        console.info("LLM 기반 합성은 현재 fallback 방식을 사용합니다")
        return self._fallback_synthesis(successful_results)

    def _fallback_synthesis(
        self, successful_results: list[ReviewResult]
    ) -> tuple[str, list[str]]:
        """LLM 합성 실패 시 fallback으로 기존 방식 사용"""
        # Summary는 단순 결합
        summary_parts = []
        for result in successful_results:
            if result.review_response.summary:
                summary_parts.append(result.review_response.summary)

        # Recommendations는 단순 중복 제거
        all_recommendations = []
        for result in successful_results:
            all_recommendations.extend(result.review_response.recommendations)

        # 중복 제거 (순서 유지)
        unique_recommendations = []
        seen = set()
        for rec in all_recommendations:
            if rec not in seen:
                unique_recommendations.append(rec)
                seen.add(rec)

        return (
            "\n\n".join(summary_parts) if summary_parts else "",
            unique_recommendations,
        )

    def _calculate_total_cost(
        self, successful_results: list[ReviewResult]
    ) -> EstimatedCost:
        """비용 합산 계산"""
        total_cost = EstimatedCost.get_zero_cost(self.model_name)

        for result in successful_results:
            total_cost = EstimatedCost(
                model=result.estimated_cost.model,
                input_cost_usd=total_cost.input_cost_usd
                + result.estimated_cost.input_cost_usd,
                output_cost_usd=total_cost.output_cost_usd
                + result.estimated_cost.output_cost_usd,
                total_cost_usd=total_cost.total_cost_usd
                + result.estimated_cost.total_cost_usd,
                input_tokens=total_cost.input_tokens
                + result.estimated_cost.input_tokens,
                output_tokens=total_cost.output_tokens
                + result.estimated_cost.output_tokens,
            )

        return total_cost
