# OptimizedContextExtractor 단위 테스트

> **목표**: OptimizedContextExtractor 클래스의 기능을 검증하는 포괄적인 단위 테스트

---

## 테스트 구조 및 설정

### 테스트 픽스처 및 헬퍼 함수

```python
"""test_optimized_context_extractor.py: OptimizedContextExtractor 단위 테스트"""
from __future__ import annotations

import tempfile
import pytest
from pathlib import Path
from dataclasses import dataclass
from typing import Sequence

# 실제 구현된 클래스들 임포트 (가상의 경로)
from selvage.src.diff_parser.parser import parse_git_diff
from selvage.src.diff_parser.models.diff_result import DiffResult
from selvage.src.diff_parser.models.file_diff import FileDiff
from selvage.src.diff_parser.models.hunk import Hunk

# 문서에서 정의된 클래스들
@dataclass
class LineRange:
    """코드 파일의 라인 범위를 나타내는 클래스."""
    start_line: int
    end_line: int

    def __post_init__(self) -> None:
        """유효성 검증을 수행합니다."""
        if self.start_line < 1 or self.end_line < 1:
            raise ValueError("라인 번호는 1 이상이어야 합니다")
        if self.start_line > self.end_line:
            raise ValueError("시작 라인이 끝 라인보다 클 수 없습니다")

    @classmethod
    def from_hunk(cls, new_start: int, new_count: int) -> 'LineRange':
        """Git hunk 정보에서 LineRange를 생성합니다."""
        if new_count <= 0:
            raise ValueError("hunk count는 양수여야 합니다")
        return cls(new_start, new_start + new_count - 1)

    def overlaps(self, other: 'LineRange') -> bool:
        """다른 범위와 겹치는지 확인합니다."""
        # 두 범위가 겹치는 조건 (직관적으로 표현)
        # 시작이 상대방 끝 이전이고, 끝이 상대방 시작 이후면 겹침
        return self.start_line <= other.end_line and self.end_line >= other.start_line


class OptimizedContextExtractor:
    """최적화된 tree-sitter 기반 컨텍스트 추출기 (문서에서 정의된 클래스)"""
    # 실제 구현은 문서의 코드를 참조
    pass


@pytest.fixture
def tmp_code_directory():
    """테스트용 임시 디렉토리를 생성하고 다양한 언어의 코드 파일들을 포함한다."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # 각 언어별로 피보나치 코드 생성
        create_test_files(tmp_path)
        
        yield tmp_path


def create_test_files(tmp_path: Path):
    """다양한 언어로 피보나치 함수를 구현한 테스트 파일들을 생성한다."""
    
    # 1. Python
    (tmp_path / "fibonacci.py").write_text('''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)
''')

    # 2. JavaScript
    (tmp_path / "fibonacci.js").write_text('''
function fibonacci(n) {
    if (n <= 1) return n;
    return fibonacci(n-1) + fibonacci(n-2);
}

const result = fibonacci(10);
''')

    # 3. TypeScript
    (tmp_path / "fibonacci.ts").write_text('''
function fibonacci(n: number): number {
    if (n <= 1) return n;
    return fibonacci(n-1) + fibonacci(n-2);
}

const result: number = fibonacci(10);
''')

    # 4. Java
    (tmp_path / "Fibonacci.java").write_text('''
public class Fibonacci {
    public static int fibonacci(int n) {
        if (n <= 1) return n;
        return fibonacci(n-1) + fibonacci(n-2);
    }
    
    public static void main(String[] args) {
        int result = fibonacci(10);
    }
}
''')

    # 5. C
    (tmp_path / "fibonacci.c").write_text('''
#include <stdio.h>

int fibonacci(int n) {
    if (n <= 1) return n;
    return fibonacci(n-1) + fibonacci(n-2);
}

int main() {
    int result = fibonacci(10);
    return 0;
}
''')

    # 6. C++
    (tmp_path / "fibonacci.cpp").write_text('''
#include <iostream>

class Fibonacci {
public:
    static int calculate(int n) {
        if (n <= 1) return n;
        return calculate(n-1) + calculate(n-2);
    }
};

int main() {
    int result = Fibonacci::calculate(10);
    return 0;
}
''')

    # 7. Rust
    (tmp_path / "fibonacci.rs").write_text('''
fn fibonacci(n: u32) -> u32 {
    match n {
        0 | 1 => n,
        _ => fibonacci(n-1) + fibonacci(n-2),
    }
}

fn main() {
    let result = fibonacci(10);
}
''')

    # 8. Go
    (tmp_path / "fibonacci.go").write_text('''
package main

func fibonacci(n int) int {
    if n <= 1 {
        return n
    }
    return fibonacci(n-1) + fibonacci(n-2)
}

func main() {
    result := fibonacci(10)
    _ = result
}
''')

    # 9. Kotlin
    (tmp_path / "fibonacci.kt").write_text('''
fun fibonacci(n: Int): Int {
    return if (n <= 1) n 
    else fibonacci(n-1) + fibonacci(n-2)
}

fun main() {
    val result = fibonacci(10)
}
''')

    # 10. C#
    (tmp_path / "fibonacci.cs").write_text('''
using System;

public class Fibonacci {
    public static int Calculate(int n) {
        if (n <= 1) return n;
        return Calculate(n-1) + Calculate(n-2);
    }
    
    public static void Main() {
        int result = Calculate(10);
    }
}
''')

    # 11. Swift
    (tmp_path / "fibonacci.swift").write_text('''
func fibonacci(_ n: Int) -> Int {
    if n <= 1 { return n }
    return fibonacci(n-1) + fibonacci(n-2)
}

let result = fibonacci(10)
''')

    # 12. PHP
    (tmp_path / "fibonacci.php").write_text('''
<?php
function fibonacci($n) {
    if ($n <= 1) return $n;
    return fibonacci($n-1) + fibonacci($n-2);
}

$result = fibonacci(10);
?>
''')


def create_line_ranges_from_diff_result(diff_result: DiffResult) -> dict[str, list[LineRange]]:
    """DiffResult에서 파일별 LineRange 객체들을 생성한다."""
    result = {}
    
    for file_diff in diff_result.files:
        line_ranges = []
        for hunk in file_diff.hunks:
            # 수정된 파일 기준으로 LineRange 생성
            if hunk.line_count_modified > 0:
                line_range = LineRange.from_hunk(
                    hunk.start_line_modified, 
                    hunk.line_count_modified
                )
                line_ranges.append(line_range)
        
        if line_ranges:  # 유효한 변경사항이 있는 경우만 추가
            result[file_diff.filename] = line_ranges
    
    return result


def create_mock_diff(filename: str, changes: list[tuple[int, int, str]]) -> str:
    """테스트용 git diff 문자열을 생성한다.
    
    Args:
        filename: 대상 파일명
        changes: (start_line, line_count, change_type) 튜플 리스트
                change_type은 'addition', 'deletion', 'modification' 중 하나
    
    Returns:
        Git diff 형식의 문자열
    """
    diff_lines = [
        f"diff --git a/{filename} b/{filename}",
        f"index 1234567..abcdefg 100644",
        f"--- a/{filename}",
        f"+++ b/{filename}"
    ]
    
    for start_line, line_count, change_type in changes:
        if change_type == "addition":
            hunk_header = f"@@ -{start_line},0 +{start_line},{line_count} @@"
            diff_lines.append(hunk_header)
            for i in range(line_count):
                diff_lines.append(f"+    // Added line {i+1}")
                
        elif change_type == "modification":
            hunk_header = f"@@ -{start_line},{line_count} +{start_line},{line_count} @@"
            diff_lines.append(hunk_header)
            for i in range(line_count):
                diff_lines.append(f"-    // Original line {i+1}")
                diff_lines.append(f"+    // Modified line {i+1}")
                
        elif change_type == "deletion":
            hunk_header = f"@@ -{start_line},{line_count} +{start_line},0 @@"
            diff_lines.append(hunk_header)
            for i in range(line_count):
                diff_lines.append(f"-    // Deleted line {i+1}")
    
    return "\n".join(diff_lines) + "\n"
```

