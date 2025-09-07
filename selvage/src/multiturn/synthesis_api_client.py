"""합성 API 클라이언트 모듈"""

import json
from typing import Any

import instructor
import openai
from google import genai

from selvage.src.config import get_api_key
from selvage.src.exceptions.json_parsing_error import JSONParsingError
from selvage.src.llm_gateway.openrouter.http_client import OpenRouterHTTPClient
from selvage.src.model_config import ModelConfig, ModelInfoDict
from selvage.src.models.model_provider import ModelProvider
from selvage.src.multiturn.synthesis_types import ApiResponseType, ClientType, T
from selvage.src.utils.base_console import console
from selvage.src.utils.json_extractor import JSONExtractor
from selvage.src.utils.llm_client_factory import LLMClientFactory
from selvage.src.utils.token.cost_estimator import CostEstimator
from selvage.src.utils.token.models import EstimatedCost


class SynthesisConfig:
    """합성 과정에서 사용되는 설정값들"""

    MAX_TOKENS = 5000
    TEMPERATURE = 0.1
    MAX_RETRIES = 2
    THINKING_BUDGET_TOKENS = 1024


class SynthesisAPIClient:
    """LLM API 호출 전용 클래스"""

    def __init__(self, model_name: str) -> None:
        """
        Args:
            model_name: 사용할 모델명
        """
        self.model_name = model_name

    def execute_synthesis(
        self,
        data: dict[str, Any],
        response_model: type[T],
        system_prompt: str,
    ) -> tuple[T | None, EstimatedCost]:
        """공통 LLM 합성 로직"""
        try:
            # 1. 모델 정보 및 API 키 검증
            model_info = self._load_model_info()
            api_key = self._load_api_key(model_info["provider"])
            if not api_key:
                return None, EstimatedCost.get_zero_cost(self.model_name)

            client = LLMClientFactory.create_client(
                model_info["provider"], api_key, model_info
            )

            # 2. 메시지 생성
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(data, ensure_ascii=False, indent=2),
                },
            ]

            # 3. API 요청 파라미터 생성 (클라이언트 타입 기반)
            params = self._create_request_params(
                messages, model_info, response_model, type(client)
            )

            # 4. 프로바이더별 API 호출 (클라이언트 타입 기반)
            if isinstance(client, OpenRouterHTTPClient):
                effective_provider = ModelProvider.OPENROUTER
            else:
                effective_provider = model_info["provider"]

            structured_response, raw_api_response = self._call_provider_api(
                effective_provider, client, params, response_model
            )

            if structured_response is None:
                console.error(f"LLM response parsing failed: {self.model_name}")
                raise JSONParsingError(
                    message=f"LLM 응답 파싱 실패: {self.model_name}",
                    raw_response="",
                    parsing_error=None,
                )

            # 5. 비용 계산
            estimated_cost = self._calculate_synthesis_cost(
                effective_provider, raw_api_response, model_info["full_name"]
            )

            return structured_response, estimated_cost

        except Exception as e:
            console.error(f"Exception occurred during LLM synthesis: {e}")
            return None, EstimatedCost.get_zero_cost(self.model_name)

    def _load_model_info(self) -> ModelInfoDict:
        """model_name으로부터 ModelInfoDict 로드"""
        config = ModelConfig()
        return config.get_model_info(self.model_name)

    def _load_api_key(self, provider: ModelProvider) -> str:
        """프로바이더별 API 키 로드"""
        return get_api_key(provider)

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
        self,
        client: instructor.Instructor,
        params: dict[str, Any],
        response_model: type[T],
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
            console.error(f"OpenAI API call failed: {e}")
            return None, None

    def _call_google_api(
        self, client: genai.Client, params: dict[str, Any], response_model: type[T]
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
            console.error(f"Google API call failed: {e}")
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
            console.error(f"Anthropic API call failed: {e}")
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

                structured_response = JSONExtractor.validate_and_parse_json(
                    response_text, response_model
                )
                return structured_response, raw_response_data
        except Exception as e:
            console.error(f"OpenRouter API call failed: {e}")
            return None, None

    def _create_request_params(
        self,
        messages: list[dict[str, str]],
        model_info: ModelInfoDict,
        response_model: type[T],
        client_type: type,
    ) -> dict[str, Any]:
        """프로바이더별 API 요청 파라미터 생성"""
        # 클라이언트 타입으로 실제 사용할 프로바이더 결정
        if client_type is OpenRouterHTTPClient:
            provider = ModelProvider.OPENROUTER
        else:
            provider = model_info["provider"]

        if provider == ModelProvider.OPENAI:
            params = {
                "model": model_info["full_name"],
                "messages": messages,
                "max_completion_tokens": SynthesisConfig.MAX_TOKENS,
                "reasoning_effort": "medium",
            }

            return params
        elif provider == ModelProvider.GOOGLE:
            # 시스템 프롬프트와 유저 메시지 구분
            system_prompt = None
            contents = []

            for message in messages:
                role = message.get("role", "")
                content = message.get("content", "")

                if role == "system":
                    system_prompt = content
                elif role == "user":
                    contents.append(content)

            # 온도 설정 (기본값: 0.1)
            temperature = SynthesisConfig.TEMPERATURE

            # config 생성
            from google.genai import types

            generation_config = types.GenerateContentConfig(
                temperature=temperature,
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=response_model,
            )

            # Gemini API 요청 파라미터 생성
            return {
                "model": model_info["full_name"],
                "contents": "\n\n".join(contents) if contents else "",
                "config": generation_config,
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
            schema_name = "summary_synthesis_response"
            schema = response_model.model_json_schema()

            # 기본 파라미터 구성
            params: dict[str, Any] = {
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
                # OpenRouter usage 정보 포함
                "usage": {
                    "include": True,
                },
            }

            # OpenRouter 전용 파라미터만 사용
            openrouter_params = model_info.get("openrouter_params", {})
            if (
                "reasoning" in openrouter_params
                and "max_tokens" in openrouter_params["reasoning"]
            ):
                openrouter_params["reasoning"]["max_tokens"] = (
                    SynthesisConfig.THINKING_BUDGET_TOKENS
                )
            params.update(openrouter_params)

            return params
        else:
            raise ValueError(f"지원하지 않는 프로바이더: {provider}")

    def _calculate_synthesis_cost(
        self,
        provider: ModelProvider,
        raw_api_response: ApiResponseType,
        model_name: str,
    ) -> EstimatedCost:
        """합성 과정에서 발생한 비용을 프로바이더별로 계산합니다."""
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
                console.warning(f"Unsupported provider: {provider}")

        except Exception as e:
            console.error(f"Error occurred while calculating synthesis cost: {e}")

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
                f"Cannot find usage information in OpenAI response: {model_name}"
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
                f"Cannot find usage information in Anthropic response: {model_name}"
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
                "Cannot find usage_metadata information in Google response: "
                f"{model_name}"
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
                f"Cannot find usage information in OpenRouter response: {model_name}"
            )
            return EstimatedCost.get_zero_cost(model_name)
