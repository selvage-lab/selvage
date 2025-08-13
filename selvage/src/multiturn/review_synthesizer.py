"""리뷰 결과 합성기"""

import importlib.resources
import json
from typing import Any, TypeVar

import anthropic
import openai
from google.genai import types as genai_types
from pydantic import BaseModel

from selvage.src.config import get_api_key, get_default_language
from selvage.src.model_config import ModelConfig, ModelInfoDict
from selvage.src.models.model_provider import ModelProvider
from selvage.src.models.review_result import ReviewResult
from selvage.src.utils.base_console import console
from selvage.src.utils.json_extractor import JSONExtractor
from selvage.src.utils.llm_client_factory import LLMClientFactory
from selvage.src.utils.token.cost_estimator import CostEstimator
from selvage.src.utils.token.models import (
    EstimatedCost,
    RecommendationSynthesisResponse,
    ReviewResponse,
    StructuredSynthesisResponse,
    SummarySynthesisResponse,
)

# 제네릭 타입 변수 정의
T = TypeVar("T", bound=BaseModel)


class SummarySynthesisResult(BaseModel):
    """Summary 합성 결과를 담는 클래스"""

    summary: str | None
    estimated_cost: EstimatedCost


class RecommendationSynthesisResult(BaseModel):
    """Recommendations 합성 결과를 담는 클래스"""

    recommendations: list[str] | None
    estimated_cost: EstimatedCost


# API 응답 타입 정의
ApiResponseType = (
    openai.types.Completion  # OpenAI instructor 응답
    | anthropic.types.Message  # Anthropic 응답
    | genai_types.GenerateContentResponse  # Google Gemini 응답
    | dict[str, Any]  # OpenRouter 응답 (dict 형태)
)

# 클라이언트 타입 정의 (typing.Any 대신 구체적인 타입 사용)
ClientType = Any | object


