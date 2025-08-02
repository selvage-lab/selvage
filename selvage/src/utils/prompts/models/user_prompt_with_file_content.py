"""파일 내용을 포함한 사용자 프롬프트 데이터 클래스 모듈"""

import json
from dataclasses import asdict, dataclass

from selvage.src.diff_parser.models import Hunk

from .file_context_info import FileContextInfo
from .formatted_hunk import FormattedHunk


@dataclass
class UserPromptWithFileContent:
    """파일 내용을 포함한 사용자 프롬프트 데이터 클래스"""

    file_name: str
    file_context: FileContextInfo
    formatted_hunks: list[FormattedHunk]

    def __init__(
        self,
        file_name: str,
        file_context: FileContextInfo | str,
        hunks: list[Hunk],
        language: str = "text",
    ) -> None:
        """UserPromptWithFileContent 객체를 초기화합니다.

        Args:
            file_name: 파일 이름
            file_context: 파일 컨텍스트 정보 (FileContextInfo 또는 문자열)
            hunks: Hunk 리스트
            language: 코드 언어 (hunks 사용 시)
        """
        self.file_name = file_name

        # 하위 호환성을 위해 문자열인 경우 FileContextInfo로 변환
        if isinstance(file_context, str):
            self.file_context = FileContextInfo.create_full_context(file_context)
        else:
            self.file_context = file_context

        self.formatted_hunks = [
            FormattedHunk(hunk, idx, language) for idx, hunk in enumerate(hunks)
        ]

    def to_message(self) -> dict[str, str]:
        """UserPromptWithFileContent를 LLM API 메시지 형식으로 변환합니다.

        Returns:
            dict[str, str]: LLM API 메시지 형식
        """
        # FileContextInfo의 enum 직렬화 문제를 해결하기 위해 수동으로 딕셔너리 구성
        data = {
            "file_name": self.file_name,
            "file_context": self.file_context.to_dict(),
            "formatted_hunks": [asdict(hunk) for hunk in self.formatted_hunks],
        }

        return {
            "role": "user",
            "content": json.dumps(
                obj=data,
                ensure_ascii=False,
            ),
        }
