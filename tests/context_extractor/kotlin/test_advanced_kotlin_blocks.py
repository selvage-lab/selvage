"""ContextExtractor 고급 Kotlin 블록 테스트 케이스."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import ContextExtractor, LineRange


class TestAdvancedKotlinBlocks:
    """고급 Kotlin 블록 타입 추출 테스트."""

    @pytest.fixture
    def sample_file_content(self) -> str:
        """테스트용 고급 샘플 파일 내용을 반환합니다."""
        file_path = Path(__file__).parent / "AdvancedKotlinSample.kt"
        return file_path.read_text(encoding="utf-8")

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Kotlin용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("kotlin")

    def test_type_alias_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """타입 별칭 추출 테스트."""
        changed_ranges = [LineRange(5, 6)]  # typealias 선언들
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        all_context = "\n".join(contexts)

        assert all_context.startswith("---- Dependencies/Imports ----")
        assert "typealias StringMap = Map<String, String>" in all_context
        assert "typealias IntProcessor = (Int) -> Int" in all_context

    def test_annotation_declaration_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """어노테이션 선언 추출 테스트."""
        changed_ranges = [LineRange(8, 12)]  # @Cacheable 어노테이션
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        all_context = "\n".join(contexts)
        assert all_context.startswith("---- Dependencies/Imports ----")
        assert "annotation class Cacheable" in all_context
        assert "@Target" in all_context
        assert "@Retention" in all_context

    def test_interface_declaration_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """인터페이스 선언 추출 테스트."""
        changed_ranges = [LineRange(17, 25)]  # Calculator 인터페이스
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        all_context = "\n".join(contexts)
        assert all_context.startswith("---- Dependencies/Imports ----")
        assert "interface Calculator" in all_context
        assert "fun calculate(a: Int, b: Int): Int" in all_context
        assert "fun getOperationName(): String" in all_context
        assert "fun describe(): String" in all_context

    def test_enum_entry_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """열거형 항목 추출 테스트."""
        changed_ranges = [LineRange(34, 36)]  # ADD enum entry
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        all_context = "\n".join(contexts)
        assert all_context.startswith("---- Dependencies/Imports ----")
        assert 'ADD("+", 1)' in all_context
        assert "override fun apply(a: Int, b: Int): Int = a + b" in all_context

    def test_object_declaration_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """싱글톤 객체 선언 추출 테스트."""
        changed_ranges = [LineRange(54, 64)]  # MathUtils object
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        all_context = "\n".join(contexts)
        assert all_context.startswith("---- Dependencies/Imports ----")
        assert "object MathUtils" in all_context
        assert "const val PI = 3.14159" in all_context
        assert "fun square(x: Int): Int" in all_context
        assert "fun fibonacci(n: Int): Int" in all_context

    def test_secondary_constructor_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """보조 생성자 추출 테스트."""
        changed_ranges = [LineRange(96, 98)]  # 첫 번째 보조 생성자
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        all_context = "\n".join(contexts)
        assert all_context.startswith("---- Dependencies/Imports ----")
        assert (
            "constructor(name: String, precision: Int, enableLogging: Boolean)"
            in all_context
        )

    def test_companion_object_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """동반 객체 추출 테스트."""
        changed_ranges = [LineRange(105, 117)]  # companion object
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        all_context = "\n".join(contexts)
        assert all_context.startswith("---- Dependencies/Imports ----")
        assert "companion object" in all_context
        assert 'const val VERSION = "2.0.0"' in all_context
        assert "fun createSimple(): AdvancedCalculator" in all_context
        assert "fun getInstanceCount(): Int = instanceCount" in all_context

    def test_lambda_expression_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """람다 표현식 추출 테스트."""
        changed_ranges = [LineRange(154, 154)]  # 람다 표현식들
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        all_context = "\n".join(contexts)
        assert all_context.startswith("---- Dependencies/Imports ----")
        assert "val doubler: IntProcessor = { x -> x * 2 }" in all_context

    def test_complex_lambda_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """복잡한 람다 표현식 추출 테스트."""
        changed_ranges = [LineRange(170, 174)]  # 복잡한 람다 표현식
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        all_context = "\n".join(contexts)
        assert all_context.startswith("---- Dependencies/Imports ----")
        assert (
            "val complexProcessor: (List<Int>) -> List<String> = { nums ->"
            in all_context
        )
        assert ".filter { it > 0 }" in all_context
        assert ".map { num ->" in all_context

    def test_data_class_companion_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """데이터 클래스의 동반 객체 추출 테스트."""
        changed_ranges = [
            LineRange(139, 148)
        ]  # Result 데이터 클래스의 companion object
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        all_context = "\n".join(contexts)
        assert all_context.startswith("---- Dependencies/Imports ----")
        assert "data class Result" in all_context
        assert "companion object" in all_context
        assert "fun success(value: Int, operation: String): Result" in all_context
        assert "fun error(operation: String): Result" in all_context

    def test_abstract_class_companion_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """추상 클래스의 동반 객체 추출 테스트."""
        changed_ranges = [LineRange(189, 199)]  # BaseProcessor의 companion object
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        all_context = "\n".join(contexts)
        assert all_context.startswith("---- Dependencies/Imports ----")
        assert "companion object" in all_context
        assert "const val DEFAULT_TIMEOUT = 5000L" in all_context
        assert (
            "fun <T> createChain(vararg processors: BaseProcessor<T>): BaseProcessor<T> {"
            in all_context
        )
