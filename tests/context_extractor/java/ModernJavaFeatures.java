/**
 * Modern Java Features 테스트용 샘플 파일 - tree-sitter 파싱 테스트에 사용됩니다.
 * Java 14+ Record, Annotation, Enum, Interface 기능들을 포함합니다.
 */

import java.util.*;
import java.lang.annotation.*;

// 커스텀 어노테이션 타입 정의
@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.TYPE, ElementType.METHOD, ElementType.FIELD})
@interface ProcessingInfo {
    String value() default "unknown";
    int priority() default 1;
    String[] tags() default {};
}

// 검증 어노테이션 타입
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.PARAMETER)
@interface Validate {
    boolean required() default true;
    String pattern() default "";
    int min() default 0;
    int max() default Integer.MAX_VALUE;
}

// 계산 모드 열거형
@ProcessingInfo(value = "calculation_modes", priority = 5)
enum CalculationMode {
    BASIC("기본 계산", 1.0),
    ADVANCED("고급 계산", 1.5),
    SCIENTIFIC("과학 계산", 2.0),
    DEBUG("디버그 모드", 0.5);
    
    private final String description;
    private final double multiplier;
    
    CalculationMode(String description, double multiplier) {
        this.description = description;
        this.multiplier = multiplier;
    }
    
    public String getDescription() {
        return description;
    }
    
    public double getMultiplier() {
        return multiplier;
    }
    
    public static CalculationMode fromString(String mode) {
        for (CalculationMode calcMode : values()) {
            if (calcMode.name().equalsIgnoreCase(mode)) {
                return calcMode;
            }
        }
        return BASIC;
    }
}

// 상태 열거형
enum ProcessingStatus {
    PENDING,
    IN_PROGRESS,
    COMPLETED,
    FAILED,
    CANCELLED
}

// 계산 인터페이스
@ProcessingInfo(value = "calculator_interface", priority = 3)
interface Calculator {
    
    /**
     * 기본 계산 메서드
     */
    double calculate(double a, double b);
    
    /**
     * 배치 계산 메서드
     */
    default List<Double> calculateBatch(List<Double> numbers) {
        if (numbers.size() < 2) {
            return numbers;
        }
        
        List<Double> results = new ArrayList<>();
        for (int i = 0; i < numbers.size() - 1; i++) {
            results.add(calculate(numbers.get(i), numbers.get(i + 1)));
        }
        return results;
    }
    
    /**
     * 결과 검증 메서드
     */
    default boolean validateResult(double result) {
        return !Double.isNaN(result) && !Double.isInfinite(result);
    }
    
    /**
     * 정적 팩토리 메서드
     */
    static Calculator createSimpleCalculator() {
        return new Calculator() {
            @Override
            public double calculate(double a, double b) {
                return a + b;
            }
        };
    }
}

// 고급 계산 인터페이스
interface AdvancedCalculator extends Calculator {
    
    /**
     * 복잡한 계산 메서드
     */
    Map<String, Object> complexCalculation(@Validate(required = true) List<Double> inputs,
                                         @Validate(min = 1, max = 10) int iterations);
    
    /**
     * 기본 구현 메서드
     */
    default String formatResult(double result, CalculationMode mode) {
        return String.format("Result: %.2f (Mode: %s)", 
                           result * mode.getMultiplier(), 
                           mode.getDescription());
    }
}

// 계산 결과 Record (Java 14+)
@ProcessingInfo(value = "calculation_result", priority = 4, tags = {"result", "data"})
record CalculationResult(
    double value,
    CalculationMode mode,
    ProcessingStatus status,
    long timestamp,
    Map<String, Object> metadata
) {
    
    /**
     * Record 생성자 검증
     */
    public CalculationResult {
        if (Double.isNaN(value) || Double.isInfinite(value)) {
            throw new IllegalArgumentException("Invalid calculation value");
        }
        if (mode == null) {
            mode = CalculationMode.BASIC;
        }
        if (status == null) {
            status = ProcessingStatus.PENDING;
        }
        if (metadata == null) {
            metadata = new HashMap<>();
        }
    }
    
    /**
     * 정적 팩토리 메서드
     */
    public static CalculationResult success(double value, CalculationMode mode) {
        return new CalculationResult(
            value, 
            mode, 
            ProcessingStatus.COMPLETED,
            System.currentTimeMillis(),
            Map.of("success", true, "error", "none")
        );
    }
    
    /**
     * 실패 결과 생성
     */
    public static CalculationResult failure(String errorMessage) {
        return new CalculationResult(
            0.0,
            CalculationMode.BASIC,
            ProcessingStatus.FAILED,
            System.currentTimeMillis(),
            Map.of("success", false, "error", errorMessage)
        );
    }
    
    /**
     * 포맷된 결과 반환
     */
    public String formatValue() {
        return String.format("%.3f", value * mode.getMultiplier());
    }
    
    /**
     * 성공 여부 확인
     */
    public boolean isSuccess() {
        return status == ProcessingStatus.COMPLETED;
    }
}