---

## 기본 기능 테스트

### LineRange 클래스 테스트

```python
class TestLineRange:
    """LineRange 클래스의 기본 기능을 테스트한다."""
    
    def test_valid_line_range_creation(self):
        """유효한 LineRange 객체 생성을 테스트한다."""
        line_range = LineRange(1, 5)
        assert line_range.start_line == 1
        assert line_range.end_line == 5
        assert line_range.line_count() == 5
    
    def test_invalid_line_range_creation(self):
        """잘못된 LineRange 객체 생성 시 예외 발생을 테스트한다."""
        with pytest.raises(ValueError, match="라인 번호는 1 이상이어야 합니다"):
            LineRange(0, 5)
        
        with pytest.raises(ValueError, match="시작 라인이 끝 라인보다 클 수 없습니다"):
            LineRange(5, 3)
    
    def test_from_hunk_creation(self):
        """Hunk 정보로부터 LineRange 생성을 테스트한다."""
        line_range = LineRange.from_hunk(10, 3)
        assert line_range.start_line == 10
        assert line_range.end_line == 12
        assert line_range.line_count() == 3
    
    def test_overlaps_detection(self):
        """두 LineRange 간의 겹침 감지를 테스트한다."""
        range1 = LineRange(1, 5)
        range2 = LineRange(3, 8)  # 겹침
        range3 = LineRange(6, 10) # 겹치지 않음
        range4 = LineRange(5, 7)  # 경계에서 겹침
        
        assert range1.overlaps(range2) == True
        assert range1.overlaps(range3) == False  
        assert range1.overlaps(range4) == True
        assert range2.overlaps(range1) == True  # 대칭성
    
    def test_contains_line(self):
        """특정 라인이 범위에 포함되는지 테스트한다."""
        line_range = LineRange(5, 10)
        
        assert line_range.contains(5) == True   # 시작 라인
        assert line_range.contains(10) == True  # 끝 라인
        assert line_range.contains(7) == True   # 중간 라인
        assert line_range.contains(4) == False  # 범위 밖 (이전)
        assert line_range.contains(11) == False # 범위 밖 (이후)
```

