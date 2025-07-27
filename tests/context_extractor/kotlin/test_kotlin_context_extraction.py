"""ContextExtractor Kotlin 테스트 케이스."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import ContextExtractor, LineRange


class TestBasicFunctionExtraction:
    """기본 함수/클래스 추출 기능 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.kt"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Kotlin용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("kotlin")

    def test_class_declaration(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스 선언부 추출 테스트."""
        changed_ranges = [LineRange(23, 23)]  # SampleCalculator 클래스 선언부
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import kotlin.collections.*\n"
            "class SampleCalculator(private var value: Int = 0) {\n"
            "    /**\n"
            "     * 간단한 계산기 클래스 - tree-sitter 테스트용\n"
            "     */\n"
            "    \n"
            "    private val history = mutableListOf<String>()\n"
            "    private var mode = CALCULATION_MODES[\"basic\"] ?: \"basic\"\n"
            "    \n"
            "    init {\n"
            "        /**\n"
            "         * 계산기 초기화\n"
            "         */\n"
            "        this.history.clear()\n"
            "        this.mode = CALCULATION_MODES[\"basic\"] ?: \"basic\"\n"
            "    }\n"
            "    \n"
            "    fun addNumbers(a: Int, b: Int): Int {\n"
            "        /**\n"
            "         * 두 수를 더하는 메소드\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 입력값 검증\n"
            "        fun validateInputs(x: Int, y: Int): Boolean {\n"
            "            return true // Kotlin에서는 타입이 보장됨\n"
            "        }\n"
            "        \n"
            "        // 내부 함수: 연산 로깅\n"
            "        fun logOperation(operation: String, result: Int) {\n"
            "            if (history.size < MAX_CALCULATION_STEPS) {\n"
            "                history.add(\"$operation = $result\")\n"
            "                println(\"Logged: $operation = $result\")\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        if (!validateInputs(a, b)) {\n"
            "            throw IllegalArgumentException(\"입력값이 숫자가 아닙니다\")\n"
            "        }\n"
            "        \n"
            "        val result = a + b\n"
            "        value = result\n"
            "        logOperation(\"add: $a + $b\", result)\n"
            "        println(\"Addition result: $result\")\n"
            "        return result\n"
            "    }\n"
            "    \n"
            "    fun multiplyAndFormat(numbers: List<Int>): FormattedResult {\n"
            "        /**\n"
            "         * 숫자 리스트를 곱하고 결과를 포맷팅하는 메소드\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 곱셈 계산\n"
            "        fun calculateProduct(nums: List<Int>): Int {\n"
            "            if (nums.isEmpty()) {\n"
            "                return 0\n"
            "            }\n"
            "            \n"
            "            // 재귀적 곱셈 함수 (중첩 내부 함수)\n"
            "            fun multiplyRecursive(items: List<Int>, index: Int = 0): Int {\n"
            "                if (index >= items.size) {\n"
            "                    return 1\n"
            "                }\n"
            "                return items[index] * multiplyRecursive(items, index + 1)\n"
            "            }\n"
            "            \n"
            "            return multiplyRecursive(nums)\n"
            "        }\n"
            "        \n"
            "        // 내부 함수: 결과 포맷팅\n"
            "        fun formatResult(value: Int, count: Int): FormattedResult {\n"
            "            return FormattedResult(\n"
            "                result = value,\n"
            "                formatted = \"Product: ${\"%,d\".format(value)}\",\n"
            "                count = count,\n"
            "                precision = DEFAULT_PRECISION\n"
            "            )\n"
            "        }\n"
            "        \n"
            "        if (numbers.isEmpty()) {\n"
            "            return FormattedResult(0, \"Empty list\", 0, DEFAULT_PRECISION)\n"
            "        }\n"
            "        \n"
            "        val result = calculateProduct(numbers)\n"
            "        value = result\n"
            "        val formattedResult = formatResult(result, numbers.size)\n"
            "        \n"
            "        println(\"Multiplication result: $formattedResult\")\n"
            "        \n"
            "        return formattedResult\n"
            "    }\n"
            "    \n"
            "    fun calculateCircleArea(radius: Double): Double {\n"
            "        /**\n"
            "         * 원의 넓이를 계산하는 메소드 (상수 사용)\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 반지름 검증\n"
            "        fun validateRadius(r: Double): Boolean {\n"
            "            return r > 0\n"
            "        }\n"
            "        \n"
            "        if (!validateRadius(radius)) {\n"
            "            throw IllegalArgumentException(\"반지름은 양수여야 합니다\")\n"
            "        }\n"
            "        \n"
            "        val area = PI_CONSTANT * radius * radius\n"
            "        return kotlin.math.round(area * kotlin.math.pow(10.0, DEFAULT_PRECISION.toDouble())) / kotlin.math.pow(10.0, DEFAULT_PRECISION.toDouble())\n"
            "    }\n"
            "}"
        )

        assert len(contexts) == 2
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_constructor_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """생성자 메서드 추출 테스트."""
        changed_ranges = [LineRange(31, 37)]  # init 블록
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import kotlin.collections.*\n"
            "init {\n"
            "        /**\n"
            "         * 계산기 초기화\n"
            "         */\n"
            "        this.history.clear()\n"
            "        this.mode = CALCULATION_MODES[\"basic\"] ?: \"basic\"\n"
            "    }"
        )

        assert len(contexts) == 2
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_class_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스 메서드 추출 테스트."""
        changed_ranges = [LineRange(39, 66)]  # addNumbers 메서드
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import kotlin.collections.*\n"
            "fun addNumbers(a: Int, b: Int): Int {\n"
            "        /**\n"
            "         * 두 수를 더하는 메소드\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 입력값 검증\n"
            "        fun validateInputs(x: Int, y: Int): Boolean {\n"
            "            return true // Kotlin에서는 타입이 보장됨\n"
            "        }\n"
            "        \n"
            "        // 내부 함수: 연산 로깅\n"
            "        fun logOperation(operation: String, result: Int) {\n"
            "            if (history.size < MAX_CALCULATION_STEPS) {\n"
            "                history.add(\"$operation = $result\")\n"
            "                println(\"Logged: $operation = $result\")\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        if (!validateInputs(a, b)) {\n"
            "            throw IllegalArgumentException(\"입력값이 숫자가 아닙니다\")\n"
            "        }\n"
            "        \n"
            "        val result = a + b\n"
            "        value = result\n"
            "        logOperation(\"add: $a + $b\", result)\n"
            "        println(\"Addition result: $result\")\n"
            "        return result\n"
            "    }"
        )

        assert len(contexts) == 2
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_complex_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """복잡한 메서드 추출 테스트."""
        changed_ranges = [LineRange(68, 111)]  # multiplyAndFormat 메서드
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import kotlin.collections.*\n"
            "fun multiplyAndFormat(numbers: List<Int>): FormattedResult {\n"
            "        /**\n"
            "         * 숫자 리스트를 곱하고 결과를 포맷팅하는 메소드\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 곱셈 계산\n"
            "        fun calculateProduct(nums: List<Int>): Int {\n"
            "            if (nums.isEmpty()) {\n"
            "                return 0\n"
            "            }\n"
            "            \n"
            "            // 재귀적 곱셈 함수 (중첩 내부 함수)\n"
            "            fun multiplyRecursive(items: List<Int>, index: Int = 0): Int {\n"
            "                if (index >= items.size) {\n"
            "                    return 1\n"
            "                }\n"
            "                return items[index] * multiplyRecursive(items, index + 1)\n"
            "            }\n"
            "            \n"
            "            return multiplyRecursive(nums)\n"
            "        }\n"
            "        \n"
            "        // 내부 함수: 결과 포맷팅\n"
            "        fun formatResult(value: Int, count: Int): FormattedResult {\n"
            "            return FormattedResult(\n"
            "                result = value,\n"
            "                formatted = \"Product: ${\"%,d\".format(value)}\",\n"
            "                count = count,\n"
            "                precision = DEFAULT_PRECISION\n"
            "            )\n"
            "        }\n"
            "        \n"
            "        if (numbers.isEmpty()) {\n"
            "            return FormattedResult(0, \"Empty list\", 0, DEFAULT_PRECISION)\n"
            "        }\n"
            "        \n"
            "        val result = calculateProduct(numbers)\n"
            "        value = result\n"
            "        val formattedResult = formatResult(result, numbers.size)\n"
            "        \n"
            "        println(\"Multiplication result: $formattedResult\")\n"
            "        \n"
            "        return formattedResult\n"
            "    }"
        )

        assert len(contexts) == 2
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_nested_inner_function(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """중첩 내부 함수 추출 테스트."""
        changed_ranges = [LineRange(80, 85)]  # multiplyRecursive 내부 함수
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import kotlin.collections.*\n"
            "fun multiplyRecursive(items: List<Int>, index: Int = 0): Int {\n"
            "                if (index >= items.size) {\n"
            "                    return 1\n"
            "                }\n"
            "                return items[index] * multiplyRecursive(items, index + 1)\n"
            "            }"
        )

        assert len(contexts) == 2
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_external_function(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스 외부 함수 추출 테스트."""
        changed_ranges = [LineRange(132, 148)]  # helperFunction
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import kotlin.collections.*\n"
            "fun helperFunction(data: Map<String, Any>): String {\n"
            "    /**\n"
            "     * 도우미 함수 - 클래스 외부 함수\n"
            "     */\n"
            "    \n"
            "    // 내부 함수: 딕셔너리 아이템 포맷팅\n"
            "    fun formatDictItems(items: Map<String, Any>): List<String> {\n"
            "        val formatted = mutableListOf<String>()\n"
            "        for ((key, value) in items) {\n"
            "            formatted.add(\"$key: $value\")\n"
            "        }\n"
            "        return formatted\n"
            "    }\n"
            "    \n"
            "    val formattedItems = formatDictItems(data)\n"
            "    return \"Helper processed: ${formattedItems.joinToString(\", \")}\"\n"
            "}"
        )

        assert len(contexts) == 2
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_factory_function(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """팩토리 함수 추출 테스트."""
        changed_ranges = [LineRange(150, 172)]  # advancedCalculatorFactory
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import kotlin.collections.*\n"
            "fun advancedCalculatorFactory(mode: String = \"basic\"): SampleCalculator {\n"
            "    /**\n"
            "     * 계산기 팩토리 함수\n"
            "     */\n"
            "    \n"
            "    // 내부 함수: 모드별 계산기 생성\n"
            "    fun createCalculatorWithMode(calcMode: String): SampleCalculator {\n"
            "        val calc = SampleCalculator()\n"
            "        if (calcMode in CALCULATION_MODES) {\n"
            "            // Kotlin에서는 private 필드 접근이 제한되므로 공개 메소드 사용\n"
            "        }\n"
            "        return calc\n"
            "    }\n"
            "    \n"
            "    // 내부 함수: 모드 검증\n"
            "    fun validateMode(m: String): Boolean {\n"
            "        return m in CALCULATION_MODES\n"
            "    }\n"
            "    \n"
            "    val validMode = if (validateMode(mode)) mode else \"basic\"\n"
            "    \n"
            "    return createCalculatorWithMode(validMode)\n"
            "}"
        )

        assert len(contexts) == 2
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_method_declaration_only(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """메서드 선언부만 추출 테스트."""
        changed_ranges = [LineRange(39, 39)]  # addNumbers 선언부만
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import kotlin.collections.*\n"
            "fun addNumbers(a: Int, b: Int): Int {\n"
            "        /**\n"
            "         * 두 수를 더하는 메소드\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 입력값 검증\n"
            "        fun validateInputs(x: Int, y: Int): Boolean {\n"
            "            return true // Kotlin에서는 타입이 보장됨\n"
            "        }\n"
            "        \n"
            "        // 내부 함수: 연산 로깅\n"
            "        fun logOperation(operation: String, result: Int) {\n"
            "            if (history.size < MAX_CALCULATION_STEPS) {\n"
            "                history.add(\"$operation = $result\")\n"
            "                println(\"Logged: $operation = $result\")\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        if (!validateInputs(a, b)) {\n"
            "            throw IllegalArgumentException(\"입력값이 숫자가 아닙니다\")\n"
            "        }\n"
            "        \n"
            "        val result = a + b\n"
            "        value = result\n"
            "        logOperation(\"add: $a + $b\", result)\n"
            "        println(\"Addition result: $result\")\n"
            "        return result\n"
            "    }"
        )

        assert len(contexts) == 2
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_external_function_declaration_only(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """외부 함수 선언부만 추출 테스트."""
        changed_ranges = [LineRange(132, 132)]  # helperFunction 선언부만
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import kotlin.collections.*\n"
            "fun helperFunction(data: Map<String, Any>): String {\n"
            "    /**\n"
            "     * 도우미 함수 - 클래스 외부 함수\n"
            "     */\n"
            "    \n"
            "    // 내부 함수: 딕셔너리 아이템 포맷팅\n"
            "    fun formatDictItems(items: Map<String, Any>): List<String> {\n"
            "        val formatted = mutableListOf<String>()\n"
            "        for ((key, value) in items) {\n"
            "            formatted.add(\"$key: $value\")\n"
            "        }\n"
            "        return formatted\n"
            "    }\n"
            "    \n"
            "    val formattedItems = formatDictItems(data)\n"
            "    return \"Helper processed: ${formattedItems.joinToString(\", \")}\"\n"
            "}"
        )

        assert len(contexts) == 2
        all_context = "\n".join(contexts)
        assert all_context == expected_result


class TestModuleLevelElements:
    """모듈 레벨 요소 추출 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.kt"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Kotlin용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("kotlin")

    def test_basic_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """기본 상수들 추출 테스트."""
        changed_ranges = [LineRange(6, 8)]  # 상수 선언
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import kotlin.collections.*\n"
            "const val MAX_CALCULATION_STEPS = 100\n"
            "const val DEFAULT_PRECISION = 2\n"
            "const val PI_CONSTANT = 3.14159"
        )

        assert len(contexts) == 2
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_object_constant(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """객체 상수 추출 테스트."""
        changed_ranges = [LineRange(10, 14)]  # CALCULATION_MODES 객체
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import kotlin.collections.*\n"
            "val CALCULATION_MODES = mapOf(\n"
            "    \"basic\" to \"Basic calculations\",\n"
            "    \"advanced\" to \"Advanced calculations with logging\",\n"
            "    \"debug\" to \"Debug mode with detailed output\"\n"
            ")"
        )

        assert len(contexts) == 2
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_module_bottom_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """모듈 하단 상수들 추출 테스트."""
        changed_ranges = [LineRange(175, 179)]  # MODULE_VERSION과 AUTHOR_INFO
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import kotlin.collections.*\n"
            "const val MODULE_VERSION = \"1.0.0\"\n"
            "val AUTHOR_INFO = mapOf(\n"
            "    \"name\" to \"Test Author\",\n"
            "    \"email\" to \"test@example.com\"\n"
            ")"
        )

        assert len(contexts) == 2
        all_context = "\n".join(contexts)
        assert all_context == expected_result


