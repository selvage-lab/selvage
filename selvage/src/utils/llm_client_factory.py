"""
LLM 클라이언트 팩토리 모듈입니다.
"""

import instructor
from anthropic import Anthropic
from google import genai

from selvage.src.model_config import ModelInfoDict
from selvage.src.models.model_provider import ModelProvider

ANTHROPIC_THINKING_MODE_TIMEOUT_SECONDS = 600.0


class LLMClientFactory:
    """LLM 클라이언트 팩토리 클래스"""

    @staticmethod
    def create_client(
        provider: ModelProvider, api_key: str, model_info: ModelInfoDict
    ) -> instructor.Instructor | genai.Client | Anthropic | object:
        """프로바이더에 맞는, 구조화된 응답을 지원하는 클라이언트를 생성합니다.

        Args:
            provider: LLM 프로바이더 (openai, anthropic, google, openrouter)
            api_key: API 키
            model_info: 모델 정보 객체

        Returns:
            instructor.Instructor: instructor 래핑된 LLM 클라이언트
            genai.Client: Google Gemini 클라이언트
            Anthropic: Claude thinking 모드용 직접 클라이언트
            object: OpenRouter HTTP 클라이언트(지연 로딩)
        Raises:
            ValueError: 지원하지 않는 프로바이더인 경우
        """
        if provider == ModelProvider.OPENAI:
            from openai import OpenAI

            return instructor.from_openai(OpenAI(api_key=api_key))
        elif provider == ModelProvider.ANTHROPIC:
            # thinking 모드인 경우 instructor 사용 안 함
            if model_info.get("thinking_mode", False):
                return Anthropic(
                    api_key=api_key,
                    timeout=ANTHROPIC_THINKING_MODE_TIMEOUT_SECONDS,
                )
                # thinking 모드는 일반 호출보다 오래 걸릴 수 있어 넉넉한 타임아웃 적용
            else:
                return instructor.from_anthropic(Anthropic(api_key=api_key))
        elif provider == ModelProvider.GOOGLE:
            return genai.Client(api_key=api_key)
        elif provider == ModelProvider.OPENROUTER:
            # Lazy import to avoid circular dependency
            from selvage.src.llm_gateway.openrouter.http_client import (
                OpenRouterHTTPClient,
            )

            return OpenRouterHTTPClient(api_key=api_key)
        else:
            raise ValueError(f"지원하지 않는 LLM 프로바이더입니다: {provider}")
