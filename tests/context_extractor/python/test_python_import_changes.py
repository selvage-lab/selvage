"""Import 문 변경 시 ContextExtractor 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import ContextExtractor, LineRange


class TestImportChanges:
    """Import 문 변경 시 추출 테스트."""

    @pytest.fixture
    def sample_import_file_content(self) -> str:
        """Import 테스트용 샘플 파일 내용을 반환합니다."""
        file_path = Path(__file__).parent / "sample_import_changes.py"
        return file_path.read_text(encoding="utf-8")

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Python용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("python")

    def test_multiline_import_changes(
        self,
        extractor: ContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """Multiline import 구문 변경 시 올바른 추출 테스트."""
        # import 문이 있는 라인들을 변경 범위로 설정 (라인 3-5: import re, from dataclasses, 빈줄)
        changed_ranges = [LineRange(3, 5)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 정확한 예상 결과 정의
        expected_context = (
            "---- Dependencies/Imports ----\n"
            "import re\n"
            "from dataclasses import dataclass\n"
            "from selvage.src.context_extractor.line_range import LineRange\n"
            "from selvage.src.diff_parser.utils.hunk_line_calculator import HunkLineCalculator"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_context

    def test_single_import_line_change(
        self,
        extractor: ContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """단일 import 라인 변경 시 추출 테스트."""
        # 단일 import 라인만 변경 (라인 3: "import re")
        changed_ranges = [LineRange(3, 3)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 예상 결과: import re와 모든 의존성 import들이 추출되어야 함
        expected_context = (
            "---- Dependencies/Imports ----\n"
            "import re\n"
            "from dataclasses import dataclass\n"
            "from selvage.src.context_extractor.line_range import LineRange\n"
            "from selvage.src.diff_parser.utils.hunk_line_calculator import HunkLineCalculator"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_context

    def test_import_and_code_mixed_changes(
        self,
        extractor: ContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """Import와 일반 코드가 섞여있을 때의 변경 테스트."""
        # import 문과 클래스 정의 부분 모두 포함
        changed_ranges = [LineRange(3, 14)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        all_context = "\n".join(contexts)

        # import 문들이 올바르게 추출되어야 함
        assert "import re" in all_context
        assert "from dataclasses import dataclass" in all_context

        # 클래스 정의도 포함되어야 함
        assert "class ImportTestClass:" in all_context
        assert "@dataclass" in all_context

    def test_from_import_line_only_strict(
        self,
        extractor: ContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """from import 라인만 변경될 때 정확한 추출 테스트 - 버그 재현용."""
        # dataclass import 라인만 변경 (라인 4: "from dataclasses import dataclass")
        changed_ranges = [LineRange(4, 4)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 올바른 예상 결과 정의
        expected_context = (
            "---- Dependencies/Imports ----\n"
            "import re\n"
            "from dataclasses import dataclass\n"
            "from selvage.src.context_extractor.line_range import LineRange\n"
            "from selvage.src.diff_parser.utils.hunk_line_calculator import HunkLineCalculator"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_context

    def test_multiline_import_range_bug_strict(
        self,
        extractor: ContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """빈 줄과 import 문이 섞인 범위에서 발생하는 버그 테스트 - 정확한 검증."""
        # 라인 6 (빈 줄)과 라인 7 (from selvage... import 시작) 포함
        changed_ranges = [LineRange(6, 7)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 올바른 예상 결과 정의
        expected_context = (
            "---- Dependencies/Imports ----\n"
            "import re\n"
            "from dataclasses import dataclass\n"
            "from selvage.src.context_extractor.line_range import LineRange\n"
            "from selvage.src.diff_parser.utils.hunk_line_calculator import HunkLineCalculator"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_context
