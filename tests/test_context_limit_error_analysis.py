"""
Context Limit 에러 직접 API 응답 분석 테스트

각 LLM provider별로 context limit을 초과했을 때 실제 API에서 반환되는
원본 에러 응답을 직접 수집하고 분석하기 위한 테스트입니다.

실행 방법:
    pytest tests/test_context_limit_error_analysis.py -v -s

주의사항:
    - 실제 API를 호출하므로 비용이 발생할 수 있습니다
    - 각 provider의 API key가 환경변수로 설정되어야 합니다
"""

import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from selvage.src.llm_gateway.gateway_factory import GatewayFactory
from selvage.src.model_config import ModelInfoDict, ModelProvider


def create_oversized_messages(
    context_limit_tokens: int,
) -> list[dict[str, Any]]:
    """Context limit을 확실히 초과하는 매우 긴 메시지를 생성합니다."""
    # context limit의 200% 수준으로 설정하여 확실히 초과
    target_tokens = int(context_limit_tokens * 2.0)

    # 대략적인 토큰 계산: 평균적으로 1 토큰 = 4 글자로 가정
    chars_per_token = 4
    target_chars = target_tokens * chars_per_token

    # 매우 긴 코드 내용 생성
    base_code = """def complex_function_{index}(a, b, c, d, e, f):
    '''매우 복잡한 함수입니다'''
    result = 0
    for i in range(1000):
        temp = a * b + c * d - e * f
        result += temp * i
        if result > 10000:
            result = result % 10000
    return result

class DataProcessor_{index}:
    def __init__(self, data):
        self.data = data
        self.results = []
    
    def process(self):
        for item in self.data:
            processed = self.transform(item)
            self.results.append(processed)
    
    def transform(self, item):
        return {{
            'value': item.get('value', 0) * 2,
            'name': item.get('name', '').upper(),
            'processed_at': 'now'
        }}

"""

    # 긴 코드 내용 생성
    long_code = ""
    index = 0
    while len(long_code) < target_chars:
        long_code += base_code.format(index=index)
        index += 1

    return [
        {
            "role": "system",
            "content": "다음 코드를 자세히 리뷰해주세요. 모든 함수와 클래스에 대해 상세한 분석을 제공해주세요.",
        },
        {
            "role": "user",
            "content": f"다음은 분석할 코드입니다:\n\n```python\n{long_code}\n```\n\n위 코드에 대해 상세한 리뷰를 해주세요.",
        },
    ]


def create_anthropic_oversized_content(
    context_limit_tokens: int,
) -> tuple[str, list[dict[str, Any]]]:
    """Anthropic API용 system과 messages를 분리하여 생성합니다."""
    # context limit의 200% 수준으로 설정
    target_tokens = int(context_limit_tokens * 2.0)
    chars_per_token = 4
    target_chars = target_tokens * chars_per_token

    # 긴 코드 내용 생성
    base_code = """def complex_function_{index}(a, b, c, d, e, f):
    '''매우 복잡한 함수입니다'''
    result = 0
    for i in range(1000):
        temp = a * b + c * d - e * f
        result += temp * i
        if result > 10000:
            result = result % 10000
    return result

class DataProcessor_{index}:
    def __init__(self, data):
        self.data = data
        self.results = []

    def process(self):
        for item in self.data:
            processed = self.transform(item)
            self.results.append(processed)

    def transform(self, item):
        return {{
            'value': item.get('value', 0) * 2,
            'name': item.get('name', '').upper(),
            'processed_at': 'now'
        }}

"""

    long_code = ""
    index = 0
    while len(long_code) < target_chars:
        long_code += base_code.format(index=index)
        index += 1

    system_content = (
        "다음 코드를 자세히 리뷰해주세요. "
        "모든 함수와 클래스에 대해 상세한 분석을 제공해주세요."
    )

    messages = [
        {
            "role": "user",
            "content": (
                f"다음은 분석할 코드입니다:\n\n```python\n{long_code}\n```\n\n"
                "위 코드에 대해 상세한 리뷰를 해주세요."
            ),
        }
    ]

    return system_content, messages


def assert_context_limit_error(error: Exception, provider: str) -> None:
    """Context limit 에러가 올바른지 검증합니다."""
    error_message = str(error).lower()

    # 공통 키워드 검증
    context_keywords = ["context", "token", "limit", "exceed", "maximum"]
    assert any(keyword in error_message for keyword in context_keywords), (
        f"에러 메시지에 context limit 관련 키워드가 없습니다: {error}"
    )

    # Provider별 특화 검증
    if provider == "openai":
        assert hasattr(error, "response"), "OpenAI 에러에 response 속성이 없습니다"
        if hasattr(error, "response") and hasattr(error.response, "status_code"):
            assert error.response.status_code == 400, (
                f"예상 HTTP 상태코드 400, 실제: {error.response.status_code}"
            )

    elif provider == "anthropic":
        # Anthropic 특화 검증
        assert (
            "claude" in error_message
            or "anthropic" in error_message
            or "token" in error_message
        )

    elif provider == "google":
        # Google 특화 검증 - quota 또는 context 관련
        assert (
            "quota" in error_message
            or "context" in error_message
            or "token" in error_message
        )


