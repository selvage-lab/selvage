/**
 * Import 변경 테스트용 샘플 파일 - multiline import 구문 포함
 */

import java.util.List;
import java.util.ArrayList;

import java.io.IOException;
import java.nio.file.Path;

public class ImportTestClass {
    /**
     * Import 변경 테스트를 위한 클래스
     */
    
    private String name;
    private int value = 0;
    
    public String processData(String data) throws IOException {
        /**
         * 데이터 처리 메서드
         */
        List<String> numbers = new ArrayList<>();
        // 간단한 숫자 추출 로직
        for (char c : data.toCharArray()) {
            if (Character.isDigit(c)) {
                numbers.add(String.valueOf(c));
            }
        }
        
        Path filePath = Path.of("/tmp/test.txt");
        return "Processed: " + numbers + ", Path: " + filePath;
    }
}

class HelperClass {
    /**
     * 도우미 클래스
     */
    
    public static String helperMethod() {
        return "Helper result";
    }
}

// 모듈 상수
class ModuleConstants {
    public static final String MODULE_CONSTANT = "test_value";
}