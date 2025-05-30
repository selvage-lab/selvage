"""
LLM API 응답의 usage 정보를 기반으로 비용을 계산하는 모듈입니다.
"""

from typing import TypedDict

import anthropic
import openai
from google.genai import types as genai_types

from selvage.src.exceptions.unsupported_model_error import UnsupportedModelError
from selvage.src.model_config import get_model_pricing
from selvage.src.utils.base_console import console
from selvage.src.utils.token.models import EstimatedCost


# 모델 가격 정보 타입 정의
class ModelPricing(TypedDict):
    input: float
    output: float


class CostEstimator:
    """LLM API 응답의 usage 정보를 이용한 비용 계산 유틸리티 클래스"""

    @staticmethod
    def _get_model_pricing(model_name: str) -> ModelPricing:
        """모델에 해당하는 가격 정보를 가져옵니다.

        Args:
            model_name: 모델 이름

        Returns:
            ModelPricing: 모델 가격 정보

        Raises:
            UnsupportedModelError: 지원되지 않는 모델인 경우
        """
        try:
            pricing_info = get_model_pricing(model_name)
            return {
                "input": pricing_info["input"],
                "output": pricing_info["output"],
            }
        except UnsupportedModelError:
            console.warning(f"지원되지 않는 모델입니다: {model_name}")
            raise

    @staticmethod
    def estimate_cost_from_openai_usage(
        model_name: str, usage: openai.types.CompletionUsage
    ) -> EstimatedCost:
        """OpenAI API 응답의 usage 정보를 이용하여 비용을 계산합니다.

        Args:
            model_name: 사용한 모델 이름
            usage: OpenAI API 응답의 usage 정보 객체

        Returns:
            EstimatedCostFromUsage: 계산된 비용 정보
        """
        try:
            # 모델 가격 정보 가져오기
            model_pricing = CostEstimator._get_model_pricing(model_name)

            # 입력 및 출력 토큰 비용 계산
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens

            input_cost = input_tokens * (model_pricing["input"] / 1000000)
            output_cost = output_tokens * (model_pricing["output"] / 1000000)
            total_cost = input_cost + output_cost

            return EstimatedCost(
                model=model_name,
                input_tokens=input_tokens,
                input_cost_usd=round(input_cost, 6),
                output_tokens=output_tokens,
                output_cost_usd=round(output_cost, 6),
                total_cost_usd=round(total_cost, 6),
            )
        except UnsupportedModelError:
            # 지원되지 않는 모델이지만 비용 계산은 진행해야 하는 경우
            console.warning(
                f"지원되지 않는 모델이지만 비용 계산을 진행합니다: {model_name}"
            )
            return EstimatedCost(
                model=model_name,
                input_tokens=usage.prompt_tokens,
                input_cost_usd=0.0,
                output_tokens=usage.completion_tokens,
                output_cost_usd=0.0,
                total_cost_usd=0.0,
            )

    @staticmethod
    def estimate_cost_from_anthropic_usage(
        model_name: str, usage: anthropic.types.Usage
    ) -> EstimatedCost:
        """Anthropic (Claude) API 응답의 usage 정보를 이용하여 비용을 계산합니다.

        Args:
            model_name: 사용한 모델 이름
            usage: Anthropic API 응답의 usage 정보 객체

        Returns:
            EstimatedCostFromUsage: 계산된 비용 정보
        """
        try:
            # 모델 가격 정보 가져오기
            model_pricing = CostEstimator._get_model_pricing(model_name)

            # 입력 및 출력 토큰 비용 계산
            input_tokens = usage.input_tokens
            output_tokens = usage.output_tokens

            input_cost = input_tokens * (model_pricing["input"] / 1000000)
            output_cost = output_tokens * (model_pricing["output"] / 1000000)
            total_cost = input_cost + output_cost

            return EstimatedCost(
                model=model_name,
                input_tokens=input_tokens,
                input_cost_usd=round(input_cost, 6),
                output_tokens=output_tokens,
                output_cost_usd=round(output_cost, 6),
                total_cost_usd=round(total_cost, 6),
            )
        except UnsupportedModelError:
            # 지원되지 않는 모델이지만 비용 계산은 진행해야 하는 경우
            console.warning(
                f"지원되지 않는 모델이지만 비용 계산을 진행합니다: {model_name}"
            )
            return EstimatedCost(
                model=model_name,
                input_tokens=usage.input_tokens,
                input_cost_usd=0.0,
                output_tokens=usage.output_tokens,
                output_cost_usd=0.0,
                total_cost_usd=0.0,
            )

    @staticmethod
    def estimate_cost_from_gemini_usage(
        model_name: str,
        usage_metadata: genai_types.GenerateContentResponseUsageMetadata,
    ) -> EstimatedCost:
        """Google (Gemini) API 응답의 usage_metadata 정보를 이용하여 비용을 계산합니다.

        Args:
            model_name: 사용한 모델 이름
            usage_metadata: Gemini API 응답의 usage_metadata 정보 객체

        Returns:
            EstimatedCostFromUsage: 계산된 비용 정보
        """
        try:
            # 모델 가격 정보 가져오기
            model_pricing = CostEstimator._get_model_pricing(model_name)

            # Gemini API의 응답 구조는 다양할 수 있음
            # 일반적인 필드명: prompt_token_count, candidates_token_count
            try:
                # Gemini API의 응답에서 토큰 수 추출
                input_tokens = getattr(usage_metadata, "prompt_token_count", 0)
                output_tokens = getattr(usage_metadata, "candidates_token_count", 0)

                # 입력 및 출력 토큰 비용 계산
                input_cost = input_tokens * (model_pricing["input"] / 1000000)
                output_cost = output_tokens * (model_pricing["output"] / 1000000)
                total_cost = input_cost + output_cost

                return EstimatedCost(
                    model=model_name,
                    input_tokens=input_tokens,
                    input_cost_usd=round(input_cost, 6),
                    output_tokens=output_tokens,
                    output_cost_usd=round(output_cost, 6),
                    total_cost_usd=round(total_cost, 6),
                )
            except Exception as e:
                console.error(f"Gemini usage 정보 처리 중 오류 발생: {e}", exception=e)
                # 속성 접근 오류가 발생한 경우
                return EstimatedCost(
                    model=model_name,
                    input_tokens=0,
                    input_cost_usd=0.0,
                    output_tokens=0,
                    output_cost_usd=0.0,
                    total_cost_usd=0.0,
                )
        except UnsupportedModelError:
            # 지원되지 않는 모델이지만 비용 계산은 진행해야 하는 경우
            console.warning(
                f"지원되지 않는 모델이지만 비용 계산을 진행합니다: {model_name}"
            )

            # 사용 가능한 값 추출 시도
            input_tokens = getattr(usage_metadata, "prompt_token_count", 0)
            output_tokens = getattr(usage_metadata, "candidates_token_count", 0)

            return EstimatedCost(
                model=model_name,
                input_tokens=input_tokens,
                input_cost_usd=0.0,
                output_tokens=output_tokens,
                output_cost_usd=0.0,
                total_cost_usd=0.0,
            )
