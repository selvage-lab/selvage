"""데코레이터 관련 ContextExtractor 테스트 케이스."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import ContextExtractor, LineRange


class TestDecoratedExtraction:
    """데코레이터가 포함된 클래스/함수 추출 테스트."""

    @pytest.fixture
    def decorated_file_content(self) -> str:
        """데코레이터가 포함된 테스트용 샘플 파일 내용을 반환합니다."""
        file_path = Path(__file__).parent / "sample_decorated_class.py"
        return file_path.read_text(encoding="utf-8")

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Python용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("python")

    def test_dataclass_extraction(
        self,
        extractor: ContextExtractor,
        decorated_file_content: str,
    ) -> None:
        """@dataclass가 붙은 클래스 추출 시 데코레이터 포함 테스트."""
        # UserInfo 클래스의 본문 내부를 변경한 경우
        changed_ranges = [LineRange(23, 24)]  # name: str 라인
        contexts = extractor.extract_contexts(decorated_file_content, changed_ranges)

        # 정확한 추출 결과 검증
        expected_result = (
            "---- Dependencies/Imports ----\n"
            "from dataclasses import dataclass, field\n"
            "from functools import wraps\n"
            "from typing import ClassVar\n"
            "---- Context Block 1 (Lines 19-30) ----\n"
            "@dataclass\n"
            "class UserInfo:\n"
            '    """사용자 정보를 담는 데이터클래스"""\n'
            "\n"
            "    name: str\n"
            "    age: int\n"
            '    email: str = field(default="")\n'
            "    active: bool = field(default=True)\n"
            "\n"
            "    def get_display_name(self) -> str:\n"
            '        """표시용 이름 반환"""\n'
            '        return f"{self.name} ({self.age})"'
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_method_with_property_decorator(
        self,
        extractor: ContextExtractor,
        decorated_file_content: str,
    ) -> None:
        """@property 데코레이터가 붙은 메서드 추출 테스트."""
        # is_debug_enabled 메서드 내부 변경
        changed_ranges = [LineRange(44, 45)]  # return self.debug_mode 라인
        contexts = extractor.extract_contexts(decorated_file_content, changed_ranges)

        # 정확한 추출 결과 검증
        expected_result = (
            "---- Dependencies/Imports ----\n"
            "from dataclasses import dataclass, field\n"
            "from functools import wraps\n"
            "from typing import ClassVar\n"
            "---- Context Block 1 (Lines 42-45) ----\n"
            "    @property\n"
            "    def is_debug_enabled(self) -> bool:\n"
            '        """디버그 모드 활성화 여부"""\n'
            "        return self.debug_mode"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_multiple_decorators(
        self,
        extractor: ContextExtractor,
        decorated_file_content: str,
    ) -> None:
        """여러 데코레이터가 붙은 메서드 추출 테스트."""
        # is_connected 메서드 내부 변경 (log_calls + property 데코레이터)
        changed_ranges = [LineRange(73, 74)]  # return True 라인
        contexts = extractor.extract_contexts(decorated_file_content, changed_ranges)

        # 정확한 추출 결과 검증
        expected_result = (
            "---- Dependencies/Imports ----\n"
            "from dataclasses import dataclass, field\n"
            "from functools import wraps\n"
            "from typing import ClassVar\n"
            "---- Context Block 1 (Lines 71-75) ----\n"
            "    @log_calls\n"
            "    @property\n"
            "    def is_connected(self) -> bool:\n"
            '        """연결 상태 확인"""\n'
            "        return True"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_decorated_function_extraction(
        self,
        extractor: ContextExtractor,
        decorated_file_content: str,
    ) -> None:
        """@log_calls 데코레이터가 붙은 함수 추출 테스트."""
        # process_user_data 함수 내부 변경
        changed_ranges = [LineRange(77, 79)]  # 함수 본문
        contexts = extractor.extract_contexts(decorated_file_content, changed_ranges)

        # 정확한 추출 결과 검증
        expected_result = (
            "---- Dependencies/Imports ----\n"
            "from dataclasses import dataclass, field\n"
            "from functools import wraps\n"
            "from typing import ClassVar\n"
            "---- Context Block 1 (Lines 78-85) ----\n"
            "@log_calls\n"
            "def process_user_data(user_info: UserInfo) -> dict:\n"
            '    """사용자 데이터 처리 함수"""\n'
            "    return {\n"
            '        "name": user_info.name,\n'
            '        "age": user_info.age,\n'
            '        "display": user_info.get_display_name(),\n'
            "    }"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_result
