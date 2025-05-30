"""
Claude 게이트웨이 구현입니다.
"""

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


class ClaudeGateway(BaseGateway):
    """Anthropic API를 사용하는 LLM 게이트웨이"""

    def _load_api_key(self) -> str:
        """Anthropic API 키를 로드합니다.

        Returns:
            str: API 키

        Raises:
            APIKeyNotFoundError: API 키가 설정되지 않은 경우
        """
        api_key = get_api_key(ModelProvider.ANTHROPIC)
        if not api_key:
            console.error("Anthropic API 키를 찾을 수 없습니다")
            raise APIKeyNotFoundError(ModelProvider.ANTHROPIC)
        return api_key

    def _set_model(self, model_info: ModelInfoDict) -> None:
        """사용할 모델을 설정합니다.

        Args:
            model_info: 모델 정보 객체

        Raises:
            InvalidModelProviderError: Claude 모델이 아닌 경우
        """
        if model_info["provider"] != ModelProvider.ANTHROPIC:
            console.warning(f"{model_info['full_name']}은(는) Claude 모델이 아닙니다.")
            raise InvalidModelProviderError(
                model_info["full_name"], ModelProvider.ANTHROPIC
            )
        else:
            console.log_info(
                f"모델 설정: {model_info['full_name']} - {model_info['description']}"
            )
            self.model = model_info

    def _create_request_params(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Anthropic API 요청 파라미터를 생성합니다.

        Args:
            messages: 메시지 리스트

        Returns:
            dict: API 요청 파라미터
        """
        # Anthropic API 요청 파라미터 생성 중 (디버그 로그 제거)

        # thinking 모드인 경우 system 메시지를 별도 처리
        if self.model.get("thinking_mode", False):
            # system 메시지와 일반 메시지 분리
            system_message = None
            user_messages = []

            for message in messages:
                if message.get("role") == "system":
                    system_message = message.get("content", "")
                else:
                    user_messages.append(message)

            # 기본 파라미터 설정
            params = {
                "model": self.get_model_name(),
                "messages": user_messages,
                "max_tokens": 48000,  # thinking 모드에서 더 긴 응답을 위한 토큰 제한 증가
            }

            # system 메시지가 있으면 별도 파라미터로 추가
            if system_message:
                params["system"] = system_message
        else:
            # 일반 모드 (instructor 사용)
            params = {
                "model": self.get_model_name(),
                "messages": messages,
                "max_tokens": 8192,
            }

        # 모델별 파라미터 설정
        model_params = self.model["params"]
        params.update(model_params)

        return params
