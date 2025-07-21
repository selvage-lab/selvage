from dataclasses import dataclass, field

from selvage.src.utils.language_detector import detect_language_from_filename

from ..constants import DELETED_FILE_PLACEHOLDER
from .hunk import Hunk


@dataclass
class FileDiff:
    """Git diff의 파일 변경사항을 나타내는 클래스"""

    filename: str
    file_content: str | None = None
    hunks: list[Hunk] = field(default_factory=list)
    language: str = ""
    additions: int = 0
    deletions: int = 0
    line_count: int = 0

    def calculate_changes(self) -> None:
        """파일의 추가/삭제 라인 수를 계산합니다."""
        self.additions = 0
        self.deletions = 0

        for hunk in self.hunks:
            for line in hunk.content.split("\n"):
                if line.startswith("+") and not line.startswith("+++"):
                    self.additions += 1
                elif line.startswith("-") and not line.startswith("---"):
                    self.deletions += 1

    def detect_language(self) -> None:
        """파일 확장자를 기반으로 언어를 감지합니다."""
        self.language = detect_language_from_filename(self.filename)

    def calculate_line_count(self) -> None:
        """파일의 총 라인 수를 계산합니다."""
        if self.file_content is None:
            self.line_count = 0
        elif self.file_content == DELETED_FILE_PLACEHOLDER:
            self.line_count = 0
        elif self.file_content.startswith(
            "[파일 읽기 오류:"
        ) or self.file_content.startswith("[파일 처리 중 예기치 않은 오류:"):
            self.line_count = 0
        else:
            # 완전히 빈 파일의 경우 라인 수는 0
            if self.file_content == "":
                self.line_count = 0
            else:
                # 개행 문자로 분할하여 라인 수 계산
                lines = self.file_content.split("\n")
                # 마지막이 빈 문자열이면 제거 (파일 끝 개행 문자 처리)
                if lines and lines[-1] == "":
                    lines = lines[:-1]
                # 빈 라인들만 있는 경우 처리
                if not lines:
                    self.line_count = 0
                else:
                    self.line_count = len(lines)

    def is_entirely_new_content(self) -> bool:
        """파일 내용이 전체 새로운 내용인지 확인합니다."""
        return self.line_count == self.additions
