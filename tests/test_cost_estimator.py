"""
CostEstimator 클래스 테스트 코드

이 테스트는 각 LLM 프로바이더의 API 응답에서 usage 정보를 이용한 비용 계산 기능을 테스트합니다.
- OpenAI API usage 정보 처리 테스트
- Claude (Anthropic) API usage 정보 처리 테스트
- Gemini (Google) API usage_metadata 정보 처리 테스트
"""

from unittest.mock import MagicMock, patch

import pytest
from anthropic.types import Usage as AnthropicUsage
from openai.types import CompletionUsage

from selvage.src.exceptions.unsupported_model_error import UnsupportedModelError
from selvage.src.utils.token import CostEstimator, EstimatedCost


class TestCostEstimator:
    """CostEstimator 클래스 테스트"""

    def test_get_model_pricing_supported_model(self) -> None:
        """지원되는 모델의 가격 정보 조회 테스트"""
        # 모델 설정 파일에 있는 지원되는 모델 테스트
        pricing = CostEstimator._get_model_pricing("gpt-4o")
        assert "input" in pricing
        assert "output" in pricing
        assert isinstance(pricing["input"], float)
        assert isinstance(pricing["output"], float)

    def test_get_model_pricing_unsupported_model(self) -> None:
        """지원되지 않는 모델의 경우 UnsupportedModelError가 발생하는지 테스트"""
        # 지원되지 않는 Claude 모델 테스트
        with pytest.raises(UnsupportedModelError) as exc_info:
            CostEstimator._get_model_pricing("claude-3-haiku-20240307")
        assert "claude-3-haiku-20240307" in str(exc_info.value)

        # 지원되지 않는 Gemini 모델 테스트
        with pytest.raises(UnsupportedModelError) as exc_info:
            CostEstimator._get_model_pricing("gemini-1.5-flash")
        assert "gemini-1.5-flash" in str(exc_info.value)

    @pytest.mark.parametrize(
        "model_name,prompt_tokens,completion_tokens,expected_input_cost,expected_output_cost",
        [
            ("gpt-4o", 1000, 500, 2.5, 10.0),  # $2.50/$10.00 per 1M
            ("o4-mini", 2000, 800, 1.1, 4.4),  # $1.10/$4.40 per 1M
        ],
    )
    def test_estimate_cost_from_openai_usage(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        expected_input_cost: float,
        expected_output_cost: float,
    ) -> None:
        """OpenAI API usage 정보를 이용한 비용 계산 테스트"""
        # OpenAI CompletionUsage 객체 생성
        usage = MagicMock(spec=CompletionUsage)
        usage.prompt_tokens = prompt_tokens
        usage.completion_tokens = completion_tokens
        usage.total_tokens = prompt_tokens + completion_tokens

        # 실제 _get_model_pricing이 호출되지 않도록 패치
        with patch.object(
            CostEstimator,
            "_get_model_pricing",
            return_value={
                "input": expected_input_cost / prompt_tokens * 1000000,
                "output": expected_output_cost / completion_tokens * 1000000,
            },
        ):
            # 비용 계산
            cost = CostEstimator.estimate_cost_from_openai_usage(model_name, usage)

            # 결과 검증
            assert isinstance(cost, EstimatedCost)
            assert cost.model == model_name
            assert cost.input_tokens == prompt_tokens
            assert cost.output_tokens == completion_tokens
            assert round(cost.input_cost_usd, 6) == round(expected_input_cost, 6)
            assert round(cost.output_cost_usd, 6) == round(expected_output_cost, 6)
            assert round(cost.total_cost_usd, 6) == round(
                expected_input_cost + expected_output_cost, 6
            )
            assert cost.within_context_limit is True

    @pytest.mark.parametrize(
        "model_name,input_tokens,output_tokens,expected_input_cost,expected_output_cost",
        [
            ("claude-3-sonnet", 1000, 500, 1.5, 7.5),  # $1.50/$7.50 per 1M
            ("claude-3-opus", 2000, 800, 3.0, 15.0),  # $3.00/$15.00 per 1M
        ],
    )
    def test_estimate_cost_from_anthropic_usage(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        expected_input_cost: float,
        expected_output_cost: float,
    ) -> None:
        """Anthropic API usage 정보를 이용한 비용 계산 테스트"""
        # Anthropic Usage 객체 생성
        usage = MagicMock(spec=AnthropicUsage)
        usage.input_tokens = input_tokens
        usage.output_tokens = output_tokens

        # 실제 _get_model_pricing이 호출되지 않도록 패치
        with patch.object(
            CostEstimator,
            "_get_model_pricing",
            return_value={
                "input": expected_input_cost / input_tokens * 1000000,
                "output": expected_output_cost / output_tokens * 1000000,
            },
        ):
            # 비용 계산
            cost = CostEstimator.estimate_cost_from_anthropic_usage(model_name, usage)

            # 결과 검증
            assert isinstance(cost, EstimatedCost)
            assert cost.model == model_name
            assert cost.input_tokens == input_tokens
            assert cost.output_tokens == output_tokens
            assert round(cost.input_cost_usd, 6) == round(expected_input_cost, 6)
            assert round(cost.output_cost_usd, 6) == round(expected_output_cost, 6)
            assert round(cost.total_cost_usd, 6) == round(
                expected_input_cost + expected_output_cost, 6
            )
            assert cost.within_context_limit is True

    @pytest.mark.parametrize(
        "model_name,prompt_token_count,candidates_token_count,expected_input_cost,expected_output_cost",
        [
            ("gemini-2.5-pro", 1000, 500, 1.25, 10.0),  # $1.25/$10.00 per 1M
            ("gemini-2.5-flash", 2000, 800, 0.15, 0.6),  # $0.15/$0.60 per 1M
        ],
    )
    def test_estimate_cost_from_gemini_usage(
        self,
        model_name: str,
        prompt_token_count: int,
        candidates_token_count: int,
        expected_input_cost: float,
        expected_output_cost: float,
    ) -> None:
        """Gemini API usage_metadata 정보를 이용한 비용 계산 테스트"""
        # Gemini usage_metadata 객체 생성
        usage_metadata = MagicMock()
        usage_metadata.prompt_token_count = prompt_token_count
        usage_metadata.candidates_token_count = candidates_token_count
        usage_metadata.total_token_count = prompt_token_count + candidates_token_count
        usage_metadata.cached_content_token_count = 0

        # 실제 _get_model_pricing이 호출되지 않도록 패치
        with patch.object(
            CostEstimator,
            "_get_model_pricing",
            return_value={
                "input": expected_input_cost / prompt_token_count * 1000000,
                "output": expected_output_cost / candidates_token_count * 1000000,
            },
        ):
            # 비용 계산
            cost = CostEstimator.estimate_cost_from_gemini_usage(
                model_name, usage_metadata
            )

            # 결과 검증
            assert isinstance(cost, EstimatedCost)
            assert cost.model == model_name
            assert cost.input_tokens == prompt_token_count
            assert cost.output_tokens == candidates_token_count
            assert round(cost.input_cost_usd, 6) == round(expected_input_cost, 6)
            assert round(cost.output_cost_usd, 6) == round(expected_output_cost, 6)
            assert round(cost.total_cost_usd, 6) == round(
                expected_input_cost + expected_output_cost, 6
            )
            assert cost.within_context_limit is True

    def test_unsupported_model_fallback(self) -> None:
        """지원되지 않는 모델에 대한 fallback 처리 테스트"""
        # 지원되지 않는 모델 이름
        model_name = "unsupported-model"

        # OpenAI CompletionUsage 객체 생성
        usage = MagicMock(spec=CompletionUsage)
        usage.prompt_tokens = 1000
        usage.completion_tokens = 500
        usage.total_tokens = 1500

        # _get_model_pricing이 UnsupportedModelError를 발생시키도록 패치
        with patch.object(
            CostEstimator,
            "_get_model_pricing",
            side_effect=UnsupportedModelError(model_name),
        ):
            # 비용 계산 - 예외가 발생하지 않고 fallback 값을 반환해야 함
            cost = CostEstimator.estimate_cost_from_openai_usage(model_name, usage)

            # 결과 검증 - 토큰 수는 유지되지만 비용은 0으로 설정
            assert cost.model == model_name
            assert cost.input_tokens == 1000
            assert cost.output_tokens == 500
            assert cost.input_cost_usd == 0.0
            assert cost.output_cost_usd == 0.0
            assert cost.total_cost_usd == 0.0