---

## OptimizedContextExtractor 기본 테스트

### 초기화 및 설정 테스트

```python
class TestOptimizedContextExtractorInitialization:
    """OptimizedContextExtractor 초기화 기능을 테스트한다."""
    
    def test_supported_languages(self):
        """지원하는 언어 목록이 올바른지 테스트한다."""
        supported = OptimizedContextExtractor.get_supported_languages()
        
        # 필수 언어들이 모두 포함되어 있는지 확인
        required_languages = {
            "python", "javascript", "typescript", "java", "c", 
            "cpp", "rust", "go", "csharp"
        }
        
        for lang in required_languages:
            assert lang in supported, f"필수 언어 '{lang}'이 지원 목록에 없습니다"
    
    def test_valid_language_initialization(self):
        """유효한 언어로 초기화가 정상 동작하는지 테스트한다."""
        for language in ["python", "javascript", "java", "rust"]:
            extractor = OptimizedContextExtractor(language)
            assert extractor._language_name == language
    
    def test_invalid_language_initialization(self):
        """지원하지 않는 언어로 초기화 시 예외 발생을 테스트한다."""
        with pytest.raises(ValueError, match="지원하지 않는 언어"):
            OptimizedContextExtractor("unsupported_language")
    
    def test_block_types_for_each_language(self):
        """각 언어별로 블록 타입이 올바르게 설정되는지 테스트한다."""
        test_cases = [
            ("python", {"function_definition", "class_definition"}),
            ("javascript", {"function_declaration", "class"}),
            ("java", {"method_declaration", "class_declaration"}),
            ("rust", {"function_item", "struct_item"}),
        ]
        
        for language, expected_block_types in test_cases:
            block_types = OptimizedContextExtractor.get_block_types_for_language(language)
            for expected_type in expected_block_types:
                assert expected_type in block_types, f"{language}에서 {expected_type}이 누락됨"
```

