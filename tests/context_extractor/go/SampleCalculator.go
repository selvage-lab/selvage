/**
 * 테스트용 샘플 클래스 - tree-sitter 파싱 테스트에 사용됩니다.
 */

package main

import (
	"fmt"
	"math"
	"strings"
)

// 파일 상수들
const (
	MaxCalculationSteps = 100
	DefaultPrecision    = 2
	PiConstant          = 3.14159
)

var CalculationModes = map[string]string{
	"basic":    "Basic calculations",
	"advanced": "Advanced calculations with logging",
	"debug":    "Debug mode with detailed output",
}

type FormattedResult struct {
	Result    int    `json:"result"`
	Formatted string `json:"formatted"`
	Count     int    `json:"count"`
	Precision int    `json:"precision"`
}

type SampleCalculator struct {
	/**
	 * 간단한 계산기 클래스 - tree-sitter 테스트용
	 */
	value   int
	history []string
	mode    string
}

func NewSampleCalculator(initialValue int) *SampleCalculator {
	/**
	 * 계산기 초기화
	 */
	return &SampleCalculator{
		value:   initialValue,
		history: make([]string, 0),
		mode:    CalculationModes["basic"],
	}
}

func (calc *SampleCalculator) AddNumbers(a, b int) (int, error) {
	/**
	 * 두 수를 더하는 메소드
	 */
	
	// 내부 함수: 입력값 검증
	validateInputs := func(x, y int) bool {
		return true // Go에서는 타입이 보장됨
	}
	
	// 내부 함수: 연산 로깅
	logOperation := func(operation string, result int) {
		if len(calc.history) < MaxCalculationSteps {
			logEntry := fmt.Sprintf("%s = %d", operation, result)
			calc.history = append(calc.history, logEntry)
			fmt.Printf("Logged: %s\n", logEntry)
		}
	}
	
	if !validateInputs(a, b) {
		return 0, fmt.Errorf("입력값이 숫자가 아닙니다")
	}
	
	result := a + b
	calc.value = result
	logOperation(fmt.Sprintf("add: %d + %d", a, b), result)
	fmt.Printf("Addition result: %d\n", result)
	
	return result, nil
}

func (calc *SampleCalculator) MultiplyAndFormat(numbers []int) FormattedResult {
	/**
	 * 숫자 리스트를 곱하고 결과를 포맷팅하는 메소드
	 */
	
	// 내부 함수: 곱셈 계산
	calculateProduct := func(nums []int) int {
		if len(nums) == 0 {
			return 0
		}
		
		// 재귀적 곱셈 함수 (중첩 내부 함수)
		var multiplyRecursive func([]int, int) int
		multiplyRecursive = func(items []int, index int) int {
			if index >= len(items) {
				return 1
			}
			return items[index] * multiplyRecursive(items, index+1)
		}
		
		return multiplyRecursive(nums, 0)
	}
	
	// 내부 함수: 결과 포맷팅
	formatResult := func(value, count int) FormattedResult {
		return FormattedResult{
			Result:    value,
			Formatted: fmt.Sprintf("Product: %d", value),
			Count:     count,
			Precision: DefaultPrecision,
		}
	}
	
	if len(numbers) == 0 {
		return FormattedResult{
			Result:    0,
			Formatted: "Empty list",
			Count:     0,
			Precision: DefaultPrecision,
		}
	}
	
	result := calculateProduct(numbers)
	calc.value = result
	formattedResult := formatResult(result, len(numbers))
	
	fmt.Printf("Multiplication result: %+v\n", formattedResult)
	
	return formattedResult
}

func (calc *SampleCalculator) CalculateCircleArea(radius float64) (float64, error) {
	/**
	 * 원의 넓이를 계산하는 메소드 (상수 사용)
	 */
	
	// 내부 함수: 반지름 검증
	validateRadius := func(r float64) bool {
		return r > 0
	}
	
	if !validateRadius(radius) {
		return 0, fmt.Errorf("반지름은 양수여야 합니다")
	}
	
	area := PiConstant * radius * radius
	precisionFactor := math.Pow(10, DefaultPrecision)
	return math.Round(area*precisionFactor) / precisionFactor, nil
}

func HelperFunction(data map[string]interface{}) string {
	/**
	 * 도우미 함수 - 클래스 외부 함수
	 */
	
	// 내부 함수: 딕셔너리 아이템 포맷팅
	formatDictItems := func(items map[string]interface{}) []string {
		var formatted []string
		for key, value := range items {
			formatted = append(formatted, fmt.Sprintf("%s: %v", key, value))
		}
		return formatted
	}
	
	formattedItems := formatDictItems(data)
	return fmt.Sprintf("Helper processed: %s", strings.Join(formattedItems, ", "))
}

func AdvancedCalculatorFactory(mode string) *SampleCalculator {
	/**
	 * 계산기 팩토리 함수
	 */
	
	// 내부 함수: 모드별 계산기 생성
	createCalculatorWithMode := func(calcMode string) *SampleCalculator {
		calc := NewSampleCalculator(0)
		if _, exists := CalculationModes[calcMode]; exists {
			calc.mode = CalculationModes[calcMode]
		}
		return calc
	}
	
	// 내부 함수: 모드 검증
	validateMode := func(m string) bool {
		_, exists := CalculationModes[m]
		return exists
	}
	
	if mode == "" {
		mode = "basic"
	}
	
	if !validateMode(mode) {
		mode = "basic"
	}
	
	return createCalculatorWithMode(mode)
}

// 모듈 레벨 상수
const ModuleVersion = "1.0.0"

var AuthorInfo = map[string]string{
	"name":  "Test Author",
	"email": "test@example.com",
}