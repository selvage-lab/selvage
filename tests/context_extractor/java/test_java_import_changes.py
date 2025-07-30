"""Java Import 문 변경 시 ContextExtractor 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import ContextExtractor, LineRange


class TestJavaImportChanges:
    """Java Import 문 변경 시 추출 테스트."""

    @pytest.fixture
    def sample_import_file_path(self) -> Path:
        """Import 테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleImportChanges.java"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Java용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("java")

    def test_multiline_java_import_changes(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """Multiline Java import 구문 변경 시 올바른 추출 테스트."""
        # import 문이 있는 라인들을 변경 범위로 설정 (라인 5-6: java.util imports)
        changed_ranges = [LineRange(5, 6)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        # 정확한 예상 결과 정의
        expected_context = (
            "---- Dependencies/Imports ----\n"
            "import java.util.List;\n"
            "import java.util.ArrayList;\n"
            "import java.io.IOException;\n"
            "import java.nio.file.Path;"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_context

    def test_single_java_import_line_change(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """단일 Java import 라인 변경 시 추출 테스트."""
        # 단일 import 라인만 변경 (라인 5: "import java.util.List;")
        changed_ranges = [LineRange(5, 5)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        # 예상 결과: 모든 import들이 추출되어야 함
        expected_contexts = (
            "---- Dependencies/Imports ----\n"
            "import java.util.List;\n"
            "import java.util.ArrayList;\n"
            "import java.io.IOException;\n"
            "import java.nio.file.Path;"
        )
        all_context = "\n".join(contexts)
        assert all_context == expected_contexts

    def test_java_import_and_code_mixed_changes(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """Java Import와 일반 코드가 섞여있을 때의 변경 테스트."""
        # import 문과 클래스 정의 부분 모두 포함
        changed_ranges = [LineRange(5, 14)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        all_context = "\n".join(contexts)

        # import 문들이 올바르게 추출되어야 함
        assert "import java.util.List;" in all_context
        assert "import java.util.ArrayList;" in all_context
        assert "import java.io.IOException;" in all_context
        assert "import java.nio.file.Path;" in all_context

        # 클래스 정의도 포함되어야 함
        assert "public class ImportTestClass {" in all_context

    def test_java_io_import_line_only_strict(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """Java IO import 라인만 변경될 때 정확한 추출 테스트 - 버그 재현용."""
        # IO import 라인만 변경 (라인 8: "import java.io.IOException;")
        changed_ranges = [LineRange(8, 8)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        # 올바른 예상 결과 정의
        expected_context = (
            "---- Dependencies/Imports ----\n"
            "import java.util.List;\n"
            "import java.util.ArrayList;\n"
            "import java.io.IOException;\n"
            "import java.nio.file.Path;"
        )
        all_context = "\n".join(contexts)
        assert all_context == expected_context

    def test_java_multiline_import_range_bug_strict(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """빈 줄과 Java import 문이 섞인 범위에서 발생하는 버그 테스트 - 정확한 검증."""
        # 라인 7 (빈 줄)과 라인 8 (import java.io.IOException; 시작) 포함
        changed_ranges = [LineRange(7, 8)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        # 올바른 예상 결과 정의
        expected_context = (
            "---- Dependencies/Imports ----\n"
            "import java.util.List;\n"
            "import java.util.ArrayList;\n"
            "import java.io.IOException;\n"
            "import java.nio.file.Path;"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_context

    def test_java_import_boundary_cases(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """Java Import 문 경계에서의 정확한 추출 테스트."""
        # 라인 8-9: 연속된 두 import 문
        changed_ranges = [LineRange(8, 9)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        # 예상 결과
        expected_context = (
            "---- Dependencies/Imports ----\n"
            "import java.util.List;\n"
            "import java.util.ArrayList;\n"
            "import java.io.IOException;\n"
            "import java.nio.file.Path;"
        )
        all_context = "\n".join(contexts)
        assert all_context == expected_context

    def test_java_empty_line_with_import_combination(
        self,
        extractor: ContextExtractor,
        sample_import_file_path: Path,
    ) -> None:
        """빈 줄과 Java import가 섞인 복잡한 조합 테스트."""
        # 라인 6-8: ArrayList import, 빈줄, IOException import
        changed_ranges = [LineRange(6, 8)]
        contexts = extractor.extract_contexts(sample_import_file_path, changed_ranges)

        expected_context = (
            "---- Dependencies/Imports ----\n"
            "import java.util.List;\n"
            "import java.util.ArrayList;\n"
            "import java.io.IOException;\n"
            "import java.nio.file.Path;"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_context