// 계산기 설정 Record
record CalculatorConfig(
    CalculationMode defaultMode,
    boolean enableLogging,
    int maxIterations,
    Map<String, String> properties
) {
    
    public CalculatorConfig {
        if (maxIterations <= 0) {
            maxIterations = 100;
        }
        if (properties == null) {
            properties = new HashMap<>();
        }
    }
    
    public static CalculatorConfig defaultConfig() {
        return new CalculatorConfig(
            CalculationMode.BASIC,
            true,
            100,
            Map.of("precision", "high", "timeout", "30s")
        );
    }
}

// 메인 계산기 클래스
@ProcessingInfo(value = "main_calculator", priority = 1, tags = {"calculator", "main"})
public class ModernCalculator implements AdvancedCalculator {
    
    private final CalculatorConfig config;
    private final List<CalculationResult> history;
    private CalculationMode currentMode;
    
    public ModernCalculator() {
        this(CalculatorConfig.defaultConfig());
    }
    
    public ModernCalculator(CalculatorConfig config) {
        this.config = config;
        this.history = new ArrayList<>();
        this.currentMode = config.defaultMode();
    }
    
    @Override
    @ProcessingInfo(value = "basic_calculation", priority = 2)
    public double calculate(double a, double b) {
        try {
            double result = a + b;
            
            CalculationResult calcResult = CalculationResult.success(result, currentMode);
            history.add(calcResult);
            
            if (config.enableLogging()) {
                System.out.println("Calculation: " + a + " + " + b + " = " + result);
            }
            
            return result;
        } catch (Exception e) {
            CalculationResult failureResult = CalculationResult.failure(e.getMessage());
            history.add(failureResult);
            throw e;
        }
    }
    
    @Override
    public Map<String, Object> complexCalculation(
            @Validate(required = true) List<Double> inputs,
            @Validate(min = 1, max = 10) int iterations) {
        
        if (inputs == null || inputs.isEmpty()) {
            throw new IllegalArgumentException("Inputs cannot be null or empty");
        }
        
        Map<String, Object> results = new HashMap<>();
        List<Double> processedValues = new ArrayList<>();
        
        for (int i = 0; i < iterations; i++) {
            List<Double> iterationResults = calculateBatch(inputs);
            processedValues.addAll(iterationResults);
        }
        
        double sum = processedValues.stream().mapToDouble(Double::doubleValue).sum();
        double average = sum / processedValues.size();
        
        results.put("sum", sum);
        results.put("average", average);
        results.put("iterations", iterations);
        results.put("processed_count", processedValues.size());
        results.put("mode", currentMode.getDescription());
        
        CalculationResult complexResult = CalculationResult.success(average, currentMode);
        history.add(complexResult);
        
        return results;
    }
    
    public void setMode(CalculationMode mode) {
        this.currentMode = mode;
    }
    
    public CalculationMode getCurrentMode() {
        return currentMode;
    }
    
    public List<CalculationResult> getHistory() {
        return new ArrayList<>(history);
    }
    
    public CalculationResult getLastResult() {
        return history.isEmpty() ? null : history.get(history.size() - 1);
    }
    
    public void clearHistory() {
        history.clear();
    }
    
    public Map<String, Object> getStatistics() {
        long successCount = history.stream()
            .mapToLong(result -> result.isSuccess() ? 1 : 0)
            .sum();
        
        double successRate = history.isEmpty() ? 0.0 : 
            (double) successCount / history.size() * 100;
        
        Map<String, Object> stats = new HashMap<>();
        stats.put("total_calculations", history.size());
        stats.put("successful_calculations", successCount);
        stats.put("success_rate", successRate);
        stats.put("current_mode", currentMode.getDescription());
        stats.put("config", config);
        
        return stats;
    }
}

// 계산기 팩토리 클래스
class CalculatorFactory {
    
    public static ModernCalculator createCalculator(CalculationMode mode) {
        CalculatorConfig config = new CalculatorConfig(
            mode,
            true,
            50,
            Map.of("factory_created", "true")
        );
        return new ModernCalculator(config);
    }
    
    public static ModernCalculator createDebugCalculator() {
        CalculatorConfig debugConfig = new CalculatorConfig(
            CalculationMode.DEBUG,
            true,
            10,
            Map.of("debug", "true", "verbose", "true")
        );
        return new ModernCalculator(debugConfig);
    }
}

// 유틸리티 클래스
final class CalculationUtils {
    
    private CalculationUtils() {
        // 유틸리티 클래스
    }
    
    public static boolean isValidNumber(double number) {
        return !Double.isNaN(number) && !Double.isInfinite(number);
    }
    
    public static String formatCalculationMode(CalculationMode mode) {
        return mode.name() + " (" + mode.getDescription() + ")";
    }
    
    public static ProcessingStatus getRandomStatus() {
        ProcessingStatus[] statuses = ProcessingStatus.values();
        return statuses[new Random().nextInt(statuses.length)];
    }
}
