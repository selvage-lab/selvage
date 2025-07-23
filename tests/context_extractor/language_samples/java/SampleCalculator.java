/**
 * 테스트용 샘플 클래스 - tree-sitter 파싱 테스트에 사용됩니다.
 */

import java.util.*;

// 파일 상수들
public class Constants {
    public static final int MAX_CALCULATION_STEPS = 100;
    public static final int DEFAULT_PRECISION = 2;
    public static final double PI_CONSTANT = 3.14159;
    
    public static final Map<String, String> CALCULATION_MODES = Map.of(
        "basic", "Basic calculations",
        "advanced", "Advanced calculations with logging",
        "debug", "Debug mode with detailed output"
    );
}

public class SampleCalculator {
    /**
     * 간단한 계산기 클래스 - tree-sitter 테스트용
     */
    
    private int value;
    private List<String> history;
    private String mode;
    
    public SampleCalculator() {
        this(0);
    }
    
    public SampleCalculator(int initialValue) {
        /**
         * 계산기 초기화
         */
        this.value = initialValue;
        this.history = new ArrayList<>();
        this.mode = Constants.CALCULATION_MODES.get("basic");
    }
    
    public int addNumbers(int a, int b) {
        /**
         * 두 수를 더하는 메소드
         */
        
        // 내부 함수: 입력값 검증
        class InputValidator {
            public static boolean validateInputs(int x, int y) {
                return true; // Java에서는 기본적으로 int 타입 검증됨
            }
        }
        
        // 내부 함수: 연산 로깅
        class OperationLogger {
            public void logOperation(String operation, int result) {
                if (history.size() < Constants.MAX_CALCULATION_STEPS) {
                    history.add(operation + " = " + result);
                    System.out.println("Logged: " + operation + " = " + result);
                }
            }
        }
        
        if (!InputValidator.validateInputs(a, b)) {
            throw new IllegalArgumentException("입력값이 숫자가 아닙니다");
        }
        
        int result = a + b;
        value = result;
        new OperationLogger().logOperation("add: " + a + " + " + b, result);
        System.out.println("Addition result: " + result);
        return result;
    }
    
    public Map<String, Object> multiplyAndFormat(List<Integer> numbers) {
        /**
         * 숫자 리스트를 곱하고 결과를 포맷팅하는 메소드
         */
        
        // 내부 함수: 곱셈 계산
        class ProductCalculator {
            public int calculateProduct(List<Integer> nums) {
                if (nums.isEmpty()) {
                    return 0;
                }
                
                // 재귀적 곱셈 함수 (중첩 내부 함수)
                class RecursiveMultiplier {
                    public int multiplyRecursive(List<Integer> items, int index) {
                        if (index >= items.size()) {
                            return 1;
                        }
                        return items.get(index) * multiplyRecursive(items, index + 1);
                    }
                }
                
                return new RecursiveMultiplier().multiplyRecursive(nums, 0);
            }
        }
        
        // 내부 함수: 결과 포맷팅
        class ResultFormatter {
            public Map<String, Object> formatResult(int value, int count) {
                Map<String, Object> result = new HashMap<>();
                result.put("result", value);
                result.put("formatted", "Product: " + String.format("%,d", value));
                result.put("count", count);
                result.put("precision", Constants.DEFAULT_PRECISION);
                return result;
            }
        }
        
        if (numbers.isEmpty()) {
            Map<String, Object> emptyResult = new HashMap<>();
            emptyResult.put("result", 0);
            emptyResult.put("formatted", "Empty list");
            return emptyResult;
        }
        
        int result = new ProductCalculator().calculateProduct(numbers);
        value = result;
        Map<String, Object> formattedResult = new ResultFormatter().formatResult(result, numbers.size());
        
        System.out.println("Multiplication result: " + formattedResult);
        
        return formattedResult;
    }
    
    public double calculateCircleArea(double radius) {
        /**
         * 원의 넓이를 계산하는 메소드 (상수 사용)
         */
        
        // 내부 함수: 반지름 검증
        class RadiusValidator {
            public static boolean validateRadius(double r) {
                return r > 0;
            }
        }
        
        if (!RadiusValidator.validateRadius(radius)) {
            throw new IllegalArgumentException("반지름은 양수여야 합니다");
        }
        
        double area = Constants.PI_CONSTANT * radius * radius;
        return Math.round(area * Math.pow(10, Constants.DEFAULT_PRECISION)) / Math.pow(10, Constants.DEFAULT_PRECISION);
    }
}

class HelperUtils {
    /**
     * 도우미 함수 - 클래스 외부 함수
     */
    
    public static String helperFunction(Map<String, Object> data) {
        
        // 내부 함수: 딕셔너리 아이템 포맷팅
        class DictFormatter {
            public List<String> formatDictItems(Map<String, Object> items) {
                List<String> formatted = new ArrayList<>();
                for (Map.Entry<String, Object> entry : items.entrySet()) {
                    formatted.add(entry.getKey() + ": " + entry.getValue());
                }
                return formatted;
            }
        }
        
        List<String> formattedItems = new DictFormatter().formatDictItems(data);
        return "Helper processed: " + String.join(", ", formattedItems);
    }
}

class CalculatorFactory {
    /**
     * 계산기 팩토리 함수
     */
    
    public static SampleCalculator advancedCalculatorFactory() {
        return advancedCalculatorFactory("basic");
    }
    
    public static SampleCalculator advancedCalculatorFactory(String mode) {
        
        // 내부 함수: 모드별 계산기 생성
        class CalculatorCreator {
            public SampleCalculator createCalculatorWithMode(String calcMode) {
                SampleCalculator calc = new SampleCalculator();
                if (Constants.CALCULATION_MODES.containsKey(calcMode)) {
                    calc.mode = Constants.CALCULATION_MODES.get(calcMode);
                }
                return calc;
            }
        }
        
        // 내부 함수: 모드 검증
        class ModeValidator {
            public static boolean validateMode(String m) {
                return Constants.CALCULATION_MODES.containsKey(m);
            }
        }
        
        if (!ModeValidator.validateMode(mode)) {
            mode = "basic";
        }
        
        return new CalculatorCreator().createCalculatorWithMode(mode);
    }
}

// 모듈 레벨 상수
class ModuleConstants {
    public static final String MODULE_VERSION = "1.0.0";
    public static final Map<String, String> AUTHOR_INFO = Map.of(
        "name", "Test Author",
        "email", "test@example.com"
    );
}