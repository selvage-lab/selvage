"""OpenRouter API 응답 모델들

OpenRouter API 응답을 OpenAI SDK 형식으로 변환하는 Pydantic 모델들을 정의합니다.
"""

from typing import Any

from pydantic import BaseModel, Field

from selvage.src.utils.base_console import console


class OpenRouterUsage(BaseModel):
    """OpenRouter API 응답의 usage를 OpenAI SDK 형식으로 변환하는 Pydantic 모델"""
    
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


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
            console.error(f"OpenRouter 응답 파싱 오류: {e}")
            console.error(f"원본 응답: {response_data}")
            # 빈 응답 반환 (기본값들로 구성)
            return cls()