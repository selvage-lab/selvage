"""ContextExtractor Java 테스트 케이스."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import ContextExtractor, LineRange


class TestBasicFunctionExtraction:
    """기본 함수/클래스 추출 기능 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.java"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Java용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("java")

    def test_class_declaration(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스 선언부 추출 테스트."""
        changed_ranges = [LineRange(20, 20)]  # SampleCalculator 클래스 선언부
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import java.util.*;\n"
            "public class SampleCalculator {\n"
            "    /**\n"
            "     * 간단한 계산기 클래스 - tree-sitter 테스트용\n"
            "     */\n"
            "    \n"
            "    private int value;\n"
            "    private List<String> history;\n"
            "    private String mode;\n"
            "    \n"
            "    public SampleCalculator() {\n"
            "        this(0);\n"
            "    }\n"
            "    \n"
            "    public SampleCalculator(int initialValue) {\n"
            "        /**\n"
            "         * 계산기 초기화\n"
            "         */\n"
            "        this.value = initialValue;\n"
            "        this.history = new ArrayList<>();\n"
            "        this.mode = Constants.CALCULATION_MODES.get(\"basic\");\n"
            "    }\n"
            "    \n"
            "    public int addNumbers(int a, int b) {\n"
            "        /**\n"
            "         * 두 수를 더하는 메소드\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 입력값 검증\n"
            "        class InputValidator {\n"
            "            public static boolean validateInputs(int x, int y) {\n"
            "                return true; // Java에서는 기본적으로 int 타입 검증됨\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        // 내부 함수: 연산 로깅\n"
            "        class OperationLogger {\n"
            "            public void logOperation(String operation, int result) {\n"
            "                if (history.size() < Constants.MAX_CALCULATION_STEPS) {\n"
            "                    history.add(operation + \" = \" + result);\n"
            "                    System.out.println(\"Logged: \" + operation + \" = \" + result);\n"
            "                }\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        if (!InputValidator.validateInputs(a, b)) {\n"
            "            throw new IllegalArgumentException(\"입력값이 숫자가 아닙니다\");\n"
            "        }\n"
            "        \n"
            "        int result = a + b;\n"
            "        value = result;\n"
            "        new OperationLogger().logOperation(\"add: \" + a + \" + \" + b, result);\n"
            "        System.out.println(\"Addition result: \" + result);\n"
            "        return result;\n"
            "    }\n"
            "    \n"
            "    public Map<String, Object> multiplyAndFormat(List<Integer> numbers) {\n"
            "        /**\n"
            "         * 숫자 리스트를 곱하고 결과를 포맷팅하는 메소드\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 곱셈 계산\n"
            "        class ProductCalculator {\n"
            "            public int calculateProduct(List<Integer> nums) {\n"
            "                if (nums.isEmpty()) {\n"
            "                    return 0;\n"
            "                }\n"
            "                \n"
            "                // 재귀적 곱셈 함수 (중첩 내부 함수)\n"
            "                class RecursiveMultiplier {\n"
            "                    public int multiplyRecursive(List<Integer> items, int index) {\n"
            "                        if (index >= items.size()) {\n"
            "                            return 1;\n"
            "                        }\n"
            "                        return items.get(index) * multiplyRecursive(items, index + 1);\n"
            "                    }\n"
            "                }\n"
            "                \n"
            "                return new RecursiveMultiplier().multiplyRecursive(nums, 0);\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        // 내부 함수: 결과 포맷팅\n"
            "        class ResultFormatter {\n"
            "            public Map<String, Object> formatResult(int value, int count) {\n"
            "                Map<String, Object> result = new HashMap<>();\n"
            "                result.put(\"result\", value);\n"
            "                result.put(\"formatted\", \"Product: \" + String.format(\"%,d\", value));\n"
            "                result.put(\"count\", count);\n"
            "                result.put(\"precision\", Constants.DEFAULT_PRECISION);\n"
            "                return result;\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        if (numbers.isEmpty()) {\n"
            "            Map<String, Object> emptyResult = new HashMap<>();\n"
            "            emptyResult.put(\"result\", 0);\n"
            "            emptyResult.put(\"formatted\", \"Empty list\");\n"
            "            return emptyResult;\n"
            "        }\n"
            "        \n"
            "        int result = new ProductCalculator().calculateProduct(numbers);\n"
            "        value = result;\n"
            "        Map<String, Object> formattedResult = new ResultFormatter().formatResult(result, numbers.size());\n"
            "        \n"
            "        System.out.println(\"Multiplication result: \" + formattedResult);\n"
            "        \n"
            "        return formattedResult;\n"
            "    }\n"
            "    \n"
            "    public double calculateCircleArea(double radius) {\n"
            "        /**\n"
            "         * 원의 넓이를 계산하는 메소드 (상수 사용)\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 반지름 검증\n"
            "        class RadiusValidator {\n"
            "            public static boolean validateRadius(double r) {\n"
            "                return r > 0;\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        if (!RadiusValidator.validateRadius(radius)) {\n"
            "            throw new IllegalArgumentException(\"반지름은 양수여야 합니다\");\n"
            "        }\n"
            "        \n"
            "        double area = Constants.PI_CONSTANT * radius * radius;\n"
            "        return Math.round(area * Math.pow(10, Constants.DEFAULT_PRECISION)) / Math.pow(10, Constants.DEFAULT_PRECISION);\n"
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
        changed_ranges = [LineRange(33, 40)]  # 파라미터 있는 생성자
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import java.util.*;\n"
            "public class SampleCalculator {\n"
            "    /**\n"
            "     * 간단한 계산기 클래스 - tree-sitter 테스트용\n"
            "     */\n"
            "    \n"
            "    private int value;\n"
            "    private List<String> history;\n"
            "    private String mode;\n"
            "    \n"
            "    public SampleCalculator() {\n"
            "        this(0);\n"
            "    }\n"
            "    \n"
            "    public SampleCalculator(int initialValue) {\n"
            "        /**\n"
            "         * 계산기 초기화\n"
            "         */\n"
            "        this.value = initialValue;\n"
            "        this.history = new ArrayList<>();\n"
            "        this.mode = Constants.CALCULATION_MODES.get(\"basic\");\n"
            "    }\n"
            "    \n"
            "    public int addNumbers(int a, int b) {\n"
            "        /**\n"
            "         * 두 수를 더하는 메소드\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 입력값 검증\n"
            "        class InputValidator {\n"
            "            public static boolean validateInputs(int x, int y) {\n"
            "                return true; // Java에서는 기본적으로 int 타입 검증됨\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        // 내부 함수: 연산 로깅\n"
            "        class OperationLogger {\n"
            "            public void logOperation(String operation, int result) {\n"
            "                if (history.size() < Constants.MAX_CALCULATION_STEPS) {\n"
            "                    history.add(operation + \" = \" + result);\n"
            "                    System.out.println(\"Logged: \" + operation + \" = \" + result);\n"
            "                }\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        if (!InputValidator.validateInputs(a, b)) {\n"
            "            throw new IllegalArgumentException(\"입력값이 숫자가 아닙니다\");\n"
            "        }\n"
            "        \n"
            "        int result = a + b;\n"
            "        value = result;\n"
            "        new OperationLogger().logOperation(\"add: \" + a + \" + \" + b, result);\n"
            "        System.out.println(\"Addition result: \" + result);\n"
            "        return result;\n"
            "    }\n"
            "    \n"
            "    public Map<String, Object> multiplyAndFormat(List<Integer> numbers) {\n"
            "        /**\n"
            "         * 숫자 리스트를 곱하고 결과를 포맷팅하는 메소드\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 곱셈 계산\n"
            "        class ProductCalculator {\n"
            "            public int calculateProduct(List<Integer> nums) {\n"
            "                if (nums.isEmpty()) {\n"
            "                    return 0;\n"
            "                }\n"
            "                \n"
            "                // 재귀적 곱셈 함수 (중첩 내부 함수)\n"
            "                class RecursiveMultiplier {\n"
            "                    public int multiplyRecursive(List<Integer> items, int index) {\n"
            "                        if (index >= items.size()) {\n"
            "                            return 1;\n"
            "                        }\n"
            "                        return items.get(index) * multiplyRecursive(items, index + 1);\n"
            "                    }\n"
            "                }\n"
            "                \n"
            "                return new RecursiveMultiplier().multiplyRecursive(nums, 0);\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        // 내부 함수: 결과 포맷팅\n"
            "        class ResultFormatter {\n"
            "            public Map<String, Object> formatResult(int value, int count) {\n"
            "                Map<String, Object> result = new HashMap<>();\n"
            "                result.put(\"result\", value);\n"
            "                result.put(\"formatted\", \"Product: \" + String.format(\"%,d\", value));\n"
            "                result.put(\"count\", count);\n"
            "                result.put(\"precision\", Constants.DEFAULT_PRECISION);\n"
            "                return result;\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        if (numbers.isEmpty()) {\n"
            "            Map<String, Object> emptyResult = new HashMap<>();\n"
            "            emptyResult.put(\"result\", 0);\n"
            "            emptyResult.put(\"formatted\", \"Empty list\");\n"
            "            return emptyResult;\n"
            "        }\n"
            "        \n"
            "        int result = new ProductCalculator().calculateProduct(numbers);\n"
            "        value = result;\n"
            "        Map<String, Object> formattedResult = new ResultFormatter().formatResult(result, numbers.size());\n"
            "        \n"
            "        System.out.println(\"Multiplication result: \" + formattedResult);\n"
            "        \n"
            "        return formattedResult;\n"
            "    }\n"
            "    \n"
            "    public double calculateCircleArea(double radius) {\n"
            "        /**\n"
            "         * 원의 넓이를 계산하는 메소드 (상수 사용)\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 반지름 검증\n"
            "        class RadiusValidator {\n"
            "            public static boolean validateRadius(double r) {\n"
            "                return r > 0;\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        if (!RadiusValidator.validateRadius(radius)) {\n"
            "            throw new IllegalArgumentException(\"반지름은 양수여야 합니다\");\n"
            "        }\n"
            "        \n"
            "        double area = Constants.PI_CONSTANT * radius * radius;\n"
            "        return Math.round(area * Math.pow(10, Constants.DEFAULT_PRECISION)) / Math.pow(10, Constants.DEFAULT_PRECISION);\n"
            "    }\n"
            "}"
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
        changed_ranges = [LineRange(42, 44)]  # addNumbers 메서드
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import java.util.*;\n"
            "public int addNumbers(int a, int b) {\n"
            "        /**\n"
            "         * 두 수를 더하는 메소드\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 입력값 검증\n"
            "        class InputValidator {\n"
            "            public static boolean validateInputs(int x, int y) {\n"
            "                return true; // Java에서는 기본적으로 int 타입 검증됨\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        // 내부 함수: 연산 로깅\n"
            "        class OperationLogger {\n"
            "            public void logOperation(String operation, int result) {\n"
            "                if (history.size() < Constants.MAX_CALCULATION_STEPS) {\n"
            "                    history.add(operation + \" = \" + result);\n"
            "                    System.out.println(\"Logged: \" + operation + \" = \" + result);\n"
            "                }\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        if (!InputValidator.validateInputs(a, b)) {\n"
            "            throw new IllegalArgumentException(\"입력값이 숫자가 아닙니다\");\n"
            "        }\n"
            "        \n"
            "        int result = a + b;\n"
            "        value = result;\n"
            "        new OperationLogger().logOperation(\"add: \" + a + \" + \" + b, result);\n"
            "        System.out.println(\"Addition result: \" + result);\n"
            "        return result;\n"
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
        changed_ranges = [
            LineRange(75, 78),
            LineRange(120, 125),
        ]  # multiplyAndFormat 메서드
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import java.util.*;\n"
            "public Map<String, Object> multiplyAndFormat(List<Integer> numbers) {\n"
            "        /**\n"
            "         * 숫자 리스트를 곱하고 결과를 포맷팅하는 메소드\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 곱셈 계산\n"
            "        class ProductCalculator {\n"
            "            public int calculateProduct(List<Integer> nums) {\n"
            "                if (nums.isEmpty()) {\n"
            "                    return 0;\n"
            "                }\n"
            "                \n"
            "                // 재귀적 곱셈 함수 (중첩 내부 함수)\n"
            "                class RecursiveMultiplier {\n"
            "                    public int multiplyRecursive(List<Integer> items, int index) {\n"
            "                        if (index >= items.size()) {\n"
            "                            return 1;\n"
            "                        }\n"
            "                        return items.get(index) * multiplyRecursive(items, index + 1);\n"
            "                    }\n"
            "                }\n"
            "                \n"
            "                return new RecursiveMultiplier().multiplyRecursive(nums, 0);\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        // 내부 함수: 결과 포맷팅\n"
            "        class ResultFormatter {\n"
            "            public Map<String, Object> formatResult(int value, int count) {\n"
            "                Map<String, Object> result = new HashMap<>();\n"
            "                result.put(\"result\", value);\n"
            "                result.put(\"formatted\", \"Product: \" + String.format(\"%,d\", value));\n"
            "                result.put(\"count\", count);\n"
            "                result.put(\"precision\", Constants.DEFAULT_PRECISION);\n"
            "                return result;\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        if (numbers.isEmpty()) {\n"
            "            Map<String, Object> emptyResult = new HashMap<>();\n"
            "            emptyResult.put(\"result\", 0);\n"
            "            emptyResult.put(\"formatted\", \"Empty list\");\n"
            "            return emptyResult;\n"
            "        }\n"
            "        \n"
            "        int result = new ProductCalculator().calculateProduct(numbers);\n"
            "        value = result;\n"
            "        Map<String, Object> formattedResult = new ResultFormatter().formatResult(result, numbers.size());\n"
            "        \n"
            "        System.out.println(\"Multiplication result: \" + formattedResult);\n"
            "        \n"
            "        return formattedResult;\n"
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
        changed_ranges = [LineRange(88, 95)]  # RecursiveMultiplier 내부 클래스
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import java.util.*;\n"
            "class RecursiveMultiplier {\n"
            "                    public int multiplyRecursive(List<Integer> items, int index) {\n"
            "                        if (index >= items.size()) {\n"
            "                            return 1;\n"
            "                        }\n"
            "                        return items.get(index) * multiplyRecursive(items, index + 1);\n"
            "                    }\n"
            "                }"
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
        changed_ranges = [LineRange(155, 160)]  # helperFunction 내부 코드 범위
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import java.util.*;\n"
            "public static String helperFunction(Map<String, Object> data) {\n"
            "        \n"
            "        // 내부 함수: 딕셔너리 아이템 포맷팅\n"
            "        class DictFormatter {\n"
            "            public List<String> formatDictItems(Map<String, Object> items) {\n"
            "                List<String> formatted = new ArrayList<>();\n"
            "                for (Map.Entry<String, Object> entry : items.entrySet()) {\n"
            "                    formatted.add(entry.getKey() + \": \" + entry.getValue());\n"
            "                }\n"
            "                return formatted;\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        List<String> formattedItems = new DictFormatter().formatDictItems(data);\n"
            "        return \"Helper processed: \" + String.join(\", \", formattedItems);\n"
            "    }"
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
        changed_ranges = [LineRange(182, 190)]  # advancedCalculatorFactory 메서드
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import java.util.*;\n"
            "public static SampleCalculator advancedCalculatorFactory(String mode) {\n"
            "        \n"
            "        // 내부 함수: 모드별 계산기 생성\n"
            "        class CalculatorCreator {\n"
            "            public SampleCalculator createCalculatorWithMode(String calcMode) {\n"
            "                SampleCalculator calc = new SampleCalculator();\n"
            "                if (Constants.CALCULATION_MODES.containsKey(calcMode)) {\n"
            "                    calc.mode = Constants.CALCULATION_MODES.get(calcMode);\n"
            "                }\n"
            "                return calc;\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        // 내부 함수: 모드 검증\n"
            "        class ModeValidator {\n"
            "            public static boolean validateMode(String m) {\n"
            "                return Constants.CALCULATION_MODES.containsKey(m);\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        if (!ModeValidator.validateMode(mode)) {\n"
            "            mode = \"basic\";\n"
            "        }\n"
            "        \n"
            "        return new CalculatorCreator().createCalculatorWithMode(mode);\n"
            "    }"
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
        changed_ranges = [LineRange(42, 42)]  # addNumbers 선언부만
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import java.util.*;\n"
            "public int addNumbers(int a, int b) {\n"
            "        /**\n"
            "         * 두 수를 더하는 메소드\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 입력값 검증\n"
            "        class InputValidator {\n"
            "            public static boolean validateInputs(int x, int y) {\n"
            "                return true; // Java에서는 기본적으로 int 타입 검증됨\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        // 내부 함수: 연산 로깅\n"
            "        class OperationLogger {\n"
            "            public void logOperation(String operation, int result) {\n"
            "                if (history.size() < Constants.MAX_CALCULATION_STEPS) {\n"
            "                    history.add(operation + \" = \" + result);\n"
            "                    System.out.println(\"Logged: \" + operation + \" = \" + result);\n"
            "                }\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        if (!InputValidator.validateInputs(a, b)) {\n"
            "            throw new IllegalArgumentException(\"입력값이 숫자가 아닙니다\");\n"
            "        }\n"
            "        \n"
            "        int result = a + b;\n"
            "        value = result;\n"
            "        new OperationLogger().logOperation(\"add: \" + a + \" + \" + b, result);\n"
            "        System.out.println(\"Addition result: \" + result);\n"
            "        return result;\n"
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
        changed_ranges = [LineRange(155, 155)]  # helperFunction 선언부만
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import java.util.*;\n"
            "public static String helperFunction(Map<String, Object> data) {\n"
            "        \n"
            "        // 내부 함수: 딕셔너리 아이템 포맷팅\n"
            "        class DictFormatter {\n"
            "            public List<String> formatDictItems(Map<String, Object> items) {\n"
            "                List<String> formatted = new ArrayList<>();\n"
            "                for (Map.Entry<String, Object> entry : items.entrySet()) {\n"
            "                    formatted.add(entry.getKey() + \": \" + entry.getValue());\n"
            "                }\n"
            "                return formatted;\n"
            "            }\n"
            "        }\n"
            "        \n"
            "        List<String> formattedItems = new DictFormatter().formatDictItems(data);\n"
            "        return \"Helper processed: \" + String.join(\", \", formattedItems);\n"
            "    }"
        )

        assert len(contexts) == 2
        all_context = "\n".join(contexts)
        assert all_context == expected_result


class TestModuleLevelElements:
    """모듈 레벨 요소 추출 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.java"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Java용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("java")

    def test_basic_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """기본 상수들 추출 테스트."""
        changed_ranges = [LineRange(9, 10)]  # Constants 클래스 내 상수들
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import java.util.*;\n"
            "public class Constants {\n"
            "    public static final int MAX_CALCULATION_STEPS = 100;\n"
            "    public static final int DEFAULT_PRECISION = 2;\n"
            "    public static final double PI_CONSTANT = 3.14159;\n"
            "    \n"
            "    public static final Map<String, String> CALCULATION_MODES = Map.of(\n"
            "        \"basic\", \"Basic calculations\",\n"
            "        \"advanced\", \"Advanced calculations with logging\",\n"
            "        \"debug\", \"Debug mode with detailed output\"\n"
            "    );\n"
            "}"
        )

        assert len(contexts) == 2
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_map_constant(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """맵 상수 추출 테스트."""
        changed_ranges = [LineRange(12, 16)]  # CALCULATION_MODES 맵
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import java.util.*;\n"
            "public class Constants {\n"
            "    public static final int MAX_CALCULATION_STEPS = 100;\n"
            "    public static final int DEFAULT_PRECISION = 2;\n"
            "    public static final double PI_CONSTANT = 3.14159;\n"
            "    \n"
            "    public static final Map<String, String> CALCULATION_MODES = Map.of(\n"
            "        \"basic\", \"Basic calculations\",\n"
            "        \"advanced\", \"Advanced calculations with logging\",\n"
            "        \"debug\", \"Debug mode with detailed output\"\n"
            "    );\n"
            "}"
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
        changed_ranges = [LineRange(212, 213)]  # MODULE_VERSION
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "import java.util.*;\n"
            "class ModuleConstants {\n"
            "    public static final String MODULE_VERSION = \"1.0.0\";\n"
            "    public static final Map<String, String> AUTHOR_INFO = Map.of(\n"
            "        \"name\", \"Test Author\",\n"
            "        \"email\", \"test@example.com\"\n"
            "    );\n"
            "}"
        )

        assert len(contexts) == 2
        all_context = "\n".join(contexts)
        assert all_context == expected_result


