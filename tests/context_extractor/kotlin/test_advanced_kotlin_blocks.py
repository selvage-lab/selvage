"""ContextExtractor 고급 Kotlin 블록 테스트 케이스."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import ContextExtractor, LineRange


class TestAdvancedKotlinBlocks:
    """고급 Kotlin 블록 타입 추출 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 고급 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "AdvancedKotlinSample.kt"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Kotlin용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("kotlin")

    def test_type_alias_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """타입 별칭 추출 테스트."""
        changed_ranges = [LineRange(5, 6)]  # typealias 선언들
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # import 문이 포함되어야 함
        assert contexts[0] == "import kotlin.collections.*"

        # typealias 선언들이 추출되어야 함
        all_context = "\n".join(contexts)
        assert "typealias StringMap = Map<String, String>" in all_context
        assert "typealias IntProcessor = (Int) -> Int" in all_context

    def test_annotation_declaration_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """어노테이션 선언 추출 테스트."""
        changed_ranges = [LineRange(8, 12)]  # @Cacheable 어노테이션
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # import 문이 포함되어야 함
        assert contexts[0] == "import kotlin.collections.*"

        # 어노테이션 선언이 추출되어야 함
        all_context = "\n".join(contexts)
        assert "annotation class Cacheable" in all_context
        assert "@Target" in all_context
        assert "@Retention" in all_context

    def test_interface_declaration_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """인터페이스 선언 추출 테스트."""
        changed_ranges = [LineRange(17, 25)]  # Calculator 인터페이스
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # import 문이 포함되어야 함
        assert contexts[0] == "import kotlin.collections.*"

        # 인터페이스 전체가 추출되어야 함
        all_context = "\n".join(contexts)
        assert "interface Calculator" in all_context
        assert "fun calculate(a: Int, b: Int): Int" in all_context
        assert "fun getOperationName(): String" in all_context
        assert "fun describe(): String" in all_context

    def test_enum_entry_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """열거형 항목 추출 테스트."""
        changed_ranges = [LineRange(34, 36)]  # ADD enum entry
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # import 문이 포함되어야 함
        assert contexts[0] == "import kotlin.collections.*"

        # enum_entry가 개별적으로 추출됨을 확인
        all_context = "\n".join(contexts)
        assert 'ADD("+", 1)' in all_context
        assert "override fun apply(a: Int, b: Int): Int = a + b" in all_context

        # enum_entry 블록 타입이 올바르게 작동하는지 확인
        assert len(contexts) >= 3  # imports + enum entry

    def test_object_declaration_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """싱글톤 객체 선언 추출 테스트."""
        changed_ranges = [LineRange(54, 64)]  # MathUtils object
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # import 문이 포함되어야 함
        assert contexts[0] == "import kotlin.collections.*"

        # 객체 전체가 추출되어야 함
        all_context = "\n".join(contexts)
        assert "object MathUtils" in all_context
        assert "const val PI = 3.14159" in all_context
        assert "fun square(x: Int): Int" in all_context
        assert "fun fibonacci(n: Int): Int" in all_context

    def test_secondary_constructor_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """보조 생성자 추출 테스트."""
        changed_ranges = [LineRange(96, 98)]  # 첫 번째 보조 생성자
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # import 문이 포함되어야 함
        assert contexts[0] == "import kotlin.collections.*"

        # 클래스 전체가 추출되어야 함 (보조 생성자는 클래스 내부에 있으므로)
        all_context = "\n".join(contexts)
        assert (
            "constructor(name: String, precision: Int, enableLogging: Boolean)"
            in all_context
        )

    def test_companion_object_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """동반 객체 추출 테스트."""
        changed_ranges = [LineRange(105, 117)]  # companion object
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # import 문이 포함되어야 함
        assert contexts[0] == "import kotlin.collections.*"

        # 동반 객체가 추출되어야 함
        all_context = "\n".join(contexts)
        assert "companion object" in all_context
        assert 'const val VERSION = "2.0.0"' in all_context
        assert "fun createSimple(): AdvancedCalculator" in all_context
        assert "fun getInstanceCount(): Int = instanceCount" in all_context

    def test_lambda_expression_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """람다 표현식 추출 테스트."""
        changed_ranges = [LineRange(154, 154)]  # 람다 표현식들
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # import 문이 포함되어야 함
        assert contexts[0] == "import kotlin.collections.*"

        # 함수 전체가 추출되어야 함 (람다는 함수 내부에 있으므로)
        all_context = "\n".join(contexts)
        assert "val doubler: IntProcessor = { x -> x * 2 }" in all_context

    def test_complex_lambda_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """복잡한 람다 표현식 추출 테스트."""
        changed_ranges = [LineRange(170, 174)]  # 복잡한 람다 표현식
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # import 문이 포함되어야 함
        assert contexts[0] == "import kotlin.collections.*"

        # 복잡한 람다 표현식이 포함된 함수가 추출되어야 함
        all_context = "\n".join(contexts)
        assert (
            "val complexProcessor: (List<Int>) -> List<String> = { nums ->"
            in all_context
        )
        assert ".filter { it > 0 }" in all_context
        assert ".map { num ->" in all_context

    def test_data_class_companion_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """데이터 클래스의 동반 객체 추출 테스트."""
        changed_ranges = [
            LineRange(139, 148)
        ]  # Result 데이터 클래스의 companion object
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # import 문이 포함되어야 함
        assert contexts[0] == "import kotlin.collections.*"

        # 데이터 클래스와 동반 객체가 추출되어야 함
        all_context = "\n".join(contexts)
        assert "data class Result" in all_context
        assert "companion object" in all_context
        assert "fun success(value: Int, operation: String): Result" in all_context
        assert "fun error(operation: String): Result" in all_context

    def test_abstract_class_companion_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """추상 클래스의 동반 객체 추출 테스트."""
        changed_ranges = [LineRange(189, 199)]  # BaseProcessor의 companion object
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # import 문이 포함되어야 함
        assert contexts[0] == "import kotlin.collections.*"

        # 추상 클래스와 동반 객체가 추출되어야 함
        all_context = "\n".join(contexts)
        assert "companion object" in all_context
        assert "const val DEFAULT_TIMEOUT = 5000L" in all_context
        assert (
            "fun <T> createChain(vararg processors: BaseProcessor<T>): BaseProcessor<T> {"
            in all_context
        )
