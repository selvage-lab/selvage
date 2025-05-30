"""
베이스 게이트웨이 클래스를 정의하는 모듈입니다.
"""

from __future__ import annotations

import abc
from collections.abc import Callable
from typing import Any

import anthropic
import google.genai.types as genai_types
import instructor
import openai
from google import genai

from selvage.src.exceptions.context_limit_exceeded_error import (
    ContextLimitExceededError,
)
from selvage.src.model_config import ModelInfoDict
from selvage.src.models.model_provider import ModelProvider
from selvage.src.models.review_result import ReviewResult
from selvage.src.utils.base_console import console
from selvage.src.utils.json_extractor import JSONExtractor
from selvage.src.utils.llm_client_factory import LLMClientFactory
from selvage.src.utils.prompts.models import ReviewPrompt, ReviewPromptWithFileContent
from selvage.src.utils.token import CostEstimator
from selvage.src.utils.token.models import (
    EstimatedCost,
    ReviewResponse,
    StructuredReviewResponse,
)
from selvage.src.utils.token.token_utils import TokenUtils


class BaseGateway(abc.ABC):
    """LLM 게이트웨이의 추상 기본 클래스"""

    @staticmethod
    def _handle_openai_cost_estimation(resp: Any, model: str) -> EstimatedCost | None:
        if (
            isinstance(resp, openai.types.Completion)
            and hasattr(resp, "usage")
            and resp.usage
        ):
            return CostEstimator.estimate_cost_from_openai_usage(model, resp.usage)
        return None

    @staticmethod
    def _handle_claude_cost_estimation(resp: Any, model: str) -> EstimatedCost | None:
        if (
            isinstance(resp, anthropic.types.Message)
            and hasattr(resp, "usage")
            and resp.usage
        ):
            return CostEstimator.estimate_cost_from_anthropic_usage(model, resp.usage)
        return None

    @staticmethod
    def _handle_google_cost_estimation(resp: Any, model: str) -> EstimatedCost | None:
        if (
            isinstance(resp, genai_types.GenerateContentResponse)
            and hasattr(resp, "usage_metadata")
            and resp.usage_metadata
        ):
            return CostEstimator.estimate_cost_from_gemini_usage(
                model, resp.usage_metadata
            )
        return None

    provider_handlers: dict[
        ModelProvider, Callable[[Any, str], EstimatedCost | None]
    ] = {
        ModelProvider.OPENAI: _handle_openai_cost_estimation,
        ModelProvider.ANTHROPIC: _handle_claude_cost_estimation,
        ModelProvider.GOOGLE: _handle_google_cost_estimation,
    }

    def __init__(self, model_info: ModelInfoDict) -> None:
        """
        Args:
            model_info: 모델 정보 객체
        """
        self.model: ModelInfoDict
        self._set_model(model_info)
        self.api_key = self._load_api_key()

    @abc.abstractmethod
    def _load_api_key(self) -> str:
        """Provider에 맞는 API 키를 로드합니다."""
        raise NotImplementedError

    @abc.abstractmethod
    def _set_model(self, model_info: ModelInfoDict) -> None:
        """사용할 모델을 설정하고 유효성을 검사합니다."""
        raise NotImplementedError

    @abc.abstractmethod
    def _create_request_params(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """
        각 프로바이더별 API 요청 파라미터를 생성합니다.
        각 하위 클래스는 해당 LLM 프로바이더에 맞는 파라미터를 구성해야 합니다.

        Args:
            messages: 메시지 리스트

        Returns:
            dict: API 요청 파라미터
        """
        raise NotImplementedError

    def get_model_name(self) -> str:
        """현재 설정된 모델의 전체 이름을 반환합니다."""
        return self.model["full_name"]

    def get_provider(self) -> ModelProvider:
        """현재 설정된 모델의 프로바이더를 반환합니다."""
        return self.model["provider"]

    def _create_client(
        self,
    ) -> instructor.Instructor | genai.Client | anthropic.Anthropic:
        """현재 프로바이더에 맞는 LLM 클라이언트를 생성합니다.

        Returns:
            instructor.Instructor | genai.Client | anthropic.Anthropic: 구조화된 응답을 지원하는 LLM 클라이언트
        """
        return LLMClientFactory.create_client(
            self.get_provider(), self.api_key, self.model
        )

    def estimate_cost(
        self,
        raw_response: openai.types.Completion
        | anthropic.types.Message
        | genai_types.GenerateContentResponse,
    ) -> EstimatedCost:
        """API 응답의 usage 정보를 이용하여 비용을 계산합니다.

        Args:
            raw_response: API 응답 객체

        Returns:
            EstimatedCostFromUsage: 비용 추정 정보 객체
        """
        model_name = self.get_model_name()
        provider = self.get_provider()

        if provider in self.provider_handlers:
            result = self.provider_handlers[provider](raw_response, model_name)
            if result:
                return result

        # usage 정보가 없는 경우 빈 응답 반환
        console.warning(
            f"Usage 정보를 찾을 수 없습니다: {provider} 모델 {model_name}. 0 비용으로 출력합니다."
        )
        return EstimatedCost.get_zero_cost(model_name)

    def validate_review_request(
        self, review_prompt: ReviewPrompt | ReviewPromptWithFileContent
    ) -> None:
        """리뷰 요청 전 유효성 검사를 수행합니다.
          input_token_count와 context_limit 을 비교하여 컨텍스트 제한을 초과한 경우 예외를 발생시킵니다.
        Args:
            review_prompt: 리뷰 프롬프트 객체

        Returns:
            None

        Raises:
            ContextLimitExceededError: 컨텍스트 제한을 초과한 경우
        """
        input_token_count = TokenUtils.count_tokens(
            review_prompt, self.get_model_name()
        )
        # input_token_count는 디버깅 정보이므로 사용자에게 표시하지 않음
        context_limit = TokenUtils.get_model_context_limit(self.get_model_name())
        if input_token_count > context_limit:
            raise ContextLimitExceededError(
                input_tokens=input_token_count,
                context_limit=context_limit,
            )

    def review_code(
        self, review_prompt: ReviewPrompt | ReviewPromptWithFileContent
    ) -> ReviewResult:
        """코드를 리뷰합니다.

        Args:
            review_prompt: 리뷰용 프롬프트 객체

        Returns:
            ReviewResult: 리뷰 결과

        Raises:
            Exception: API 호출 중 오류가 발생한 경우
        """
        # 요청 준비
        try:
            self.validate_review_request(review_prompt)
        except ContextLimitExceededError as e:
            console.error(f"컨텍스트 제한 초과: {str(e)}", exception=e)
            return ReviewResult.get_error_result(e, self.get_model_name())
        messages = review_prompt.to_messages()

        try:
            # 클라이언트 초기화
            client = self._create_client()

            # API 요청 파라미터 생성
            params = self._create_request_params(messages)

            # API 요청 송신
            if isinstance(client, instructor.Instructor):
                structured_response, raw_api_response = (
                    client.chat.completions.create_with_completion(
                        response_model=StructuredReviewResponse, max_retries=2, **params
                    )
                )
            elif isinstance(client, genai.Client):
                try:
                    raw_api_response = client.models.generate_content(**params)
                    response_text = raw_api_response.text
                    if response_text is None:
                        return ReviewResult.get_empty_result(self.get_model_name())

                    structured_response = StructuredReviewResponse.model_validate_json(
                        response_text
                    )
                except Exception as parse_error:
                    console.error(
                        f"응답 파싱 오류: {str(parse_error)}", exception=parse_error
                    )
                    return ReviewResult.get_error_result(
                        parse_error, self.get_model_name()
                    )
            elif isinstance(client, anthropic.Anthropic):
                try:
                    raw_api_response = client.messages.create(**params)
                    response_text = None
                    for block in raw_api_response.content:
                        if block.type == "text":
                            response_text = block.text

                    if response_text is None:
                        return ReviewResult.get_empty_result(self.get_model_name())

                    structured_response = JSONExtractor.validate_and_parse_json(
                        response_text, StructuredReviewResponse
                    )

                    if structured_response is None:
                        return ReviewResult.get_empty_result(self.get_model_name())

                except Exception as parse_error:
                    console.error(
                        f"응답 파싱 오류: {str(parse_error)}", exception=parse_error
                    )
                    return ReviewResult.get_error_result(
                        parse_error, self.get_model_name()
                    )

            # 응답 처리
            if not structured_response:
                return ReviewResult.get_empty_result(self.get_model_name())

            return ReviewResult(
                review_response=ReviewResponse.from_structured_response(
                    structured_response
                ),
                estimated_cost=self.estimate_cost(raw_api_response),
            )

        except Exception as e:
            console.error(f"리뷰 요청 중 오류 발생: {str(e)}", exception=e)
            return ReviewResult.get_error_result(e, self.get_model_name())
