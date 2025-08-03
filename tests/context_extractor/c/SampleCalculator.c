/**
 * 테스트용 샘플 클래스 - tree-sitter 파싱 테스트에 사용됩니다.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <math.h>

// 파일 상수들
#define MAX_CALCULATION_STEPS 100
#define DEFAULT_PRECISION 2
#define PI_CONSTANT 3.14159

typedef struct {
    char basic[50];
    char advanced[50];
    char debug[50];
} CalculationModes;

static const CalculationModes CALCULATION_MODES = {
    .basic = "Basic calculations",
    .advanced = "Advanced calculations with logging",
    .debug = "Debug mode with detailed output"
};

typedef struct {
    int result;
    char formatted[100];
    int count;
    int precision;
} FormattedResult;

typedef struct {
    int value;
    char history[MAX_CALCULATION_STEPS][100];
    int history_count;
    char mode[50];
} SampleCalculator;

// 생성자 함수
SampleCalculator* create_sample_calculator(int initial_value) {
    /**
     * 계산기 초기화
     */
    SampleCalculator* calc = (SampleCalculator*)malloc(sizeof(SampleCalculator));
    calc->value = initial_value;
    calc->history_count = 0;
    strcpy(calc->mode, CALCULATION_MODES.basic);
    return calc;
}

int add_numbers(SampleCalculator* calc, int a, int b) {
    /**
     * 두 수를 더하는 메소드
     */
    
    // 내부 함수: 입력값 검증
    bool validate_inputs(int x, int y) {
        return true; // C에서는 타입이 보장됨
    }
    
    // 내부 함수: 연산 로깅
    void log_operation(SampleCalculator* calc, const char* operation, int result) {
        if (calc->history_count < MAX_CALCULATION_STEPS) {
            sprintf(calc->history[calc->history_count], "%s = %d", operation, result);
            calc->history_count++;
            printf("Logged: %s = %d\n", operation, result);
        }
    }
    
    if (!validate_inputs(a, b)) {
        printf("Error: 입력값이 숫자가 아닙니다\n");
        return -1;
    }
    
    int result = a + b;
    calc->value = result;
    
    char operation[50];
    sprintf(operation, "add: %d + %d", a, b);
    log_operation(calc, operation, result);
    printf("Addition result: %d\n", result);
    
    return result;
}

FormattedResult multiply_and_format(SampleCalculator* calc, int* numbers, int size) {
    /**
     * 숫자 리스트를 곱하고 결과를 포맷팅하는 메소드
     */
    
    // 내부 함수: 곱셈 계산
    int calculate_product(int* nums, int size) {
        if (size == 0) {
            return 0;
        }
        
        // 재귀적 곱셈 함수 (중첩 내부 함수)
        int multiply_recursive(int* items, int size, int index) {
            if (index >= size) {
                return 1;
            }
            return items[index] * multiply_recursive(items, size, index + 1);
        }
        
        return multiply_recursive(nums, size, 0);
    }
    
    // 내부 함수: 결과 포맷팅
    FormattedResult format_result(int value, int count) {
        FormattedResult result;
        result.result = value;
        sprintf(result.formatted, "Product: %d", value);
        result.count = count;
        result.precision = DEFAULT_PRECISION;
        return result;
    }
    
    FormattedResult empty_result = {0, "Empty list", 0, DEFAULT_PRECISION};
    
    if (size == 0) {
        return empty_result;
    }
    
    int result = calculate_product(numbers, size);
    calc->value = result;
    FormattedResult formatted_result = format_result(result, size);
    
    printf("Multiplication result: result=%d, count=%d\n", 
           formatted_result.result, formatted_result.count);
    
    return formatted_result;
}

double calculate_circle_area(SampleCalculator* calc, double radius) {
    /**
     * 원의 넓이를 계산하는 메소드 (상수 사용)
     */
    
    // 내부 함수: 반지름 검증
    bool validate_radius(double r) {
        return r > 0;
    }
    
    if (!validate_radius(radius)) {
        printf("Error: 반지름은 양수여야 합니다\n");
        return -1.0;
    }
    
    double area = PI_CONSTANT * radius * radius;
    return round(area * pow(10, DEFAULT_PRECISION)) / pow(10, DEFAULT_PRECISION);
}

char* helper_function(char* data[][2], int size) {
    /**
     * 도우미 함수 - 클래스 외부 함수
     */
    
    // 내부 함수: 딕셔너리 아이템 포맷팅
    void format_dict_items(char* items[][2], int size, char* result) {
        strcpy(result, "");
        for (int i = 0; i < size; i++) {
            char item[100];
            sprintf(item, "%s: %s", items[i][0], items[i][1]);
            if (i > 0) {
                strcat(result, ", ");
            }
            strcat(result, item);
        }
    }
    
    static char result[500];
    char formatted_items[400];
    format_dict_items(data, size, formatted_items);
    sprintf(result, "Helper processed: %s", formatted_items);
    return result;
}

SampleCalculator* advanced_calculator_factory(const char* mode) {
    /**
     * 계산기 팩토리 함수
     */
    
    // 내부 함수: 모드별 계산기 생성
    SampleCalculator* create_calculator_with_mode(const char* calc_mode) {
        SampleCalculator* calc = create_sample_calculator(0);
        if (strcmp(calc_mode, "basic") == 0) {
            strcpy(calc->mode, CALCULATION_MODES.basic);
        } else if (strcmp(calc_mode, "advanced") == 0) {
            strcpy(calc->mode, CALCULATION_MODES.advanced);
        } else if (strcmp(calc_mode, "debug") == 0) {
            strcpy(calc->mode, CALCULATION_MODES.debug);
        }
        return calc;
    }
    
    // 내부 함수: 모드 검증
    bool validate_mode(const char* m) {
        return (strcmp(m, "basic") == 0 || 
                strcmp(m, "advanced") == 0 || 
                strcmp(m, "debug") == 0);
    }
    
    const char* valid_mode = validate_mode(mode) ? mode : "basic";
    
    return create_calculator_with_mode(valid_mode);
}

// 메모리 해제 함수
void destroy_sample_calculator(SampleCalculator* calc) {
    if (calc) {
        free(calc);
    }
}

// 모듈 레벨 상수
static const char* MODULE_VERSION = "1.0.0";
static const char* AUTHOR_NAME = "Test Author";
static const char* AUTHOR_EMAIL = "test@example.com";