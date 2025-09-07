"""Google Gemini API를 사용하는 LLM 게이트웨이"""

from typing import Any

from selvage.src.exceptions.api_key_not_found_error import APIKeyNotFoundError
from selvage.src.exceptions.invalid_model_provider_error import (
    InvalidModelProviderError,
)
from selvage.src.llm_gateway.base_gateway import BaseGateway
from selvage.src.model_config import ModelInfoDict
from selvage.src.models.model_provider import ModelProvider
from selvage.src.utils.base_console import console
from selvage.src.utils.token.models import StructuredReviewResponse

from . import get_api_key


class GoogleGateway(BaseGateway):
    """Google Gemini API를 사용하는 LLM 게이트웨이"""

    def _load_api_key(self) -> str:
        """Google API 키를 로드합니다.

        Returns:
            str: API 키

        Raises:
            APIKeyNotFoundError: API 키가 설정되지 않은 경우
        """
        api_key = get_api_key(ModelProvider.GOOGLE)
        if not api_key:
            console.error("Cannot find Google API key")
            raise APIKeyNotFoundError(ModelProvider.GOOGLE)
        return api_key

    def _set_model(self, model_info: ModelInfoDict) -> None:
        """사용할 모델을 설정합니다.

        Args:
            model_info: 모델 정보 객체

        Raises:
            InvalidModelProviderError: Google 모델이 아닌 경우
        """
        if model_info["provider"] != ModelProvider.GOOGLE:
            console.warning(f"{model_info['full_name']} is not a Google model.")
            raise InvalidModelProviderError(
                model_info["full_name"], ModelProvider.GOOGLE
            )
        else:
            console.log_info(
                f"모델 설정: {model_info['full_name']} - {model_info['description']}"
            )
            self.model = model_info

    def _create_request_params(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Google Gemini API 요청 파라미터를 생성합니다.

        Args:
            messages: 메시지 리스트

        Returns:
            dict: API 요청 파라미터
        """
        system_prompt = None
        contents = []

        # 시스템 프롬프트와 유저 메시지 구분
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")

            if role == "system":
                system_prompt = content
            elif role == "user":
                contents.append(content)

        # 온도 설정 (기본값: 0.0)
        temperature = self.model["params"].get("temperature", 0.0)

        # config 생성
        from google.genai import types

        generation_config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=StructuredReviewResponse,
        )

        # Gemini API 요청 파라미터 생성
        params = {
            "model": self.model["full_name"],
            "contents": "\n\n".join(contents) if contents else "",
            "config": generation_config,
        }

        return params