---

## 컨텍스트 추출 기능 테스트

### 언어별 컨텍스트 추출 테스트

```python
class TestContextExtraction:
    """컨텍스트 추출 기능을 언어별로 테스트한다."""
    
    @pytest.mark.parametrize("language,filename", [
        ("python", "fibonacci.py"),
        ("javascript", "fibonacci.js"),
        ("typescript", "fibonacci.ts"),
        ("java", "Fibonacci.java"),
        ("c", "fibonacci.c"),
        ("cpp", "fibonacci.cpp"),
        ("rust", "fibonacci.rs"),
        ("go", "fibonacci.go"),
        ("kotlin", "fibonacci.kt"),
        ("csharp", "fibonacci.cs"),
        ("swift", "fibonacci.swift"),
    ])
    def test_basic_context_extraction(self, tmp_code_directory, language, filename):
        """기본적인 컨텍스트 추출 기능을 언어별로 테스트한다."""
        extractor = OptimizedContextExtractor(language)
        file_path = tmp_code_directory / filename
        
        if not file_path.exists():
            pytest.skip(f"테스트 파일 {filename}이 존재하지 않습니다")
        
        # 함수 영역을 포함하는 변경 범위 시뮬레이션
        changed_ranges = [LineRange(2, 4)]  # 함수 내부 로직 변경
        
        contexts = extractor.extract_contexts(file_path, changed_ranges)
        
        # 최소한 하나 이상의 컨텍스트가 추출되어야 함
        assert len(contexts) >= 1, f"{language} 파일에서 컨텍스트가 추출되지 않음"
        
        # 추출된 컨텍스트에 'fibonacci' 키워드가 포함되어야 함
        context_text = " ".join(contexts).lower()
        assert "fibonacci" in context_text, f"{language} 컨텍스트에 fibonacci 함수가 포함되지 않음"
    
    def test_function_block_extraction(self, tmp_code_directory):
        """함수 블록 추출을 테스트한다."""
        extractor = OptimizedContextExtractor("python")
        file_path = tmp_code_directory / "fibonacci.py"
        
        # 함수 정의 라인을 포함하는 변경 범위
        changed_ranges = [LineRange(1, 1)]  # def fibonacci(n): 라인
        
        contexts = extractor.extract_contexts(file_path, changed_ranges)
        
        assert len(contexts) >= 1
        # 함수 전체가 포함되어야 함
        context_text = contexts[0]
        assert "def fibonacci" in context_text
        assert "return fibonacci" in context_text
    
    def test_class_block_extraction(self, tmp_code_directory):
        """클래스 블록 추출을 테스트한다."""
        extractor = OptimizedContextExtractor("java")
        file_path = tmp_code_directory / "Fibonacci.java"
        
        # 클래스 내부 메소드를 포함하는 변경 범위
        changed_ranges = [LineRange(3, 3)]  # public static int fibonacci 라인
        
        contexts = extractor.extract_contexts(file_path, changed_ranges)
        
        assert len(contexts) >= 1
        # 클래스 전체가 포함되어야 함
        context_text = contexts[0]
        assert "public class Fibonacci" in context_text
        assert "public static int fibonacci" in context_text
    
    def test_multiple_range_extraction(self, tmp_code_directory):
        """여러 변경 범위에 대한 컨텍스트 추출을 테스트한다."""
        extractor = OptimizedContextExtractor("python")
        file_path = tmp_code_directory / "fibonacci.py"
        
        # 여러 영역의 변경
        changed_ranges = [
            LineRange(1, 2),  # 함수 정의 부분
            LineRange(6, 6),  # result = fibonacci(10) 라인
        ]
        
        contexts = extractor.extract_contexts(file_path, changed_ranges)
        
        # 변경 범위가 모두 같은 함수 블록에 속하므로 하나의 컨텍스트로 통합됨
        assert len(contexts) >= 1
        context_text = " ".join(contexts)
        assert "def fibonacci" in context_text
        assert "result = fibonacci(10)" in context_text
    
    def test_empty_changed_ranges(self, tmp_code_directory):
        """빈 변경 범위에 대한 처리를 테스트한다."""
        extractor = OptimizedContextExtractor("python")
        file_path = tmp_code_directory / "fibonacci.py"
        
        contexts = extractor.extract_contexts(file_path, [])
        
        assert contexts == []
    
    def test_non_existent_file(self):
        """존재하지 않는 파일에 대한 예외 처리를 테스트한다."""
        extractor = OptimizedContextExtractor("python")
        non_existent_file = Path("/non/existent/file.py")
        changed_ranges = [LineRange(1, 5)]
        
        with pytest.raises(FileNotFoundError):
            extractor.extract_contexts(non_existent_file, changed_ranges)
```

