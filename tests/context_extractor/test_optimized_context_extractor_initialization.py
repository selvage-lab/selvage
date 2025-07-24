import pytest

from selvage.src.context_extractor import ContextExtractor


class TestContextExtractorInitialization:
    """ContextExtractor 초기화 기능을 테스트한다."""

    def test_supported_languages(self):
        """지원하는 언어 목록이 올바른지 테스트한다."""
        supported = ContextExtractor.get_supported_languages()

        # 필수 언어들이 모두 포함되어 있는지 확인
        required_languages = {
            "python",
            "javascript",
            "typescript",
            "java",
            "c",
            "cpp",
            "go",
            "csharp",
        }

        for lang in required_languages:
            assert lang in supported, f"필수 언어 '{lang}'이 지원 목록에 없습니다"

    def test_valid_language_initialization(self):
        """유효한 언어로 초기화가 정상 동작하는지 테스트한다."""
        for language in ["python", "javascript", "java"]:
            extractor = ContextExtractor(language)
            assert extractor._language_name == language

    def test_invalid_language_initialization(self):
        """지원하지 않는 언어로 초기화 시 예외 발생을 테스트한다."""
        with pytest.raises(ValueError, match="지원하지 않는 언어"):
            ContextExtractor("unsupported_language")

    def test_block_types_for_each_language(self):
        """각 언어별로 블록 타입이 올바르게 설정되는지 테스트한다."""
        test_cases = [
            ("python", {"function_definition", "class_definition"}),
            ("javascript", {"function_declaration", "class"}),
            ("java", {"method_declaration", "class_declaration"}),
        ]

        for language, expected_block_types in test_cases:
            block_types = ContextExtractor.get_block_types_for_language(language)
            for expected_type in expected_block_types:
                assert expected_type in block_types, (
                    f"{language}에서 {expected_type}이 누락됨"
                )
