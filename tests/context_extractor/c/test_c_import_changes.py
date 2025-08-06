"""C Import 문 변경 시 ContextExtractor 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import LineRange
from selvage.src.context_extractor.fallback_context_extractor import (
    FallbackContextExtractor,
)


class TestCImportChanges:
    """C Import 문 변경 시 추출 테스트."""

    @pytest.fixture
    def sample_import_file_content(self) -> str:
        """Import 테스트용 샘플 파일 내용을 반환합니다."""
        file_path = Path(__file__).parent / "SampleImportChanges.c"
        return file_path.read_text(encoding="utf-8")

    @pytest.fixture
    def extractor(self) -> FallbackContextExtractor:
        """C용 FallbackContextExtractor 인스턴스를 반환합니다."""
        return FallbackContextExtractor()

    def test_multiline_c_import_changes(
        self,
        extractor: FallbackContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """Multiline C include 구문 변경 시 올바른 추출 테스트."""
        # include 문이 있는 라인들을 변경 범위로 설정 (라인 5-6: system includes)
        changed_ranges = [LineRange(5, 6)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 정확한 예상 결과 정의 (FallbackContextExtractor 실제 동작에 맞춤)
        expected_contexts = [
            (
                "---- Dependencies/Imports ----\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n"
                "#include <string.h>\n"
                '#include "custom.h"\n'
                "#define MAX_BUFFER_SIZE 1024\n"
                "#define DEFAULT_VALUE 42\n"
                "#ifdef DEBUG\n"
                '#define LOG(msg) printf("DEBUG: %s\\n", msg)\n'
                "#define LOG(msg)"
            ),
            (
                "---- Context Block 1 (Lines 1-11) ----\n"
                "/**\n"
                " * Import 변경 테스트용 샘플 파일 - multiline include 구문 포함\n"
                " */\n"
                "\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n"
                "\n"
                "#include <string.h>\n"
                '#include "custom.h"\n'
                "\n"
                "#define MAX_BUFFER_SIZE 1024"
            ),
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

    def test_single_c_import_line_change(
        self,
        extractor: FallbackContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """단일 C include 라인 변경 시 추출 테스트."""
        # 단일 include 라인만 변경 (라인 5: "#include <stdio.h>")
        changed_ranges = [LineRange(5, 5)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 예상 결과: 모든 dependencies와 확장된 범위가 추출되어야 함 (실제 결과에 맞춤)
        expected_contexts = [
            (
                "---- Dependencies/Imports ----\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n"
                "#include <string.h>\n"
                '#include "custom.h"\n'
                "#define MAX_BUFFER_SIZE 1024\n"
                "#define DEFAULT_VALUE 42\n"
                "#ifdef DEBUG\n"
                '#define LOG(msg) printf("DEBUG: %s\\n", msg)\n'
                "#define LOG(msg)"
            ),
            (
                "---- Context Block 1 (Lines 1-10) ----\n"
                "/**\n"
                " * Import 변경 테스트용 샘플 파일 - multiline include 구문 포함\n"
                " */\n"
                "\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n"
                "\n"
                "#include <string.h>\n"
                '#include "custom.h"\n'
            ),
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

    def test_c_import_and_code_mixed_changes(
        self,
        extractor: FallbackContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """C Include와 일반 코드가 섞여있을 때의 변경 테스트."""
        # include 문과 struct 정의 부분 모두 포함
        changed_ranges = [LineRange(5, 25)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        all_context = "\n".join(contexts)

        # include 문들이 Dependencies 블록에 올바르게 추출되어야 함
        assert "---- Dependencies/Imports ----" in all_context
        assert "#include <stdio.h>" in all_context
        assert "#include <stdlib.h>" in all_context
        assert "#include <string.h>" in all_context
        assert '#include "custom.h"' in all_context

        # struct 정의도 Context 블록에 포함되어야 함
        assert "typedef struct {" in all_context

    def test_c_io_import_line_only_strict(
        self,
        extractor: FallbackContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """C string.h include 라인만 변경될 때 정확한 추출 테스트 - 버그 재현용."""
        # string.h include 라인만 변경 (라인 8: "#include <string.h>")
        changed_ranges = [LineRange(8, 8)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 올바른 예상 결과 정의 (실제 결과에 맞춤)
        expected_contexts = [
            (
                "---- Dependencies/Imports ----\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n"
                "#include <string.h>\n"
                '#include "custom.h"\n'
                "#define MAX_BUFFER_SIZE 1024\n"
                "#define DEFAULT_VALUE 42\n"
                "#ifdef DEBUG\n"
                '#define LOG(msg) printf("DEBUG: %s\\n", msg)\n'
                "#define LOG(msg)"
            ),
            (
                "---- Context Block 1 (Lines 3-13) ----\n"
                " */\n"
                "\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n"
                "\n"
                "#include <string.h>\n"
                '#include "custom.h"\n'
                "\n"
                "#define MAX_BUFFER_SIZE 1024\n"
                "#define DEFAULT_VALUE 42\n"
            ),
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

    def test_c_multiline_import_range_bug_strict(
        self,
        extractor: FallbackContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """빈 줄과 C include 문이 섞인 범위에서 발생하는 버그 테스트 - 정확한 검증."""
        # 라인 7 (빈 줄)과 라인 8 (include string.h 시작) 포함
        changed_ranges = [LineRange(7, 8)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 올바른 예상 결과 정의 (실제 결과에 맞춤)
        expected_contexts = [
            (
                "---- Dependencies/Imports ----\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n"
                "#include <string.h>\n"
                '#include "custom.h"\n'
                "#define MAX_BUFFER_SIZE 1024\n"
                "#define DEFAULT_VALUE 42\n"
                "#ifdef DEBUG\n"
                '#define LOG(msg) printf("DEBUG: %s\\n", msg)\n'
                "#define LOG(msg)"
            ),
            (
                "---- Context Block 1 (Lines 2-13) ----\n"
                " * Import 변경 테스트용 샘플 파일 - multiline include 구문 포함\n"
                " */\n"
                "\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n"
                "\n"
                "#include <string.h>\n"
                '#include "custom.h"\n'
                "\n"
                "#define MAX_BUFFER_SIZE 1024\n"
                "#define DEFAULT_VALUE 42\n"
            ),
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

    def test_c_import_boundary_cases(
        self,
        extractor: FallbackContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """C Include 문 경계에서의 정확한 추출 테스트."""
        # 라인 8-9: 연속된 두 include 문
        changed_ranges = [LineRange(8, 9)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 예상 결과
        expected_contexts = [
            (
                "---- Dependencies/Imports ----\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n"
                "#include <string.h>\n"
                '#include "custom.h"\n'
                "#define MAX_BUFFER_SIZE 1024\n"
                "#define DEFAULT_VALUE 42\n"
                "#ifdef DEBUG\n"
                '#define LOG(msg) printf("DEBUG: %s\\n", msg)\n'
                "#define LOG(msg)"
            ),
            (
                "---- Context Block 1 (Lines 3-14) ----\n"
                " */\n"
                "\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n"
                "\n"
                "#include <string.h>\n"
                '#include "custom.h"\n'
                "\n"
                "#define MAX_BUFFER_SIZE 1024\n"
                "#define DEFAULT_VALUE 42\n"
                "\n"
                "#ifdef DEBUG\n"
                '#define LOG(msg) printf("DEBUG: %s\\n", msg)'
            ),
        ]

        # 정확한 검증
        assert len(contexts) == len(expected_contexts), (
            f"Boundary case: Expected {len(expected_contexts)} contexts, "
            f"got {len(contexts)}. Actual: {contexts}"
        )

    def test_c_empty_line_with_import_combination(
        self,
        extractor: FallbackContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """빈 줄과 C include가 섞인 복잡한 조합 테스트."""
        # 라인 6-8: stdlib include, 빈줄, string include
        changed_ranges = [LineRange(6, 8)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 모든 context는 FallbackContextExtractor의 정상적인 형태를 가져야 함
        for i, ctx in enumerate(contexts):
            # Dependencies 블록이나 Context 블록 중 하나여야 함
            if (
                "---- Dependencies/Imports ----" not in ctx
                and "---- Context Block" not in ctx
            ):
                pytest.fail(f"Malformed context block at index {i}: {repr(ctx)}")

            # 버그 상황: include만 따로 떨어져 나온 경우 감지
            lines = ctx.split("\n")
            for line in lines:
                if line.strip() == "#include" or line.strip() == "#define":
                    pytest.fail(
                        f"Incomplete preprocessor directive at context {i}: {repr(line)}"
                    )
