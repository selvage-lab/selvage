"""
Proactive Token Checker Module

이 모듈은 리뷰 요청 전에 프롬프트의 총 토큰 수를 계산하여
Multiturn 모드로 진입할지 판단하는 기능을 제공합니다.
"""

import logging

import tiktoken

from selvage.src.utils.prompts.models import (
    ReviewPromptWithFileContent,
    UserPromptWithFileContent,
)

logger = logging.getLogger(__name__)


class ProactiveTokenChecker:
    """프롬프트의 토큰 수를 사전 계산하는 클래스"""

    def __init__(self) -> None:
        """ProactiveTokenChecker 초기화"""
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"tiktoken encoding 초기화 실패: {e}")
            self.encoding = None

    def calculate_total_tokens(self, review_prompt: ReviewPromptWithFileContent) -> int:
        """ReviewPromptWithFileContent의 총 토큰 수를 계산합니다.

        Args:
            review_prompt: 리뷰 프롬프트 객체

        Returns:
            총 토큰 수 (System prompt + User prompts)
        """
        try:
            if self.encoding is None:
                return self._fallback_estimate_tokens(review_prompt)

            # 1. System prompt 토큰 계산
            system_prompt_tokens = self._calculate_system_prompt_tokens(review_prompt)

            # 2. User prompts 토큰 계산
            user_prompts_tokens = sum(
                self._calculate_user_prompt_tokens(prompt)
                for prompt in review_prompt.user_prompts
            )

            total_tokens = system_prompt_tokens + user_prompts_tokens

            # 상세 로깅
            from selvage.src.utils.base_console import console

            console.info(
                f"[Token Calculation] System: {system_prompt_tokens:,} | "
                f"User: {user_prompts_tokens:,} | "
                f"Total: {total_tokens:,} tokens"
            )
            logger.debug(
                f"Total tokens calculated: {total_tokens} "
                f"(system: {system_prompt_tokens}, user: {user_prompts_tokens})"
            )

            return total_tokens

        except Exception as e:
            from selvage.src.utils.base_console import console

            logger.warning(f"토큰 계산 실패, fallback 사용: {e}")
            console.warning(
                f"[Token Calculation] tiktoken failed, using fallback estimation: {e}"
            )
            return self._fallback_estimate_tokens(review_prompt)

    def _calculate_system_prompt_tokens(
        self, review_prompt: ReviewPromptWithFileContent
    ) -> int:
        """System prompt의 토큰 수를 계산합니다."""
        system_content = review_prompt.system_prompt.content
        if not system_content:
            return 0

        return len(self.encoding.encode(system_content))

    def _calculate_user_prompt_tokens(
        self, user_prompt: UserPromptWithFileContent
    ) -> int:
        """단일 User prompt의 토큰 수를 계산합니다.

        Args:
            user_prompt: UserPromptWithFileContent 객체

        Returns:
            토큰 수
        """
        # file_context 토큰 계산
        context_content = user_prompt.file_context.context
        context_tokens = (
            len(self.encoding.encode(str(context_content))) if context_content else 0
        )

        # formatted_hunks 토큰 계산
        hunks_tokens = 0
        for hunk in user_prompt.formatted_hunks:
            # before_code와 after_code의 실제 텍스트 내용으로 토큰 계산
            hunk_text = hunk.before_code + hunk.after_code
            hunks_tokens += len(self.encoding.encode(hunk_text))

        return context_tokens + hunks_tokens

    def _fallback_estimate_tokens(
        self, review_prompt: ReviewPromptWithFileContent
    ) -> int:
        """tiktoken이 실패한 경우 문자열 길이 기반으로 토큰 수를 추정합니다.

        Args:
            review_prompt: 리뷰 프롬프트 객체

        Returns:
            추정 토큰 수
        """
        # System prompt 문자열 길이
        system_content = review_prompt.system_prompt.content or ""
        system_chars = len(system_content)

        # User prompts 문자열 길이
        user_chars = 0
        for user_prompt in review_prompt.user_prompts:
            context_content = str(user_prompt.file_context.context or "")
            user_chars += len(context_content)

            for hunk in user_prompt.formatted_hunks:
                hunk_text = hunk.before_code + hunk.after_code
                user_chars += len(hunk_text)

        total_chars = system_chars + user_chars

        # 1토큰 ≈ 3.5자 (코드의 토큰 밀도 고려)
        # prompt_splitter.py:209와 동일한 추정 로직
        estimated_tokens = int(total_chars / 3.5)

        from selvage.src.utils.base_console import console

        console.info(
            f"[Fallback Estimation] Chars: {total_chars:,} | "
            f"Estimated tokens: {estimated_tokens:,} (ratio: 3.5)"
        )
        logger.debug(
            f"Fallback token estimation: {estimated_tokens} "
            f"(chars: {total_chars}, ratio: 3.5)"
        )

        return estimated_tokens
