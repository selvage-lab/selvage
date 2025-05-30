"""파일 내용을 포함한 사용자 프롬프트 데이터 클래스 모듈"""

import json
from dataclasses import asdict, dataclass

from selvage.src.diff_parser.models import Hunk

from .formatted_hunk import FormattedHunk


@dataclass
class UserPromptWithFileContent:
    """파일 내용을 포함한 사용자 프롬프트 데이터 클래스"""

    file_name: str
    file_content: str
    formatted_hunks: list[FormattedHunk]

    def __init__(
        self,
        file_name: str,
        file_content: str,
        hunks: list[Hunk],
        language: str = "text",
    ) -> None:
        """UserPromptWithFileContent 객체를 초기화합니다.

        Args:
            file_name: 파일 이름
            file_content: 파일 내용
            hunks: Hunk 리스트 (formatted_hunks와 함께 사용하면 안됨)
            formatted_hunks: FormattedHunk 리스트 (hunks와 함께 사용하면 안됨)
            language: 코드 언어 (hunks 사용 시)
        """
        self.file_name = file_name
        self.file_content = file_content
        self.formatted_hunks = [
            FormattedHunk(hunk, idx, language) for idx, hunk in enumerate(hunks)
        ]

    def to_message(self) -> dict[str, str]:
        """UserPromptWithFileContent를 LLM API 메시지 형식으로 변환합니다.

        Returns:
            dict[str, str]: LLM API 메시지 형식
        """
        return {
            "role": "user",
            "content": json.dumps(
                obj=asdict(self),
                ensure_ascii=False,
            ),
        }
