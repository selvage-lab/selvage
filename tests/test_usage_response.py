"""
instructor를 사용하여 LLM API의 usage 정보를 확인하는 테스트 코드입니다.

이 테스트는 OpenAI와 Claude API에서 다음을 확인합니다:
1. instructor의 create_with_completion 메서드를 사용한 구조화된 응답 추출
2. 원본 응답(raw completion) 객체 구조 비교
3. 각 API의 usage 정보 비교

## OpenAI와 Claude의 usage 정보 차이
- OpenAI: prompt_tokens, completion_tokens, total_tokens 필드 제공
- Claude: input_tokens, output_tokens 필드 제공

## 실행 방법
API 키를 환경 변수로 설정한 후 실행:
```
export OPENAI_API_KEY=your_openai_key
export ANTHROPIC_API_KEY=your_anthropic_key
python -m tests.test_usage_response
```
"""

import anthropic
import instructor
import openai
import pytest
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from selvage.src.config import get_api_key
from selvage.src.model_config import ModelProvider


class SimpleResponse(BaseModel):
    """간단한 구조화된 응답 모델"""

    content: str
    items: list[str]
    score: float | None = None


@pytest.mark.skip(reason="핵심 테스트 모듈이 아님")
def test_openai_instructor_usage():
    """OpenAI API의 usage 정보를 assert로 검증합니다."""
    openai_api_key = get_api_key(ModelProvider.OPENAI)
    client = openai.OpenAI(api_key=openai_api_key)
    instructor_client = instructor.from_openai(client)
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": "당신은 유용한 AI 어시스턴트입니다."},
        {
            "role": "user",
            "content": "다음 항목을 포함하는 구조화된 응답을 생성해주세요: 1. 오늘의 날씨에 대한 내용, 2. 추천 활동 목록 3개",
        },
    ]
    structured_response, raw_response = (
        instructor_client.chat.completions.create_with_completion(
            model="gpt-3.5-turbo",
            response_model=SimpleResponse,
            messages=messages,
            max_retries=2,
        )
    )
    assert hasattr(raw_response, "usage"), "OpenAI 응답에 usage 필드가 없습니다."
    usage = raw_response.usage
    assert isinstance(
        usage, openai.types.CompletionUsage
    ), f"OpenAI usage 타입이 다릅니다: {type(usage)}"
    for field in ["prompt_tokens", "completion_tokens", "total_tokens"]:
        assert hasattr(usage, field), f"OpenAI usage에 {field} 필드가 없습니다."


@pytest.mark.skip(reason="핵심 테스트 모듈이 아님")
def test_claude_instructor_usage():
    """Claude API의 usage 정보를 assert로 검증합니다."""
    claude_api_key = get_api_key(ModelProvider.ANTHROPIC)
    client = anthropic.Anthropic(api_key=claude_api_key)
    instructor_client = instructor.from_anthropic(client)
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": "당신은 유용한 AI 어시스턴트입니다."},
        {
            "role": "user",
            "content": "다음 항목을 포함하는 구조화된 응답을 생성해주세요: 1. 오늘의 날씨에 대한 내용, 2. 추천 활동 목록 3개",
        },
    ]
    structured_response, raw_response = (
        instructor_client.messages.create_with_completion(
            model="claude-3-haiku-20240307",
            response_model=SimpleResponse,
            messages=messages,
            max_tokens=1000,
            max_retries=2,
        )
    )
    assert hasattr(raw_response, "usage"), "Claude 응답에 usage 필드가 없습니다."
    usage = raw_response.usage
    assert isinstance(
        usage, anthropic.types.Usage
    ), f"Claude usage 타입이 다릅니다: {type(usage)}"
    for field in ["input_tokens", "output_tokens"]:
        assert hasattr(usage, field), f"Claude usage에 {field} 필드가 없습니다."


@pytest.mark.skip(reason="핵심 테스트 모듈이 아님")
def test_gemini_usage():
    """Gemini(Google) API의 usage 정보를 assert로 검증합니다."""
    try:
        from google import genai
    except ImportError:
        pytest.skip("google-genai 패키지가 설치되어 있지 않습니다.")
    gemini_api_key = get_api_key(ModelProvider.GOOGLE)
    client = genai.Client(api_key=gemini_api_key)
    model = "gemini-1.5-flash-latest"
    prompt = "오늘의 날씨와 추천 활동 3가지를 알려줘."
    params = {
        "model": model,
        "contents": prompt,
        "config": {
            "max_output_tokens": 256,
        },
    }

    print("Gemini API 요청 중...")
    response = client.models.generate_content(**params)
    usage = getattr(response, "usage_metadata", None)
    assert usage is not None, "Gemini 응답에 usage_metadata가 없습니다."
    for field in [
        "total_token_count",
        "prompt_token_count",
        "candidates_token_count",
        "cached_content_token_count",
    ]:
        assert hasattr(
            usage, field
        ), f"Gemini usage_metadata에 {field} 필드가 없습니다."


if __name__ == "__main__":
    print("OpenAI API 테스트 시작...")
    test_openai_instructor_usage()

    print("\n" + "=" * 50 + "\n")

    print("Anthropic API 테스트 시작...")
    test_claude_instructor_usage()

    print("\n" + "=" * 50 + "\n")

    print("Gemini API 테스트 시작...")
    test_gemini_usage()
