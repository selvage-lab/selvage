"""FallbackContextExtractor: 지원하지 않는 언어를 위한 범용 컨텍스트 추출기."""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

from .line_range import LineRange
from .meaningless_change_filter import MeaninglessChangeFilter


class FallbackContextExtractor:
    """지원하지 않는 언어를 위한 범용 컨텍스트 추출기.

    tree-sitter를 사용할 수 없는 언어에 대해 텍스트 기반으로
    컨텍스트를 추출하는 fallback 구현체입니다.

    주요 특징:
    - 변경 라인 범위를 앞뒤로 5줄씩 확장
    - 겹치는 범위들을 병합하여 최적화
    - 정규표현식으로 범용 import 패턴 추출
    - 주석 및 빈 라인 필터링
    """

    # 범용 import/dependency 패턴들
    IMPORT_PATTERNS = [
        # C/C++
        r'^\s*#include\s*[<"].*[>"].*$',
        r"^\s*#define\s+\w+.*$",
        r"^\s*#ifdef\s+\w+.*$",
        r"^\s*#ifndef\s+\w+.*$",
        # C#
        r"^\s*using\s+[\w\.]+\s*;.*$",
        r"^\s*using\s+static\s+[\w\.]+\s*;.*$",
        # Go
        r"^\s*import\s*[\(\"].*[\)\"].*$",
        r"^\s*package\s+\w+.*$",
        # Rust
        r"^\s*use\s+[\w:]+.*$",
        r"^\s*extern\s+crate\s+\w+.*$",
        r"^\s*mod\s+\w+.*$",
        # Swift
        r"^\s*import\s+\w+.*$",
        r"^\s*@import\s+\w+.*$",
        # Dart/Flutter
        r'^\s*import\s+[\'"].*[\'"].*$',
        r'^\s*part\s+[\'"].*[\'"].*$',
        r"^\s*part\s+of\s+.*$",
        # PHP
        r'^\s*(require|require_once|include|include_once)\s*[\(\'""].*$',
        r"^\s*use\s+[\w\\]+.*$",
        # Ruby
        r'^\s*(require|load)\s+[\'"].*[\'"].*$',
        r"^\s*include\s+\w+.*$",
        # Perl
        r"^\s*use\s+[\w:]+.*$",
        r'^\s*require\s+[\'"].*[\'"].*$',
        # 범용 패턴 (다른 언어들)
        r'^\s*(require|include|load|import)\s*[\(\'""].*$',
    ]

    def __init__(self) -> None:
        """추출기 초기화."""
        # 정규표현식 컴파일
        self._import_regex = re.compile("|".join(self.IMPORT_PATTERNS), re.MULTILINE)
        # 무의미한 변경 필터링 객체
        self._filter = MeaninglessChangeFilter()

    def extract_contexts(
        self, file_content: str | None, changed_ranges: Sequence[LineRange]
    ) -> list[str]:
        """변경된 라인 범위들을 기반으로 컨텍스트 블록들을 추출한다.

        Args:
            file_content: 분석할 파일의 내용
            changed_ranges: 변경된 라인 범위들 (LineRange 객체들)

        Returns:
            추출된 컨텍스트 코드 블록들의 리스트

        Raises:
            ValueError: 파일 내용이 없거나 처리 오류
        """
        if not changed_ranges:
            return []

        # 1. 파일 내용 검증
        if not file_content:
            raise ValueError("파일 내용이 비어있습니다")

        try:
            code_text = file_content
            lines = code_text.splitlines()
        except Exception as e:
            raise ValueError(f"파일 내용 처리 오류: {e}") from e

        # 2. 1줄 무의미 변경 필터링
        meaningful_ranges = self._filter.filter_meaningful_ranges_with_lines(
            lines, changed_ranges
        )

        # 의미있는 변경이 없으면 빈 결과 반환
        if not meaningful_ranges:
            return []

        # 3. 변경 범위 확장 및 병합
        expanded_ranges = self._expand_ranges(meaningful_ranges)
        merged_ranges = self._merge_overlapping_ranges(expanded_ranges)

        # 4. Import 문 추출
        import_statements = self._extract_import_statements(code_text)

        # 5. 각 범위에서 컨텍스트 추출
        context_blocks = []

        # Import 문들을 하나의 블럭으로 그룹핑
        if import_statements:
            import_block = self._format_import_block(import_statements)
            context_blocks.append(import_block)

        # 변경된 범위의 컨텍스트를 구분선과 함께 추가
        for i, line_range in enumerate(merged_ranges, 1):
            context = self._extract_context_from_range(lines, line_range)
            if context:
                formatted_context = self._format_context_block(context, line_range, i)
                context_blocks.append(formatted_context)

        return context_blocks

    def _expand_ranges(self, ranges: Sequence[LineRange]) -> list[LineRange]:
        """변경 범위들을 앞뒤로 5줄씩 확장한다.

        Args:
            ranges: 원본 변경 범위들

        Returns:
            확장된 범위들의 리스트
        """
        expanded = []
        for line_range in ranges:
            # 앞뒤로 5줄씩 확장 (최소 1라인 보장)
            start = max(1, line_range.start_line - 5)
            end = line_range.end_line + 5
            expanded.append(LineRange(start, end))
        return expanded

    def _merge_overlapping_ranges(self, ranges: list[LineRange]) -> list[LineRange]:
        """겹치는 범위들을 병합하여 가장 큰 영역으로 통합한다.

        Args:
            ranges: 확장된 범위들

        Returns:
            병합된 범위들의 리스트 (시작 라인 기준 정렬)
        """
        if not ranges:
            return []

        # 시작 라인 기준으로 정렬
        sorted_ranges = sorted(ranges, key=lambda r: r.start_line)
        merged = [sorted_ranges[0]]

        for current in sorted_ranges[1:]:
            last_merged = merged[-1]

            # 현재 범위가 마지막 병합된 범위와 겹치거나 인접한 경우
            if current.start_line <= last_merged.end_line + 1:
                # 병합: 더 큰 끝 라인으로 확장
                merged[-1] = LineRange(
                    last_merged.start_line, max(last_merged.end_line, current.end_line)
                )
            else:
                # 겹치지 않으면 새로운 범위로 추가
                merged.append(current)

        return merged

    def _extract_import_statements(self, code_text: str) -> list[str]:
        """정규표현식으로 import 관련 문장들을 추출한다.

        Args:
            code_text: 전체 파일 텍스트

        Returns:
            추출된 import 문들의 리스트
        """
        import_lines = []

        # 각 라인별로 import 패턴 검사
        for line in code_text.splitlines():
            if self._import_regex.match(line):
                stripped_line = line.strip()
                if stripped_line and self._filter._is_meaningful_line(stripped_line):
                    import_lines.append(stripped_line)

        return import_lines

    def _extract_context_from_range(
        self, lines: list[str], line_range: LineRange
    ) -> str | None:
        """지정된 라인 범위에서 의미있는 컨텍스트를 추출한다.

        Args:
            lines: 파일의 모든 라인들
            line_range: 추출할 라인 범위

        Returns:
            추출된 컨텍스트 문자열 (의미있는 내용이 없으면 None)
        """
        # 범위 내 라인들 추출 (1-based 인덱스를 0-based로 변환)
        start_idx = max(0, line_range.start_line - 1)
        end_idx = min(len(lines), line_range.end_line)

        # 범위 내 모든 라인 추출 (원본 구조 보존)
        context_lines = []
        for i in range(start_idx, end_idx):
            if i < len(lines):
                context_lines.append(lines[i])

        # 라인이 있으면 컨텍스트 반환 (빈 라인, 주석 포함)
        if context_lines:
            return "\n".join(context_lines)

        return None

    def _format_import_block(self, import_statements: list[str]) -> str:
        """Import 문들을 하나의 블럭으로 포맷팅한다.

        Args:
            import_statements: Import 문들의 리스트

        Returns:
            포맷팅된 import 블럭
        """
        if not import_statements:
            return ""

        import_content = "\n".join(import_statements)
        return f"---- Dependencies/Imports ----\n{import_content}"

    def _format_context_block(
        self, context: str, line_range: LineRange, block_number: int
    ) -> str:
        """컨텍스트 블럭을 구분선과 함께 포맷팅한다.

        Args:
            context: 추출된 컨텍스트 내용
            line_range: 해당 라인 범위
            block_number: 블럭 번호

        Returns:
            포맷팅된 컨텍스트 블럭
        """
        header = (
            f"---- Context Block {block_number} "
            f"(Lines {line_range.start_line}-{line_range.end_line}) ----"
        )

        return f"{header}\n{context}"
