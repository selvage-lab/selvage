"""ReviewSynthesizer 테스트"""

from unittest.mock import Mock

import pytest

from selvage.src.models.review_result import ReviewResult
from selvage.src.multiturn.review_synthesizer import ReviewSynthesizer
from selvage.src.utils.token.models import EstimatedCost, ReviewResponse, ReviewIssue


class TestReviewSynthesizer:
    """ReviewSynthesizer 클래스 테스트"""

    @pytest.fixture
    def mock_llm_gateway(self) -> Mock:
        """Mock BaseGateway 생성"""
        gateway = Mock()
        gateway.get_model_name.return_value = "test-model"
        gateway.get_provider.return_value = Mock(value="test-provider")
        
        # 합성 요청에 대한 성공적인 응답 설정
        gateway.review_code.return_value = ReviewResult.get_success_result(
            review_response=ReviewResponse(
                summary="통합된 요약: 코드 품질이 전반적으로 향상되었습니다.",
                recommendations=[
                    "중복 코드를 제거하세요",
                    "에러 처리를 개선하세요",
                    "테스트 커버리지를 늘리세요"
                ],
                issues=[],
            ),
            estimated_cost=EstimatedCost.get_zero_cost("test-model"),
        )
        
        return gateway

    @pytest.fixture
    def sample_review_results(self) -> list[ReviewResult]:
        """테스트용 ReviewResult 리스트 생성"""
        results = []
        
        # 첫 번째 청크 결과
        result1 = ReviewResult.get_success_result(
            review_response=ReviewResponse(
                summary="첫 번째 청크 요약: 새로운 함수가 추가되었습니다.",
                recommendations=[
                    "함수명을 더 명확하게 변경하세요",
                    "에러 처리를 추가하세요"
                ],
                issues=[
                    ReviewIssue(
                        type="style",
                        line_number=10,
                        file="test1.py",
                        description="함수명 컨벤션",
                        severity="info"
                    )
                ],
            ),
            estimated_cost=EstimatedCost(
                model="test-model",
                input_tokens=1000,
                input_cost_usd=0.01,
                output_tokens=200,
                output_cost_usd=0.02,
                total_cost_usd=0.03
            ),
        )
        
        # 두 번째 청크 결과
        result2 = ReviewResult.get_success_result(
            review_response=ReviewResponse(
                summary="두 번째 청크 요약: 기존 로직이 개선되었습니다.",
                recommendations=[
                    "에러 처리를 추가하세요",  # 중복
                    "주석을 더 상세하게 작성하세요"
                ],
                issues=[
                    ReviewIssue(
                        type="bug",
                        line_number=25,
                        file="test2.py",
                        description="잠재적 null pointer 오류",
                        severity="warning"
                    )
                ],
            ),
            estimated_cost=EstimatedCost(
                model="test-model",
                input_tokens=800,
                input_cost_usd=0.008,
                output_tokens=150,
                output_cost_usd=0.015,
                total_cost_usd=0.023
            ),
        )
        
        results.extend([result1, result2])
        return results

    @pytest.fixture
    def review_synthesizer(self, mock_llm_gateway: Mock) -> ReviewSynthesizer:
        """ReviewSynthesizer 인스턴스 생성"""
        return ReviewSynthesizer(mock_llm_gateway.get_model_name())

    def test_synthesize_review_results_success(
        self,
        review_synthesizer: ReviewSynthesizer,
        sample_review_results: list[ReviewResult],
        mock_llm_gateway: Mock,
    ) -> None:
        """성공적인 리뷰 결과 합성 테스트"""
        # When: 리뷰 결과 합성
        result = review_synthesizer.synthesize_review_results(sample_review_results)

        # Then: 합성된 결과 반환
        assert result.success is True
        assert result.review_response.summary is not None
        assert len(result.review_response.recommendations) > 0
        
        # Issues는 모든 청크의 이슈가 포함되어야 함
        assert len(result.review_response.issues) == 2
        
        # 모델명이 일치해야 함
        assert result.estimated_cost.model == "test-model"
        
        # 비용이 합산되어야 함
        assert result.estimated_cost.input_tokens == 1800  # 1000 + 800
        assert result.estimated_cost.total_cost_usd == 0.053  # 0.03 + 0.023
        
        # 현재는 fallback 방식을 사용하므로 LLM 호출 없음
        assert mock_llm_gateway.review_code.call_count == 0

    def test_synthesize_empty_results(
        self,
        review_synthesizer: ReviewSynthesizer,
        mock_llm_gateway: Mock,
    ) -> None:
        """빈 리뷰 결과 리스트 처리 테스트"""
        # When: 빈 리스트로 합성
        result = review_synthesizer.synthesize_review_results([])

        # Then: 빈 결과 반환
        assert result.success is True
        assert result.estimated_cost.model == "test-model"
        
        # LLM이 호출되지 않아야 함
        assert mock_llm_gateway.review_code.call_count == 0

    def test_synthesize_failed_results_only(
        self,
        review_synthesizer: ReviewSynthesizer,
        mock_llm_gateway: Mock,
    ) -> None:
        """실패한 결과들만 있을 때 테스트"""
        # Given: 실패한 결과들
        failed_results = [
            ReviewResult.get_error_result(
                error=Exception("Test error"),
                model="test-model",
                provider="test-provider"
            )
        ]

        # When: 실패한 결과들로 합성
        result = review_synthesizer.synthesize_review_results(failed_results)

        # Then: 빈 결과 반환
        assert result.success is True
        assert result.estimated_cost.model == "test-model"
        
        # LLM이 호출되지 않아야 함
        assert mock_llm_gateway.review_code.call_count == 0

    def test_synthesize_with_fallback_deduplication(
        self,
        sample_review_results: list[ReviewResult],
        mock_llm_gateway: Mock,
    ) -> None:
        """Fallback 방식의 중복 제거 테스트"""
        # Given: ReviewSynthesizer 인스턴스
        synthesizer = ReviewSynthesizer(mock_llm_gateway.get_model_name())

        # When: 합성 실행
        result = synthesizer.synthesize_review_results(sample_review_results)

        # Then: fallback으로 기본 합성 실행되어야 함
        assert result.success is True
        assert result.review_response.summary is not None
        assert len(result.review_response.recommendations) > 0
        
        # 중복 제거가 되어야 함 (fallback의 특징)
        unique_recommendations = set(result.review_response.recommendations)
        assert "에러 처리를 추가하세요" in unique_recommendations
        
        # 중복 제거로 인해 실제 권장사항 개수가 4개보다 적어야 함
        # (원본: [함수명 변경, 에러 처리, 에러 처리 중복, 주석 작성] = 4개 → 3개로 중복 제거)
        assert len(result.review_response.recommendations) == 3

    def test_model_name_consistency(
        self,
        review_synthesizer: ReviewSynthesizer,
        sample_review_results: list[ReviewResult],
        mock_llm_gateway: Mock,
    ) -> None:
        """모델명 일관성 테스트"""
        # When: 합성 실행
        result = review_synthesizer.synthesize_review_results(sample_review_results)

        # Then: 모델명이 gateway의 모델명과 일치해야 함
        assert result.estimated_cost.model == mock_llm_gateway.get_model_name()
        assert result.estimated_cost.model == "test-model"

    def test_cost_calculation(
        self,
        review_synthesizer: ReviewSynthesizer,
        sample_review_results: list[ReviewResult],
        mock_llm_gateway: Mock,
    ) -> None:
        """비용 계산 정확성 테스트"""
        # When: 합성 실행
        result = review_synthesizer.synthesize_review_results(sample_review_results)

        # Then: 비용이 정확히 합산되어야 함
        expected_input_tokens = 1000 + 800  # 각 result의 input_tokens 합
        expected_total_cost = 0.03 + 0.023  # 각 result의 total_cost_usd 합
        
        assert result.estimated_cost.input_tokens == expected_input_tokens
        assert abs(result.estimated_cost.total_cost_usd - expected_total_cost) < 0.001