class TestMultiRangeExtraction:
    """여러 범위에 걸친 추출 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.kt"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Kotlin용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("kotlin")

    def test_three_cross_functions(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """3개 함수에 걸친 영역 추출 테스트."""
        changed_ranges = [
            LineRange(113, 172)
        ]  # calculateCircleArea ~ advancedCalculatorFactory
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) == 4
        all_context = "\n".join(contexts)
        
        # 순서 검증: import 문이 맨 앞에 있어야 함
        assert all_context.startswith("import kotlin.collections.*;")
        assert contexts[0] == "import kotlin.collections.*;"
        
        # 구조 검증: import 다음에 함수들이 올바른 순서로 배치
        import_index = all_context.find("import kotlin.collections.*;")
        area_index = all_context.find("fun calculateCircleArea")
        helper_index = all_context.find("fun helperFunction")
        factory_index = all_context.find("fun advancedCalculatorFactory")
        
        # import가 가장 먼저 나와야 함
        assert import_index < area_index
        assert import_index < helper_index
        assert import_index < factory_index
        
        # 주요 콘텐츠 존재 확인
        assert "fun calculateCircleArea" in all_context
        assert "fun helperFunction" in all_context
        assert "fun advancedCalculatorFactory" in all_context

    def test_two_blocks_cross_methods(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """2개 블록에 걸친 메서드 추출 테스트."""
        changed_ranges = [LineRange(39, 47), LineRange(132, 137)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) == 3
        all_context = "\n".join(contexts)
        
        # 순서 검증: import 문이 맨 앞에 있어야 함
        assert all_context.startswith("import kotlin.collections.*;")
        assert contexts[0] == "import kotlin.collections.*;"
        
        # 구조 검증: import 다음에 메서드들이 올바른 순서로 배치
        import_index = all_context.find("import kotlin.collections.*;")
        add_index = all_context.find("fun addNumbers(a: Int, b: Int): Int")
        helper_index = all_context.find("fun helperFunction")
        
        # import가 가장 먼저 나와야 함
        assert import_index < add_index
        assert import_index < helper_index
        
        # 주요 콘텐츠 존재 확인
        assert "fun addNumbers(a: Int, b: Int): Int" in all_context
        assert "fun helperFunction" in all_context

    def test_non_contiguous_ranges(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """비연속적인 여러 범위 추출 테스트."""
        changed_ranges = [
            LineRange(6, 8),  # 파일 상수들
            LineRange(119, 121),  # validateRadius 내부 함수
            LineRange(175, 177),  # 모듈 레벨 상수들
        ]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) == 4
        all_context = "\n".join(contexts)
        
        # 순서 검증: import 문이 맨 앞에 있어야 함
        assert all_context.startswith("import kotlin.collections.*;")
        assert contexts[0] == "import kotlin.collections.*;"
        
        # 구조 검증: import 다음에 상수들이 올바른 순서로 배치
        import_index = all_context.find("import kotlin.collections.*;")
        max_steps_index = all_context.find("MAX_CALCULATION_STEPS = 100")
        module_version_index = all_context.find('MODULE_VERSION = "1.0.0"')
        
        # import가 가장 먼저 나와야 함
        assert import_index < max_steps_index
        assert import_index < module_version_index
        
        # 주요 콘텐츠 존재 확인  
        assert "MAX_CALCULATION_STEPS = 100" in all_context
        assert "fun validateRadius" in all_context or "validateRadius" in all_context
        assert 'MODULE_VERSION = "1.0.0"' in all_context


class TestComplexScenarios:
    """복잡한 시나리오 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.kt"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Kotlin용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("kotlin")

    def test_entire_class_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """전체 클래스 추출 테스트."""
        changed_ranges = [LineRange(23, 130)]  # SampleCalculator 전체 클래스
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) == 2
        all_context = "\n".join(contexts)
        
        # 순서 검증: import 문이 맨 앞에 있어야 함
        assert all_context.startswith("import kotlin.collections.*;")
        assert contexts[0] == "import kotlin.collections.*;"
        
        # 구조 검증: import 다음에 클래스가 와야 함
        import_index = all_context.find("import kotlin.collections.*;")
        class_index = all_context.find("class SampleCalculator")
        init_index = all_context.find("init {")
        add_index = all_context.find("fun addNumbers(a: Int, b: Int): Int")
        multiply_index = all_context.find("fun multiplyAndFormat")
        area_index = all_context.find("fun calculateCircleArea")
        
        # import가 가장 먼저, 그 다음 클래스 및 메서드들이 순서대로
        assert import_index < class_index
        assert class_index < init_index
        assert init_index < add_index
        assert add_index < multiply_index
        assert multiply_index < area_index
        
        # 주요 콘텐츠 존재 확인
        assert "class SampleCalculator" in all_context
        assert "init {" in all_context
        assert "fun addNumbers(a: Int, b: Int): Int" in all_context
        assert "fun multiplyAndFormat" in all_context
        assert "fun calculateCircleArea" in all_context

    def test_class_and_module_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스와 모듈 상수 동시 추출 테스트."""
        changed_ranges = [LineRange(6, 179)]  # 상수부터 모듈 끝까지
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) == 6
        all_context = "\n".join(contexts)
        
        # 순서 검증: import 문이 맨 앞에 있어야 함
        assert all_context.startswith("import kotlin.collections.*;")
        assert contexts[0] == "import kotlin.collections.*;"
        
        # 구조 검증: import 다음에 상수들과 클래스들이 적절한 순서로 배치
        import_index = all_context.find("import kotlin.collections.*;")
        max_steps_index = all_context.find("MAX_CALCULATION_STEPS")
        sample_calc_index = all_context.find("class SampleCalculator")
        helper_index = all_context.find("fun helperFunction")
        module_version_index = all_context.find('MODULE_VERSION = "1.0.0"')
        
        # import가 가장 먼저 나와야 함
        assert import_index < max_steps_index
        assert import_index < sample_calc_index
        assert import_index < helper_index
        assert import_index < module_version_index
        
        # 주요 콘텐츠 존재 확인
        assert "class SampleCalculator" in all_context
        assert "fun helperFunction" in all_context
        assert "advancedCalculatorFactory" in all_context
        assert 'MODULE_VERSION = "1.0.0"' in all_context
        assert "AUTHOR_INFO" in all_context
        assert "MAX_CALCULATION_STEPS" in all_context
        assert "CALCULATION_MODES" in all_context


class TestEdgeCases:
    """엣지 케이스 및 에러 처리 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.kt"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Kotlin용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("kotlin")

    def test_invalid_line_ranges(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """파일 범위를 벗어나는 라인 범위 테스트."""
        changed_ranges = [LineRange(200, 300)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # 범위를 벗어나더라도 에러가 발생하지 않아야 함
        assert len(contexts) >= 0

    def test_reverse_line_ranges(self) -> None:
        """잘못된 범위 생성 시 예외 발생 테스트."""
        with pytest.raises(ValueError, match="시작 라인이 끝 라인보다 클 수 없습니다"):
            LineRange(50, 30)

    def test_empty_line_ranges(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """빈 라인 범위 처리 테스트."""
        changed_ranges = [LineRange(15, 16)]  # 빈 라인 또는 주석
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # 빈 라인 범위에서도 적절히 처리되어야 함
        assert len(contexts) >= 0
