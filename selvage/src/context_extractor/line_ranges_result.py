"""LineRangesResult: 파일별 LineRange 결과를 나타내는 클래스."""

from __future__ import annotations

from dataclasses import dataclass

from .line_range import LineRange


@dataclass
class LineRangesResult:
    """파일별 LineRange 결과를 나타내는 클래스."""
    file_name: str
    line_ranges: list[LineRange]