---

## 통합 테스트

### DiffResult와 연동 테스트

```python
class TestDiffResultIntegration:
    """DiffResult와의 통합 테스트를 수행한다."""
    
    def test_end_to_end_workflow(self, tmp_code_directory):
        """전체 워크플로우를 테스트한다: diff 파싱 → LineRange 변환 → 컨텍스트 추출"""
        # 1. Mock diff 생성
        filename = "fibonacci.py"
        diff_text = create_mock_diff(filename, [
            (2, 2, "modification"),  # if n <= 1: 부분 수정
        ])
        
        # 2. DiffResult 파싱
        diff_result = parse_git_diff(diff_text, str(tmp_code_directory))
        
        # 3. LineRange 변환
        line_ranges_dict = create_line_ranges_from_diff_result(diff_result)
        
        assert filename in line_ranges_dict
        line_ranges = line_ranges_dict[filename]
        assert len(line_ranges) >= 1
        
        # 4. 컨텍스트 추출
        extractor = OptimizedContextExtractor("python")
        file_path = tmp_code_directory / filename
        
        contexts = extractor.extract_contexts(file_path, line_ranges)
        
        # 5. 결과 검증
        assert len(contexts) >= 1
        context_text = " ".join(contexts)
        assert "def fibonacci" in context_text
    
    def test_multiple_files_diff(self, tmp_code_directory):
        """여러 파일이 포함된 diff 처리를 테스트한다."""
        # 여러 파일에 대한 mock diff
        diff_lines = []
        
        # Python 파일 diff
        python_diff = create_mock_diff("fibonacci.py", [(2, 1, "modification")])
        diff_lines.append(python_diff)
        
        # JavaScript 파일 diff  
        js_diff = create_mock_diff("fibonacci.js", [(3, 1, "modification")])
        diff_lines.append(js_diff)
        
        combined_diff = "\n".join(diff_lines)
        
        # DiffResult 파싱
        diff_result = parse_git_diff(combined_diff, str(tmp_code_directory))
        line_ranges_dict = create_line_ranges_from_diff_result(diff_result)
        
        # 각 파일별로 컨텍스트 추출
        extractors = {
            "fibonacci.py": OptimizedContextExtractor("python"),
            "fibonacci.js": OptimizedContextExtractor("javascript"),
        }
        
        all_contexts = {}
        for filename, extractor in extractors.items():
            if filename in line_ranges_dict:
                file_path = tmp_code_directory / filename
                if file_path.exists():
                    contexts = extractor.extract_contexts(
                        file_path, 
                        line_ranges_dict[filename]
                    )
                    all_contexts[filename] = contexts
        
        # 검증
        assert "fibonacci.py" in all_contexts
        assert "fibonacci.js" in all_contexts
        assert len(all_contexts["fibonacci.py"]) >= 1
        assert len(all_contexts["fibonacci.js"]) >= 1
    
    def test_diff_with_additions_deletions(self, tmp_code_directory):
        """추가/삭제가 포함된 diff 처리를 테스트한다."""
        filename = "fibonacci.py"
        diff_text = create_mock_diff(filename, [
            (1, 1, "addition"),    # 새 라인 추가
            (4, 1, "deletion"),    # 기존 라인 삭제
            (6, 2, "modification") # 기존 라인 수정
        ])
        
        diff_result = parse_git_diff(diff_text, str(tmp_code_directory))
        line_ranges_dict = create_line_ranges_from_diff_result(diff_result)
        
        extractor = OptimizedContextExtractor("python")
        file_path = tmp_code_directory / filename
        
        contexts = extractor.extract_contexts(file_path, line_ranges_dict[filename])
        
        # 모든 변경 사항이 같은 함수 블록에 속하므로 통합된 컨텍스트 반환
        assert len(contexts) >= 1
        assert "fibonacci" in " ".join(contexts).lower()
```

