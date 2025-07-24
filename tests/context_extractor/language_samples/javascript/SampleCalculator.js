/**
 * 테스트용 샘플 클래스 - tree-sitter 파싱 테스트에 사용됩니다.
 */

const fs = require('fs');
const path = require('path');
const util = require('util');

// 파일 상수들
const MAX_CALCULATION_STEPS = 100;
const DEFAULT_PRECISION = 2;
const PI_CONSTANT = 3.14159;

const CALCULATION_MODES = {
    basic: "Basic calculations",
    advanced: "Advanced calculations with logging",
    debug: "Debug mode with detailed output"
};

class SampleCalculator {
    /**
     * 간단한 계산기 클래스 - tree-sitter 테스트용
     */
    
    constructor(initialValue = 0) {
        /**
         * 계산기 초기화
         */
        this.value = initialValue;
        this.history = [];
        this.mode = CALCULATION_MODES.basic;
    }
    
    addNumbers(a, b) {
        /**
         * 두 수를 더하는 메소드
         */
        
        // 내부 함수: 입력값 검증
        function validateInputs(x, y) {
            return typeof x === 'number' && typeof y === 'number';
        }
        
        // 내부 함수: 연산 로깅
        const logOperation = (operation, result) => {
            if (this.history.length < MAX_CALCULATION_STEPS) {
                this.history.push(`${operation} = ${result}`);
                console.log(`Logged: ${operation} = ${result}`);
            }
        };
        
        if (!validateInputs(a, b)) {
            throw new Error("입력값이 숫자가 아닙니다");
        }
        
        const result = a + b;
        this.value = result;
        logOperation(`add: ${a} + ${b}`, result);
        console.log(`Addition result: ${result}`);
        return result;
    }
    
    multiplyAndFormat(numbers) {
        /**
         * 숫자 리스트를 곱하고 결과를 포맷팅하는 메소드
         */
        
        // 내부 함수: 곱셈 계산
        function calculateProduct(nums) {
            if (nums.length === 0) {
                return 0;
            }
            
            // 재귀적 곱셈 함수 (중첩 내부 함수)
            function multiplyRecursive(items, index = 0) {
                if (index >= items.length) {
                    return 1;
                }
                return items[index] * multiplyRecursive(items, index + 1);
            }
            
            return multiplyRecursive(nums);
        }
        
        // 내부 함수: 결과 포맷팅
        const formatResult = (value, count) => {
            return {
                result: value,
                formatted: `Product: ${value.toLocaleString()}`,
                count: count,
                precision: DEFAULT_PRECISION
            };
        };
        
        if (numbers.length === 0) {
            return { result: 0, formatted: "Empty list" };
        }
        
        const result = calculateProduct(numbers);
        this.value = result;
        const formattedResult = formatResult(result, numbers.length);
        
        console.log(`Multiplication result: ${JSON.stringify(formattedResult)}`);
        
        return formattedResult;
    }
    
    calculateCircleArea(radius) {
        /**
         * 원의 넓이를 계산하는 메소드 (상수 사용)
         */
        
        // 내부 함수: 반지름 검증
        function validateRadius(r) {
            return r > 0;
        }
        
        if (!validateRadius(radius)) {
            throw new Error("반지름은 양수여야 합니다");
        }
        
        const area = PI_CONSTANT * radius * radius;
        return Math.round(area * Math.pow(10, DEFAULT_PRECISION)) / Math.pow(10, DEFAULT_PRECISION);
    }
}

function helperFunction(data) {
    /**
     * 도우미 함수 - 클래스 외부 함수
     */
    
    // 내부 함수: 딕셔너리 아이템 포맷팅
    function formatDictItems(items) {
        const formatted = [];
        for (const [key, value] of Object.entries(items)) {
            formatted.push(`${key}: ${value}`);
        }
        return formatted;
    }
    
    const formattedItems = formatDictItems(data);
    return `Helper processed: ${formattedItems.join(', ')}`;
}

function advancedCalculatorFactory(mode = "basic") {
    /**
     * 계산기 팩토리 함수
     */
    
    // 내부 함수: 모드별 계산기 생성
    function createCalculatorWithMode(calcMode) {
        const calc = new SampleCalculator();
        if (calcMode in CALCULATION_MODES) {
            calc.mode = CALCULATION_MODES[calcMode];
        }
        return calc;
    }
    
    // 내부 함수: 모드 검증
    function validateMode(m) {
        return m in CALCULATION_MODES;
    }
    
    if (!validateMode(mode)) {
        mode = "basic";
    }
    
    return createCalculatorWithMode(mode);
}

// 모듈 레벨 상수
const MODULE_VERSION = "1.0.0";
const AUTHOR_INFO = {
    name: "Test Author",
    email: "test@example.com"
};

module.exports = { SampleCalculator, helperFunction, advancedCalculatorFactory };