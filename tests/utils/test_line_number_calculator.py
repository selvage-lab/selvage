"""LineNumberCalculator에 대한 유닛 테스트."""

import pytest

from selvage.src.utils.line_number_calculator import calculate_line_number


@pytest.fixture
def sample_python_file(tmpdir) -> str:
    """테스트용 샘플 Python 파일을 생성합니다.

    Args:
        tmpdir: pytest의 임시 디렉토리 픽스처

    Returns:
        str: 생성된 샘플 파일의 경로
    """
    sample_code = """def hello_world():
    print("Hello")
    return "world"

class TestClass:
    def method(self):
        pass

# class TestClass in comment
def another_function():
    return 42

class TestClass:
    def duplicate_method(self):
        pass

def multiline_function():
    x = 1
    y = 2
    return x + y
"""

    sample_file = tmpdir.join("sample_code.py")
    sample_file.write(sample_code)

    return str(sample_file)


class TestLineNumberCalculator:
    """LineNumberCalculator에 대한 테스트 클래스."""

    def test_calculate_line_number_exact_match_success(
        self, sample_python_file: str
    ) -> None:
        """정확한 매칭으로 target_code를 찾아서 올바른 라인 번호를 반환하는지 테스트.

        Args:
            sample_python_file: 샘플 Python 파일 경로 픽스처
        """
        # Given
        target_code = "class TestClass:"

        # When
        line_number = calculate_line_number(
            sample_python_file, target_code
        )

        # Then - 첫 번째 정확한 매치인 라인 5를 반환해야 함
        assert line_number == 5

    def test_calculate_line_number_partial_match_not_found(
        self, sample_python_file: str
    ) -> None:
        """부분 매칭은 지원하지 않으므로 일치하지 않으면 None을 반환하는지 테스트.

        Args:
            sample_python_file: 샘플 Python 파일 경로 픽스처
        """
        # Given - 부분적으로만 일치하는 코드
        target_code = "class TestClass"

        # When
        line_number = calculate_line_number(
            sample_python_file, target_code
        )

        # Then - 정확히 일치하지 않으므로 None을 반환해야 함
        assert line_number is None

    def test_calculate_line_number_exact_method_match(
        self, sample_python_file: str
    ) -> None:
        """정확한 메서드 매칭이 작동하는지 테스트.

        Args:
            sample_python_file: 샘플 Python 파일 경로 픽스처
        """
        # Given - 정확히 일치하는 메서드 정의
        target_code = "def method(self):"

        # When
        line_number = calculate_line_number(
            sample_python_file, target_code
        )

        # Then - 정확한 매치인 라인 6을 반환해야 함
        assert line_number == 6

    def test_calculate_line_number_avoid_comment_match(
        self, sample_python_file: str
    ) -> None:
        """정확한 매칭으로 주석 라인을 피하고 실제 코드를 찾는지 테스트.

        Args:
            sample_python_file: 샘플 Python 파일 경로 픽스처
        """
        # Given
        target_code = "class TestClass:"

        # When
        line_number = calculate_line_number(
            sample_python_file, target_code
        )

        # Then - 주석(라인 8)이 아닌 실제 클래스 정의(라인 5)를 반환해야 함
        assert line_number == 5

    def test_calculate_line_number_not_found(self, sample_python_file: str) -> None:
        """존재하지 않는 코드를 검색할 때 None을 반환하는지 테스트.

        Args:
            sample_python_file: 샘플 Python 파일 경로 픽스처
        """
        # Given
        target_code = "non_existent_code"

        # When
        line_number = calculate_line_number(
            sample_python_file, target_code
        )

        # Then
        assert line_number is None

    def test_calculate_line_number_multiline_success(
        self, sample_python_file: str
    ) -> None:
        """멀티라인 target_code를 올바르게 찾을 수 있는지 테스트.

        Args:
            sample_python_file: 샘플 Python 파일 경로 픽스처
        """
        # Given - 3줄 짜리 연속된 코드
        target_code = """def multiline_function():
    x = 1
    y = 2"""

        # When
        line_number = calculate_line_number(
            sample_python_file, target_code
        )

        # Then - 첫 번째 라인의 위치 반환 (라인 17)
        assert line_number == 17

    def test_calculate_line_number_multiline_complete_function(
        self, sample_python_file: str
    ) -> None:
        """전체 함수를 멀티라인으로 찾을 수 있는지 테스트.

        Args:
            sample_python_file: 샘플 Python 파일 경로 픽스처
        """
        # Given - 전체 함수 4줄
        target_code = """def multiline_function():
    x = 1
    y = 2
    return x + y"""

        # When
        line_number = calculate_line_number(
            sample_python_file, target_code
        )

        # Then - 첫 번째 라인의 위치 반환 (라인 17)
        assert line_number == 17

    def test_calculate_line_number_multiline_partial_no_match(
        self, sample_python_file: str
    ) -> None:
        """멀티라인에서 일부만 일치하는 경우 None을 반환하는지 테스트.

        Args:
            sample_python_file: 샘플 Python 파일 경로 픽스처
        """
        # Given - 첫 번째 라인만 일치하고 두 번째 라인이 다름
        target_code = """def multiline_function():
    x = 999"""

        # When
        line_number = calculate_line_number(
            sample_python_file, target_code
        )

        # Then - 전체가 일치하지 않으므로 None 반환
        assert line_number is None

    def test_calculate_line_number_single_line_still_works(
        self, sample_python_file: str
    ) -> None:
        """기존 단일 라인 지원이 여전히 작동하는지 테스트.

        Args:
            sample_python_file: 샘플 Python 파일 경로 픽스처
        """
        # Given
        target_code = "return x + y"

        # When
        line_number = calculate_line_number(
            sample_python_file, target_code
        )

        # Then - 속하는 라인 20을 반환
        assert line_number == 20

    @pytest.mark.slow
    def test_calculate_line_number_performance_large_file(self, tmpdir) -> None:
        """큰 파일에서의 성능을 테스트.

        Args:
            tmpdir: pytest의 임시 디렉토리 픽스처
        """
        import time

        # Given - 큰 파일 생성 (1000줄)
        large_content = []
        for i in range(1000):
            large_content.append(f"def function_{i}():")
            large_content.append(f"    return {i}")
            large_content.append("")

        # 타겟 코드를 마지막에 추가
        large_content.extend(
            ["def target_function():", "    x = 999", "    y = 888", "    return x + y"]
        )

        large_file = tmpdir.join("large_file.py")
        large_file.write("\n".join(large_content))

        target_code = """def target_function():
    x = 999
    y = 888"""

        # When - 성능 측정
        start_time = time.time()
        line_number = calculate_line_number(
            str(large_file), target_code
        )
        elapsed_time = time.time() - start_time

        # Then - 올바른 결과와 단시간 내 수행
        assert line_number == 3001  # 1000 * 3 + 1
        assert elapsed_time < 0.1  # 100ms 이내 수행

    def test_calculate_line_number_first_line_optimization(self, tmpdir) -> None:
        """첫 번째 라인 최적화가 올바르게 작동하는지 테스트.

        Args:
            tmpdir: pytest의 임시 디렉토리 픽스처
        """
        # Given - 첫 번째 라인이 여러 번 나타나지만 전체는 한 번만 매칭
        content = """def duplicate_first_line():
    print("first")

def duplicate_first_line():
    print("different")

def duplicate_first_line():
    print("target")
    return "found"""

        test_file = tmpdir.join("optimization_test.py")
        test_file.write(content)

        target_code = """def duplicate_first_line():
    print("target")
    return "found"""

        # When
        line_number = calculate_line_number(
            str(test_file), target_code
        )

        # Then - 첫 번째 완전한 매칭의 시작 라인 반환
        assert line_number == 7  # 세 번째 def duplicate_first_line() 시작
