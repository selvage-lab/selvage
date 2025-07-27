"""ContextExtractor JavaScript 테스트 케이스."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import ContextExtractor, LineRange


class TestBasicFunctionExtraction:
    """기본 함수/클래스 추출 기능 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.js"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """JavaScript용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("javascript")

    def test_class_declaration(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스 선언부 추출 테스트."""
        changed_ranges = [LineRange(26, 27)]  # SampleCalculator 클래스 선언부 (Python과 동일하게 전체 클래스 반환)
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "require('fs')\n"
            "require('path')\n"
            "require('util')\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import { basename, dirname } from 'path';\n"
            "import axios from 'axios';\n"
            "class SampleCalculator {\n"
            "    /**\n"
            "     * 간단한 계산기 클래스 - tree-sitter 테스트용\n"
            "     */\n"
            "    \n"
            "    constructor(initialValue = 0) {\n"
            "        /**\n"
            "         * 계산기 초기화\n"
            "         */\n"
            "        this.value = initialValue;\n"
            "        this.history = [];\n"
            "        this.mode = CALCULATION_MODES.basic;\n"
            "    }\n"
            "    \n"
            "    addNumbers(a, b) {\n"
            "        /**\n"
            "         * 두 수를 더하는 메소드\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 입력값 검증\n"
            "        function validateInputs(x, y) {\n"
            "            return typeof x === 'number' && typeof y === 'number';\n"
            "        }\n"
            "        \n"
            "        // 내부 함수: 연산 로깅\n"
            "        const logOperation = (operation, result) => {\n"
            "            if (this.history.length < MAX_CALCULATION_STEPS) {\n"
            "                this.history.push(`${operation} = ${result}`);\n"
            "                console.log(`Logged: ${operation} = ${result}`);\n"
            "            }\n"
            "        };\n"
            "        \n"
            "        if (!validateInputs(a, b)) {\n"
            "            throw new Error(\"입력값이 숫자가 아닙니다\");\n"
            "        }\n"
            "        \n"
            "        const result = a + b;\n"
            "        this.value = result;\n"
            "        logOperation(`add: ${a} + ${b}`, result);\n"
            "        console.log(`Addition result: ${result}`);\n"
            "        return result;\n"
            "    }\n"
            "    \n"
            "    multiplyAndFormat(numbers) {\n"
            "        /**\n"
            "         * 숫자 리스트를 곱하고 결과를 포맷팅하는 메소드\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 곱셈 계산\n"
            "        function calculateProduct(nums) {\n"
            "            if (nums.length === 0) {\n"
            "                return 0;\n"
            "            }\n"
            "            \n"
            "            // 재귀적 곱셈 함수 (중첩 내부 함수)\n"
            "            function multiplyRecursive(items, index = 0) {\n"
            "                if (index >= items.length) {\n"
            "                    return 1;\n"
            "                }\n"
            "                return items[index] * multiplyRecursive(items, index + 1);\n"
            "            }\n"
            "            \n"
            "            return multiplyRecursive(nums);\n"
            "        }\n"
            "        \n"
            "        // 내부 함수: 결과 포맷팅\n"
            "        const formatResult = (value, count) => {\n"
            "            return {\n"
            "                result: value,\n"
            "                formatted: `Product: ${value.toLocaleString()}`,\n"
            "                count: count,\n"
            "                precision: DEFAULT_PRECISION\n"
            "            };\n"
            "        };\n"
            "        \n"
            "        if (numbers.length === 0) {\n"
            "            return { result: 0, formatted: \"Empty list\" };\n"
            "        }\n"
            "        \n"
            "        const result = calculateProduct(numbers);\n"
            "        this.value = result;\n"
            "        const formattedResult = formatResult(result, numbers.length);\n"
            "        \n"
            "        console.log(`Multiplication result: ${JSON.stringify(formattedResult)}`);\n"
            "        \n"
            "        return formattedResult;\n"
            "    }\n"
            "    \n"
            "    calculateCircleArea(radius) {\n"
            "        /**\n"
            "         * 원의 넓이를 계산하는 메소드 (상수 사용)\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 반지름 검증\n"
            "        function validateRadius(r) {\n"
            "            return r > 0;\n"
            "        }\n"
            "        \n"
            "        if (!validateRadius(radius)) {\n"
            "            throw new Error(\"반지름은 양수여야 합니다\");\n"
            "        }\n"
            "        \n"
            "        const area = PI_CONSTANT * radius * radius;\n"
            "        return Math.round(area * Math.pow(10, DEFAULT_PRECISION)) / Math.pow(10, DEFAULT_PRECISION);\n"
            "    }\n"
            "}"
        )

        assert len(contexts) == 7
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_constructor_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """생성자 메서드 추출 테스트."""
        changed_ranges = [LineRange(35, 37)]  # constructor 메서드
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "require('fs')\n"
            "require('path')\n"
            "require('util')\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import { basename, dirname } from 'path';\n"
            "import axios from 'axios';\n"
            "constructor(initialValue = 0) {\n"
            "        /**\n"
            "         * 계산기 초기화\n"
            "         */\n"
            "        this.value = initialValue;\n"
            "        this.history = [];\n"
            "        this.mode = CALCULATION_MODES.basic;\n"
            "    }"
        )

        assert len(contexts) == 7
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_class_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스 메서드 추출 테스트."""
        changed_ranges = [
            LineRange(46, 63)
        ]  # addNumbers 메서드 (import 문 6줄 추가로 인한 라인 번호 조정)
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "require('fs')\n"
            "require('path')\n"
            "require('util')\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import { basename, dirname } from 'path';\n"
            "import axios from 'axios';\n"
            "addNumbers(a, b) {\n"
            "        /**\n"
            "         * 두 수를 더하는 메소드\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 입력값 검증\n"
            "        function validateInputs(x, y) {\n"
            "            return typeof x === 'number' && typeof y === 'number';\n"
            "        }\n"
            "        \n"
            "        // 내부 함수: 연산 로깅\n"
            "        const logOperation = (operation, result) => {\n"
            "            if (this.history.length < MAX_CALCULATION_STEPS) {\n"
            "                this.history.push(`${operation} = ${result}`);\n"
            "                console.log(`Logged: ${operation} = ${result}`);\n"
            "            }\n"
            "        };\n"
            "        \n"
            "        if (!validateInputs(a, b)) {\n"
            '            throw new Error("입력값이 숫자가 아닙니다");\n'
            "        }\n"
            "        \n"
            "        const result = a + b;\n"
            "        this.value = result;\n"
            "        logOperation(`add: ${a} + ${b}`, result);\n"
            "        console.log(`Addition result: ${result}`);\n"
            "        return result;\n"
            "    }"
        )

        assert len(contexts) == 7
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_complex_method(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """복잡한 메서드 추출 테스트."""
        changed_ranges = [LineRange(71, 109)]  # multiplyAndFormat 메서드
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "require('fs')\n"
            "require('path')\n"
            "require('util')\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import { basename, dirname } from 'path';\n"
            "import axios from 'axios';\n"
            "multiplyAndFormat(numbers) {\n"
            "        /**\n"
            "         * 숫자 리스트를 곱하고 결과를 포맷팅하는 메소드\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 곱셈 계산\n"
            "        function calculateProduct(nums) {\n"
            "            if (nums.length === 0) {\n"
            "                return 0;\n"
            "            }\n"
            "            \n"
            "            // 재귀적 곱셈 함수 (중첩 내부 함수)\n"
            "            function multiplyRecursive(items, index = 0) {\n"
            "                if (index >= items.length) {\n"
            "                    return 1;\n"
            "                }\n"
            "                return items[index] * multiplyRecursive(items, index + 1);\n"
            "            }\n"
            "            \n"
            "            return multiplyRecursive(nums);\n"
            "        }\n"
            "        \n"
            "        // 내부 함수: 결과 포맷팅\n"
            "        const formatResult = (value, count) => {\n"
            "            return {\n"
            "                result: value,\n"
            "                formatted: `Product: ${value.toLocaleString()}`,\n"
            "                count: count,\n"
            "                precision: DEFAULT_PRECISION\n"
            "            };\n"
            "        };\n"
            "        \n"
            "        if (numbers.length === 0) {\n"
            '            return { result: 0, formatted: "Empty list" };\n'
            "        }\n"
            "        \n"
            "        const result = calculateProduct(numbers);\n"
            "        this.value = result;\n"
            "        const formattedResult = formatResult(result, numbers.length);\n"
            "        \n"
            "        console.log(`Multiplication result: ${JSON.stringify(formattedResult)}`);\n"
            "        \n"
            "        return formattedResult;\n"
            "    }"
        )

        assert len(contexts) == 7
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_nested_inner_function(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """중첩 내부 함수 추출 테스트."""
        changed_ranges = [LineRange(82, 85)]  # multiplyRecursive 내부 함수
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "require('fs')\n"
            "require('path')\n"
            "require('util')\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import { basename, dirname } from 'path';\n"
            "import axios from 'axios';\n"
            "function multiplyRecursive(items, index = 0) {\n"
            "                if (index >= items.length) {\n"
            "                    return 1;\n"
            "                }\n"
            "                return items[index] * multiplyRecursive(items, index + 1);\n"
            "            }"
        )

        assert len(contexts) == 7
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_external_function(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스 외부 함수 추출 테스트."""
        changed_ranges = [LineRange(134, 148)]  # helperFunction
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "require('fs')\n"
            "require('path')\n"
            "require('util')\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import { basename, dirname } from 'path';\n"
            "import axios from 'axios';\n"
            "function helperFunction(data) {\n"
            "    /**\n"
            "     * 도우미 함수 - 클래스 외부 함수\n"
            "     */\n"
            "    \n"
            "    // 내부 함수: 딕셔너리 아이템 포맷팅\n"
            "    function formatDictItems(items) {\n"
            "        const formatted = [];\n"
            "        for (const [key, value] of Object.entries(items)) {\n"
            "            formatted.push(`${key}: ${value}`);\n"
            "        }\n"
            "        return formatted;\n"
            "    }\n"
            "    \n"
            "    const formattedItems = formatDictItems(data);\n"
            "    return `Helper processed: ${formattedItems.join(', ')}`;\n"
            "}"
        )

        assert len(contexts) == 7
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_factory_function(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """팩토리 함수 추출 테스트."""
        changed_ranges = [LineRange(151, 170)]  # advancedCalculatorFactory
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "require('fs')\n"
            "require('path')\n"
            "require('util')\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import { basename, dirname } from 'path';\n"
            "import axios from 'axios';\n"
            'function advancedCalculatorFactory(mode = "basic") {\n'
            "    /**\n"
            "     * 계산기 팩토리 함수\n"
            "     */\n"
            "    \n"
            "    // 내부 함수: 모드별 계산기 생성\n"
            "    function createCalculatorWithMode(calcMode) {\n"
            "        const calc = new SampleCalculator();\n"
            "        if (calcMode in CALCULATION_MODES) {\n"
            "            calc.mode = CALCULATION_MODES[calcMode];\n"
            "        }\n"
            "        return calc;\n"
            "    }\n"
            "    \n"
            "    // 내부 함수: 모드 검증\n"
            "    function validateMode(m) {\n"
            "        return m in CALCULATION_MODES;\n"
            "    }\n"
            "    \n"
            "    if (!validateMode(mode)) {\n"
            '        mode = "basic";\n'
            "    }\n"
            "    \n"
            "    return createCalculatorWithMode(mode);\n"
            "}"
        )

        assert len(contexts) == 7
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_method_declaration_only(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """메서드 선언부만 추출 테스트."""
        changed_ranges = [LineRange(40, 40)]  # addNumbers 선언부만
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "require('fs')\n"
            "require('path')\n"
            "require('util')\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import { basename, dirname } from 'path';\n"
            "import axios from 'axios';\n"
            "addNumbers(a, b) {\n"
            "        /**\n"
            "         * 두 수를 더하는 메소드\n"
            "         */\n"
            "        \n"
            "        // 내부 함수: 입력값 검증\n"
            "        function validateInputs(x, y) {\n"
            "            return typeof x === 'number' && typeof y === 'number';\n"
            "        }\n"
            "        \n"
            "        // 내부 함수: 연산 로깅\n"
            "        const logOperation = (operation, result) => {\n"
            "            if (this.history.length < MAX_CALCULATION_STEPS) {\n"
            "                this.history.push(`${operation} = ${result}`);\n"
            "                console.log(`Logged: ${operation} = ${result}`);\n"
            "            }\n"
            "        };\n"
            "        \n"
            "        if (!validateInputs(a, b)) {\n"
            '            throw new Error("입력값이 숫자가 아닙니다");\n'
            "        }\n"
            "        \n"
            "        const result = a + b;\n"
            "        this.value = result;\n"
            "        logOperation(`add: ${a} + ${b}`, result);\n"
            "        console.log(`Addition result: ${result}`);\n"
            "        return result;\n"
            "    }"
        )

        assert len(contexts) == 7
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_external_function_declaration_only(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """외부 함수 선언부만 추출 테스트."""
        changed_ranges = [LineRange(133, 133)]  # helperFunction 선언부만
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "require('fs')\n"
            "require('path')\n"
            "require('util')\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import { basename, dirname } from 'path';\n"
            "import axios from 'axios';\n"
            "function helperFunction(data) {\n"
            "    /**\n"
            "     * 도우미 함수 - 클래스 외부 함수\n"
            "     */\n"
            "    \n"
            "    // 내부 함수: 딕셔너리 아이템 포맷팅\n"
            "    function formatDictItems(items) {\n"
            "        const formatted = [];\n"
            "        for (const [key, value] of Object.entries(items)) {\n"
            "            formatted.push(`${key}: ${value}`);\n"
            "        }\n"
            "        return formatted;\n"
            "    }\n"
            "    \n"
            "    const formattedItems = formatDictItems(data);\n"
            "    return `Helper processed: ${formattedItems.join(', ')}`;\n"
            "}"
        )

        assert len(contexts) == 7
        all_context = "\n".join(contexts)
        assert all_context == expected_result


class TestModuleLevelElements:
    """모듈 레벨 요소 추출 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.js"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """JavaScript용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("javascript")

    def test_basic_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """기본 상수들 추출 테스트."""
        changed_ranges = [LineRange(16, 18)]  # 상수 선언
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "require('fs')\n"
            "require('path')\n"
            "require('util')\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import { basename, dirname } from 'path';\n"
            "import axios from 'axios';\n"
            "const MAX_CALCULATION_STEPS = 100;\n"
            "const DEFAULT_PRECISION = 2;\n"
            "const PI_CONSTANT = 3.14159;"
        )

        assert len(contexts) == 9
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_object_constant(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """객체 상수 추출 테스트."""
        changed_ranges = [LineRange(20, 21)]  # CALCULATION_MODES 객체
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "require('fs')\n"
            "require('path')\n"
            "require('util')\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import { basename, dirname } from 'path';\n"
            "import axios from 'axios';\n"
            "const CALCULATION_MODES = {\n"
            '    basic: "Basic calculations",\n'
            '    advanced: "Advanced calculations with logging",\n'
            '    debug: "Debug mode with detailed output"\n'
            "};"
        )

        assert len(contexts) == 7
        all_context = "\n".join(contexts)
        assert all_context == expected_result

    def test_module_bottom_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """모듈 하단 상수들 추출 테스트."""
        changed_ranges = [LineRange(178, 178)]  # MODULE_VERSION
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "require('fs')\n"
            "require('path')\n"
            "require('util')\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import { basename, dirname } from 'path';\n"
            "import axios from 'axios';\n"
            'const MODULE_VERSION = "1.0.0";'
        )

        assert len(contexts) == 7
        all_context = "\n".join(contexts)
        assert all_context == expected_result


