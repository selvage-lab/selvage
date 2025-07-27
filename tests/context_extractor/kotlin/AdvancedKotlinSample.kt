import kotlin.collections.*
import kotlin.reflect.*

// 타입 별칭 선언
typealias StringMap = Map<String, String>
typealias IntProcessor = (Int) -> Int

// 커스텀 어노테이션 선언
@Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION)
@Retention(AnnotationRetention.RUNTIME)
annotation class Cacheable(val value: String = "default")

@Target(AnnotationTarget.PROPERTY)
annotation class Validated(val pattern: String)

// 인터페이스 선언
interface Calculator {
    fun calculate(a: Int, b: Int): Int
    fun getOperationName(): String
    
    // 인터페이스의 기본 구현
    fun describe(): String {
        return "Calculator: ${getOperationName()}"
    }
}

interface Processor<T> {
    fun process(input: T): T
    fun validate(input: T): Boolean
}

// 열거형 선언
enum class Operation(val symbol: String, val priority: Int) {
    ADD("+", 1) {
        override fun apply(a: Int, b: Int): Int = a + b
    },
    SUBTRACT("-", 1) {
        override fun apply(a: Int, b: Int): Int = a - b
    },
    MULTIPLY("*", 2) {
        override fun apply(a: Int, b: Int): Int = a * b
    },
    DIVIDE("/", 2) {
        override fun apply(a: Int, b: Int): Int = a / b
    };
    
    abstract fun apply(a: Int, b: Int): Int
    
    fun getDescription(): String {
        return "$name ($symbol) - Priority: $priority"
    }
}

// 싱글톤 객체 선언
object MathUtils {
    const val PI = 3.14159
    const val E = 2.71828
    
    fun square(x: Int): Int {
        return x * x
    }
    
    fun cube(x: Int): Int {
        return x * x * x
    }
    
    fun fibonacci(n: Int): Int {
        return if (n <= 1) n else fibonacci(n - 1) + fibonacci(n - 2)
    }
}

object StringUtils {
    fun reverse(input: String): String {
        return input.reversed()
    }
    
    fun isPalindrome(input: String): Boolean {
        val cleaned = input.lowercase().filter { it.isLetterOrDigit() }
        return cleaned == cleaned.reversed()
    }
}

// 동반 객체와 보조 생성자를 가진 클래스
@Cacheable("advanced-calculator")
class AdvancedCalculator private constructor(
    private val name: String,
    private val precision: Int
) : Calculator {
    
    private val history = mutableListOf<String>()
    
    // 주 생성자
    constructor(name: String) : this(name, 2)
    
    // 보조 생성자
    constructor(name: String, precision: Int, enableLogging: Boolean) : this(name, precision) {
        if (enableLogging) {
            history.add("Calculator '$name' initialized with precision $precision")
        }
    }
    
    // 또 다른 보조 생성자
    constructor() : this("DefaultCalculator", 2, false)
    
    companion object {
        const val VERSION = "2.0.0"
        const val MAX_PRECISION = 10
        private var instanceCount = 0
        
        fun createSimple(): AdvancedCalculator {
            instanceCount++
            return AdvancedCalculator("Simple-$instanceCount")
        }
        
        fun createAdvanced(precision: Int): AdvancedCalculator {
            instanceCount++
            return AdvancedCalculator("Advanced-$instanceCount", precision, true)
        }
        
        fun getInstanceCount(): Int = instanceCount
    }
    
    override fun calculate(a: Int, b: Int): Int {
        val result = a + b
        history.add("$a + $b = $result")
        return result
    }
    
    override fun getOperationName(): String = "Addition"
    
    fun getHistory(): List<String> = history.toList()
    
    fun clearHistory() {
        history.clear()
    }
}

// 데이터 클래스 with 동반 객체
data class Result(val value: Int, val operation: String, val timestamp: Long) {
    companion object {
        fun success(value: Int, operation: String): Result {
            return Result(value, operation, System.currentTimeMillis())
        }
        
        fun error(operation: String): Result {
            return Result(-1, "ERROR: $operation", System.currentTimeMillis())
        }
    }
}

// 람다 표현식들을 포함한 함수
fun processNumbers(numbers: List<Int>): StringMap {
    // 람다 표현식으로 작업 정의
    val doubler: IntProcessor = { x -> x * 2 }
    val squarer: IntProcessor = { x -> x * x }
    val incrementer: IntProcessor = { x -> x + 1 }
    
    // 고차 함수와 람다
    val operations = mapOf<String, IntProcessor>(
        "double" to doubler,
        "square" to squarer,
        "increment" to incrementer,
        "halve" to { x -> x / 2 },
        "negate" to { x -> -x }
    )
    
    // 복잡한 람다 표현식
    val complexProcessor: (List<Int>) -> List<String> = { nums ->
        nums.filter { it > 0 }
            .map { num -> 
                operations.entries.associate { (name, op) ->
                    "$name($num)" to op(num).toString()
                }.entries.joinToString(", ") { "${it.key}=${it.value}" }
            }
    }
    
    val results = complexProcessor(numbers)
    
    return results.mapIndexed { index, result -> 
        "result_$index" to result 
    }.toMap()
}

// 추상 클래스 with 동반 객체
abstract class BaseProcessor<T> {
    abstract fun process(input: T): T
    
    companion object {
        const val DEFAULT_TIMEOUT = 5000L
        
        fun <T> createChain(vararg processors: BaseProcessor<T>): BaseProcessor<T> {
            return object : BaseProcessor<T>() {
                override fun process(input: T): T {
                    return processors.fold(input) { acc, processor -> 
                        processor.process(acc) 
                    }
                }
            }
        }
    }
}