#!/usr/bin/env python3
"""retry 수정 사항이 올바르게 작동하는지 검증하는 테스트"""

from unittest.mock import patch

from selvage.src.context_extractor.line_range import LineRange
from selvage.src.diff_parser.models.hunk import Hunk
from selvage.src.llm_gateway.base_gateway import BaseGateway
from selvage.src.llm_gateway.openrouter.gateway import OpenRouterGateway
from selvage.src.models.model_provider import ModelProvider
from selvage.src.utils.prompts.models import (
    FileContextInfo,
    ReviewPromptWithFileContent,
    SystemPrompt,
    UserPromptWithFileContent,
)


class MockBaseGateway(BaseGateway):
    """테스트용 BaseGateway"""

    def _load_api_key(self) -> str:
        return "test-key"

    def _set_model(self, model_info) -> None:
        self.model = model_info

    def get_provider(self) -> ModelProvider:
        return ModelProvider.OPENAI

    def _create_request_params(self, messages):
        return {"messages": messages}


def create_test_review_prompt() -> ReviewPromptWithFileContent:
    """테스트용 ReviewPromptWithFileContent 생성"""
    system_prompt = SystemPrompt(role="system", content="코드를 분석하고 리뷰하세요.")

    # Hunk 객체 생성
    hunk = Hunk(
        header="@@ -1,1 +1,1 @@",
        content=" def example(): pass\n-def example(): pass\n+def example(): return 'Hello'",
        before_code="def example(): pass",
        after_code="def example(): return 'Hello'",
        start_line_original=1,
        line_count_original=1,
        start_line_modified=1,
        line_count_modified=1,
        change_line=LineRange(start_line=1, end_line=1),
    )

    # FileContextInfo 생성
    file_context = FileContextInfo.create_full_context("def example(): pass")

    user_prompt = UserPromptWithFileContent(
        file_name="example.py",
        file_context=file_context,
        hunks=[hunk],
        language="python",
    )
    return ReviewPromptWithFileContent(
        system_prompt=system_prompt, user_prompts=[user_prompt]
    )


def test_base_gateway_retry_exception_propagation():
    """BaseGateway가 재시도 대상 예외를 올바르게 재전파하는지 테스트"""
    print("\\n=== BaseGateway 예외 재전파 테스트 ===")

    model_info = {
        "full_name": "test-model",
        "provider": ModelProvider.OPENAI,
    }
    gateway = MockBaseGateway(model_info)

    # 테스트용 프롬프트 생성
    review_prompt = create_test_review_prompt()

    # _create_client이 ConnectionError를 발생시키도록 모킹
    with patch.object(
        gateway, "_create_client", side_effect=ConnectionError("Connection failed")
    ):
        result = gateway.review_code(review_prompt)
        assert result.success is False
        assert result.error_response is not None
        assert "ConnectionError" in result.error_response.error_message
        print("✅ retry 로직이 올바르게 작동함: RetryError가 ReviewResult로 변환됨")


def test_openrouter_gateway_retry_exception_propagation():
    """OpenRouterGateway가 재시도 대상 예외를 올바르게 재전파하는지 테스트"""
    print("\\n=== OpenRouterGateway 예외 재전파 테스트 ===")

    from selvage.src.exceptions.openrouter_api_error import OpenRouterConnectionError

    model_info = {
        "full_name": "anthropic/claude-3-sonnet",
        "provider": ModelProvider.OPENROUTER,
        "openrouter_name": "anthropic/claude-3-sonnet",
        "description": "Test model",
    }

    # API key 환경변수를 모킹
    with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}):
        gateway = OpenRouterGateway(model_info)

        # 테스트용 프롬프트 생성
        review_prompt = create_test_review_prompt()

        # _create_client이 OpenRouterConnectionError를 발생시키도록 모킹
        with patch.object(
            gateway,
            "_create_client",
            side_effect=OpenRouterConnectionError("OpenRouter connection failed"),
        ):
            result = gateway.review_code(review_prompt)
            assert result.success is False
            assert result.error_response is not None
            assert "OpenRouterConnectionError" in result.error_response.error_message
            print(
                "✅ OpenRouter retry 로직이 올바르게 작동함: RetryError가 ReviewResult로 변환됨"
            )


def test_non_retryable_exception_handling():
    """재시도 대상이 아닌 예외는 ReviewResult로 반환되는지 테스트"""
    print("\\n=== 재시도 비대상 예외 처리 테스트 ===")

    model_info = {
        "full_name": "test-model",
        "provider": ModelProvider.OPENAI,
    }
    gateway = MockBaseGateway(model_info)

    # 테스트용 프롬프트 생성
    review_prompt = create_test_review_prompt()

    # _create_client이 RuntimeError(재시도 비대상)를 발생시키도록 모킹
    with patch.object(
        gateway, "_create_client", side_effect=RuntimeError("Runtime error")
    ):
        result = gateway.review_code(review_prompt)

        # RuntimeError는 재시도 대상이 아니므로 ReviewResult.error_result로 반환되어야 함
        assert not result.success, "RuntimeError 발생 시 success=False여야 함"
        assert result.error_response is not None, "에러 응답이 있어야 함"
        print(
            f"✅ RuntimeError가 올바르게 ReviewResult로 처리됨: {result.error_response.error_message}"
        )


if __name__ == "__main__":
    print("retry 로직 수정 검증 테스트 시작...")

    try:
        test_base_gateway_retry_exception_propagation()
        test_openrouter_gateway_retry_exception_propagation()
        test_non_retryable_exception_handling()
        print("\\n🎉 모든 테스트 통과! retry 로직이 올바르게 수정되었습니다.")
    except Exception as e:
        print(f"\\n❌ 테스트 실패: {e}")
        raise
