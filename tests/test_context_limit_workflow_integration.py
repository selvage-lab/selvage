"""
Context Limit 에러 처리 통합 테스트

실제 코드 리뷰 워크플로우를 통해 context limit을 초과했을 때
ErrorPatternParser와 ReviewResult가 올바르게 작동하는지 검증합니다.

실행 방법:
    pytest tests/test_context_limit_workflow_integration.py -v -s

주의사항:
    - 실제 API를 호출하므로 비용이 발생할 수 있습니다
    - 각 provider의 API key가 환경변수로 설정되어야 합니다
"""

import os

import pytest

from selvage.src.llm_gateway.gateway_factory import GatewayFactory
from selvage.src.utils.prompts.models import (
    FileContextInfo,
    ReviewPromptWithFileContent,
    SystemPrompt,
    UserPromptWithFileContent,
)


class ContextLimitWorkflowTester:
    """Context limit 워크플로우 테스트를 위한 클래스"""

    def create_oversized_content(self, context_limit_tokens: int) -> str:
        """Context limit을 확실히 초과하는 매우 긴 코드 내용을 생성합니다."""
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

        return long_code

    def create_oversized_review_prompt(
        self, context_limit_tokens: int
    ) -> ReviewPromptWithFileContent:
        """Context limit을 초과하는 ReviewPromptWithFileContent를 생성합니다."""

        # 큰 코드 내용 생성
        oversized_code = self.create_oversized_content(context_limit_tokens)

        # 시스템 프롬프트 생성
        system_prompt = SystemPrompt(
            role="system",
            content="다음 코드를 자세히 리뷰해주세요. 모든 함수와 클래스에 대해 상세한 분석을 제공해주세요.",
        )

        # 파일 컨텍스트 생성
        file_context = FileContextInfo.create_full_context(oversized_code)

        # UserPromptWithFileContent 생성 (빈 hunks 리스트 사용)
        user_prompt = UserPromptWithFileContent(
            file_name="test_large_file.py",
            file_context=file_context,
            hunks=[],  # 빈 hunks로 설정
            language="python",
        )

        return ReviewPromptWithFileContent(
            system_prompt=system_prompt, user_prompts=[user_prompt]
        )


# 전역 테스터 인스턴스
tester = ContextLimitWorkflowTester()


@pytest.mark.integration
def test_openai_context_limit_workflow():
    """OpenAI API의 context limit 에러를 실제 워크플로우로 검증합니다."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not found")

    model_name = "gpt-5.3-codex"
    context_limit = 1000000

    print("\\n=== OpenAI Context Limit 워크플로우 테스트 ===")
    print(f"모델: {model_name}")
    print(f"Context Limit: {context_limit:,} tokens")

    try:
        # 실제 워크플로우와 동일하게 gateway 생성
        gateway = GatewayFactory.create(model=model_name)

        # Context limit을 초과하는 review prompt 생성
        review_prompt = tester.create_oversized_review_prompt(context_limit)

        print(
            f"프롬프트 크기: 약 {len(review_prompt.to_combined_text()) // 4:,} tokens 추정"
        )

        # 실제 코드 리뷰 워크플로우 수행
        review_result = gateway.review_code(review_prompt)

        # 결과 검증
        print("\\n📊 검증 결과:")
        print(f"   success: {review_result.success}")
        print(f"   error_response: {review_result.error_response}")

        if review_result.error_response:
            print(f"   error_type: {review_result.error_response.error_type}")
            print(
                f"   error_message: {review_result.error_response.error_message[:100]}..."
            )

        # 검증: 실패해야 하고, context limit 에러로 식별되어야 함
        assert review_result.success is False, (
            "Context limit 초과 시 success=False여야 합니다"
        )
        assert review_result.error_response is not None, "에러 응답이 있어야 합니다"
        # 에러 타입 검증 - context limit 에러로 엄격하게 식별
        assert review_result.error_response.error_type == "context_limit_exceeded", (
            f"에러 타입이 'context_limit_exceeded'여야 합니다. "
            f"실제: {review_result.error_response.error_type}"
        )

        print("✅ OpenAI Context Limit 워크플로우 테스트 성공!")

    except Exception as e:
        pytest.fail(f"예상치 못한 예외 발생: {e}")


@pytest.mark.integration
def test_anthropic_context_limit_workflow():
    """Anthropic API의 context limit 에러를 실제 워크플로우로 검증합니다."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not found")

    model_name = "claude-sonnet-4"
    context_limit = 2000000

    print("\\n=== Anthropic Context Limit 워크플로우 테스트 ===")
    print(f"모델: {model_name}")
    print(f"Context Limit: {context_limit:,} tokens")

    try:
        # 실제 워크플로우와 동일하게 gateway 생성
        gateway = GatewayFactory.create(model=model_name)

        # Context limit을 초과하는 review prompt 생성
        review_prompt = tester.create_oversized_review_prompt(context_limit)

        print(
            f"프롬프트 크기: 약 {len(review_prompt.to_combined_text()) // 4:,} tokens 추정"
        )

        # 실제 코드 리뷰 워크플로우 수행
        review_result = gateway.review_code(review_prompt)

        # 결과 검증
        print("\\n📊 검증 결과:")
        print(f"   success: {review_result.success}")
        print(f"   error_response: {review_result.error_response}")

        if review_result.error_response:
            print(f"   error_type: {review_result.error_response.error_type}")
            print(
                f"   error_message: {review_result.error_response.error_message[:100]}..."
            )

        # 검증: 실패해야 하고, 에러 응답이 있어야 함
        assert review_result.success is False, (
            "Context limit 초과 시 success=False여야 합니다"
        )
        assert review_result.error_response is not None, "에러 응답이 있어야 합니다"
        # 에러 타입 검증 - context limit 에러로 엄격하게 식별
        assert review_result.error_response.error_type == "context_limit_exceeded", (
            f"에러 타입이 'context_limit_exceeded'여야 합니다. "
            f"실제: {review_result.error_response.error_type}"
        )

        print("✅ Anthropic Context Limit 워크플로우 테스트 성공!")

    except Exception as e:
        pytest.fail(f"예상치 못한 예외 발생: {e}")


