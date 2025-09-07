"""OpenAI API를 사용하는 LLM 게이트웨이"""

from typing import Any

from selvage.src.exceptions.api_key_not_found_error import APIKeyNotFoundError
from selvage.src.exceptions.invalid_model_provider_error import (
    InvalidModelProviderError,
)
from selvage.src.llm_gateway.base_gateway import BaseGateway
from selvage.src.model_config import ModelInfoDict
from selvage.src.models.model_provider import ModelProvider
from selvage.src.utils.base_console import console

from . import get_api_key


class OpenAIGateway(BaseGateway):
    """OpenAI API를 사용하는 LLM 게이트웨이"""

    def _load_api_key(self) -> str:
        """OpenAI API 키를 로드합니다.

        Returns:
            str: API 키

        Raises:
            APIKeyNotFoundError: API 키가 설정되지 않은 경우
        """
        api_key = get_api_key(ModelProvider.OPENAI)
        if not api_key:
            console.error("Cannot find OpenAI API key")
            raise APIKeyNotFoundError(ModelProvider.OPENAI)
        return api_key

    def _set_model(self, model_info: ModelInfoDict) -> None:
        """사용할 모델을 설정합니다.

        Args:
            model_info: model_info 객체

        Raises:
            InvalidModelProviderError: OpenAI 모델이 아닌 경우
        """
        if model_info["provider"] != ModelProvider.OPENAI:
            console.warning(f"{model_info['full_name']} is not an OpenAI model.")

            raise InvalidModelProviderError(
                model_info["full_name"], ModelProvider.OPENAI
            )

        console.log_info(
            f"모델 설정: {model_info['full_name']} - {model_info['description']}"
        )
        self.model = model_info

    def _create_request_params(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """OpenAI API 요청 파라미터를 생성합니다.

        Args:
            messages: 메시지 리스트

        Returns:
            dict: API 요청 파라미터
        """
        # 기본 파라미터 설정
        params = {
            "model": self.get_model_name(),
            "messages": messages,
        }

        # 모델별 파라미터 설정
        model_params = self.model["params"]
        params.update(model_params)

        return params
