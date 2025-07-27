import kotlin.collections.*
import kotlin.math.*
import kotlin.text.*

// 파일 상수들
const val MAX_CALCULATION_STEPS = 100
const val DEFAULT_PRECISION = 2
const val PI_CONSTANT = 3.14159

val CALCULATION_MODES = mapOf(
    "basic" to "Basic calculations",
    "advanced" to "Advanced calculations with logging",
    "debug" to "Debug mode with detailed output"
)

data class FormattedResult(
    val result: Int,
    val formatted: String,
    val count: Int,
    val precision: Int
)

class SampleCalculator(private var value: Int = 0) {
    /**
     * 간단한 계산기 클래스 - tree-sitter 테스트용
     */
    
    private val history = mutableListOf<String>()
    private var mode = CALCULATION_MODES["basic"] ?: "basic"
    
    init {
        /**
         * 계산기 초기화
         */
        this.history.clear()
        this.mode = CALCULATION_MODES["basic"] ?: "basic"
    }
    
    fun addNumbers(a: Int, b: Int): Int {
        /**
         * 두 수를 더하는 메소드
         */
        
        // 내부 함수: 입력값 검증
        fun validateInputs(x: Int, y: Int): Boolean {
            return true // Kotlin에서는 타입이 보장됨
        }
        
        // 내부 함수: 연산 로깅
        fun logOperation(operation: String, result: Int) {
            if (history.size < MAX_CALCULATION_STEPS) {
                history.add("$operation = $result")
                println("Logged: $operation = $result")
            }
        }
        
        if (!validateInputs(a, b)) {
            throw IllegalArgumentException("입력값이 숫자가 아닙니다")
        }
        
        val result = a + b
        value = result
        logOperation("add: $a + $b", result)
        println("Addition result: $result")
        return result
    }
    
    fun multiplyAndFormat(numbers: List<Int>): FormattedResult {
        /**
         * 숫자 리스트를 곱하고 결과를 포맷팅하는 메소드
         */
        
        // 내부 함수: 곱셈 계산
        fun calculateProduct(nums: List<Int>): Int {
            if (nums.isEmpty()) {
                return 0
            }
            
            // 재귀적 곱셈 함수 (중첩 내부 함수)
            fun multiplyRecursive(items: List<Int>, index: Int = 0): Int {
                if (index >= items.size) {
                    return 1
                }
                return items[index] * multiplyRecursive(items, index + 1)
            }
            
            return multiplyRecursive(nums)
        }
        
        // 내부 함수: 결과 포맷팅
        fun formatResult(value: Int, count: Int): FormattedResult {
            return FormattedResult(
                result = value,
                formatted = "Product: ${"%,d".format(value)}",
                count = count,
                precision = DEFAULT_PRECISION
            )
        }
        
        if (numbers.isEmpty()) {
            return FormattedResult(0, "Empty list", 0, DEFAULT_PRECISION)
        }
        
        val result = calculateProduct(numbers)
        value = result
        val formattedResult = formatResult(result, numbers.size)
        
        println("Multiplication result: $formattedResult")
        
        return formattedResult
    }
    
    fun calculateCircleArea(radius: Double): Double {
        /**
         * 원의 넓이를 계산하는 메소드 (상수 사용)
         */
        
        // 내부 함수: 반지름 검증
        fun validateRadius(r: Double): Boolean {
            return r > 0
        }
        
        if (!validateRadius(radius)) {
            throw IllegalArgumentException("반지름은 양수여야 합니다")
        }
        
        val area = PI_CONSTANT * radius * radius
        return kotlin.math.round(area * kotlin.math.pow(10.0, DEFAULT_PRECISION.toDouble())) / kotlin.math.pow(10.0, DEFAULT_PRECISION.toDouble())
    }
}

fun helperFunction(data: Map<String, Any>): String {
    /**
     * 도우미 함수 - 클래스 외부 함수
     */
    
    // 내부 함수: 딕셔너리 아이템 포맷팅
    fun formatDictItems(items: Map<String, Any>): List<String> {
        val formatted = mutableListOf<String>()
        for ((key, value) in items) {
            formatted.add("$key: $value")
        }
        return formatted
    }
    
    val formattedItems = formatDictItems(data)
    return "Helper processed: ${formattedItems.joinToString(", ")}"
}

fun advancedCalculatorFactory(mode: String = "basic"): SampleCalculator {
    /**
     * 계산기 팩토리 함수
     */
    
    // 내부 함수: 모드별 계산기 생성
    fun createCalculatorWithMode(calcMode: String): SampleCalculator {
        val calc = SampleCalculator()
        if (calcMode in CALCULATION_MODES) {
            // Kotlin에서는 private 필드 접근이 제한되므로 공개 메소드 사용
        }
        return calc
    }
    
    // 내부 함수: 모드 검증
    fun validateMode(m: String): Boolean {
        return m in CALCULATION_MODES
    }
    
    val validMode = if (validateMode(mode)) mode else "basic"
    
    return createCalculatorWithMode(validMode)
}

// 모듈 레벨 상수
const val MODULE_VERSION = "1.0.0"
val AUTHOR_INFO = mapOf(
    "name" to "Test Author",
    "email" to "test@example.com"
)
