from dataclasses import dataclass, field

from selvage.src.utils.language_detector import detect_language_from_filename

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
