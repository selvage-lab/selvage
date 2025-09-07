"""OpenRouter API 응답 모델들

OpenRouter API 응답을 OpenAI SDK 형식으로 변환하는 Pydantic 모델들을 정의합니다.
"""

from typing import Any

from pydantic import BaseModel, Field

from selvage.src.utils.base_console import console


class OpenRouterCostDetails(BaseModel):
    """OpenRouter API 응답의 cost_details"""

    upstream_inference_cost: float | None = None


class OpenRouterTokenDetails(BaseModel):
    """OpenRouter API 응답의 토큰 세부 정보"""

    reasoning_tokens: int | None = None
    cached_tokens: int | None = None


class OpenRouterUsage(BaseModel):
    """OpenRouter API 응답의 usage를 OpenAI SDK 형식으로 변환하는 Pydantic 모델"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    is_byok: bool = False
    cost_details: OpenRouterCostDetails | None = None
    completion_tokens_details: OpenRouterTokenDetails | None = None
    prompt_tokens_details: OpenRouterTokenDetails | None = None


class OpenRouterMessage(BaseModel):
    """OpenRouter API 응답의 message를 OpenAI SDK 형식으로 변환하는 Pydantic 모델"""

    content: str = ""
    role: str = "assistant"


class OpenRouterChoice(BaseModel):
    """OpenRouter API 응답의 choice를 OpenAI SDK 형식으로 변환하는 Pydantic 모델"""

    message: OpenRouterMessage
    finish_reason: str = ""


class OpenRouterResponse(BaseModel):
    """OpenRouter API 응답을 OpenAI SDK 형식으로 변환하는 Pydantic 모델"""

    choices: list[OpenRouterChoice] = Field(default_factory=list)
    usage: OpenRouterUsage = Field(default_factory=OpenRouterUsage)
    model: str = ""

    @classmethod
    def from_dict(cls, response_data: dict[str, Any]) -> "OpenRouterResponse":
        """딕셔너리에서 OpenRouterResponse 인스턴스를 생성합니다.

        Args:
            response_data: OpenRouter API 응답 딕셔너리

        Returns:
            OpenRouterResponse: 변환된 응답 객체
        """
        try:
            return cls.model_validate(response_data)
        except Exception as e:
            console.error(f"OpenRouter response parsing error: {e}")
            console.error(f"Raw response: {response_data}")
            # 빈 응답 반환 (기본값들로 구성)
            return cls()
