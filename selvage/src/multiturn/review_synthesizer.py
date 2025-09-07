"""리뷰 결과 합성기"""

from selvage.src.models.review_result import ReviewResult
from selvage.src.multiturn.synthesis_api_client import SynthesisAPIClient
from selvage.src.multiturn.synthesis_prompt_manager import SynthesisPromptManager
from selvage.src.utils.base_console import console
from selvage.src.utils.token.models import (
    EstimatedCost,
    ReviewResponse,
    SummarySynthesisResponse,
)


class SummarySynthesisResult:
    """Summary 합성 결과를 담는 클래스"""

    def __init__(self, summary: str | None, estimated_cost: EstimatedCost) -> None:
        self.summary = summary
        self.estimated_cost = estimated_cost


class ReviewSynthesizer:
    """여러 리뷰 결과를 합성하는 메인 조정자 클래스"""

    def __init__(self, model_name: str) -> None:
        """
        Args:
            model_name: 사용할 모델명
        """
        self.model_name = model_name
        self.api_client = SynthesisAPIClient(model_name)
        self.prompt_manager = SynthesisPromptManager()

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

        # 1. Issues는 단순 합산 (기존 방식 유지)
        all_issues = []
        for result in successful_results:
            all_issues.extend(result.review_response.issues)

        # 2. Summary LLM 합성
        synthesized_summary = None
        summary_synthesis_cost = None

        try:
            summary_result = self._synthesize_summary_with_llm(successful_results)
            if summary_result and summary_result.summary:
                synthesized_summary = summary_result.summary
                summary_synthesis_cost = summary_result.estimated_cost
            else:
                console.warning(
                    "Summary LLM synthesis failed. Processing with fallback."
                )
                synthesized_summary = self._fallback_summary(successful_results)
        except Exception as e:
            console.warning(
                f"Summary LLM synthesis failed: {e}. Processing with fallback."
            )
            synthesized_summary = self._fallback_summary(successful_results)

        # 3. Recommendations 합성 (단순 합산)
        synthesized_recommendations = self._combine_recommendations_simple(
            successful_results
        )

        # 4. 비용 합산 (기존 리뷰 비용 + 합성 비용)
        total_cost = self._calculate_total_cost(
            successful_results, summary_synthesis_cost, None
        )

        # 5. 최종 결과 생성
        synthesized_review_response = ReviewResponse(
            summary=synthesized_summary,
            recommendations=synthesized_recommendations,
            issues=all_issues,
            score=successful_results[
                0
            ].review_response.score,  # 첫 번째 결과의 점수 사용
        )

        return ReviewResult.get_success_result(
            review_response=synthesized_review_response, estimated_cost=total_cost
        )

    def _combine_recommendations_simple(
        self, successful_results: list[ReviewResult]
    ) -> list[str]:
        """권장사항 단순 합산 (overlap=0 환경에서 정보 보존 우선)"""
        all_recs = []
        for result in successful_results:
            all_recs.extend(result.review_response.recommendations)

        # 완전 동일한 권장사항만 제거 (단순하고 안전)
        unique_recs = list(dict.fromkeys(all_recs))
        return unique_recs

    def _synthesize_summary_with_llm(
        self, successful_results: list[ReviewResult]
    ) -> SummarySynthesisResult | None:
        """Summary만 LLM으로 합성"""
        try:
            # 1. Summary 데이터 추출
            summaries = [
                r.review_response.summary
                for r in successful_results
                if r.review_response.summary
            ]

            if not summaries:
                return None

            # 2. 합성 데이터 준비
            synthesis_data = {
                "task": "summary_synthesis",
                "summaries": summaries,
            }

            # 3. 프롬프트 가져오기
            system_prompt = self.prompt_manager.get_system_prompt_for_task(
                "summary_synthesis"
            )

            # 4. API 클라이언트를 통한 합성 호출
            structured_response, estimated_cost = self.api_client.execute_synthesis(
                synthesis_data, SummarySynthesisResponse, system_prompt
            )

            if structured_response is None:
                return SummarySynthesisResult(
                    summary=None,
                    estimated_cost=EstimatedCost.get_zero_cost(self.model_name),
                )

            return SummarySynthesisResult(
                summary=structured_response.summary, estimated_cost=estimated_cost
            )

        except Exception as e:
            console.error(f"Exception occurred during Summary LLM synthesis: {e}")
            raise e

    def _fallback_summary(self, successful_results: list[ReviewResult]) -> str:
        """fallback summary 생성 로직"""
        summaries = [
            r.review_response.summary
            for r in successful_results
            if r.review_response.summary
        ]

        if not summaries:
            return "리뷰 결과를 합성할 수 없습니다."
        elif len(summaries) == 1:
            return summaries[0]
        else:
            # 가장 긴 summary를 대표로 선택
            return max(summaries, key=len)

    def _calculate_total_cost(
        self,
        successful_results: list[ReviewResult],
        summary_synthesis_cost: EstimatedCost | None = None,
        recommendations_synthesis_cost: EstimatedCost | None = None,
    ) -> EstimatedCost:
        """비용 합산 계산 (기존 리뷰 비용 + 합성 비용)"""
        total_cost = EstimatedCost.get_zero_cost(self.model_name)

        # 기존 리뷰 결과들의 비용 합산
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

        # Summary 합성 비용 추가
        if summary_synthesis_cost:
            total_cost = EstimatedCost(
                model=total_cost.model,
                input_cost_usd=total_cost.input_cost_usd
                + summary_synthesis_cost.input_cost_usd,
                output_cost_usd=total_cost.output_cost_usd
                + summary_synthesis_cost.output_cost_usd,
                total_cost_usd=total_cost.total_cost_usd
                + summary_synthesis_cost.total_cost_usd,
                input_tokens=total_cost.input_tokens
                + summary_synthesis_cost.input_tokens,
                output_tokens=total_cost.output_tokens
                + summary_synthesis_cost.output_tokens,
            )

        # Recommendations 합성 비용 추가
        if recommendations_synthesis_cost:
            total_cost = EstimatedCost(
                model=total_cost.model,
                input_cost_usd=total_cost.input_cost_usd
                + recommendations_synthesis_cost.input_cost_usd,
                output_cost_usd=total_cost.output_cost_usd
                + recommendations_synthesis_cost.output_cost_usd,
                total_cost_usd=total_cost.total_cost_usd
                + recommendations_synthesis_cost.total_cost_usd,
                input_tokens=total_cost.input_tokens
                + recommendations_synthesis_cost.input_tokens,
                output_tokens=total_cost.output_tokens
                + recommendations_synthesis_cost.output_tokens,
            )

        return total_cost
