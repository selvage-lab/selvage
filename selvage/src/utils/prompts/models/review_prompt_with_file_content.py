"""파일 내용을 포함한 리뷰 프롬프트 데이터 클래스 모듈"""

from dataclasses import dataclass

from .system_prompt import SystemPrompt
from .user_prompt_with_file_content import UserPromptWithFileContent


@dataclass
class ReviewPromptWithFileContent:
    """파일 내용을 포함한 리뷰 프롬프트 데이터 클래스"""

    system_prompt: SystemPrompt
    user_prompts: list[UserPromptWithFileContent]

    def to_messages(self) -> list[dict[str, str]]:
        """ReviewPromptWithFileContent를 LLM API 메시지 목록으로 변환합니다.

        Returns:
            list[dict[str, str | Any]]: LLM API 메시지 목록
        """
        messages: list[dict[str, str]] = [
            {"role": self.system_prompt.role, "content": self.system_prompt.content}
        ]
        for user_prompt in self.user_prompts:
            messages.append(user_prompt.to_message())
        return messages

    def to_combined_text(self) -> str:
        """ReviewPromptWithFileContent를 문자열로 변환합니다.

        Returns:
            str: 문자열로 변환된 ReviewPromptWithFileContent
        """
        combined_text = ""
        combined_text += self.system_prompt.content + "\n\n"
        for user_prompt in self.user_prompts:
            combined_text += user_prompt.to_message()["content"] + "\n\n"
        return combined_text