class TestMultiRangeExtraction:
    """여러 범위에 걸친 추출 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.js"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """JavaScript용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("javascript")

    def test_three_cross_functions(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """3개 함수에 걸친 영역 추출 테스트."""
        changed_ranges = [
            LineRange(114, 175)
        ]  # calculateCircleArea ~ advancedCalculatorFactory
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) == 9
        all_context = "\n".join(contexts)
        # 전체 결과가 너무 길어서 주요 버전만 검증
        assert "calculateCircleArea(radius)" in all_context
        assert "function helperFunction" in all_context
        assert "function advancedCalculatorFactory" in all_context
        # import 문들 검증
        assert "require('fs')" in all_context
        assert "import { readFile, writeFile } from 'fs/promises';" in all_context

    def test_two_blocks_cross_methods(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """2개 블록에 걸친 메서드 추출 테스트."""
        changed_ranges = [LineRange(40, 43), LineRange(133, 137)]  # 라인 번호 조정
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) == 8
        all_context = "\n".join(contexts)
        # 전체 결과가 길어서 주요 콘텐츠만 검증
        assert "addNumbers(a, b)" in all_context
        assert "function helperFunction" in all_context
        # import 문들 검증
        assert "require('fs')" in all_context
        assert "import { readFile, writeFile } from 'fs/promises';" in all_context

    def test_non_contiguous_ranges(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """비연속적인 여러 범위 추출 테스트."""
        changed_ranges = [
            LineRange(16, 18),  # 파일 상수들
            LineRange(120, 122),  # validateRadius 내부 함수
            LineRange(178, 178),  # 모듈 레벨 상수들
        ]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        expected_result = (
            "require('fs')\n"
            "require('path')\n"
            "require('util')\n"
            "import { readFile, writeFile } from 'fs/promises';\n"
            "import { basename, dirname } from 'path';\n"
            "import axios from 'axios';\n"
            "const MAX_CALCULATION_STEPS = 100;\n"
            "const DEFAULT_PRECISION = 2;\n"
            "const PI_CONSTANT = 3.14159;\n"
            "function validateRadius(r) {\n"
            "            return r > 0;\n"
            "        }\n"
            'const MODULE_VERSION = "1.0.0";'
        )

        assert len(contexts) == 11
        all_context = "\n".join(contexts)
        assert all_context == expected_result


class TestComplexScenarios:
    """복잡한 시나리오 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.js"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """JavaScript용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("javascript")

    def test_entire_class_extraction(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """전체 클래스 추출 테스트."""
        changed_ranges = [LineRange(26, 131)]  # SampleCalculator 전체 클래스
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) == 7
        all_context = "\n".join(contexts)
        # 전체 클래스 결과가 매우 길어서 주요 콘텐츠만 검증
        assert "class SampleCalculator" in all_context
        assert "constructor(initialValue = 0)" in all_context
        assert "addNumbers(a, b)" in all_context
        assert "multiplyAndFormat(numbers)" in all_context
        assert "calculateCircleArea(radius)" in all_context
        # import 문들 검증
        assert "require('fs')" in all_context
        assert "import { readFile, writeFile } from 'fs/promises';" in all_context

    def test_class_and_module_constants(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """클래스와 모듈 상수 동시 추출 테스트."""
        changed_ranges = [LineRange(16, 182)]  # 상수부터 모듈 끝까지
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        assert len(contexts) == 16
        all_context = "\n".join(contexts)
        # 전체 결과가 매우 길어서 주요 콘텐츠만 검증
        assert "class SampleCalculator" in all_context
        assert 'MODULE_VERSION = "1.0.0"' in all_context
        assert "MAX_CALCULATION_STEPS = 100" in all_context
        assert "CALCULATION_MODES = {" in all_context
        assert "function helperFunction" in all_context
        assert "function advancedCalculatorFactory" in all_context
        # import 문들 검증
        assert "require('fs')" in all_context
        assert "import { readFile, writeFile } from 'fs/promises';" in all_context


class TestEdgeCases:
    """엣지 케이스 및 에러 처리 테스트."""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleCalculator.js"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """JavaScript용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("javascript")

    def test_invalid_line_ranges(
        self,
        extractor: ContextExtractor,
        sample_file_path: Path,
    ) -> None:
        """파일 범위를 벗어나는 라인 범위 테스트."""
        changed_ranges = [LineRange(200, 300)]
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # 범위를 벗어나더라도 에러가 발생하지 않아야 함
        # import 문들만 반환되어야 함
        assert len(contexts) == 6
        all_context = "\n".join(contexts)
        assert "require('fs')" in all_context
        assert "import { readFile, writeFile } from 'fs/promises';" in all_context

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
        changed_ranges = [LineRange(14, 15)]  # 빈 라인 또는 주석
        contexts = extractor.extract_contexts(sample_file_path, changed_ranges)

        # 빈 라인 범위에서도 적절히 처리되어야 함
        # import 문들과 기본 상수 반환
        assert len(contexts) == 7
        all_context = "\n".join(contexts)
        assert "require('fs')" in all_context
        assert "import { readFile, writeFile } from 'fs/promises';" in all_context
