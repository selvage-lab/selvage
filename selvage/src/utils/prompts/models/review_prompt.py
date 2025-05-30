"""리뷰 프롬프트 데이터 클래스 모듈"""

from dataclasses import dataclass
from typing import Any

from .system_prompt import SystemPrompt
from .user_prompt import UserPrompt


@dataclass
class ReviewPrompt:
    """리뷰 프롬프트 데이터 클래스"""

    system_prompt: SystemPrompt
    user_prompts: list[UserPrompt]

    def to_messages(self) -> list[dict[str, str | Any]]:
        """ReviewPrompt를 LLM API 메시지 목록으로 변환합니다.

        Returns:
            list[dict[str, str | Any]]: LLM API 메시지 목록
        """
        messages: list[dict[str, str | Any]] = [
            {"role": self.system_prompt.role, "content": self.system_prompt.content}
        ]
        for user_prompt in self.user_prompts:
            messages.append(user_prompt.to_message())
        return messages

    def to_combined_text(self) -> str:
        """ReviewPrompt를 문자열로 변환합니다.

        Returns:
            str: 문자열로 변환된 ReviewPrompt
        """
        combined_text = ""
        combined_text += self.system_prompt.content + "\n\n"
        for user_prompt in self.user_prompts:
            combined_text += user_prompt.to_message()["content"] + "\n\n"
        return combined_text
