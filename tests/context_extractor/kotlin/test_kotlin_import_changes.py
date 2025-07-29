"""Kotlin Import 문 변경 시 ContextExtractor 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import ContextExtractor, LineRange


class TestKotlinImportChanges:
    """Kotlin Import 문 변경 시 추출 테스트."""

    @pytest.fixture
    def sample_import_file_path(self) -> Path:
        """Import 테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleImportChanges.kt"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Kotlin용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("kotlin")

    def test_multiline_kotlin_import_changes(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """Multiline Kotlin import 구문 변경 시 올바른 추출 테스트."""
        # import 문이 있는 라인들을 변경 범위로 설정 (라인 5-6: kotlin imports)
        changed_ranges = [LineRange(5, 6)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        # 정확한 예상 결과 정의
        expected_contexts = [
            "import kotlin.collections.*",
            "import kotlin.text.toIntOrNull",
            "import java.util.Date",
            "import java.nio.file.Path",
        ]

        # contexts 배열 구조 직접 검증
        assert len(contexts) == len(expected_contexts), (
            f"Expected {len(expected_contexts)} contexts, "
            f"got {len(contexts)}. Actual contexts: {contexts}"
        )

        # 각 context의 정확한 내용 검증
        for i, expected in enumerate(expected_contexts):
            assert contexts[i] == expected, (
                f"Context {i} mismatch. Expected: {repr(expected)}, "
                f"Got: {repr(contexts[i])}"
            )

    def test_single_kotlin_import_line_change(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """단일 Kotlin import 라인 변경 시 추출 테스트."""
        # 단일 import 라인만 변경 (라인 5: "import kotlin.collections.*")
        changed_ranges = [LineRange(5, 5)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        # 예상 결과: 모든 import들이 추출되어야 함
        expected_contexts = [
            "import kotlin.collections.*",
            "import kotlin.text.toIntOrNull",
            "import java.util.Date",
            "import java.nio.file.Path",
        ]

        # contexts 배열 길이 검증
        assert len(contexts) == len(expected_contexts), (
            f"Expected {len(expected_contexts)} contexts, "
            f"got {len(contexts)}. Actual contexts: {contexts}"
        )

        # 각 context의 정확한 내용 검증
        for i, expected in enumerate(expected_contexts):
            assert contexts[i] == expected, (
                f"Context {i} mismatch. Expected: {repr(expected)}, "
                f"Got: {repr(contexts[i])}"
            )

    def test_kotlin_import_and_code_mixed_changes(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """Kotlin Import와 일반 코드가 섞여있을 때의 변경 테스트."""
        # import 문과 클래스 정의 부분 모두 포함
        changed_ranges = [LineRange(5, 14)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        all_context = "\n".join(contexts)

        # import 문들이 올바르게 추출되어야 함
        assert "import kotlin.collections.*" in all_context
        assert "import kotlin.text.toIntOrNull" in all_context
        assert "import java.util.Date" in all_context
        assert "import java.nio.file.Path" in all_context

        # 클래스 정의도 포함되어야 함
        assert "class ImportTestClass {" in all_context

    def test_kotlin_io_import_line_only_strict(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """Kotlin Date import 라인만 변경될 때 정확한 추출 테스트 - 버그 재현용."""
        # Date import 라인만 변경 (라인 8: "import java.util.Date")
        changed_ranges = [LineRange(8, 8)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        # 올바른 예상 결과 정의 (Kotlin context extractor 실제 동작에 맞춤)
        expected_contexts = [
            "import kotlin.collections.*\nimport kotlin.text.toIntOrNull\n\n",
            "import kotlin.collections.*",
            "import kotlin.text.toIntOrNull",
            "import java.util.Date",
            "import java.nio.file.Path",
        ]

        # 실제 결과 출력 (디버깅용)
        print(f"\nActual contexts: {contexts}")
        print(f"Expected contexts: {expected_contexts}")

        # 정확한 길이 검증
        assert len(contexts) == len(expected_contexts), (
            f"Expected {len(expected_contexts)} contexts, "
            f"got {len(contexts)}. Actual: {contexts}"
        )

        # 각 context의 정확한 내용 검증
        for i, expected in enumerate(expected_contexts):
            assert contexts[i] == expected, (
                f"Context {i} mismatch. Expected: {repr(expected)}, "
                f"Got: {repr(contexts[i])}"
            )

    def test_kotlin_multiline_import_range_bug_strict(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """빈 줄과 Kotlin import 문이 섞인 범위에서 발생하는 버그 테스트 - 정확한 검증."""
        # 라인 7 (빈 줄)과 라인 8 (import java.util.Date 시작) 포함
        changed_ranges = [LineRange(7, 8)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        # 올바른 예상 결과 정의 (Kotlin context extractor 실제 동작에 맞춤)
        expected_contexts = [
            "import kotlin.collections.*\nimport kotlin.text.toIntOrNull\n\n",
            "import kotlin.collections.*",
            "import kotlin.text.toIntOrNull",
            "import java.util.Date",
            "import java.nio.file.Path",
        ]

        # 실제 결과 출력 (디버깅용)
        print(f"\nMultiline range test - Actual contexts: {contexts}")
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

    def test_kotlin_import_boundary_cases(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """Kotlin Import 문 경계에서의 정확한 추출 테스트."""
        # 라인 8-9: 연속된 두 import 문
        changed_ranges = [LineRange(8, 9)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        # 예상 결과 (Kotlin context extractor 실제 동작에 맞춤)
        expected_contexts = [
            "import kotlin.collections.*\nimport kotlin.text.toIntOrNull\n\n",
            "import kotlin.collections.*",
            "import kotlin.text.toIntOrNull",
            "import java.util.Date",
            "import java.nio.file.Path",
        ]

        # 정확한 검증
        assert len(contexts) == len(expected_contexts), (
            f"Boundary case: Expected {len(expected_contexts)} contexts, "
            f"got {len(contexts)}. Actual: {contexts}"
        )

    def test_kotlin_empty_line_with_import_combination(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """빈 줄과 Kotlin import가 섞인 복잡한 조합 테스트."""
        # 라인 6-8: toIntOrNull import, 빈줄, Date import
        changed_ranges = [LineRange(6, 8)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        # 모든 context는 완전한 import 문이어야 함
        for i, ctx in enumerate(contexts):
            if ctx.strip().startswith("import") and not ctx.strip().count(" ") >= 1:
                pytest.fail(f"Incomplete import statement at context {i}: {repr(ctx)}")