@pytest.fixture
def models_config() -> dict[str, Any]:
    """models.yml에서 모델 설정을 로드하는 fixture"""
    models_yml_path = (
        Path(__file__).parent.parent / "selvage" / "resources" / "models.yml"
    )

    with open(models_yml_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config["models"]


def test_openai_context_limit_error() -> None:
    """OpenAI API의 context limit 에러를 검증합니다."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not found")

    model_info: ModelInfoDict = {
        "full_name": "gpt-4o",
        "aliases": [],
        "description": "Context limit test",
        "provider": ModelProvider.OPENAI,
        "params": {"temperature": 0.0},
        "thinking_mode": False,
        "pricing": {"input": 2.5, "output": 10.0, "description": "Test"},
        "context_limit": 128000,
    }

    with pytest.raises(Exception) as exc_info:
        gateway = GatewayFactory.create(model_info["full_name"])
        messages = create_oversized_messages(model_info["context_limit"])

        # 직접 클라이언트 생성 및 호출
        client = gateway._create_client()
        params = gateway._create_request_params(messages)

        # 직접 API 호출 (Instructor 클라이언트의 underlying client 접근)
        if hasattr(client, "client"):
            # Instructor 객체인 경우 underlying client 사용
            underlying_client = client.client
            underlying_client.chat.completions.create(**params)
        else:
            # 일반 OpenAI 클라이언트인 경우
            client.chat.completions.create(**params)

    # 에러 검증
    assert_context_limit_error(exc_info.value, "openai")


def test_anthropic_context_limit_error() -> None:
    """Anthropic API의 context limit 에러를 검증합니다."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not found")

    model_info: ModelInfoDict = {
        "full_name": "claude-sonnet-4-20250514",
        "aliases": ["claude-sonnet-4"],
        "description": "Context limit test",
        "provider": ModelProvider.ANTHROPIC,
        "params": {"temperature": 0.0},
        "thinking_mode": False,
        "pricing": {"input": 3.0, "output": 15.0, "description": "Test"},
        "context_limit": 200000,
    }

    with pytest.raises(Exception) as exc_info:
        gateway = GatewayFactory.create(model_info["full_name"])
        # Anthropic 전용 메서드 사용하여 system과 messages 분리
        system_content, messages = create_anthropic_oversized_content(
            model_info["context_limit"]
        )

        # 직접 클라이언트 생성
        client = gateway._create_client()

        # Anthropic API 직접 호출 - system을 별도 파라미터로 전달
        if hasattr(client, "client"):
            # Instructor 객체인 경우 underlying client 사용
            underlying_client = client.client
            underlying_client.messages.create(
                model=model_info["full_name"],
                max_tokens=1000,
                system=system_content,
                messages=messages,
                temperature=0.0,
            )
        else:
            # 일반 Anthropic 클라이언트인 경우
            client.messages.create(
                model=model_info["full_name"],
                max_tokens=1000,
                system=system_content,
                messages=messages,
                temperature=0.0,
            )

    # 에러 검증
    assert_context_limit_error(exc_info.value, "anthropic")


def test_google_context_limit_error() -> None:
    """Google API의 context limit 에러를 검증합니다."""
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not found")

    model_info: ModelInfoDict = {
        "full_name": "gemini-2.5-flash",
        "aliases": [],
        "description": "Context limit test",
        "provider": ModelProvider.GOOGLE,
        "params": {"temperature": 0.0},
        "thinking_mode": False,
        "pricing": {"input": 0.15, "output": 0.6, "description": "Test"},
        "context_limit": 1048576,
    }

    with pytest.raises(Exception) as exc_info:
        gateway = GatewayFactory.create(model_info["full_name"])
        messages = create_oversized_messages(model_info["context_limit"])

        # 직접 클라이언트 생성 및 호출
        client = gateway._create_client()
        params = gateway._create_request_params(messages)

        # 직접 API 호출
        client.models.generate_content(**params)

    # 에러 검증
    assert_context_limit_error(exc_info.value, "google")


@pytest.mark.parametrize("model_name", ["qwen3-coder", "kimi-k2", "deepseek-r1-0528"])
def test_openrouter_models_context_limit_error(
    models_config: dict[str, Any], model_name: str
) -> None:
    """OpenRouter 모델들의 실제 context limit을 사용한 에러 테스트"""
    if not os.getenv("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY not found")

    # models.yml에서 실제 모델 정보 가져오기
    if model_name not in models_config:
        pytest.skip(f"Model {model_name} not found in models.yml")

    model_config = models_config[model_name]

    # ModelInfoDict 형식으로 변환 (provider 문자열을 enum으로 변환)
    provider_map = {
        "openai": ModelProvider.OPENAI,
        "anthropic": ModelProvider.ANTHROPIC,
        "google": ModelProvider.GOOGLE,
        "openrouter": ModelProvider.OPENROUTER,
    }

    model_info: ModelInfoDict = {
        "full_name": model_config["full_name"],
        "aliases": model_config.get("aliases", []),
        "description": model_config["description"],
        "provider": provider_map[model_config["provider"]],
        "params": model_config["params"],
        "thinking_mode": model_config.get("thinking_mode", False),
        "pricing": model_config["pricing"],
        "context_limit": model_config["context_limit"],  # 실제 context limit 사용
    }

    # OpenRouter 모델만 openrouter_name 추가
    if "openrouter_name" in model_config:
        model_info["openrouter_name"] = model_config["openrouter_name"]

    with pytest.raises(Exception) as exc_info:
        gateway = GatewayFactory.create(model_info["full_name"])
        messages = create_oversized_messages(model_info["context_limit"])

        # 직접 클라이언트 생성 및 호출
        client = gateway._create_client()
        params = gateway._create_request_params(messages)

        # 직접 API 호출 (OpenRouter 전용 클라이언트)
        with client as http_client:
            http_client.create_completion(**params)

    # 에러 검증
    assert_context_limit_error(exc_info.value, "openrouter")


if __name__ == "__main__":
    print("Context Limit Error Analysis Test")
    print("실행 방법: pytest tests/test_context_limit_error_analysis.py -v -s")
