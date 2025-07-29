/**
 * Import 변경 테스트용 샘플 파일 - multiline import 구문 포함
 */

import kotlin.collections.*
import kotlin.text.toIntOrNull

import java.util.Date
import java.nio.file.Path

class ImportTestClass {
    /**
     * Import 변경 테스트를 위한 클래스
     */
    
    private var name: String = ""
    private var value: Int = 0
    
    fun processData(data: String): String {
        /**
         * 데이터 처리 메서드
         */
        val numbers = mutableListOf<String>()
        // 간단한 숫자 추출 로직
        for (c in data.toCharArray()) {
            if (c.isDigit()) {
                numbers.add(c.toString())
            }
        }
        
        val filePath = Path.of("/tmp/test.txt")
        val currentDate = Date()
        return "Processed: $numbers, Path: $filePath, Date: $currentDate"
    }
}

class HelperClass {
    /**
     * 도우미 클래스
     */
    
    companion object {
        fun helperMethod(): String {
            return "Helper result"
        }
    }
}

// 모듈 상수
object ModuleConstants {
    const val MODULE_CONSTANT = "test_value"
}