"""Modern Java Features ContextExtractor 테스트 케이스."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import ContextExtractor, LineRange


class TestAnnotationExtraction:
    """어노테이션 타입 추출 기능 테스트."""

    @pytest.fixture
    def sample_file_content(self) -> str:
        """테스트용 샘플 파일 내용을 반환합니다."""
        file_path = Path(__file__).parent / "ModernJavaFeatures.java"
        return file_path.read_text(encoding="utf-8")

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Java용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("java")

    def test_processing_info_annotation(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """ProcessingInfo 어노테이션 타입 추출 테스트."""
        changed_ranges = [LineRange(11, 16)]  # ProcessingInfo annotation
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        expected_result = (
            "---- Dependencies/Imports ----\n"
            "import java.util.*;\n"
            "import java.lang.annotation.*;\n"
            "---- Context Block 1 (Lines 10-16) ----\n"
            "@Retention(RetentionPolicy.RUNTIME)\n"
            "@Target({ElementType.TYPE, ElementType.METHOD, ElementType.FIELD})\n"
            "@interface ProcessingInfo {\n"
            '    String value() default "unknown";\n'
            "    int priority() default 1;\n"
            "    String[] tags() default {};\n"
            "}"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_validate_annotation(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """Validate 어노테이션 타입 추출 테스트."""
        changed_ranges = [LineRange(19, 25)]  # Validate annotation
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        expected_result = (
            "---- Dependencies/Imports ----\n"
            "import java.util.*;\n"
            "import java.lang.annotation.*;\n"
            "---- Context Block 1 (Lines 19-26) ----\n"
            "@Retention(RetentionPolicy.RUNTIME)\n"
            "@Target(ElementType.PARAMETER)\n"
            "@interface Validate {\n"
            "    boolean required() default true;\n"
            '    String pattern() default "";\n'
            "    int min() default 0;\n"
            "    int max() default Integer.MAX_VALUE;\n"
            "}"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_result


class TestEnumExtraction:
    """열거형 추출 기능 테스트."""

    @pytest.fixture
    def sample_file_content(self) -> str:
        """테스트용 샘플 파일 내용을 반환합니다."""
        file_path = Path(__file__).parent / "ModernJavaFeatures.java"
        return file_path.read_text(encoding="utf-8")

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Java용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("java")

    def test_calculation_mode_enum(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """CalculationMode 열거형 추출 테스트."""
        changed_ranges = [LineRange(28, 35)]  # CalculationMode enum constants
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        expected_result = (
            "---- Dependencies/Imports ----\n"
            "import java.util.*;\n"
            "import java.lang.annotation.*;\n"
            "---- Context Block 1 (Lines 28-60) ----\n"
            "// 계산 모드 열거형\n"
            '@ProcessingInfo(value = "calculation_modes", priority = 5)\n'
            "enum CalculationMode {\n"
            '    BASIC("기본 계산", 1.0),\n'
            '    ADVANCED("고급 계산", 1.5),\n'
            '    SCIENTIFIC("과학 계산", 2.0),\n'
            '    DEBUG("디버그 모드", 0.5);\n'
            "    \n"
            "    private final String description;\n"
            "    private final double multiplier;\n"
            "    \n"
            "    CalculationMode(String description, double multiplier) {\n"
            "        this.description = description;\n"
            "        this.multiplier = multiplier;\n"
            "    }\n"
            "    \n"
            "    public String getDescription() {\n"
            "        return description;\n"
            "    }\n"
            "    \n"
            "    public double getMultiplier() {\n"
            "        return multiplier;\n"
            "    }\n"
            "    \n"
            "    public static CalculationMode fromString(String mode) {\n"
            "        for (CalculationMode calcMode : values()) {\n"
            "            if (calcMode.name().equalsIgnoreCase(mode)) {\n"
            "                return calcMode;\n"
            "            }\n"
            "        }\n"
            "        return BASIC;\n"
            "    }\n"
            "}"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_processing_status_enum(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """ProcessingStatus 열거형 추출 테스트."""
        changed_ranges = [LineRange(62, 69)]  # ProcessingStatus enum
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        expected_result = (
            "---- Dependencies/Imports ----\n"
            "import java.util.*;\n"
            "import java.lang.annotation.*;\n"
            "---- Context Block 1 (Lines 62-69) ----\n"
            "// 상태 열거형\n"
            "enum ProcessingStatus {\n"
            "    PENDING,\n"
            "    IN_PROGRESS,\n"
            "    COMPLETED,\n"
            "    FAILED,\n"
            "    CANCELLED\n"
            "}"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_enum_method(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """열거형 메서드 추출 테스트."""
        changed_ranges = [LineRange(52, 58)]  # fromString method in enum
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        expected_result = (
            "---- Dependencies/Imports ----\n"
            "import java.util.*;\n"
            "import java.lang.annotation.*;\n"
            "---- Context Block 1 (Lines 52-59) ----\n"
            "public static CalculationMode fromString(String mode) {\n"
            "        for (CalculationMode calcMode : values()) {\n"
            "            if (calcMode.name().equalsIgnoreCase(mode)) {\n"
            "                return calcMode;\n"
            "            }\n"
            "        }\n"
            "        return BASIC;\n"
            "    }"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_result


class TestInterfaceExtraction:
    """인터페이스 추출 기능 테스트."""

    @pytest.fixture
    def sample_file_content(self) -> str:
        """테스트용 샘플 파일 내용을 반환합니다."""
        file_path = Path(__file__).parent / "ModernJavaFeatures.java"
        return file_path.read_text(encoding="utf-8")

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Java용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("java")

    def test_calculator_interface(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """Calculator 인터페이스 추출 테스트."""
        changed_ranges = [LineRange(72, 110)]  # Calculator interface
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        expected_result = (
            "---- Dependencies/Imports ----\n"
            "import java.util.*;\n"
            "import java.lang.annotation.*;\n"
            "---- Context Block 1 (Lines 72-113) ----\n"
            '@ProcessingInfo(value = "calculator_interface", priority = 3)\n'
            "interface Calculator {\n"
            "    \n"
            "    /**\n"
            "     * 기본 계산 메서드\n"
            "     */\n"
            "    double calculate(double a, double b);\n"
            "    \n"
            "    /**\n"
            "     * 배치 계산 메서드\n"
            "     */\n"
            "    default List<Double> calculateBatch(List<Double> numbers) {\n"
            "        if (numbers.size() < 2) {\n"
            "            return numbers;\n"
            "        }\n"
            "        \n"
            "        List<Double> results = new ArrayList<>();\n"
            "        for (int i = 0; i < numbers.size() - 1; i++) {\n"
            "            results.add(calculate(numbers.get(i), numbers.get(i + 1)));\n"
            "        }\n"
            "        return results;\n"
            "    }\n"
            "    \n"
            "    /**\n"
            "     * 결과 검증 메서드\n"
            "     */\n"
            "    default boolean validateResult(double result) {\n"
            "        return !Double.isNaN(result) && !Double.isInfinite(result);\n"
            "    }\n"
            "    \n"
            "    /**\n"
            "     * 정적 팩토리 메서드\n"
            "     */\n"
            "    static Calculator createSimpleCalculator() {\n"
            "        return new Calculator() {\n"
            "            @Override\n"
            "            public double calculate(double a, double b) {\n"
            "                return a + b;\n"
            "            }\n"
            "        };\n"
            "    }\n"
            "}"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_advanced_calculator_interface(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """AdvancedCalculator 인터페이스 추출 테스트."""
        changed_ranges = [LineRange(115, 132)]  # AdvancedCalculator interface
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        expected_result = (
            "---- Dependencies/Imports ----\n"
            "import java.util.*;\n"
            "import java.lang.annotation.*;\n"
            "---- Context Block 1 (Lines 115-132) ----\n"
            "// 고급 계산 인터페이스\n"
            "interface AdvancedCalculator extends Calculator {\n"
            "    \n"
            "    /**\n"
            "     * 복잡한 계산 메서드\n"
            "     */\n"
            "    Map<String, Object> complexCalculation(@Validate(required = true) List<Double> inputs,\n"
            "                                         @Validate(min = 1, max = 10) int iterations);\n"
            "    \n"
            "    /**\n"
            "     * 기본 구현 메서드\n"
            "     */\n"
            "    default String formatResult(double result, CalculationMode mode) {\n"
            '        return String.format("Result: %.2f (Mode: %s)", \n'
            "                           result * mode.getMultiplier(), \n"
            "                           mode.getDescription());\n"
            "    }\n"
            "}"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_interface_default_method(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """인터페이스 default 메서드 추출 테스트."""
        changed_ranges = [LineRange(83, 92)]  # calculateBatch default method
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        expected_result = (
            "---- Dependencies/Imports ----\n"
            "import java.util.*;\n"
            "import java.lang.annotation.*;\n"
            "---- Context Block 1 (Lines 83-93) ----\n"
            "default List<Double> calculateBatch(List<Double> numbers) {\n"
            "        if (numbers.size() < 2) {\n"
            "            return numbers;\n"
            "        }\n"
            "        \n"
            "        List<Double> results = new ArrayList<>();\n"
            "        for (int i = 0; i < numbers.size() - 1; i++) {\n"
            "            results.add(calculate(numbers.get(i), numbers.get(i + 1)));\n"
            "        }\n"
            "        return results;\n"
            "    }"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_result


class TestRecordExtraction:
    """Record 클래스 추출 기능 테스트."""

    @pytest.fixture
    def sample_file_content(self) -> str:
        """테스트용 샘플 파일 내용을 반환합니다."""
        file_path = Path(__file__).parent / "ModernJavaFeatures.java"
        return file_path.read_text(encoding="utf-8")

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Java용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("java")

    def test_calculation_result_record(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """CalculationResult Record 추출 테스트."""
        changed_ranges = [LineRange(135, 194)]  # CalculationResult record declaration
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        expected_result = (
            "---- Dependencies/Imports ----\n"
            "import java.util.*;\n"
            "import java.lang.annotation.*;\n"
            "---- Context Block 1 (Lines 135-201) ----\n"
            '@ProcessingInfo(value = "calculation_result", priority = 4, tags = {"result", "data"})\n'
            "record CalculationResult(\n"
            "    double value,\n"
            "    CalculationMode mode,\n"
            "    ProcessingStatus status,\n"
            "    long timestamp,\n"
            "    Map<String, Object> metadata\n"
            ") {\n"
            "    \n"
            "    /**\n"
            "     * Record 생성자 검증\n"
            "     */\n"
            "    public CalculationResult {\n"
            "        if (Double.isNaN(value) || Double.isInfinite(value)) {\n"
            '            throw new IllegalArgumentException("Invalid calculation value");\n'
            "        }\n"
            "        if (mode == null) {\n"
            "            mode = CalculationMode.BASIC;\n"
            "        }\n"
            "        if (status == null) {\n"
            "            status = ProcessingStatus.PENDING;\n"
            "        }\n"
            "        if (metadata == null) {\n"
            "            metadata = new HashMap<>();\n"
            "        }\n"
            "    }\n"
            "    \n"
            "    /**\n"
            "     * 정적 팩토리 메서드\n"
            "     */\n"
            "    public static CalculationResult success(double value, CalculationMode mode) {\n"
            "        return new CalculationResult(\n"
            "            value, \n"
            "            mode, \n"
            "            ProcessingStatus.COMPLETED,\n"
            "            System.currentTimeMillis(),\n"
            '            Map.of("success", true, "error", "none")\n'
            "        );\n"
            "    }\n"
            "    \n"
            "    /**\n"
            "     * 실패 결과 생성\n"
            "     */\n"
            "    public static CalculationResult failure(String errorMessage) {\n"
            "        return new CalculationResult(\n"
            "            0.0,\n"
            "            CalculationMode.BASIC,\n"
            "            ProcessingStatus.FAILED,\n"
            "            System.currentTimeMillis(),\n"
            '            Map.of("success", false, "error", errorMessage)\n'
            "        );\n"
            "    }\n"
            "    \n"
            "    /**\n"
            "     * 포맷된 결과 반환\n"
            "     */\n"
            "    public String formatValue() {\n"
            '        return String.format("%.3f", value * mode.getMultiplier());\n'
            "    }\n"
            "    \n"
            "    /**\n"
            "     * 성공 여부 확인\n"
            "     */\n"
            "    public boolean isSuccess() {\n"
            "        return status == ProcessingStatus.COMPLETED;\n"
            "    }\n"
            "}"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_calculator_config_record(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """CalculatorConfig Record 추출 테스트."""
        changed_ranges = [LineRange(204, 222)]  # CalculatorConfig record
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        expected_result = (
            "---- Dependencies/Imports ----\n"
            "import java.util.*;\n"
            "import java.lang.annotation.*;\n"
            "---- Context Block 1 (Lines 204-228) ----\n"
            "record CalculatorConfig(\n"
            "    CalculationMode defaultMode,\n"
            "    boolean enableLogging,\n"
            "    int maxIterations,\n"
            "    Map<String, String> properties\n"
            ") {\n"
            "    \n"
            "    public CalculatorConfig {\n"
            "        if (maxIterations <= 0) {\n"
            "            maxIterations = 100;\n"
            "        }\n"
            "        if (properties == null) {\n"
            "            properties = new HashMap<>();\n"
            "        }\n"
            "    }\n"
            "    \n"
            "    public static CalculatorConfig defaultConfig() {\n"
            "        return new CalculatorConfig(\n"
            "            CalculationMode.BASIC,\n"
            "            true,\n"
            "            100,\n"
            '            Map.of("precision", "high", "timeout", "30s")\n'
            "        );\n"
            "    }\n"
            "}"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_record_method(
        self,
        extractor: ContextExtractor,
        sample_file_content: str,
    ) -> None:
        """Record 메서드 추출 테스트."""
        changed_ranges = [LineRange(191, 193)]  # formatValue method in record
        contexts = extractor.extract_contexts(sample_file_content, changed_ranges)

        expected_result = (
            "---- Dependencies/Imports ----\n"
            "import java.util.*;\n"
            "import java.lang.annotation.*;\n"
            "---- Context Block 1 (Lines 191-193) ----\n"
            "public String formatValue() {\n"
            '        return String.format("%.3f", value * mode.getMultiplier());\n'
            "    }"
        )

        all_context = "\n".join(contexts)
        assert all_context == expected_result