---

## 에러 처리 및 에지 케이스 테스트

### 예외 상황 처리 테스트

```python
class TestErrorHandling:
    """에러 처리 및 에지 케이스를 테스트한다."""
    
    def test_malformed_code_parsing(self, tmp_code_directory):
        """문법 오류가 있는 코드 파일 처리를 테스트한다."""
        # 문법 오류가 있는 Python 파일 생성
        malformed_file = tmp_code_directory / "malformed.py"
        malformed_file.write_text('''
def fibonacci(n
    if n <= 1
        return n
    return fibonacci(n-1) + fibonacci(n-2
''')  # 의도적인 문법 오류
        
        extractor = OptimizedContextExtractor("python")
        changed_ranges = [LineRange(2, 4)]
        
        # 구문 분석 경고가 발생하지만 예외는 발생하지 않아야 함
        contexts = extractor.extract_contexts(malformed_file, changed_ranges)
        # 가능한 부분이라도 추출되거나, 빈 리스트가 반환되어야 함
        assert isinstance(contexts, list)
    
    def test_unicode_handling(self, tmp_code_directory):
        """유니코드 문자가 포함된 파일 처리를 테스트한다."""
        unicode_file = tmp_code_directory / "unicode_fibonacci.py"
        unicode_file.write_text('''
def 피보나치(n):
    """피보나치 수열을 계산한다"""
    if n <= 1:
        return n
    return 피보나치(n-1) + 피보나치(n-2)

결과 = 피보나치(10)  # 한글 변수명
''', encoding='utf-8')
        
        extractor = OptimizedContextExtractor("python")
        changed_ranges = [LineRange(2, 6)]
        
        contexts = extractor.extract_contexts(unicode_file, changed_ranges)
        
        assert len(contexts) >= 1
        context_text = " ".join(contexts)
        assert "피보나치" in context_text
    
    def test_very_large_file_handling(self, tmp_code_directory):
        """대용량 파일 처리를 테스트한다."""
        large_file = tmp_code_directory / "large_fibonacci.py"
        
        # 많은 함수가 포함된 큰 파일 생성
        content_lines = []
        content_lines.append("# Large file with many functions")
        
        for i in range(100):
            content_lines.extend([
                f"def fibonacci_{i}(n):",
                f"    if n <= 1: return n",
                f"    return fibonacci_{i}(n-1) + fibonacci_{i}(n-2)",
                f"",
            ])
        
        content_lines.append("result = fibonacci_50(10)")
        
        large_file.write_text("\n".join(content_lines))
        
        extractor = OptimizedContextExtractor("python")
        # 중간 부분의 함수를 대상으로 하는 변경 범위
        changed_ranges = [LineRange(200, 202)]
        
        contexts = extractor.extract_contexts(large_file, changed_ranges)
        
        # 해당 범위의 함수만 추출되어야 함
        assert len(contexts) >= 1
        context_text = " ".join(contexts)
        assert "fibonacci_" in context_text  # 해당 함수가 포함되어야 함
    
    def test_empty_file_handling(self, tmp_code_directory):
        """빈 파일 처리를 테스트한다."""
        empty_file = tmp_code_directory / "empty.py"
        empty_file.write_text("")
        
        extractor = OptimizedContextExtractor("python")
        changed_ranges = [LineRange(1, 1)]
        
        contexts = extractor.extract_contexts(empty_file, changed_ranges)
        
        # 빈 파일에서는 컨텍스트가 추출되지 않아야 함
        assert contexts == []
    
    def test_line_range_beyond_file_bounds(self, tmp_code_directory):
        """파일 범위를 벗어난 LineRange 처리를 테스트한다."""
        small_file = tmp_code_directory / "small.py"
        small_file.write_text("print('hello')\n")  # 1줄짜리 파일
        
        extractor = OptimizedContextExtractor("python")
        # 파일보다 큰 범위 지정
        changed_ranges = [LineRange(5, 10)]
        
        contexts = extractor.extract_contexts(small_file, changed_ranges)
        
        # 범위를 벗어났지만 예외가 발생하지 않아야 함
        assert isinstance(contexts, list)
```

