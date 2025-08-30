"""합성 API 관련 타입 정의 모듈"""

from typing import Any, TypeVar

import anthropic
import instructor
import openai
from anthropic import Anthropic
from google import genai
from google.genai import types as genai_types
from pydantic import BaseModel

from selvage.src.llm_gateway.openrouter.http_client import OpenRouterHTTPClient

# 제네릭 타입 변수 정의
T = TypeVar("T", bound=BaseModel)

# API 응답 타입 정의
ApiResponseType = (
    openai.types.Completion
    | anthropic.types.Message
    | genai_types.GenerateContentResponse
    | dict[str, Any]
)

# 클라이언트 타입 정의 (LLMClientFactory 반환 타입과 일치)
ClientType = instructor.Instructor | genai.Client | Anthropic | OpenRouterHTTPClient
