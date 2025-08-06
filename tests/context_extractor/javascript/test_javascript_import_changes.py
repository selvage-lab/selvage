"""JavaScript Import 문 변경 시 ContextExtractor 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import ContextExtractor, LineRange


class TestJavaScriptImportChanges:
    """JavaScript Import 문 변경 시 추출 테스트."""

    @pytest.fixture
    def sample_import_file_content(self) -> str:
        """Import 테스트용 샘플 파일 내용을 반환합니다."""
        file_path = Path(__file__).parent / "SampleImportChanges.js"
        return file_path.read_text(encoding="utf-8")

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """JavaScript용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("javascript")

    def test_multiline_javascript_import_changes(
        self,
        extractor: ContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """Multiline JavaScript import 구문 변경 시 올바른 추출 테스트."""
        # import 문이 있는 라인들을 변경 범위로 설정 (라인 5-6: CommonJS imports)
        changed_ranges = [LineRange(5, 6)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 정확한 예상 결과 정의 (JavaScript context extractor 실제 동작에 맞춤)
        expected_context = (
            "---- Dependencies/Imports ----\n"
            "const fs = require('fs');\n"
            "const path = require('path');\n"
            "const util = require('util');\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import { basename, dirname } from 'path';\n"
            "import axios from 'axios';"
        )

        all_context = "\n".join(contexts)
        assert expected_context in all_context

    def test_single_javascript_import_line_change(
        self,
        extractor: ContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """단일 JavaScript import 라인 변경 시 추출 테스트."""
        # 단일 import 라인만 변경 (라인 5: "const fs = require('fs');")
        changed_ranges = [LineRange(5, 5)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 예상 결과: 모든 import들이 추출되어야 함 (JavaScript context extractor 실제 동작에 맞춤)
        expected_context = (
            "---- Dependencies/Imports ----\n"
            "const fs = require('fs');\n"
            "const path = require('path');\n"
            "const util = require('util');\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import { basename, dirname } from 'path';\n"
            "import axios from 'axios';"
        )

        all_context = "\n".join(contexts)
        assert expected_context in all_context

    def test_javascript_import_and_code_mixed_changes(
        self,
        extractor: ContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """JavaScript Import와 일반 코드가 섞여있을 때의 변경 테스트."""
        # import 문과 클래스 정의 부분 모두 포함
        changed_ranges = [LineRange(6, 26)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        all_context = "\n".join(contexts)

        # import 문들이 올바르게 추출되어야 함
        assert "const fs = require('fs');" in all_context
        assert "const path = require('path');" in all_context
        assert "const util = require('util');" in all_context
        assert "import { readFile, writeFile } from 'fs/promises';" in all_context
        assert "import { basename, dirname } from 'path';" in all_context
        assert "import axios from 'axios';" in all_context

        # 클래스 정의도 포함되어야 함
        assert "class ImportTestClass {" in all_context

    def test_javascript_io_import_line_only_strict(
        self,
        extractor: ContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """JavaScript fs/promises import 라인만 변경될 때 정확한 추출 테스트 - 버그 재현용."""
        changed_ranges = [LineRange(11, 11)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        expected_context = (
            "---- Dependencies/Imports ----\n"
            "const fs = require('fs');\n"
            "const path = require('path');\n"
            "const util = require('util');\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import { basename, dirname } from 'path';\n"
            "import axios from 'axios';"
        )

        all_context = "\n".join(contexts)
        assert expected_context in all_context

    def test_javascript_multiline_import_range_bug_strict(
        self,
        extractor: ContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """빈 줄과 JavaScript import 문이 섞인 범위에서 발생하는 버그 테스트 - 정확한 검증."""
        changed_ranges = [LineRange(11, 12)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        expected_context = (
            "---- Dependencies/Imports ----\n"
            "const fs = require('fs');\n"
            "const path = require('path');\n"
            "const util = require('util');\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import { basename, dirname } from 'path';\n"
            "import axios from 'axios';"
        )

        all_context = "\n".join(contexts)
        assert expected_context in all_context

    def test_javascript_import_boundary_cases(
        self,
        extractor: ContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """JavaScript Import 문 경계에서의 정확한 추출 테스트."""
        # 라인 9-10: 연속된 두 import 문
        changed_ranges = [LineRange(11, 13)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 예상 결과
        expected_context = (
            "---- Dependencies/Imports ----\n"
            "const fs = require('fs');\n"
            "const path = require('path');\n"
            "const util = require('util');\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import { basename, dirname } from 'path';\n"
            "import axios from 'axios';"
        )

        # 정확한 검증
        all_context = "\n".join(contexts)
        assert expected_context in all_context

    def test_javascript_empty_line_with_import_combination(
        self,
        extractor: ContextExtractor,
        sample_import_file_content: str,
    ) -> None:
        """빈 줄과 JavaScript import가 섞인 복잡한 조합 테스트."""
        # 라인 7-9: util import, 빈줄, fs/promises import
        changed_ranges = [LineRange(8, 11)]
        contexts = extractor.extract_contexts(
            sample_import_file_content, changed_ranges
        )

        # 예상 결과
        expected_context = (
            "---- Dependencies/Imports ----\n"
            "const fs = require('fs');\n"
            "const path = require('path');\n"
            "const util = require('util');\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import { basename, dirname } from 'path';\n"
            "import axios from 'axios';"
        )

        # 정확한 검증
        all_context = "\n".join(contexts)
        assert expected_context in all_context
