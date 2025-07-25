/**
 * 테스트용 샘플 클래스 - tree-sitter 파싱 테스트에 사용됩니다.
 */

using System;
using System.Collections.Generic;
using System.Linq;

// 파일 상수들
public static class Constants
{
    public const int MAX_CALCULATION_STEPS = 100;
    public const int DEFAULT_PRECISION = 2;
    public const double PI_CONSTANT = 3.14159;
    
    public static readonly Dictionary<string, string> CALCULATION_MODES = new Dictionary<string, string>
    {
        { "basic", "Basic calculations" },
        { "advanced", "Advanced calculations with logging" },
        { "debug", "Debug mode with detailed output" }
    };
}

public struct FormattedResult
{
    public int Result;
    public string Formatted;
    public int Count;
    public int Precision;
}

public class SampleCalculator
{
    /**
     * 간단한 계산기 클래스 - tree-sitter 테스트용
     */
    
    private int value;
    private List<string> history;
    private string mode;
    
    public SampleCalculator() : this(0)
    {
    }
    
    public SampleCalculator(int initialValue)
    {
        /**
         * 계산기 초기화
         */
        this.value = initialValue;
        this.history = new List<string>();
        this.mode = Constants.CALCULATION_MODES["basic"];
    }
    
    public int AddNumbers(int a, int b)
    {
        /**
         * 두 수를 더하는 메소드
         */
        
        // 내부 함수: 입력값 검증
        bool ValidateInputs(int x, int y)
        {
            return true; // C#에서는 타입이 보장됨
        }
        
        // 내부 함수: 연산 로깅
        void LogOperation(string operation, int result)
        {
            if (history.Count < Constants.MAX_CALCULATION_STEPS)
            {
                string logEntry = $"{operation} = {result}";
                history.Add(logEntry);
                Console.WriteLine($"Logged: {logEntry}");
            }
        }
        
        if (!ValidateInputs(a, b))
        {
            throw new ArgumentException("입력값이 숫자가 아닙니다");
        }
        
        int result = a + b;
        value = result;
        LogOperation($"add: {a} + {b}", result);
        Console.WriteLine($"Addition result: {result}");
        
        return result;
    }
    
    public FormattedResult MultiplyAndFormat(List<int> numbers)
    {
        /**
         * 숫자 리스트를 곱하고 결과를 포맷팅하는 메소드
         */
        
        // 내부 함수: 곱셈 계산
        int CalculateProduct(List<int> nums)
        {
            if (nums.Count == 0)
            {
                return 0;
            }
            
            // 재귀적 곱셈 함수 (중첩 내부 함수)
            int MultiplyRecursive(List<int> items, int index = 0)
            {
                if (index >= items.Count)
                {
                    return 1;
                }
                return items[index] * MultiplyRecursive(items, index + 1);
            }
            
            return MultiplyRecursive(nums);
        }
        
        // 내부 함수: 결과 포맷팅
        FormattedResult FormatResult(int value, int count)
        {
            return new FormattedResult
            {
                Result = value,
                Formatted = $"Product: {value:N0}",
                Count = count,
                Precision = Constants.DEFAULT_PRECISION
            };
        }
        
        if (numbers.Count == 0)
        {
            return new FormattedResult
            {
                Result = 0,
                Formatted = "Empty list",
                Count = 0,
                Precision = Constants.DEFAULT_PRECISION
            };
        }
        
        int result = CalculateProduct(numbers);
        value = result;
        FormattedResult formattedResult = FormatResult(result, numbers.Count);
        
        Console.WriteLine($"Multiplication result: {formattedResult}");
        
        return formattedResult;
    }
    
    public double CalculateCircleArea(double radius)
    {
        /**
         * 원의 넓이를 계산하는 메소드 (상수 사용)
         */
        
        // 내부 함수: 반지름 검증
        bool ValidateRadius(double r)
        {
            return r > 0;
        }
        
        if (!ValidateRadius(radius))
        {
            throw new ArgumentException("반지름은 양수여야 합니다");
        }
        
        double area = Constants.PI_CONSTANT * radius * radius;
        return Math.Round(area * Math.Pow(10, Constants.DEFAULT_PRECISION)) / Math.Pow(10, Constants.DEFAULT_PRECISION);
    }
}

public static class HelperUtils
{
    /**
     * 도우미 함수 - 클래스 외부 함수
     */
    
    public static string HelperFunction(Dictionary<string, object> data)
    {
        
        // 내부 함수: 딕셔너리 아이템 포맷팅
        List<string> FormatDictItems(Dictionary<string, object> items)
        {
            var formatted = new List<string>();
            foreach (var kvp in items)
            {
                formatted.Add($"{kvp.Key}: {kvp.Value}");
            }
            return formatted;
        }
        
        List<string> formattedItems = FormatDictItems(data);
        return $"Helper processed: {string.Join(", ", formattedItems)}";
    }
}

public static class CalculatorFactory
{
    /**
     * 계산기 팩토리 함수
     */
    
    public static SampleCalculator AdvancedCalculatorFactory(string mode = "basic")
    {
        
        // 내부 함수: 모드별 계산기 생성
        SampleCalculator CreateCalculatorWithMode(string calcMode)
        {
            var calc = new SampleCalculator();
            if (Constants.CALCULATION_MODES.ContainsKey(calcMode))
            {
                // C#에서는 private 필드 접근이 제한되므로 reflection 필요하지만 여기서는 생략
            }
            return calc;
        }
        
        // 내부 함수: 모드 검증
        bool ValidateMode(string m)
        {
            return Constants.CALCULATION_MODES.ContainsKey(m);
        }
        
        if (!ValidateMode(mode))
        {
            mode = "basic";
        }
        
        return CreateCalculatorWithMode(mode);
    }
}

// 모듈 레벨 상수
public static class ModuleConstants
{
    public const string MODULE_VERSION = "1.0.0";
    public static readonly Dictionary<string, string> AUTHOR_INFO = new Dictionary<string, string>
    {
        { "name", "Test Author" },
        { "email", "test@example.com" }
    };
}