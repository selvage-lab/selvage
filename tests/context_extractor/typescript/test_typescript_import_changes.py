"""TypeScript Import 문 변경 시 ContextExtractor 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import ContextExtractor, LineRange


class TestTypeScriptImportChanges:
    """TypeScript Import 문 변경 시 추출 테스트."""

    @pytest.fixture
    def sample_import_file_content(self) -> str:
        """Import 테스트용 샘플 파일 내용을 반환합니다."""
        file_path = Path(__file__).parent / "SampleImportChanges.ts"
        return file_path.read_text(encoding="utf-8")

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """TypeScript용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("typescript")

    def test_multiline_typescript_import_changes(
        self,
        extractor: ContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """Multiline TypeScript import 구문 변경 시 올바른 추출 테스트."""
        # import 문이 있는 라인들을 변경 범위로 설정 (라인 5-6: namespace & named imports)
        changed_ranges = [LineRange(5, 6)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 정확한 예상 결과 정의 (TypeScript context extractor 실제 동작에 맞춤)
        expected_context = (
            "---- Dependencies/Imports ----\n"
            "import * as fs from 'fs';\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import path from 'path';\n"
            "import type { Stats } from 'fs';"
        )

        all_context = "\n".join(contexts)
        assert expected_context in all_context

    def test_single_typescript_import_line_change(
        self,
        extractor: ContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """단일 TypeScript import 라인 변경 시 추출 테스트."""
        # 단일 import 라인만 변경 (라인 5: "import * as fs from 'fs';")
        changed_ranges = [LineRange(5, 5)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 예상 결과: 모든 import들이 추출되어야 함
        expected_context = (
            "---- Dependencies/Imports ----\n"
            "import * as fs from 'fs';\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import path from 'path';\n"
            "import type { Stats } from 'fs';"
        )

        all_context = "\n".join(contexts)
        assert expected_context in all_context

    def test_typescript_import_and_code_mixed_changes(
        self,
        extractor: ContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """TypeScript Import와 일반 코드가 섞여있을 때의 변경 테스트."""
        # import 문과 interface 정의 부분 모두 포함
        changed_ranges = [LineRange(5, 15)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        all_context = "\n".join(contexts)

        # import 문들이 올바르게 추출되어야 함
        assert "import * as fs from 'fs';" in all_context
        assert "import { readFile, writeFile } from 'fs/promises';" in all_context
        assert "import path from 'path';" in all_context
        assert "import type { Stats } from 'fs';" in all_context

        # interface 정의도 포함되어야 함
        assert "interface ProcessResult {" in all_context

    def test_typescript_io_import_line_only_strict(
        self,
        extractor: ContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """TypeScript fs/promises import 라인만 변경될 때 정확한 추출 테스트 - 버그 재현용."""
        # fs/promises import 라인만 변경 (라인 6: "import { readFile, writeFile } from 'fs/promises';")
        changed_ranges = [LineRange(6, 6)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 올바른 예상 결과 정의
        expected_context = (
            "---- Dependencies/Imports ----\n"
            "import * as fs from 'fs';\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import path from 'path';\n"
            "import type { Stats } from 'fs';"
        )

        all_context = "\n".join(contexts)
        assert expected_context in all_context

    def test_typescript_multiline_import_range_bug_strict(
        self,
        extractor: ContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """빈 줄과 TypeScript import 문이 섞인 범위에서 발생하는 버그 테스트 - 정확한 검증."""
        # 라인 7 (빈 줄)과 라인 8 (import path 시작) 포함
        changed_ranges = [LineRange(7, 8)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 올바른 예상 결과 정의
        expected_context = (
            "---- Dependencies/Imports ----\n"
            "import * as fs from 'fs';\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import path from 'path';\n"
            "import type { Stats } from 'fs';"
        )

        all_context = "\n".join(contexts)
        assert expected_context in all_context

    def test_typescript_import_boundary_cases(
        self,
        extractor: ContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """TypeScript Import 문 경계에서의 정확한 추출 테스트."""
        # 라인 8-9: 연속된 두 import 문
        changed_ranges = [LineRange(8, 9)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 예상 결과
        expected_context = (
            "---- Dependencies/Imports ----\n"
            "import * as fs from 'fs';\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import path from 'path';\n"
            "import type { Stats } from 'fs';"
        )

        # 정확한 검증
        all_context = "\n".join(contexts)
        assert expected_context in all_context

    def test_typescript_empty_line_with_import_combination(
        self,
        extractor: ContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """빈 줄과 TypeScript import가 섞인 복잡한 조합 테스트."""
        # 라인 6-8: fs/promises import, 빈줄, path import
        changed_ranges = [LineRange(6, 8)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 모든 context는 완전한 import 문이어야 함
        for i, ctx in enumerate(contexts):
            if (
                ctx.strip().startswith("import")
                and "from" not in ctx
                and "type" not in ctx
            ):
                if not (ctx.strip().endswith("';") or "default" in ctx):
                    pytest.fail(
                        f"Incomplete import statement at context {i}: {repr(ctx)}"
                    )
