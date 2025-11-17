"""
Proactive Token Checker 테스트 모듈.
"""

import unittest
from unittest.mock import MagicMock, patch

from selvage.src.utils.proactive_token_checker import ProactiveTokenChecker


class TestProactiveTokenChecker(unittest.TestCase):
    """ProactiveTokenChecker 테스트 클래스."""

    def setUp(self) -> None:
        """테스트 시작 전 설정."""
        self.token_checker = ProactiveTokenChecker()

    def test_calculate_total_tokens_basic(self) -> None:
        """기본적인 토큰 계산 테스트."""
        # Given: Mock 리뷰 프롬프트
        mock_review_prompt = MagicMock()
        mock_review_prompt.system_prompt.content = "System prompt content"
        mock_review_prompt.user_prompts = [MagicMock()]

        mock_user_prompt = mock_review_prompt.user_prompts[0]
        mock_user_prompt.file_context.context = "def hello():\n    print('Hello')"
        mock_user_prompt.formatted_hunks = [MagicMock()]
        mock_user_prompt.formatted_hunks[0].before_code = "def hello():\n    print('Hello')"
        mock_user_prompt.formatted_hunks[0].after_code = "def hello():\n    print('Hello, World!')"

        # When: 토큰 수 계산
        total_tokens = self.token_checker.calculate_total_tokens(mock_review_prompt)

        # Then: 양수의 토큰 수 반환
        self.assertIsInstance(total_tokens, int)
        self.assertGreater(total_tokens, 0)

    def test_calculate_total_tokens_with_multiple_prompts(self) -> None:
        """여러 user prompt가 있는 경우 토큰 계산 테스트."""
        # Given: 여러 파일의 Mock 리뷰 프롬프트
        mock_review_prompt = MagicMock()
        mock_review_prompt.system_prompt.content = "System prompt content"
        mock_review_prompt.user_prompts = [MagicMock(), MagicMock(), MagicMock()]

        for i, mock_user_prompt in enumerate(mock_review_prompt.user_prompts):
            mock_user_prompt.file_context.context = f"def function{i}():\n    pass"
            mock_user_prompt.formatted_hunks = [MagicMock()]
            mock_user_prompt.formatted_hunks[0].before_code = f"def function{i}():\n    pass"
            mock_user_prompt.formatted_hunks[0].after_code = f"def function{i}():\n    return {i}"

        # When: 토큰 수 계산
        total_tokens = self.token_checker.calculate_total_tokens(mock_review_prompt)

        # Then: 모든 프롬프트의 토큰 합산
        self.assertIsInstance(total_tokens, int)
        self.assertGreater(total_tokens, 0)

    def test_calculate_total_tokens_empty_context(self) -> None:
        """빈 컨텍스트가 있는 경우 토큰 계산 테스트."""
        # Given: 빈 컨텍스트를 가진 Mock 프롬프트
        mock_review_prompt = MagicMock()
        mock_review_prompt.system_prompt.content = "System prompt"
        mock_review_prompt.user_prompts = [MagicMock()]

        mock_user_prompt = mock_review_prompt.user_prompts[0]
        mock_user_prompt.file_context.context = None
        mock_user_prompt.formatted_hunks = [MagicMock()]
        mock_user_prompt.formatted_hunks[0].before_code = ""
        mock_user_prompt.formatted_hunks[0].after_code = "def new_function():\n    pass"

        # When: 토큰 수 계산
        total_tokens = self.token_checker.calculate_total_tokens(mock_review_prompt)

        # Then: 에러 없이 토큰 수 반환
        self.assertIsInstance(total_tokens, int)
        self.assertGreaterEqual(total_tokens, 0)

    def test_calculate_system_prompt_tokens(self) -> None:
        """System prompt 토큰 계산 테스트."""
        # Given: System prompt가 있는 Mock 리뷰 프롬프트
        mock_review_prompt = MagicMock()
        mock_review_prompt.system_prompt.content = "This is a system prompt for code review."

        # When: System prompt 토큰 수 계산
        system_tokens = self.token_checker._calculate_system_prompt_tokens(
            mock_review_prompt
        )

        # Then: 양수의 토큰 수 반환
        self.assertIsInstance(system_tokens, int)
        self.assertGreater(system_tokens, 0)

    def test_calculate_user_prompt_tokens(self) -> None:
        """User prompt 토큰 계산 테스트."""
        # Given: Mock User prompt
        mock_user_prompt = MagicMock()
        mock_user_prompt.file_context.context = "def hello():\n    print('Hello')"
        mock_user_prompt.formatted_hunks = [MagicMock()]
        mock_user_prompt.formatted_hunks[0].before_code = "def hello():\n    print('Hello')"
        mock_user_prompt.formatted_hunks[0].after_code = "def hello():\n    print('Hello, World!')"

        # When: User prompt 토큰 수 계산
        user_tokens = self.token_checker._calculate_user_prompt_tokens(mock_user_prompt)

        # Then: 양수의 토큰 수 반환
        self.assertIsInstance(user_tokens, int)
        self.assertGreater(user_tokens, 0)

    @patch("selvage.src.utils.proactive_token_checker.tiktoken.get_encoding")
    def test_fallback_estimate_when_tiktoken_fails(
        self, mock_get_encoding: MagicMock
    ) -> None:
        """tiktoken 실패 시 fallback 추정 테스트."""
        # Given: tiktoken이 실패하도록 설정
        mock_get_encoding.side_effect = Exception("tiktoken error")
        token_checker = ProactiveTokenChecker()

        mock_review_prompt = MagicMock()
        mock_review_prompt.system_prompt.content = "System prompt content"
        mock_review_prompt.user_prompts = [MagicMock()]

        mock_user_prompt = mock_review_prompt.user_prompts[0]
        mock_user_prompt.file_context.context = "def hello():\n    print('Hello')"
        mock_user_prompt.formatted_hunks = [MagicMock()]
        mock_user_prompt.formatted_hunks[0].before_code = "def hello():\n    print('Hello')"
        mock_user_prompt.formatted_hunks[0].after_code = "def hello():\n    print('Hello, World!')"

        # When: 토큰 수 계산 (fallback 사용)
        total_tokens = token_checker.calculate_total_tokens(mock_review_prompt)

        # Then: fallback으로 추정된 토큰 수 반환
        self.assertIsInstance(total_tokens, int)
        self.assertGreater(total_tokens, 0)

    def test_large_context_token_calculation(self) -> None:
        """대용량 컨텍스트 토큰 계산 테스트."""
        # Given: 큰 컨텍스트를 가진 Mock 프롬프트
        large_context = "def function():\n    pass\n" * 1000  # 긴 코드
        mock_review_prompt = MagicMock()
        mock_review_prompt.system_prompt.content = "System prompt"
        mock_review_prompt.user_prompts = [MagicMock()]

        mock_user_prompt = mock_review_prompt.user_prompts[0]
        mock_user_prompt.file_context.context = large_context
        mock_user_prompt.formatted_hunks = [MagicMock()]
        mock_user_prompt.formatted_hunks[0].before_code = "def old():\n    pass"
        mock_user_prompt.formatted_hunks[0].after_code = "def new():\n    return True"

        # When: 토큰 수 계산
        total_tokens = self.token_checker.calculate_total_tokens(mock_review_prompt)

        # Then: 큰 값의 토큰 수 반환
        self.assertIsInstance(total_tokens, int)
        # 대략 5천 토큰 이상 예상 (실제 값은 인코딩에 따라 다름)
        self.assertGreater(total_tokens, 1000)


if __name__ == "__main__":
    unittest.main()
