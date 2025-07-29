"""Import 문 변경 시 ContextExtractor 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import ContextExtractor, LineRange


class TestImportChanges:
    """Import 문 변경 시 추출 테스트."""

    @pytest.fixture
    def sample_import_file_path(self) -> Path:
        """Import 테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "sample_import_changes.py"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Python용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("python")

    def test_multiline_import_changes(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """Multiline import 구문 변경 시 올바른 추출 테스트."""
        # import 문이 있는 라인들을 변경 범위로 설정 (라인 3-5: import re, from dataclasses, 빈줄)
        changed_ranges = [LineRange(3, 5)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        # 정확한 예상 결과 정의
        expected_contexts = [
            "import re",
            "from dataclasses import dataclass",
            "from selvage.src.context_extractor.line_range import LineRange",
            "from selvage.src.diff_parser.utils.hunk_line_calculator import HunkLineCalculator",
        ]

        # contexts 배열 구조 직접 검증
        assert len(contexts) == len(expected_contexts), (
            f"Expected {len(expected_contexts)} contexts, got {len(contexts)}. "
            f"Actual contexts: {contexts}"
        )

        # 각 context의 정확한 내용 검증
        for i, expected in enumerate(expected_contexts):
            assert contexts[i] == expected, (
                f"Context {i} mismatch. Expected: {repr(expected)}, "
                f"Got: {repr(contexts[i])}"
            )

        # 버그 감지: 'from'만 있는 잘못된 context 직접 확인
        isolated_from_contexts = [ctx for ctx in contexts if ctx.strip() == "from"]
        assert len(isolated_from_contexts) == 0, (
            f"Found {len(isolated_from_contexts)} isolated 'from' contexts: "
            f"{isolated_from_contexts}"
        )

    def test_single_import_line_change(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """단일 import 라인 변경 시 추출 테스트."""
        # 단일 import 라인만 변경 (라인 3: "import re")
        changed_ranges = [LineRange(3, 3)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        # 예상 결과: import re와 모든 의존성 import들이 추출되어야 함
        expected_contexts = [
            "import re",
            "from dataclasses import dataclass",
            "from selvage.src.context_extractor.line_range import LineRange",
            "from selvage.src.diff_parser.utils.hunk_line_calculator import HunkLineCalculator",
        ]

        # contexts 배열 길이 검증
        assert len(contexts) == len(expected_contexts), (
            f"Expected {len(expected_contexts)} contexts, got {len(contexts)}. "
            f"Actual contexts: {contexts}"
        )

        # 각 context의 정확한 내용 검증
        for i, expected in enumerate(expected_contexts):
            assert contexts[i] == expected, (
                f"Context {i} mismatch. Expected: {repr(expected)}, "
                f"Got: {repr(contexts[i])}"
            )

        # 버그 감지: 'from'만 있는 잘못된 context가 없어야 함
        isolated_from_contexts = [ctx for ctx in contexts if ctx.strip() == "from"]
        assert len(isolated_from_contexts) == 0, (
            f"Found isolated 'from' contexts: {isolated_from_contexts}"
        )

    def test_import_and_code_mixed_changes(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """Import와 일반 코드가 섞여있을 때의 변경 테스트."""
        # import 문과 클래스 정의 부분 모두 포함
        changed_ranges = [LineRange(3, 14)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

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
        sample_import_file_path: Path,
    ) -> None:
        """from import 라인만 변경될 때 정확한 추출 테스트 - 버그 재현용."""
        # dataclass import 라인만 변경 (라인 4: "from dataclasses import dataclass")
        changed_ranges = [LineRange(4, 4)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        # 올바른 예상 결과 정의
        expected_contexts = [
            "import re",
            "from dataclasses import dataclass",
            "from selvage.src.context_extractor.line_range import LineRange",
            "from selvage.src.diff_parser.utils.hunk_line_calculator import HunkLineCalculator",
        ]

        # 실제 결과 출력 (디버깅용)
        print(f"\nActual contexts: {contexts}")
        print(f"Expected contexts: {expected_contexts}")

        # 정확한 길이 검증
        assert len(contexts) == len(expected_contexts), (
            f"Expected {len(expected_contexts)} contexts, got {len(contexts)}. "
            f"Actual: {contexts}"
        )

        # 각 context의 정확한 내용 검증
        for i, expected in enumerate(expected_contexts):
            assert contexts[i] == expected, (
                f"Context {i} mismatch. Expected: {repr(expected)}, "
                f"Got: {repr(contexts[i])}"
            )

    def test_multiline_import_range_bug_strict(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """빈 줄과 import 문이 섞인 범위에서 발생하는 버그 테스트 - 정확한 검증."""
        # 라인 6 (빈 줄)과 라인 7 (from selvage... import 시작) 포함
        changed_ranges = [LineRange(6, 7)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        # 올바른 예상 결과 정의
        expected_contexts = [
            "import re",
            "from dataclasses import dataclass",
            "from selvage.src.context_extractor.line_range import LineRange",
            (
                "from selvage.src.diff_parser.utils.hunk_line_calculator import "
                "HunkLineCalculator"
            ),
        ]

        # 실제 결과 출력 (디버깅용)
        print(f"\nMultiline range test - Actual contexts: {contexts}")
        print(f"Expected contexts: {expected_contexts}")

        # 버그 감지: 'from'만 있는 context 직접 확인
        isolated_from_contexts = [ctx for ctx in contexts if ctx.strip() == "from"]
        assert len(isolated_from_contexts) == 0, (
            f"Found {len(isolated_from_contexts)} isolated 'from' contexts "
            f"in multiline range. Full contexts array: {contexts}"
        )

        # 정확한 길이 검증
        assert len(contexts) == len(expected_contexts), (
            f"Expected {len(expected_contexts)} contexts, got {len(contexts)}. "
            f"Actual: {contexts}"
        )

        # 각 context의 정확한 내용 검증
        for i, expected in enumerate(expected_contexts):
            assert contexts[i] == expected, (
                f"Context {i} mismatch. Expected: {repr(expected)}, "
                f"Got: {repr(contexts[i])}"
            )

    def test_exact_import_boundary_cases(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """Import 문 경계에서의 정확한 추출 테스트."""
        # 라인 7-8: 연속된 두 from import 문
        changed_ranges = [LineRange(7, 8)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        # 예상 결과
        expected_contexts = [
            "import re",
            "from dataclasses import dataclass",
            "from selvage.src.context_extractor.line_range import LineRange",
            (
                "from selvage.src.diff_parser.utils.hunk_line_calculator import "
                "HunkLineCalculator"
            ),
        ]

        # 버그 감지
        isolated_from_contexts = [ctx for ctx in contexts if ctx.strip() == "from"]
        assert len(isolated_from_contexts) == 0, (
            f"Found {len(isolated_from_contexts)} isolated 'from' contexts: "
            f"{isolated_from_contexts}. Full contexts: {contexts}"
        )

        # 정확한 검증
        assert len(contexts) == len(expected_contexts), (
            f"Boundary case: Expected {len(expected_contexts)} contexts, "
            f"got {len(contexts)}. Actual: {contexts}"
        )

    def test_empty_line_with_import_combination(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """빈 줄과 import가 섞인 복잡한 조합 테스트."""
        # 라인 4-7: 빈줄, from dataclasses, 빈줄, from selvage 시작
        changed_ranges = [LineRange(4, 7)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        # 버그 감지가 핵심 목적
        isolated_from_contexts = [ctx for ctx in contexts if ctx.strip() == "from"]
        assert len(isolated_from_contexts) == 0, (
            f"Found {len(isolated_from_contexts)} isolated 'from' contexts: "
            f"{isolated_from_contexts}. Full contexts: {contexts}"
        )

        # 모든 context는 완전한 import 문이어야 함
        for i, ctx in enumerate(contexts):
            if ctx.strip().startswith("from") and "import" not in ctx:
                pytest.fail(
                    f"Incomplete from statement at context {i}: {repr(ctx)}"
                )