@pytest.mark.integration
@pytest.mark.parametrize(
    "model_name,context_limit",
    [
        ("qwen3-coder", 1000000),
        ("kimi-k2", 200000),
    ],
)
def test_openrouter_context_limit_workflow(model_name, context_limit):
    """OpenRouter API의 context limit 에러를 실제 워크플로우로 검증합니다."""
    if not os.getenv("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY not found")

    print(f"\\n=== OpenRouter ({model_name}) Context Limit 워크플로우 테스트 ===")
    print(f"모델: {model_name}")
    print(f"Context Limit: {context_limit:,} tokens")

    try:
        # 실제 워크플로우와 동일하게 gateway 생성
        gateway = GatewayFactory.create(model=model_name)

        # Context limit을 초과하는 review prompt 생성
        review_prompt = tester.create_oversized_review_prompt(context_limit)

        print(
            f"프롬프트 크기: 약 {len(review_prompt.to_combined_text()) // 4:,} tokens 추정"
        )

        # 실제 코드 리뷰 워크플로우 수행
        review_result = gateway.review_code(review_prompt)

        # 결과 검증
        print("\\n📊 검증 결과:")
        print(f"   success: {review_result.success}")
        print(f"   error_response: {review_result.error_response}")

        if review_result.error_response:
            print(f"   error_type: {review_result.error_response.error_type}")
            print(
                f"   error_message: {review_result.error_response.error_message[:100]}..."
            )

        # 검증: 실패해야 하고, 에러 응답이 있어야 함
        assert review_result.success is False, (
            "Context limit 초과 시 success=False여야 합니다"
        )
        assert review_result.error_response is not None, "에러 응답이 있어야 합니다"
        # 에러 타입 검증 - context limit 에러로 엄격하게 식별
        assert review_result.error_response.error_type == "context_limit_exceeded", (
            f"에러 타입이 'context_limit_exceeded'여야 합니다. "
            f"실제: {review_result.error_response.error_type}"
        )

        print(f"✅ OpenRouter ({model_name}) Context Limit 워크플로우 테스트 성공!")

    except Exception as e:
        pytest.fail(f"예상치 못한 예외 발생: {e}")


@pytest.mark.integration
def test_google_context_limit_workflow():
    """Google Gemini API의 context limit 에러를 실제 워크플로우로 검증합니다."""
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not found")

    model_name = "gemini-3-flash"
    context_limit = 1048576  # Gemini의 높은 context limit

    print("\\n=== Google Gemini Context Limit 워크플로우 테스트 ===")
    print(f"모델: {model_name}")
    print(f"Context Limit: {context_limit:,} tokens")

    try:
        # 실제 워크플로우와 동일하게 gateway 생성
        gateway = GatewayFactory.create(model=model_name)

        # Context limit을 초과하는 review prompt 생성
        review_prompt = tester.create_oversized_review_prompt(context_limit)

        print(
            f"프롬프트 크기: 약 {len(review_prompt.to_combined_text()) // 4:,} tokens 추정"
        )

        # 실제 코드 리뷰 워크플로우 수행
        review_result = gateway.review_code(review_prompt)

        # 결과 검증
        print("\\n📊 검증 결과:")
        print(f"   success: {review_result.success}")
        print(f"   error_response: {review_result.error_response}")

        if review_result.error_response:
            print(f"   error_type: {review_result.error_response.error_type}")
            print(
                f"   error_message: {review_result.error_response.error_message[:100]}..."
            )

        # 검증: 실패해야 하고, 에러가 식별되어야 함
        assert review_result.success is False, (
            "Context limit 초과 시 success=False여야 합니다"
        )
        assert review_result.error_response is not None, "에러 응답이 있어야 합니다"

        # 에러 타입 검증 - context limit 에러로 엄격하게 식별
        assert review_result.error_response.error_type == "context_limit_exceeded", (
            f"에러 타입이 'context_limit_exceeded'여야 합니다. "
            f"실제: {review_result.error_response.error_type}"
        )

        print("✅ Google Gemini Context Limit 워크플로우 테스트 성공!")

    except Exception as e:
        pytest.fail(f"예상치 못한 예외 발생: {e}")
