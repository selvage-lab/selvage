"""OpenRouter Gateway

OpenRouter API를 통한 LLM 서비스 게이트웨이를 제공합니다.
"""

import os
from typing import Any

from tenacity import (
    after_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from selvage.src.exceptions.api_key_not_found_error import APIKeyNotFoundError
from selvage.src.exceptions.invalid_model_provider_error import (
    InvalidModelProviderError,
)
from selvage.src.exceptions.openrouter_api_error import (
    OpenRouterConnectionError,
    OpenRouterResponseError,
)
from selvage.src.exceptions.unsupported_model_error import UnsupportedModelError
from selvage.src.llm_gateway.base_gateway import BaseGateway
from selvage.src.model_config import ModelInfoDict
from selvage.src.models.model_provider import ModelProvider
from selvage.src.models.review_result import ReviewResult
from selvage.src.utils.base_console import console
from selvage.src.utils.json_extractor import JSONExtractor
from selvage.src.utils.prompts.models import ReviewPromptWithFileContent
from selvage.src.utils.token.models import (
    EstimatedCost,
    ReviewResponse,
    StructuredReviewResponse,
)

from .http_client import OpenRouterHTTPClient
from .models import OpenRouterResponse

# OpenRouter API 요청 파라미터 타입
RequestParams = dict[str, Any]


class OpenRouterGateway(BaseGateway):
    """OpenRouter API를 사용하는 LLM 게이트웨이"""

    def _load_api_key(self) -> str:
        """OpenRouter API 키를 환경변수에서 로드합니다.

        Returns:
            str: API 키

        Raises:
            APIKeyNotFoundError: API 키가 설정되지 않은 경우
        """
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            console.error("OpenRouter API 키를 찾을 수 없습니다")
            console.info("환경변수 OPENROUTER_API_KEY를 설정하세요:")
            console.print("  export OPENROUTER_API_KEY=your_openrouter_api_key")
            raise APIKeyNotFoundError(ModelProvider.OPENROUTER)
        return api_key

    def _set_model(self, model_info: ModelInfoDict) -> None:
        """사용할 모델을 설정합니다.

        Args:
            model_info: 모델 정보 객체

        Raises:
            InvalidModelProviderError: OpenRouter에서 지원하지 않는 모델인 경우
            UnsupportedModelError:
                OpenRouter에서 지원하지 않는 기능을 사용하는 모델인 경우
        """
        # OpenRouter를 통해 사용 가능한 모델인지 확인
        # 1. provider가 openrouter이거나 anthropic(Claude 모델)인 경우 허용
        # 2. openrouter_name 필드가 있는 모델은 허용
        if not model_info.get("openrouter_name"):
            console.warning(
                f"{model_info['full_name']}은(는) OpenRouter에서 "
                "지원하지 않는 모델입니다."
            )
            raise InvalidModelProviderError(
                model_info["full_name"], ModelProvider.OPENROUTER
            )

        # OpenRouter에서는 Claude 모델의 thinking 모드만 지원
        if model_info.get("thinking_mode", False):
            # Claude 모델이 아닌 경우 thinking 모드 지원하지 않음
            if model_info["provider"] != ModelProvider.ANTHROPIC:
                console.error(
                    f"OpenRouter는 {model_info['full_name']}의 thinking 모드를 "
                    "지원하지 않습니다"
                )
                console.info("해결 방법:")
                console.print("  1. claude-sonnet-4 사용")
                console.print("  2. ANTHROPIC_API_KEY 환경 변수 설정")
                raise UnsupportedModelError(
                    f"OpenRouter는 {model_info['full_name']}의 thinking 모드를 "
                    "지원하지 않습니다"
                )

        console.log_info(
            f"OpenRouter를 통한 모델 설정: {model_info['full_name']} - "
            f"{model_info['description']}"
        )
        self.model = model_info

    def _create_request_params(self, messages: list[dict[str, Any]]) -> RequestParams:
        """OpenRouter API 요청 파라미터를 생성합니다.

        Args:
            messages: 메시지 리스트

        Returns:
            dict: API 요청 파라미터
        """
        # OpenRouter는 OpenAI 호환 API를 제공하므로 유사한 형태로 구성
        # 모델명을 OpenRouter 형식으로 변환
        # (예: claude-sonnet-4 -> anthropic/claude-sonnet-4)
        openrouter_model_name = self._convert_to_openrouter_model_name(
            self.model["full_name"]
        )

        # 기본 파라미터 설정
        params = {
            "model": openrouter_model_name,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_review_response",
                    "strict": True,
                    "schema": self._get_json_schema(),
                },
            },
            "usage": {
                "include": True,
            },
        }

        # 모델별 파라미터 설정
        model_params = self.model["params"].copy()

        # thinking 파라미터 처리 (Claude 모델용)
        thinking_config = model_params.pop("thinking", None)
        if thinking_config and self._is_claude_model(openrouter_model_name):
            # Claude의 thinking 파라미터를 OpenRouter의 reasoning 형식으로 변환
            budget_tokens = thinking_config.get("budget_tokens")
            if budget_tokens:
                params["reasoning"] = {"max_tokens": budget_tokens}
                console.log_info(f"확장 사고 모드 활성화: max_tokens={budget_tokens}")

        params.update(model_params)

        return params

    def _convert_to_openrouter_model_name(self, selvage_model_name: str) -> str:
        """Selvage 모델명을 OpenRouter 형식으로 변환합니다.

        Args:
            selvage_model_name: Selvage에서 사용하는 모델명

        Returns:
            str: OpenRouter 형식의 모델명
        """
        # models.yml에서 openrouter_name 필드 확인
        openrouter_name = self.model.get("openrouter_name")
        if openrouter_name:
            return openrouter_name

        # openrouter_name이 설정되지 않은 경우 원래 모델명 반환
        return selvage_model_name

    def _get_json_schema(self) -> dict:
        """OpenRouter에서 사용할 JSON Schema를 생성합니다.

        Returns:
            dict: JSON Schema (Pydantic ConfigDict로 additionalProperties 자동 처리)
        """
        return StructuredReviewResponse.model_json_schema()

    def _is_claude_model(self, model_name: str) -> bool:
        """OpenRouter 모델명이 Claude 모델인지 확인합니다.

        Args:
            model_name: OpenRouter 형식의 모델명

        Returns:
            bool: Claude 모델이면 True, 아니면 False
        """
        return model_name.startswith("anthropic/claude")

    def _create_client(self) -> OpenRouterHTTPClient:
        """OpenRouter API 클라이언트를 생성합니다.

        OpenRouter의 확장 파라미터(reasoning 등)를 지원하는
        사용자 정의 HTTP 클라이언트를 반환합니다.

        Returns:
            OpenRouterHTTPClient: OpenRouter API 클라이언트
        """
        return OpenRouterHTTPClient(self.api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(
            (
                OpenRouterResponseError,
                OpenRouterConnectionError,
                ConnectionError,
                TimeoutError,
            )
        ),
        before_sleep=before_sleep_log(console.logger, log_level="INFO"),
        after=after_log(console.logger, log_level="DEBUG"),
    )
    def review_code(self, review_prompt: ReviewPromptWithFileContent) -> ReviewResult:
        """OpenRouter API를 사용하여 코드를 리뷰합니다.

        Args:
            review_prompt: 리뷰용 프롬프트 객체

        Returns:
            ReviewResult: 리뷰 결과

        Raises:
            Exception: API 호출 중 오류가 발생한 경우
        """
        messages = review_prompt.to_messages()

        # estimated_cost 변수를 미리 초기화하여 예외 발생 시에도 안전하게 사용
        estimated_cost = EstimatedCost.get_zero_cost(self.get_model_name())

        try:
            # 클라이언트 초기화 및 컨텍스트 매니저 사용
            with self._create_client() as client:
                # API 요청 파라미터 생성
                params = self._create_request_params(messages)

                # OpenRouter API 호출
                raw_response_data = client.create_completion(**params)

                # 응답을 OpenAI SDK 형식으로 변환
                raw_api_response = OpenRouterResponse.from_dict(raw_response_data)

                # API 응답 검증 및 텍스트 추출
                self._validate_api_response(raw_api_response, raw_response_data)
                response_text = self._extract_response_content(
                    raw_api_response, raw_response_data
                )

                # JSON 파싱
                structured_response = JSONExtractor.validate_and_parse_json(
                    response_text, StructuredReviewResponse
                )

                # 구조화된 응답 검증
                self._validate_structured_response(structured_response, response_text)

                # 비용 계산 - OpenRouter usage에서 cost 정보 추출
                usage = raw_api_response.usage
                if usage and usage.cost > 0:
                    estimated_cost = EstimatedCost(
                        model=self.get_model_name(),
                        input_tokens=usage.prompt_tokens,
                        input_cost_usd=0.0,  # OpenRouter는 세분화된 비용 미제공
                        output_tokens=usage.completion_tokens,
                        output_cost_usd=0.0,  # OpenRouter는 세분화된 비용 미제공
                        total_cost_usd=usage.cost,
                    )
                else:
                    # usage 정보가 없거나 cost가 0인 경우 0 비용 반환
                    estimated_cost = EstimatedCost.get_zero_cost(self.get_model_name())

                # ReviewResponse 생성
                review_response = ReviewResponse.from_structured_response(
                    structured_response
                )

                return ReviewResult(
                    review_response=review_response,
                    estimated_cost=estimated_cost,
                )

        except Exception as e:
            console.error(f"OpenRouter API 호출 중 오류 발생: {str(e)}", exception=e)
            return ReviewResult.get_error_result(
                e, self.get_model_name(), self.get_provider().value
            )

    def _validate_api_response(
        self, raw_api_response: OpenRouterResponse, raw_response_data: dict
    ) -> None:
        """OpenRouter API 응답의 기본 구조를 검증합니다.

        Args:
            raw_api_response: 파싱된 응답 객체
            raw_response_data: 원본 응답 데이터

        Raises:
            OpenRouterResponseError: choices가 없는 경우
        """
        if not raw_api_response.choices:
            error_msg = "OpenRouter API 응답에 choices가 없습니다"
            console.error(error_msg)
            if console.is_debug_mode():
                console.error(f"원본 응답: {raw_response_data}")
            raise OpenRouterResponseError(
                error_msg, raw_response=raw_response_data, missing_field="choices"
            )

    def _extract_response_content(
        self, raw_api_response: OpenRouterResponse, raw_response_data: dict
    ) -> str:
        """응답에서 텍스트 내용을 추출하고 검증합니다.

        Args:
            raw_api_response: 파싱된 응답 객체
            raw_response_data: 원본 응답 데이터

        Returns:
            str: 추출된 응답 텍스트

        Raises:
            OpenRouterResponseError: content가 없는 경우
        """
        response_text = raw_api_response.choices[0].message.content
        if not response_text:
            error_msg = "OpenRouter API 응답에 content가 없습니다"
            console.error(error_msg)
            if console.is_debug_mode():
                console.error(f"원본 응답: {raw_response_data}")
            raise OpenRouterResponseError(
                error_msg, raw_response=raw_response_data, missing_field="content"
            )
        return response_text

    def _validate_structured_response(
        self, structured_response: StructuredReviewResponse | None, response_text: str
    ) -> None:
        """구조화된 응답의 유효성을 검증합니다.

        Args:
            structured_response: 파싱된 구조화된 응답
            response_text: 원본 응답 텍스트

        Raises:
            OpenRouterResponseError: 구조화된 응답이 None인 경우
        """
        if structured_response is None:
            error_msg = "OpenRouter API 응답에서 유효한 JSON을 파싱할 수 없습니다"
            console.error(error_msg)
            console.error(f"원본 응답: {response_text}")
            raise OpenRouterResponseError(error_msg)