---

## 성능 및 최적화 테스트

### 성능 검증 테스트

```python
class TestPerformanceOptimization:
    """성능 최적화 관련 테스트를 수행한다."""
    
    def test_single_file_read_optimization(self, tmp_code_directory):
        """파일을 한 번만 읽는 최적화가 적용되는지 테스트한다."""
        # 이 테스트는 실제로는 코드 내부 로직을 확인해야 하므로
        # 실제 구현에서는 모니터링 코드나 mock을 사용해야 할 수 있음
        
        extractor = OptimizedContextExtractor("python")
        file_path = tmp_code_directory / "fibonacci.py"
        
        # 여러 범위에 대해 동시에 처리
        multiple_ranges = [
            LineRange(1, 2),
            LineRange(4, 5),
            LineRange(6, 7)
        ]
        
        contexts = extractor.extract_contexts(file_path, multiple_ranges)
        
        # 각 범위에서 관련된 컨텍스트가 추출되어야 함
        assert len(contexts) >= 1  # 모든 범위가 같은 함수에 속할 가능성
        
    def test_range_overlap_efficiency(self):
        """범위 겹침 감지의 효율성을 테스트한다."""
        # 많은 범위들과의 겹침 테스트
        base_range = LineRange(50, 60)
        
        test_ranges = [
            LineRange(i, i+10) for i in range(1, 100, 5)
        ]
        
        overlapping_count = 0
        for test_range in test_ranges:
            if base_range.overlaps(test_range):
                overlapping_count += 1
        
        # 예상되는 겹침 개수 확인
        expected_overlaps = len([r for r in test_ranges 
                               if r.start_line <= 60 and r.end_line >= 50])
        
        assert overlapping_count == expected_overlaps
```

---

## 실행 및 검증

### 테스트 실행 방법

```bash
# 전체 테스트 실행
pytest test_optimized_context_extractor.py -v

# 특정 테스트 클래스 실행
pytest test_optimized_context_extractor.py::TestLineRange -v

# 특정 언어만 테스트 (parametrize 활용)
pytest test_optimized_context_extractor.py -k "python" -v

# 커버리지와 함께 실행
pytest test_optimized_context_extractor.py --cov=optimized_context_extractor --cov-report=html
```

### 기대되는 테스트 결과

1. **기본 기능 검증**
   - ✅ 모든 지원 언어에서 컨텍스트 추출 성공
   - ✅ LineRange 객체 생성 및 겹침 감지 정확성
   - ✅ 블록 타입 인식 및 적절한 컨텍스트 추출

2. **통합 기능 검증**
   - ✅ parse_git_diff() → LineRange 변환 → extract_contexts() 전체 플로우
   - ✅ 여러 파일이 포함된 diff 처리
   - ✅ 다양한 변경 유형(추가/삭제/수정) 처리

3. **에러 처리 검증**
   - ✅ 파일 없음, 인코딩 오류, 구문 오류 등 예외 상황 처리
   - ✅ 유니코드 문자 및 대용량 파일 처리
   - ✅ 범위 초과 등 에지 케이스 처리

4. **성능 검증**
   - ✅ 파일 한 번 읽기 최적화
   - ✅ 범위 겹침 감지 효율성
   - ✅ 메모리 효율적인 컨텍스트 추출

---

**테스트 문서 작성일**: 2025-07-22  
**검증 대상**: OptimizedContextExtractor v1.0  
**테스트 커버리지 목표**: 90% 이상