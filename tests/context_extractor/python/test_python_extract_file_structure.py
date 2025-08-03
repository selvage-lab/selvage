from pathlib import Path

import pytest
from tree_sitter_language_pack import get_language, get_parser

from selvage.src.context_extractor.context_extractor import ContextExtractor


class TestPythonContextTree:
    """Tree Sitter를 활용해 간소화된 파이썬 파일의 구조 추출 테스트"""

    @pytest.fixture
    def sample_file_path(self) -> Path:
        """테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "sample_class.py"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Python용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("python")

    def test_python_context_tree(
        self,
        sample_file_path: Path,
    ):
        language = get_language("python")
        parser = get_parser("python")

        # 전용 쿼리 파일 사용
        query_path = Path(__file__).parent / "python-structure.scm"
        query_scm = query_path.read_text()
        tree = parser.parse(sample_file_path.read_bytes())
        query = language.query(query_scm)
        captures = query.captures(tree.root_node)
        
        # captures를 활용한 파일 구조 추출
        file_structure = self._extract_file_structure(captures, tree)
        
        print("Generated file structure:")
        print(file_structure)
        
        # 예상되는 완전한 파일 구조 (module docstring, import, 모든 함수 포함)
        triple_quotes = '"""'
        module_doc = "테스트용 샘플 클래스 - tree-sitter 파싱 테스트에 사용됩니다."
        expected_structure = f'''{triple_quotes}{module_doc}{triple_quotes}

import json
from typing import Any
class SampleCalculator:
       {triple_quotes}간단한 계산기 클래스 - tree-sitter 테스트용{triple_quotes}
   def __init__(self, initial_value: int = 0):
          {triple_quotes}계산기 초기화{triple_quotes}
   def add_numbers(self, a: int, b: int) -> int:
          {triple_quotes}두 수를 더하는 메소드{triple_quotes}
      def validate_inputs(x: int, y: int) -> bool:
             {triple_quotes}내부 함수: 입력값 검증{triple_quotes}
      def log_operation(operation: str, result: int) -> None:
             {triple_quotes}내부 함수: 연산 로깅{triple_quotes}
   def multiply_and_format(self, numbers: list[int]) -> dict[str, Any]:
          {triple_quotes}숫자 리스트를 곱하고 결과를 포맷팅하는 메소드{triple_quotes}
      def calculate_product(nums: list[int]) -> int:
             {triple_quotes}내부 함수: 곱셈 계산{triple_quotes}
         def multiply_recursive(items: list[int], index: int = 0) -> int:
                {triple_quotes}재귀적 곱셈 함수 (중첩 내부 함수){triple_quotes}
      def format_result(value: int, count: int) -> dict[str, Any]:
             {triple_quotes}내부 함수: 결과 포맷팅{triple_quotes}
   def calculate_circle_area(self, radius: float) -> float:
          {triple_quotes}원의 넓이를 계산하는 메소드 (상수 사용){triple_quotes}
      def validate_radius(r: float) -> bool:
             {triple_quotes}내부 함수: 반지름 검증{triple_quotes}
def helper_function(data: dict) -> str:
       {triple_quotes}도우미 함수 - 클래스 외부 함수{triple_quotes}
   def format_dict_items(items: dict) -> list[str]:
          {triple_quotes}내부 함수: 딕셔너리 아이템 포맷팅{triple_quotes}
def advanced_calculator_factory(mode: str = "basic") -> SampleCalculator:
       {triple_quotes}계산기 팩토리 함수{triple_quotes}
   def create_calculator_with_mode(calc_mode: str) -> SampleCalculator:
          {triple_quotes}내부 함수: 모드별 계산기 생성{triple_quotes}
   def validate_mode(m: str) -> bool:
          {triple_quotes}내부 함수: 모드 검증{triple_quotes}'''
        
        # 엄격한 완전 일치 검증
        assert file_structure == expected_structure, (
            f"실제 출력과 예상 구조가 다릅니다.\n"
            f"실제:\n{repr(file_structure)}\n"
            f"예상:\n{repr(expected_structure)}"
        )

    def _extract_file_structure(self, captures, tree) -> str:
        """captures 데이터를 활용하여 파일 구조를 텍스트로 생성합니다."""
        source_code = tree.root_node.text.decode('utf-8').split('\n')
        
        def clean_docstring(docstring_text: str) -> str:
            """docstring 텍스트에서 따옴표를 제거하고 정리합니다."""
            if docstring_text.startswith('"""') and docstring_text.endswith('"""'):
                return docstring_text[3:-3].strip()
            elif docstring_text.startswith("'''") and docstring_text.endswith("'''"):
                return docstring_text[3:-3].strip()
            elif docstring_text.startswith('"') and docstring_text.endswith('"'):
                return docstring_text[1:-1].strip()
            elif docstring_text.startswith("'") and docstring_text.endswith("'"):
                return docstring_text[1:-1].strip()
            return docstring_text.strip()
        
        # captures를 위에서부터 순회하면서 구조 생성
        result_lines = []
        
        # 모든 captures를 위치별로 정렬
        all_captures = []
        for tag, nodes in captures.items():
            for node in nodes:
                all_captures.append({
                    'node': node,
                    'tag': tag,
                    'start_row': node.start_point[0],
                    'start_col': node.start_point[1],
                })
        
        # 위치별로 정렬
        all_captures.sort(key=lambda x: (x['start_row'], x['start_col']))
        
        # 클래스 범위 찾기
        class_ranges = []
        for capture in all_captures:
            if capture['tag'] == 'class.definition':
                class_start = capture['start_row']
                class_end = capture['node'].end_point[0]
                class_ranges.append((class_start, class_end))
        
        # 순회하면서 구조 생성 (클래스 내부 요소만)
        for capture in all_captures:
            node = capture['node']
            tag = capture['tag']
            start_row = capture['start_row']
            start_col = capture['start_col']
            
            # 모든 함수 포함 (클래스 내부/외부 구분 없이)
            
            # 들여쓰기 계산 (4칸 = 1레벨)
            indent_level = start_col // 4
            indent_spaces = '   ' * indent_level
            
            if tag == 'module.docstring':
                # 모듈 docstring 추가
                docstring_text = node.text.decode('utf-8')
                cleaned_docstring = clean_docstring(docstring_text)
                triple_quotes = chr(34) * 3  # """ 문자열
                docstring_line = f'{triple_quotes}{cleaned_docstring}{triple_quotes}'
                result_lines.append(docstring_line)
                result_lines.append('')  # 빈 줄 추가
                
            elif tag in [
                'import.statement', 
                'import.from_statement', 
                'import.future_statement'
            ]:
                # import 문 추가
                import_line = source_code[start_row].strip()
                result_lines.append(import_line)
                
            elif tag == 'class.definition':
                # 클래스 시그니처 추출
                signature = source_code[start_row].strip()
                result_lines.append(signature)
                
            elif tag == 'function.definition':
                # 함수 시그니처 추출
                signature = source_code[start_row].strip()
                result_lines.append(f"{indent_spaces}{signature}")
                
            elif tag in ['class.docstring', 'function.docstring']:
                # docstring 추가
                docstring_text = node.text.decode('utf-8')
                cleaned_docstring = clean_docstring(docstring_text)
                
                # docstring은 함수/클래스보다 한 단계 더 들여쓰기
                docstring_indent = indent_spaces + '    '
                triple_quotes = chr(34) * 3  # """ 문자열
                docstring_line = (
                    f'{docstring_indent}{triple_quotes}{cleaned_docstring}{triple_quotes}'
                )
                result_lines.append(docstring_line)
        
        return '\n'.join(result_lines)
