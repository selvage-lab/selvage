"""ReviewSynthesizer 실제 LLM API 통합 테스트"""

import json
from pathlib import Path
from typing import Any

import pytest

from selvage.src.config import get_api_key
from selvage.src.models.model_provider import ModelProvider
from selvage.src.models.review_result import ReviewResult
from selvage.src.multiturn.review_synthesizer import ReviewSynthesizer
from selvage.src.utils.token.models import EstimatedCost, ReviewIssue, ReviewResponse


def has_api_key(provider: ModelProvider) -> bool:
    """API 키가 설정되어 있는지 확인"""
    try:
        api_key = get_api_key(provider)
        return bool(api_key and api_key.strip())
    except Exception:
        return False


def has_any_api_key() -> bool:
    """최소 하나의 API 키라도 설정되어 있는지 확인"""
    return any(has_api_key(provider) for provider in ModelProvider)


@pytest.mark.integration
class TestReviewSynthesizerRealIntegration:
    """ReviewSynthesizer 실제 LLM API 통합 테스트"""

    @pytest.fixture
    def sample_multiturn_data(self) -> dict[str, Any]:
        """실제 multiturn 결과 데이터 로드"""
        test_data_path = (
            Path(__file__).parent.parent / "data" / "sample_multiturn_results.json"
        )
        with test_data_path.open(encoding="utf-8") as f:
            return json.load(f)

    @pytest.fixture
    def complex_multiturn_data(self) -> dict[str, Any]:
        """복잡한 multiturn 결과 데이터 로드 (더 많은 이슈와 권장사항 포함)"""
        test_data_path = (
            Path(__file__).parent.parent / "data" / "complex_multiturn_results.json"
        )
        with test_data_path.open(encoding="utf-8") as f:
            return json.load(f)

    @pytest.fixture
    def integration_review_results(
        self, sample_multiturn_data: dict[str, Any]
    ) -> list[ReviewResult]:
        """실제 multiturn 데이터 기반 ReviewResult 리스트 생성 (성공한 것만)"""
        results = []

        for chunk_data in sample_multiturn_data["chunks"]:
            if chunk_data["success"]:
                # 성공한 청크만 ReviewResult로 변환
                issues = []
                if chunk_data["review_response"].get("issues"):
                    for issue_data in chunk_data["review_response"]["issues"]:
                        issues.append(
                            ReviewIssue(
                                type=issue_data["type"],
                                line_number=issue_data.get("line_number"),
                                file=issue_data["file"],
                                description=issue_data["description"],
                                severity=issue_data["severity"],
                                suggestion=issue_data.get("suggestion"),
                            )
                        )

                review_response = ReviewResponse(
                    summary=chunk_data["review_response"]["summary"],
                    recommendations=chunk_data["review_response"]["recommendations"],
                    issues=issues,
                    score=chunk_data["review_response"].get("score"),
                )

                estimated_cost = EstimatedCost(
                    model=chunk_data["estimated_cost"]["model"],
                    input_tokens=chunk_data["estimated_cost"]["input_tokens"],
                    input_cost_usd=chunk_data["estimated_cost"]["input_cost_usd"],
                    output_tokens=chunk_data["estimated_cost"]["output_tokens"],
                    output_cost_usd=chunk_data["estimated_cost"]["output_cost_usd"],
                    total_cost_usd=chunk_data["estimated_cost"]["total_cost_usd"],
                )

                result = ReviewResult.get_success_result(
                    review_response=review_response, estimated_cost=estimated_cost
                )
                results.append(result)

        return results

    @pytest.fixture
    def complex_integration_review_results(
        self, complex_multiturn_data: dict[str, Any]
    ) -> list[ReviewResult]:
        """복잡한 multiturn 데이터 기반 ReviewResult 리스트 생성"""
        results = []

        for chunk_data in complex_multiturn_data["chunks"]:
            if chunk_data["success"]:
                # 성공한 청크만 ReviewResult로 변환
                issues = []
                if chunk_data["review_response"].get("issues"):
                    for issue_data in chunk_data["review_response"]["issues"]:
                        issues.append(
                            ReviewIssue(
                                type=issue_data["type"],
                                line_number=issue_data.get("line_number"),
                                file=issue_data["file"],
                                description=issue_data["description"],
                                severity=issue_data["severity"],
                                suggestion=issue_data.get("suggestion"),
                            )
                        )

                review_response = ReviewResponse(
                    summary=chunk_data["review_response"]["summary"],
                    recommendations=chunk_data["review_response"]["recommendations"],
                    issues=issues,
                    score=chunk_data["review_response"].get("score"),
                )

                estimated_cost = EstimatedCost(
                    model=chunk_data["estimated_cost"]["model"],
                    input_tokens=chunk_data["estimated_cost"]["input_tokens"],
                    input_cost_usd=chunk_data["estimated_cost"]["input_cost_usd"],
                    output_tokens=chunk_data["estimated_cost"]["output_tokens"],
                    output_cost_usd=chunk_data["estimated_cost"]["output_cost_usd"],
                    total_cost_usd=chunk_data["estimated_cost"]["total_cost_usd"],
                )

                result = ReviewResult.get_success_result(
                    review_response=review_response, estimated_cost=estimated_cost
                )
                results.append(result)

        return results

    @pytest.mark.skipif(
        not has_api_key(ModelProvider.OPENAI), reason="OpenAI API key not available"
    )
    def test_real_openai_integration(
        self, integration_review_results: list[ReviewResult]
    ) -> None:
        """실제 OpenAI API를 호출하는 통합 테스트"""
        # Given: 실제 OpenAI 환경
        synthesizer = ReviewSynthesizer("gpt-4o-mini")  # 더 저렴한 모델 사용

        # When: 실제 API 호출하여 합성
        result = synthesizer.synthesize_review_results(integration_review_results)

        # Then: 실제 LLM 응답 검증
        assert result.success is True
        assert result.review_response.summary is not None
        assert len(result.review_response.summary) > 20  # 의미 있는 요약
        assert len(result.review_response.recommendations) > 0

        # LLM이 생성한 내용 품질 검증
        summary_lower = result.review_response.summary.lower()
        assert any(
            keyword in summary_lower for keyword in ["code", "review", "ktor", "kotlin"]
        )

        # 비용이 실제로 발생했는지 확인
        assert result.estimated_cost.total_cost_usd > 0
        assert result.estimated_cost.input_tokens > 0
        assert result.estimated_cost.output_tokens > 0

    @pytest.mark.skipif(
        not has_api_key(ModelProvider.ANTHROPIC),
        reason="Anthropic API key not available",
    )
    def test_real_anthropic_integration(
        self, integration_review_results: list[ReviewResult]
    ) -> None:
        """실제 Anthropic API를 호출하는 통합 테스트"""
        # Given: 실제 Anthropic 환경
        synthesizer = ReviewSynthesizer("claude-sonnet-4")

        # When: 실제 API 호출하여 합성
        result = synthesizer.synthesize_review_results(integration_review_results)

        # Then: 실제 LLM 응답 검증
        assert result.success is True
        assert result.review_response.summary is not None
        assert len(result.review_response.summary) > 20
        assert len(result.review_response.recommendations) > 0

        # Claude 응답 품질 확인 (실제 응답 내용이 의미 있는지)
        summary_lower = result.review_response.summary.lower()
        assert any(
            keyword in summary_lower
            for keyword in [
                "code",
                "review",
                "implementation",
                "ktor",
                "kotlin",
                "api",
                "klib",
                "파일",
                "모듈",
            ]
        )

        # 실제 응답이 fallback이 아닌 LLM 생성인지 확인 (fallback과 다른 패턴)
        assert result.review_response.summary != "리뷰 결과를 합성할 수 없습니다."

    @pytest.mark.skipif(
        not has_api_key(ModelProvider.GOOGLE), reason="Google API key not available"
    )
    def test_real_google_integration(
        self, integration_review_results: list[ReviewResult]
    ) -> None:
        """실제 Google Gemini API를 호출하는 통합 테스트"""
        # Given: 실제 Google 환경
        synthesizer = ReviewSynthesizer("gemini-2.5-flash")  # 더 저렴한 모델 사용

        # When: 실제 API 호출하여 합성
        result = synthesizer.synthesize_review_results(integration_review_results)

        # Then: 실제 LLM 응답 검증
        assert result.success is True
        assert result.review_response.summary is not None
        assert len(result.review_response.summary) > 20
        assert len(result.review_response.recommendations) > 0

    @pytest.mark.skipif(
        not has_api_key(ModelProvider.OPENROUTER),
        reason="OpenRouter API key not available",
    )
    def test_real_openrouter_integration(
        self, integration_review_results: list[ReviewResult]
    ) -> None:
        """실제 OpenRouter API를 호출하는 통합 테스트"""
        # Given: 실제 OpenRouter 환경 (저렴한 모델 사용)
        synthesizer = ReviewSynthesizer("qwen3-coder")

        # When: 실제 API 호출하여 합성
        result = synthesizer.synthesize_review_results(integration_review_results)

        # Then: 실제 LLM 응답 검증
        assert result.success is True
        assert result.review_response.summary is not None
        assert len(result.review_response.summary) > 20
        assert len(result.review_response.recommendations) > 0

    @pytest.mark.parametrize(
        "model_name",
        [
            "gpt-4o",  # OpenAI
            "claude-sonnet-4",  # Anthropic (일반)
            "claude-sonnet-4-thinking",  # Anthropic (thinking 모드)
            "gemini-2.5-flash",  # Google
            "qwen3-coder",  # OpenRouter
        ],
    )
    def test_integration_with_parametrized_models(
        self, model_name: str, integration_review_results: list[ReviewResult]
    ) -> None:
        """Parametrized 모델별 통합 테스트 (API 키가 모두 설정되어 있다고 가정)"""

        # Given: 실제 환경
        synthesizer = ReviewSynthesizer(model_name)

        # When: 실제 API 호출하여 합성
        result = synthesizer.synthesize_review_results(integration_review_results)

        # Then: 실제 LLM 통합 동작 검증
        assert result.success is True
        assert result.review_response.summary is not None
        assert len(result.review_response.summary) > 10
        assert len(result.review_response.recommendations) > 0

        # Issues는 원본 데이터에서 가져와짐
        assert len(result.review_response.issues) == 3

        # 실제 비용 발생 확인
        assert result.estimated_cost.total_cost_usd >= 0  # 일부 무료 모델은 0일 수 있음

        print(f"\n=== {model_name} 합성 결과 분석 ===")
        print(f"합성된 Summary: {result.review_response.summary}")
        print(
            f"\n합성된 Recommendations ({len(result.review_response.recommendations)}개):"
        )
        for i, rec in enumerate(result.review_response.recommendations, 1):
            print(f"  {i}. {rec}")
        print(f"\n유지된 Issues ({len(result.review_response.issues)}개):")
        for i, issue in enumerate(result.review_response.issues, 1):
            print(f"  {i}. {issue.type}/{issue.severity}: {issue.description}")
        print("\n비용 정보:")
        print(f"  총 비용: ${result.estimated_cost.total_cost_usd}")
        print(f"  입력 토큰: {result.estimated_cost.input_tokens}")
        print(f"  출력 토큰: {result.estimated_cost.output_tokens}")
        print("===========================\n")

    @pytest.mark.parametrize(
        "model_name",
        [
            "gpt-4o",  # OpenAI
            "claude-sonnet-4",  # Anthropic (일반)
            "claude-sonnet-4-thinking",  # Anthropic (thinking 모드)
            "gemini-2.5-flash",  # Google
            "qwen3-coder",  # OpenRouter
        ],
    )
    def test_integration_with_complex_dataset(
        self, model_name: str, complex_integration_review_results: list[ReviewResult]
    ) -> None:
        """복잡한 데이터셋으로 Parametrized 모델별 통합 테스트"""

        # Given: 복잡한 데이터셋 (더 많은 이슈와 권장사항 포함)
        synthesizer = ReviewSynthesizer(model_name)

        # When: 실제 API 호출하여 합성
        result = synthesizer.synthesize_review_results(complex_integration_review_results)

        # Then: 실제 LLM 통합 동작 검증
        assert result.success is True
        assert result.review_response.summary is not None
        assert len(result.review_response.summary) > 10
        assert len(result.review_response.recommendations) > 0

        # 복잡한 데이터셋의 Issues는 더 많음 (총 9개: 3+0+2+4)
        assert len(result.review_response.issues) == 9

        # 실제 비용 발생 확인
        assert result.estimated_cost.total_cost_usd >= 0  # 일부 무료 모델은 0일 수 있음
        
        # 복잡한 데이터셋 합성 결과 품질 분석을 위한 출력
        print(f"\n=== {model_name} 복잡한 데이터셋 합성 결과 분석 ===")
        print(f"합성된 Summary: {result.review_response.summary}")
        print(f"\n합성된 Recommendations ({len(result.review_response.recommendations)}개):")
        for i, rec in enumerate(result.review_response.recommendations, 1):
            print(f"  {i}. {rec}")
        print(f"\n유지된 Issues ({len(result.review_response.issues)}개):")
        for i, issue in enumerate(result.review_response.issues, 1):
            print(f"  {i}. {issue.type}/{issue.severity}: {issue.description[:80]}...")
        print(f"\n비용 정보:")
        print(f"  총 비용: ${result.estimated_cost.total_cost_usd}")
        print(f"  입력 토큰: {result.estimated_cost.input_tokens}")
        print(f"  출력 토큰: {result.estimated_cost.output_tokens}")
        print("========== 복잡한 데이터셋 완료 ==========\n")

    def test_integration_no_api_key_fallback_behavior(
        self, integration_review_results: list[ReviewResult]
    ) -> None:
        """API 키 없이도 fallback으로 동작하는 통합 테스트"""
        # Given: 존재하지 않는 모델 (API 키 없음)
        synthesizer = ReviewSynthesizer("non-existent-model")

        # When: API 키 없는 상태에서 합성 시도
        result = synthesizer.synthesize_review_results(integration_review_results)

        # Then: fallback으로 성공적으로 처리
        assert result.success is True
        assert result.review_response.summary is not None
        assert len(result.review_response.recommendations) > 0
        assert len(result.review_response.issues) == 3  # 원본 이슈 유지

    def test_integration_with_minimal_data(self) -> None:
        """최소한의 데이터로 통합 테스트"""
        # Given: 간단한 ReviewResult 하나
        simple_result = ReviewResult.get_success_result(
            review_response=ReviewResponse(
                summary="간단한 코드 리뷰: 함수가 추가되었습니다.",
                recommendations=["함수명을 개선하세요", "주석을 추가하세요"],
                issues=[],
            ),
            estimated_cost=EstimatedCost.get_zero_cost("test-model"),
        )

        synthesizer = ReviewSynthesizer("test-model")

        # When: 합성 실행
        result = synthesizer.synthesize_review_results([simple_result])

        # Then: 단일 결과는 그대로 반환 (fallback)
        assert result.success is True
        assert (
            result.review_response.summary == "간단한 코드 리뷰: 함수가 추가되었습니다."
        )
        assert len(result.review_response.recommendations) == 2

    def test_integration_cost_tracking(
        self, integration_review_results: list[ReviewResult]
    ) -> None:
        """실제 API 비용 추적 통합 테스트"""
        # Given: 저렴한 모델로 비용 추적 테스트
        model_name = "gpt-4o-mini"
        synthesizer = ReviewSynthesizer(model_name)

        # When: 실제 API 호출
        result = synthesizer.synthesize_review_results(integration_review_results)

        # Then: 비용 추적 검증
        assert result.success is True

        # 실제 API 호출 시 토큰 소모 확인
        if result.estimated_cost.total_cost_usd > 0:  # 유료 모델인 경우
            assert result.estimated_cost.input_tokens > 1000  # 충분한 입력
            assert result.estimated_cost.output_tokens > 50  # LLM 응답
            assert result.estimated_cost.input_cost_usd >= 0
            assert result.estimated_cost.output_cost_usd >= 0
