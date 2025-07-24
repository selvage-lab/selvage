/**
 * 테스트용 샘플 클래스 - tree-sitter 파싱 테스트에 사용됩니다.
 */

import Foundation

// 파일 상수들
let MAX_CALCULATION_STEPS = 100
let DEFAULT_PRECISION = 2
let PI_CONSTANT = 3.14159

let CALCULATION_MODES: [String: String] = [
    "basic": "Basic calculations",
    "advanced": "Advanced calculations with logging",
    "debug": "Debug mode with detailed output"
]

struct FormattedResult {
    let result: Int
    let formatted: String
    let count: Int
    let precision: Int
}

class SampleCalculator {
    /**
     * 간단한 계산기 클래스 - tree-sitter 테스트용
     */
    
    private var value: Int = 0
    private var history: [String] = []
    private var mode: String
    
    init(initialValue: Int = 0) {
        /**
         * 계산기 초기화
         */
        self.value = initialValue
        self.history = []
        self.mode = CALCULATION_MODES["basic"] ?? "basic"
    }
    
    func addNumbers(a: Int, b: Int) throws -> Int {
        /**
         * 두 수를 더하는 메소드
         */
        
        // 내부 함수: 입력값 검증
        func validateInputs(x: Int, y: Int) -> Bool {
            return true // Swift에서는 타입이 보장됨
        }
        
        // 내부 함수: 연산 로깅
        func logOperation(operation: String, result: Int) {
            if history.count < MAX_CALCULATION_STEPS {
                let logEntry = "\(operation) = \(result)"
                history.append(logEntry)
                print("Logged: \(logEntry)")
            }
        }
        
        guard validateInputs(x: a, y: b) else {
            throw NSError(domain: "SampleCalculator", code: 1, userInfo: [NSLocalizedDescriptionKey: "입력값이 숫자가 아닙니다"])
        }
        
        let result = a + b
        value = result
        logOperation(operation: "add: \(a) + \(b)", result: result)
        print("Addition result: \(result)")
        
        return result
    }
    
    func multiplyAndFormat(numbers: [Int]) -> FormattedResult {
        /**
         * 숫자 리스트를 곱하고 결과를 포맷팅하는 메소드
         */
        
        // 내부 함수: 곱셈 계산
        func calculateProduct(nums: [Int]) -> Int {
            if nums.isEmpty {
                return 0
            }
            
            // 재귀적 곱셈 함수 (중첩 내부 함수)
            func multiplyRecursive(items: [Int], index: Int = 0) -> Int {
                if index >= items.count {
                    return 1
                }
                return items[index] * multiplyRecursive(items: items, index: index + 1)
            }
            
            return multiplyRecursive(items: nums)
        }
        
        // 내부 함수: 결과 포맷팅
        func formatResult(value: Int, count: Int) -> FormattedResult {
            let formatter = NumberFormatter()
            formatter.numberStyle = .decimal
            let formattedValue = formatter.string(from: NSNumber(value: value)) ?? "\(value)"
            
            return FormattedResult(
                result: value,
                formatted: "Product: \(formattedValue)",
                count: count,
                precision: DEFAULT_PRECISION
            )
        }
        
        if numbers.isEmpty {
            return FormattedResult(
                result: 0,
                formatted: "Empty list",
                count: 0,
                precision: DEFAULT_PRECISION
            )
        }
        
        let result = calculateProduct(nums: numbers)
        value = result
        let formattedResult = formatResult(value: result, count: numbers.count)
        
        print("Multiplication result: \(formattedResult)")
        
        return formattedResult
    }
    
    func calculateCircleArea(radius: Double) throws -> Double {
        /**
         * 원의 넓이를 계산하는 메소드 (상수 사용)
         */
        
        // 내부 함수: 반지름 검증
        func validateRadius(r: Double) -> Bool {
            return r > 0
        }
        
        guard validateRadius(r: radius) else {
            throw NSError(domain: "SampleCalculator", code: 2, userInfo: [NSLocalizedDescriptionKey: "반지름은 양수여야 합니다"])
        }
        
        let area = PI_CONSTANT * radius * radius
        let precisionFactor = pow(10.0, Double(DEFAULT_PRECISION))
        return (area * precisionFactor).rounded() / precisionFactor
    }
}

func helperFunction(data: [String: Any]) -> String {
    /**
     * 도우미 함수 - 클래스 외부 함수
     */
    
    // 내부 함수: 딕셔너리 아이템 포맷팅
    func formatDictItems(items: [String: Any]) -> [String] {
        var formatted: [String] = []
        for (key, value) in items {
            formatted.append("\(key): \(value)")
        }
        return formatted
    }
    
    let formattedItems = formatDictItems(items: data)
    return "Helper processed: \(formattedItems.joined(separator: ", "))"
}

func advancedCalculatorFactory(mode: String = "basic") -> SampleCalculator {
    /**
     * 계산기 팩토리 함수
     */
    
    // 내부 함수: 모드별 계산기 생성
    func createCalculatorWithMode(calcMode: String) -> SampleCalculator {
        let calc = SampleCalculator()
        if CALCULATION_MODES.keys.contains(calcMode) {
            // Swift에서는 private 속성 접근이 제한되므로 여기서는 생략
        }
        return calc
    }
    
    // 내부 함수: 모드 검증
    func validateMode(m: String) -> Bool {
        return CALCULATION_MODES.keys.contains(m)
    }
    
    let validMode = validateMode(m: mode) ? mode : "basic"
    
    return createCalculatorWithMode(calcMode: validMode)
}

// 모듈 레벨 상수
let MODULE_VERSION = "1.0.0"
let AUTHOR_INFO: [String: String] = [
    "name": "Test Author",
    "email": "test@example.com"
]