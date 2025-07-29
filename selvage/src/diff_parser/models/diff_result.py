import json
from dataclasses import asdict, dataclass, field
from typing import Any

from .file_diff import FileDiff


@dataclass
class DiffResult:
    """Git diff 결과를 나타내는 클래스"""

    files: list[FileDiff] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """DiffResult를 딕셔너리로 변환합니다."""
        return {
            "files": [asdict(file) for file in self.files],
            "total_additions": sum(file.additions for file in self.files),
            "total_deletions": sum(file.deletions for file in self.files),
            "language_stats": self._get_language_stats(),
        }

    def to_json(self, indent: int = 2) -> str:
        """DiffResult를 JSON 문자열로 변환합니다."""
        return json.dumps(self.to_dict(), indent=indent)

    def _get_language_stats(self) -> dict[str, int]:
        """언어별 파일 수 통계를 반환합니다."""
        stats = {}
        for file in self.files:
            if file.language:
                stats[file.language] = stats.get(file.language, 0) + 1
        return stats

    def is_include_entirely_new_content(self) -> bool:
        """전체 새로운 내용을 포함하는 파일이 있는지 확인합니다."""
        return any(file.is_entirely_new_content() for file in self.files)