class SynthesisConfig:
    """합성 과정에서 사용되는 설정값들"""

    MAX_TOKENS = 5000
    TEMPERATURE = 0.1
    MAX_RETRIES = 2


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

        # 2. Summary와 Recommendations를 분리하여 LLM 합성
        synthesized_summary = None
        synthesized_recommendations = None
        summary_synthesis_cost = None
        recommendations_synthesis_cost = None

        # 2.1 Summary LLM 합성
        try:
            summary_result = self._synthesize_summary_with_llm(successful_results)
            if summary_result and summary_result.summary:
                synthesized_summary = summary_result.summary
                summary_synthesis_cost = summary_result.estimated_cost
                console.info("Summary LLM 합성 성공")
            else:
                synthesized_summary = self._fallback_summary(successful_results)
                console.info("Summary fallback 적용")
        except Exception as e:
            console.warning(f"Summary LLM 합성 실패: {e}. fallback으로 처리됩니다.")
            synthesized_summary = self._fallback_summary(successful_results)

        # 2.2 Recommendations 합성
        synthesized_recommendations = self._combine_recommendations_simple(
            successful_results
        )

        # 3. 비용 합산 (기존 리뷰 비용 + 합성 비용)
        total_cost = self._calculate_total_cost(
            successful_results, summary_synthesis_cost, recommendations_synthesis_cost
        )

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

    def _load_model_info(self) -> ModelInfoDict:
        """model_name으로부터 ModelInfoDict 로드"""
        config = ModelConfig()
        return config.get_model_info(self.model_name)

    def _load_api_key(self, provider: ModelProvider) -> str:
        """프로바이더별 API 키 로드"""
        return get_api_key(provider)

    def _get_summary_synthesis_prompt(self) -> str:
        """Summary 전용 합성 프롬프트 로드"""
        file_ref = importlib.resources.files(
            "selvage.resources.prompt.synthesis"
        ).joinpath("summary_synthesis_prompt.txt")
        with importlib.resources.as_file(file_ref) as file_path:
            base_prompt = file_path.read_text(encoding="utf-8")

        user_language = get_default_language()
        return base_prompt.replace("{{LANGUAGE}}", user_language)

    def _get_recommendation_synthesis_prompt(self) -> str:
        """Recommendations 전용 합성 프롬프트 로드"""
        file_ref = importlib.resources.files(
            "selvage.resources.prompt.synthesis"
        ).joinpath("recommendation_synthesis_prompt.txt")
        with importlib.resources.as_file(file_ref) as file_path:
            base_prompt = file_path.read_text(encoding="utf-8")

        user_language = get_default_language()
        return base_prompt.replace("{{LANGUAGE}}", user_language)

    def _execute_generic_llm_synthesis(
        self,
        data: dict[str, Any],
        response_model: type[T],
    ) -> tuple[T | None, EstimatedCost]:
        """공통 LLM 합성 로직 - 코드 중복 제거"""
        try:
            # 1. 모델 정보 및 API 키 검증
            model_info = self._load_model_info()
            api_key = self._load_api_key(model_info["provider"])
            if not api_key:
                return None, EstimatedCost.get_zero_cost(self.model_name)

            client = LLMClientFactory.create_client(
                model_info["provider"], api_key, model_info
            )

            # 2. 메시지 생성 (데이터는 호출부에서 준비)
            system_prompt = self._get_system_prompt_for_task(data["task"])
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(data, ensure_ascii=False, indent=2),
                },
            ]

            # 3. API 요청 파라미터 생성
            params = self._create_request_params(messages, model_info, response_model)

            # 4. 프로바이더별 API 호출
            provider = model_info["provider"]
            structured_response, raw_api_response = self._call_provider_api(
                provider, client, params, response_model
            )

            if structured_response is None:
                return None, EstimatedCost.get_zero_cost(self.model_name)

            # 5. 비용 계산
            estimated_cost = self._calculate_synthesis_cost(
                provider, raw_api_response, model_info["full_name"]
            )

            return structured_response, estimated_cost

        except Exception as e:
            console.error(f"LLM 합성 중 예외 발생: {e}")
            return None, EstimatedCost.get_zero_cost(self.model_name)

    def _get_system_prompt_for_task(self, task: str) -> str:
        """작업 타입에 따른 시스템 프롬프트 반환"""
        if task == "summary_synthesis":
            return self._get_summary_synthesis_prompt()
        elif task == "recommendation_synthesis":
            return self._get_recommendation_synthesis_prompt()
        else:
            raise ValueError(f"지원하지 않는 작업 타입: {task}")

    def _call_provider_api(
        self,
        provider: ModelProvider,
        client: ClientType,
        params: dict[str, Any],
        response_model: type[T],
    ) -> tuple[T | None, ApiResponseType | None]:
        """프로바이더별 API 호출 로직"""
        if provider == ModelProvider.OPENAI:
            return self._call_openai_api(client, params, response_model)
        elif provider == ModelProvider.GOOGLE:
            return self._call_google_api(client, params, response_model)
        elif provider == ModelProvider.ANTHROPIC:
            return self._call_anthropic_api(client, params, response_model)
        elif provider == ModelProvider.OPENROUTER:
            return self._call_openrouter_api(client, params, response_model)
        else:
            raise ValueError(f"지원하지 않는 프로바이더: {provider}")

    def _call_openai_api(
        self, client: ClientType, params: dict[str, Any], response_model: type[T]
    ) -> tuple[T | None, ApiResponseType | None]:
        """OpenAI API 호출 전략"""
        try:
            structured_response, raw_response = (
                client.chat.completions.create_with_completion(
                    response_model=response_model,
                    max_retries=SynthesisConfig.MAX_RETRIES,
                    **params,
                )
            )
            return structured_response, raw_response
        except Exception as e:
            console.error(f"OpenAI API 호출 실패: {e}")
            return None, None

    def _call_google_api(
        self, client: ClientType, params: dict[str, Any], response_model: type[T]
    ) -> tuple[T | None, ApiResponseType | None]:
        """Google Gemini API 호출 전략"""
        try:
            raw_response = client.models.generate_content(**params)
            response_text = raw_response.text
            if response_text is None:
                return None, None

            structured_response = JSONExtractor.validate_and_parse_json(
                response_text, response_model
            )
            return structured_response, raw_response
        except Exception as e:
            console.error(f"Google API 호출 실패: {e}")
            return None, None

    def _call_anthropic_api(
        self, client: ClientType, params: dict[str, Any], response_model: type[T]
    ) -> tuple[T | None, ApiResponseType | None]:
        """Anthropic Claude API 호출 전략"""
        try:
            model_info = self._load_model_info()
            if model_info.get("thinking_mode", False):
                # thinking 모드는 직접 호출
                raw_response = client.messages.create(**params)
                response_text = None
                for block in raw_response.content:
                    if block.type == "text":
                        response_text = block.text

                if response_text is None:
                    return None, None

                structured_response = JSONExtractor.validate_and_parse_json(
                    response_text, response_model
                )
                return structured_response, raw_response
            else:
                # 일반 모드는 instructor 사용
                structured_response, raw_response = (
                    client.chat.completions.create_with_completion(
                        response_model=response_model,
                        max_retries=SynthesisConfig.MAX_RETRIES,
                        **params,
                    )
                )
                return structured_response, raw_response
        except Exception as e:
            console.error(f"Anthropic API 호출 실패: {e}")
            return None, None

    def _call_openrouter_api(
        self, client: ClientType, params: dict[str, Any], response_model: type[T]
    ) -> tuple[T | None, ApiResponseType | None]:
        """OpenRouter API 호출 전략"""
        try:
            with client as openrouter_client:
                raw_response_data = openrouter_client.create_completion(**params)

                from selvage.src.llm_gateway.openrouter.models import OpenRouterResponse

                openrouter_response = OpenRouterResponse.from_dict(raw_response_data)

                if not openrouter_response.choices:
                    return None, None

                response_text = openrouter_response.choices[0].message.content
                if not response_text:
                    return None, None

                structured_response = response_model.model_validate_json(response_text)
                return structured_response, raw_response_data
        except Exception as e:
            console.error(f"OpenRouter API 호출 실패: {e}")
            return None, None

    def _synthesize_summary_with_llm(
        self, successful_results: list[ReviewResult]
    ) -> SummarySynthesisResult | None:
        """Summary만 LLM으로 합성 (리팩터링된 버전)"""
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

            # 3. 통합 LLM 합성 호출
            structured_response, estimated_cost = self._execute_generic_llm_synthesis(
                synthesis_data, SummarySynthesisResponse
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
            console.error(f"Summary LLM 합성 중 예외 발생: {e}")
            return SummarySynthesisResult(
                summary=None,
                estimated_cost=EstimatedCost.get_zero_cost(self.model_name),
            )

    def _synthesize_recommendations_with_llm(
        self, successful_results: list[ReviewResult]
    ) -> RecommendationSynthesisResult | None:
        """Recommendations만 LLM으로 합성 (리팩터링된 버전)"""
        try:
            # 1. Recommendations 데이터 추출
            all_recommendations = []
            for result in successful_results:
                all_recommendations.extend(result.review_response.recommendations)

            if not all_recommendations:
                return []

            # 2. 합성 데이터 준비
            synthesis_data = {
                "task": "recommendation_synthesis",
                "recommendations": all_recommendations,
            }

            # 3. 통합 LLM 합성 호출
            structured_response, estimated_cost = self._execute_generic_llm_synthesis(
                synthesis_data, RecommendationSynthesisResponse
            )

            if structured_response is None:
                return RecommendationSynthesisResult(
                    recommendations=None,
                    estimated_cost=EstimatedCost.get_zero_cost(self.model_name),
                )

            return RecommendationSynthesisResult(
                recommendations=structured_response.recommendations,
                estimated_cost=estimated_cost,
            )

        except Exception as e:
            console.error(f"Recommendations LLM 합성 중 예외 발생: {e}")
            return RecommendationSynthesisResult(
                recommendations=None,
                estimated_cost=EstimatedCost.get_zero_cost(self.model_name),
            )

    def _create_request_params(
        self,
        messages: list[dict[str, str]],
        model_info: ModelInfoDict,
        response_model: type[T],
    ) -> dict[str, Any]:
        """프로바이더별 API 요청 파라미터 생성 (통합 버전)"""
        provider = model_info["provider"]

        if provider == ModelProvider.OPENAI:
            return {
                "model": model_info["full_name"],
                "messages": messages,
                "max_tokens": SynthesisConfig.MAX_TOKENS,
                "temperature": SynthesisConfig.TEMPERATURE,
            }
        elif provider == ModelProvider.GOOGLE:
            # Gemini용 메시지 형식 변환
            contents = []
            for msg in messages:
                if msg["role"] == "system":
                    contents.append(
                        {
                            "role": "user",
                            "parts": [{"text": f"System: {msg['content']}"}],
                        }
                    )
                else:
                    contents.append(
                        {"role": msg["role"], "parts": [{"text": msg["content"]}]}
                    )

            return {
                "model": model_info["full_name"],
                "contents": contents,
            }
        elif provider == ModelProvider.ANTHROPIC:
            # system 메시지 분리
            system_content = None
            anthropic_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_content = msg["content"]
                else:
                    anthropic_messages.append(msg)

            params = {
                "model": model_info["full_name"],
                "messages": anthropic_messages,
                "max_tokens": SynthesisConfig.MAX_TOKENS,
                "temperature": SynthesisConfig.TEMPERATURE,
            }

            if system_content:
                params["system"] = system_content

            return params
        elif provider == ModelProvider.OPENROUTER:
            # OpenRouter용 파라미터 (OpenAI 호환 + JSON Schema)
            openrouter_model_name = model_info.get(
                "openrouter_name", model_info["full_name"]
            )

            # 응답 모델에 따라 스키마 이름과 스키마를 동적으로 설정
            schema_name = "synthesis_response"
            schema = response_model.model_json_schema()

            if response_model == SummarySynthesisResponse:
                schema_name = "summary_synthesis_response"
            elif response_model == RecommendationSynthesisResponse:
                schema_name = "recommendation_synthesis_response"
            elif response_model == StructuredSynthesisResponse:
                schema_name = "structured_synthesis_response"

            return {
                "model": openrouter_model_name,
                "messages": messages,
                "max_tokens": SynthesisConfig.MAX_TOKENS,
                "temperature": SynthesisConfig.TEMPERATURE,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_name,
                        "strict": True,
                        "schema": schema,
                    },
                },
                "usage": {
                    "include_usage": True,
                },
            }
        else:
            raise ValueError(f"지원하지 않는 프로바이더: {provider}")

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

    def _calculate_synthesis_cost(
        self,
        provider: ModelProvider,
        raw_api_response: ApiResponseType,
        model_name: str,
    ) -> EstimatedCost:
        """합성 과정에서 발생한 비용을 프로바이더별로 계산합니다.

        Args:
            provider: 모델 프로바이더
            raw_api_response: API 응답 객체
            model_name: 모델 이름

        Returns:
            EstimatedCost: 계산된 비용 정보
        """
        try:
            if provider == ModelProvider.OPENAI:
                return self._calculate_openai_synthesis_cost(
                    raw_api_response, model_name
                )
            elif provider == ModelProvider.ANTHROPIC:
                return self._calculate_anthropic_synthesis_cost(
                    raw_api_response, model_name
                )
            elif provider == ModelProvider.GOOGLE:
                return self._calculate_google_synthesis_cost(
                    raw_api_response, model_name
                )
            elif provider == ModelProvider.OPENROUTER:
                return self._calculate_openrouter_synthesis_cost(
                    raw_api_response, model_name
                )
            else:
                console.warning(f"지원하지 않는 프로바이더입니다: {provider}")

        except Exception as e:
            console.error(f"합성 비용 계산 중 오류 발생: {e}")

        # 오류 발생 시 또는 usage 정보가 없는 경우 0 비용 반환
        return EstimatedCost.get_zero_cost(model_name)

    def _calculate_openai_synthesis_cost(
        self, raw_api_response: ApiResponseType, model_name: str
    ) -> EstimatedCost:
        """OpenAI 프로바이더의 합성 비용을 계산합니다."""
        if hasattr(raw_api_response, "usage") and raw_api_response.usage:
            return CostEstimator.estimate_cost_from_openai_usage(
                model_name, raw_api_response.usage
            )
        else:
            console.warning(
                f"OpenAI 응답에서 usage 정보를 찾을 수 없습니다: {model_name}"
            )
            return EstimatedCost.get_zero_cost(model_name)

    def _calculate_anthropic_synthesis_cost(
        self, raw_api_response: ApiResponseType, model_name: str
    ) -> EstimatedCost:
        """Anthropic 프로바이더의 합성 비용을 계산합니다."""
        if hasattr(raw_api_response, "usage") and raw_api_response.usage:
            return CostEstimator.estimate_cost_from_anthropic_usage(
                model_name, raw_api_response.usage
            )
        else:
            console.warning(
                f"Anthropic 응답에서 usage 정보를 찾을 수 없습니다: {model_name}"
            )
            return EstimatedCost.get_zero_cost(model_name)

    def _calculate_google_synthesis_cost(
        self, raw_api_response: ApiResponseType, model_name: str
    ) -> EstimatedCost:
        """Google 프로바이더의 합성 비용을 계산합니다."""
        if (
            hasattr(raw_api_response, "usage_metadata")
            and raw_api_response.usage_metadata
        ):
            return CostEstimator.estimate_cost_from_gemini_usage(
                model_name, raw_api_response.usage_metadata
            )
        else:
            console.warning(
                f"Google 응답에서 usage_metadata 정보를 찾을 수 없습니다: {model_name}"
            )
            return EstimatedCost.get_zero_cost(model_name)

    def _calculate_openrouter_synthesis_cost(
        self, raw_api_response: ApiResponseType, model_name: str
    ) -> EstimatedCost:
        """OpenRouter 프로바이더의 합성 비용을 계산합니다."""
        if isinstance(raw_api_response, dict) and "usage" in raw_api_response:
            usage_dict = raw_api_response["usage"]
            # OpenAI 형식의 Usage 객체로 변환
            usage = openai.types.CompletionUsage(
                prompt_tokens=usage_dict.get("prompt_tokens", 0),
                completion_tokens=usage_dict.get("completion_tokens", 0),
                total_tokens=usage_dict.get("total_tokens", 0),
            )
            return CostEstimator.estimate_cost_from_openai_usage(model_name, usage)
        else:
            console.warning(
                f"OpenRouter 응답에서 usage 정보를 찾을 수 없습니다: {model_name}"
            )
            return EstimatedCost.get_zero_cost(model_name)