class TestMultiRangeExtraction:
    """여러 범위에 걸친 추출 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.java"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Java용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("java")

    def test_three_cross_classes(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """3개 클래스에 걸친 영역 추출 테스트."""
        changed_ranges = [
            LineRange(129, 210)
        ]  # calculateCircleArea ~ CalculatorFactory
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) == 5
        all_context = "\n".join(contexts)
        # 전체 결과가 너무 길어서 주요 콘텐츠만 검증
        assert "public double calculateCircleArea" in all_context
        assert "public static String helperFunction" in all_context
        assert "public static SampleCalculator advancedCalculatorFactory" in all_context
        # import 문 검증
        assert "import java.util.*;" in all_context

    def test_two_blocks_cross_methods(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """2개 블록에 걸친 메서드 추출 테스트."""
        changed_ranges = [LineRange(42, 47), LineRange(155, 160)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) == 3
        all_context = "\n".join(contexts)
        # 전체 결과가 길어서 주요 콘텐츠만 검증
        assert "public int addNumbers(int a, int b)" in all_context
        assert "public static String helperFunction" in all_context
        # import 문 검증
        assert "import java.util.*;" in all_context

    def test_non_contiguous_ranges(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """비연속적인 여러 범위 추출 테스트."""
        changed_ranges = [
            LineRange(9, 10),  # Constants 클래스 상수들
            LineRange(135, 137),  # RadiusValidator 내부 클래스
            LineRange(212, 213),  # 모듈 레벨 상수들
        ]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) == 4
        all_context = "\n".join(contexts)
        # 전체 결과가 길어서 주요 콘텐츠만 검증
        assert "MAX_CALCULATION_STEPS = 100" in all_context
        assert "class RadiusValidator" in all_context or "validateRadius" in all_context
        assert 'MODULE_VERSION = "1.0.0"' in all_context
        # import 문 검증
        assert "import java.util.*;" in all_context


class TestComplexScenarios:
    """복잡한 시나리오 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.java"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Java용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("java")

    def test_entire_class_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """전체 클래스 추출 테스트."""
        changed_ranges = [LineRange(20, 148)]  # SampleCalculator 전체 클래스
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) == 2
        all_context = "\n".join(contexts)
        # 전체 결과가 너무 길어서 주요 콘텐츠만 검증
        assert "public class SampleCalculator" in all_context
        assert "public SampleCalculator(int initialValue)" in all_context
        assert "public int addNumbers(int a, int b)" in all_context
        assert "public Map<String, Object> multiplyAndFormat" in all_context
        assert "public double calculateCircleArea" in all_context
        # import 문 검증
        assert "import java.util.*;" in all_context

    def test_class_and_module_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스와 모듈 상수 동시 추출 테스트."""
        changed_ranges = [LineRange(8, 217)]  # Constants 클래스부터 모듈 상수까지
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) == 7
        all_context = "\n".join(contexts)
        # 전체 결과가 매우 길어서 주요 콘텐츠만 검증
        assert "public class SampleCalculator" in all_context
        assert "public static String helperFunction" in all_context
        assert "public static SampleCalculator advancedCalculatorFactory" in all_context
        assert 'MODULE_VERSION = "1.0.0"' in all_context
        assert "AUTHOR_INFO" in all_context
        # 상수들 검증
        assert "MAX_CALCULATION_STEPS" in all_context
        assert "CALCULATION_MODES" in all_context
        # import 문 검증
        assert "import java.util.*;" in all_context


class TestEdgeCases:
    """엣지 케이스 및 에러 처리 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.java"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Java용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("java")

    def test_invalid_line_ranges(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """파일 범위를 벗어나는 라인 범위 테스트."""
        changed_ranges = [LineRange(200, 300)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # 범위를 벗어나더라도 에러가 발생하지 않아야 함
        # import 문만 반환되어야 함
        assert len(contexts) == 4
        all_context = "\n".join(contexts)
        assert "import java.util.*;" in all_context

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
        # import 문과 기본 상수 반환
        assert len(contexts) == 2
        all_context = "\n".join(contexts)
        assert "import java.util.*;" in all_context
