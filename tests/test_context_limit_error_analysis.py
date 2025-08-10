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

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import yaml

from selvage.src.llm_gateway.gateway_factory import GatewayFactory
from selvage.src.model_config import ModelInfoDict, ModelProvider


@dataclass
class ContextLimitErrorAnalysis:
    """Context limit 에러 분석 결과"""

    provider: str
    model: str
    context_limit: int
    error_type: str
    error_code: str | None
    error_message: str
    http_status_code: int | None
    raw_error_data: dict[str, Any]
    timestamp: str


class ContextLimitTester:
    """Context limit 에러 테스트를 위한 클래스"""

    def __init__(self) -> None:
        self.results: list[ContextLimitErrorAnalysis] = []
        self.results_dir = Path("tests/results")
        self.results_dir.mkdir(exist_ok=True)

    def create_oversized_messages(
        self, context_limit_tokens: int
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
        self, context_limit_tokens: int
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

    def analyze_error(
        self, provider: str, model: str, context_limit: int, error: Exception
    ) -> ContextLimitErrorAnalysis:
        """에러를 분석하여 구조화된 데이터로 변환합니다."""
        error_type = type(error).__name__
        error_message = str(error)
        error_code = None
        http_status = None
        raw_data = {}

        # OpenAI 에러 처리
        if hasattr(error, "response") and hasattr(error.response, "status_code"):
            http_status = error.response.status_code
            try:
                raw_data = error.response.json()
                if "error" in raw_data:
                    error_info = raw_data["error"]
                    if isinstance(error_info, dict):
                        error_code = error_info.get("code") or error_info.get("type")
            except Exception as json_error:
                # JSON 파싱 실패 로깅
                print(f"   JSON 파싱 실패: {json_error}")

        # Anthropic 에러 처리
        if hasattr(error, "status_code"):
            http_status = error.status_code
        if hasattr(error, "type"):
            error_code = error.type

        # Anthropic 에러 상세 정보 추출
        if hasattr(error, "body") and isinstance(error.body, dict):
            raw_data.update(error.body)
            if "error" in error.body:
                error_info = error.body["error"]
                if isinstance(error_info, dict):
                    error_code = error_info.get("type") or error_code
                    # 토큰 정보나 context limit 정보 추출 시도
                    error_msg = error_info.get("message", "")
                    if "tokens" in error_msg.lower():
                        raw_data["contains_token_info"] = True

        # 추가 에러 정보 수집
        if hasattr(error, "code"):
            error_code = error.code

        # OpenAI/OpenRouter 에러에서 토큰 정보 추출
        if "tokens" in error_message.lower() and provider in ["openai", "openrouter"]:
            # 에러 메시지에서 실제 토큰 수와 최대 토큰 수 추출 시도
            import re

            token_match = re.search(
                r"(\d+,?\d*)\s+tokens.*maximum.*?(\d+,?\d*)\s+tokens", error_message
            )
            if token_match:
                raw_data["actual_tokens"] = token_match.group(1).replace(",", "")
                raw_data["max_tokens"] = token_match.group(2).replace(",", "")

        # Google 에러에서 quota 정보 추출
        if provider == "google" and "quota" in error_message.lower():
            raw_data["quota_exceeded"] = True
            if hasattr(error, "response") and hasattr(error.response, "json"):
                try:
                    google_error_data = error.response.json()
                    if (
                        "error" in google_error_data
                        and "details" in google_error_data["error"]
                    ):
                        raw_data["google_quota_details"] = google_error_data["error"][
                            "details"
                        ]
                except Exception as json_error:
                    print(f"   Google JSON 파싱 실패: {json_error}")

        return ContextLimitErrorAnalysis(
            provider=provider,
            model=model,
            context_limit=context_limit,
            error_type=error_type,
            error_code=error_code,
            error_message=error_message,
            http_status_code=http_status,
            raw_error_data=raw_data,
            timestamp=datetime.now().isoformat(),
        )

    def save_results(self):
        """분석 결과를 JSON 파일로 저장합니다."""
        if not self.results:
            print("저장할 결과가 없습니다.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"context_limit_errors_{timestamp}.json"
        filepath = self.results_dir / filename

        results_dict = {
            "analysis_timestamp": datetime.now().isoformat(),
            "total_results": len(self.results),
            "results": [asdict(result) for result in self.results],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False)

        print(f"\n분석 결과 저장됨: {filepath}")
        print(f"총 {len(self.results)}개의 에러 응답 분석 완료")


# 전역 테스터 인스턴스
tester = ContextLimitTester()


@pytest.fixture
def models_config():
    """models.yml에서 모델 설정을 로드하는 fixture"""
    models_yml_path = (
        Path(__file__).parent.parent / "selvage" / "resources" / "models.yml"
    )

    with open(models_yml_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config["models"]


def test_openai_context_limit_error():
    """OpenAI API의 context limit 에러를 직접 수집합니다."""
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

    print("\n=== OpenAI Context Limit 테스트 ===")
    print(f"모델: {model_info['full_name']}")
    print(f"Context Limit: {model_info['context_limit']:,} tokens")

    try:
        gateway = GatewayFactory.create(model_info["full_name"])
        messages = tester.create_oversized_messages(model_info["context_limit"])

        # 직접 클라이언트 생성 및 호출
        client = gateway._create_client()
        params = gateway._create_request_params(messages)

        print(f"프롬프트 크기: 약 {len(str(messages)) // 4:,} tokens 추정")

        # 직접 API 호출 (Instructor 클라이언트의 underlying client 접근)
        if hasattr(client, "client"):
            # Instructor 객체인 경우 underlying client 사용
            underlying_client = client.client
            underlying_client.chat.completions.create(**params)
        else:
            # 일반 OpenAI 클라이언트인 경우
            client.chat.completions.create(**params)

        print(
            "⚠️ 에러가 발생하지 않았습니다. Context limit이 예상보다 높을 수 있습니다."
        )

    except Exception as e:
        analysis = tester.analyze_error(
            "openai", model_info["full_name"], model_info["context_limit"], e
        )
        tester.results.append(analysis)

        print("✅ Context limit 에러 캐치:")
        print(f"   에러 타입: {analysis.error_type}")
        print(f"   에러 코드: {analysis.error_code}")
        print(f"   HTTP 상태: {analysis.http_status_code}")
        print(f"   메시지: {analysis.error_message[:100]}...")


def test_anthropic_context_limit_error():
    """Anthropic API의 context limit 에러를 직접 수집합니다."""
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

    print("\n=== Anthropic Context Limit 테스트 ===")
    print(f"모델: {model_info['full_name']}")
    print(f"Context Limit: {model_info['context_limit']:,} tokens")

    try:
        gateway = GatewayFactory.create(model_info["full_name"])
        # Anthropic 전용 메서드 사용하여 system과 messages 분리
        system_content, messages = tester.create_anthropic_oversized_content(
            model_info["context_limit"]
        )

        # 직접 클라이언트 생성
        client = gateway._create_client()

        print(f"프롬프트 크기: 약 {len(str(messages)) // 4:,} tokens 추정")

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

        print(
            "⚠️ 에러가 발생하지 않았습니다. Context limit이 예상보다 높을 수 있습니다."
        )

    except Exception as e:
        analysis = tester.analyze_error(
            "anthropic", model_info["full_name"], model_info["context_limit"], e
        )
        tester.results.append(analysis)

        print("✅ Context limit 에러 캐치:")
        print(f"   에러 타입: {analysis.error_type}")
        print(f"   에러 코드: {analysis.error_code}")
        print(f"   HTTP 상태: {analysis.http_status_code}")
        print(f"   메시지: {analysis.error_message[:100]}...")


def test_google_context_limit_error():
    """Google API의 context limit 에러를 직접 수집합니다."""
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

    print("\n=== Google Context Limit 테스트 ===")
    print(f"모델: {model_info['full_name']}")
    print(f"Context Limit: {model_info['context_limit']:,} tokens")

    try:
        gateway = GatewayFactory.create(model_info["full_name"])
        messages = tester.create_oversized_messages(model_info["context_limit"])

        # 직접 클라이언트 생성 및 호출
        client = gateway._create_client()
        params = gateway._create_request_params(messages)

        print(f"프롬프트 크기: 약 {len(str(messages)) // 4:,} tokens 추정")

        # 직접 API 호출
        client.models.generate_content(**params)

        print(
            "⚠️ 에러가 발생하지 않았습니다. Context limit이 예상보다 높을 수 있습니다."
        )

    except Exception as e:
        analysis = tester.analyze_error(
            "google", model_info["full_name"], model_info["context_limit"], e
        )
        tester.results.append(analysis)

        print("✅ Context limit 에러 캐치:")
        print(f"   에러 타입: {analysis.error_type}")
        print(f"   에러 코드: {analysis.error_code}")
        print(f"   HTTP 상태: {analysis.http_status_code}")
        print(f"   메시지: {analysis.error_message[:100]}...")


@pytest.mark.parametrize("model_name", ["qwen3-coder", "kimi-k2", "deepseek-r1-0528"])
def test_openrouter_models_context_limit_error(models_config, model_name):
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

    print(f"\n=== OpenRouter ({model_name}) Context Limit 테스트 ===")
    print(f"모델: {model_info['full_name']}")
    print(f"실제 Context Limit: {model_info['context_limit']:,} tokens")

    try:
        gateway = GatewayFactory.create(model_info["full_name"])
        messages = tester.create_oversized_messages(model_info["context_limit"])

        # 직접 클라이언트 생성 및 호출
        client = gateway._create_client()
        params = gateway._create_request_params(messages)

        print(f"프롬프트 크기: 약 {len(str(messages)) // 4:,} tokens 추정")

        # 직접 API 호출 (OpenRouter 전용 클라이언트)
        with client as http_client:
            http_client.create_completion(**params)

        print(
            "⚠️ 에러가 발생하지 않았습니다. Context limit이 예상보다 높을 수 있습니다."
        )

    except Exception as e:
        analysis = tester.analyze_error(
            "openrouter", model_info["full_name"], model_info["context_limit"], e
        )
        tester.results.append(analysis)

        print("✅ Context limit 에러 캐치:")
        print(f"   에러 타입: {analysis.error_type}")
        print(f"   에러 코드: {analysis.error_code}")
        print(f"   HTTP 상태: {analysis.http_status_code}")
        print(f"   메시지: {analysis.error_message[:100]}...")


def test_save_analysis_results():
    """분석 결과를 저장하고 요약을 출력합니다."""
    print("\n=== Context Limit 에러 분석 완료 ===")

    if not tester.results:
        print("❌ 분석된 결과가 없습니다.")
        print("   API key를 확인하고 다른 테스트들을 먼저 실행해주세요.")
        return

    # 결과 저장
    tester.save_results()

    # 요약 출력
    print("\n📊 분석 요약:")
    for result in tester.results:
        print(f"\n🔍 {result.provider.upper()} - {result.model}")
        print(f"   에러 타입: {result.error_type}")
        print(f"   에러 코드: {result.error_code}")
        print(f"   HTTP 상태: {result.http_status_code}")
        print(f"   메시지: {result.error_message[:150]}...")


if __name__ == "__main__":
    print("Context Limit Error Analysis Test")
    print("실행 방법: pytest tests/test_context_limit_error_analysis.py -v -s")
