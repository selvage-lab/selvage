"""
OpenRouter 게이트웨이 구현입니다.
"""

import os
from typing import Any

import instructor
from openai import OpenAI

from selvage.src.exceptions.api_key_not_found_error import APIKeyNotFoundError
from selvage.src.exceptions.invalid_model_provider_error import (
    InvalidModelProviderError,
)
from selvage.src.exceptions.unsupported_model_error import UnsupportedModelError
from selvage.src.llm_gateway.base_gateway import BaseGateway
from selvage.src.model_config import ModelInfoDict
from selvage.src.models.model_provider import ModelProvider
from selvage.src.utils.base_console import console


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
            InvalidModelProviderError: Claude 모델이 아닌 경우
            UnsupportedModelError: OpenRouter에서 지원하지 않는 기능을 사용하는 모델인 경우
        """
        # OpenRouter를 통해 Claude 모델을 사용하므로 원래 provider가 anthropic이어야 함
        if model_info["provider"] != ModelProvider.ANTHROPIC:
            console.warning(f"{model_info['full_name']}은(는) Claude 모델이 아닙니다.")
            raise InvalidModelProviderError(
                model_info["full_name"], ModelProvider.ANTHROPIC
            )

        # OpenRouter에서는 thinking 모드를 지원하지 않음
        if model_info.get("thinking_mode", False):
            console.error(
                f"OpenRouter는 thinking 모드를 지원하지 않습니다: {model_info['full_name']}"
            )
            console.info("해결 방법:")
            console.print(
                "  1. Anthropic 직접 사용: selvage config claude-provider anthropic"
            )
            console.print("  2. 일반 Claude 모델 사용: --model claude-sonnet-4")
            raise UnsupportedModelError(
                f"OpenRouter는 thinking 모드를 지원하지 않습니다: {model_info['full_name']}"
            )

        console.log_info(
            f"OpenRouter를 통한 모델 설정: {model_info['full_name']} - {model_info['description']}"
        )
        self.model = model_info

    def _create_request_params(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """OpenRouter API 요청 파라미터를 생성합니다.

        Args:
            messages: 메시지 리스트

        Returns:
            dict: API 요청 파라미터
        """
        # OpenRouter는 OpenAI 호환 API를 제공하므로 유사한 형태로 구성
        # 모델명을 OpenRouter 형식으로 변환 (예: claude-sonnet-4 -> anthropic/claude-sonnet-4)
        openrouter_model_name = self._convert_to_openrouter_model_name(
            self.model["full_name"]
        )

        # 기본 파라미터 설정
        params = {
            "model": openrouter_model_name,
            "messages": messages,
            "max_tokens": 8192,
        }

        # 모델별 파라미터 설정
        model_params = self.model["params"].copy()
        params.update(model_params)

        return params

    def _convert_to_openrouter_model_name(self, selvage_model_name: str) -> str:
        """Selvage 모델명을 OpenRouter 형식으로 변환합니다.

        Args:
            selvage_model_name: Selvage에서 사용하는 모델명

        Returns:
            str: OpenRouter 형식의 모델명
        """
        # Claude 모델명 매핑 테이블
        model_mapping = {
            "claude-sonnet-4-20250514": "anthropic/claude-sonnet-4",
            "claude-sonnet-4": "anthropic/claude-sonnet-4",  # alias 지원
        }

        return model_mapping.get(selvage_model_name, selvage_model_name)

    def _create_client(self) -> instructor.Instructor:
        """OpenRouter API 클라이언트를 생성합니다.

        OpenAI SDK를 사용하되 base_url을 OpenRouter로 변경하고,
        instructor로 래핑하여 구조화된 응답을 지원합니다.

        Returns:
            instructor.Instructor: 구조화된 응답을 지원하는 클라이언트
        """
        openai_client = OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        return instructor.from_openai(openai_client)
