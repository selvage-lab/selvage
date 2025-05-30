"""사용자 프롬프트 데이터 클래스 모듈"""

import json
from dataclasses import asdict, dataclass


@dataclass
class UserPrompt:
    """사용자 프롬프트 데이터 클래스"""

    hunk_idx: str
    file_name: str
    before_code: str
    after_code: str
    after_code_start_line_number: int
    language: str

    def to_message(self) -> dict[str, str]:
        """UserPrompt를 LLM API 메시지 형식으로 변환합니다.

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
