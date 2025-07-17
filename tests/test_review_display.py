"""ReviewDisplay 클래스의 단위 테스트."""

import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from rich.console import Console

from selvage.src.model_config import ModelInfoDict
from selvage.src.models.model_provider import ModelProvider
from selvage.src.utils.review_display import (
    ReviewDisplay,
    _create_recommendations_panel,
    _create_syntax_block,
    _detect_language_from_filename,
    _format_severity_badge,
    _load_review_log,
    _shorten_path,
)
from selvage.src.utils.token.models import EstimatedCost


@pytest.fixture
def review_display():
    """ReviewDisplay 인스턴스를 생성하는 픽스처."""
    return ReviewDisplay()


@pytest.fixture
def mock_model_info() -> ModelInfoDict:
    """테스트용 모델 정보를 생성하는 픽스처."""
    return {
        "full_name": "claude-sonnet-4-20250514",
        "aliases": ["claude-sonnet-4"],
        "description": "하이브리드 추론 모델로 고급 코딩 및 명령 수행 최적화",
        "provider": ModelProvider.ANTHROPIC,
        "params": {
            "temperature": 0.1,
            "max_tokens": 4096,
        },
        "thinking_mode": False,
        "pricing": {
            "input": 3.0,
            "output": 15.0,
            "description": "1M 토큰당 가격 (USD)",
        },
        "context_limit": 200000,
    }


@pytest.fixture
def mock_estimated_cost():
    """테스트용 비용 정보를 생성하는 픽스처."""
    return EstimatedCost(
        model="claude-sonnet-4-20250514",
        input_tokens=15420,
        input_cost_usd=0.046,
        output_tokens=3250,
        output_cost_usd=0.049,
        total_cost_usd=0.095,
        within_context_limit=True,
    )


@pytest.fixture
def mock_log_path():
    """테스트용 로그 경로를 생성하는 픽스처."""
    return str(
        Path.home()
        / "Development"
        / "my-project"
        / "review_logs"
        / "2024-01-15_code_review_claude.md"
    )


@pytest.fixture
def mock_review_log_data():
    """테스트용 리뷰 로그 데이터를 생성하는 픽스처."""
    return {
        "id": "20240115_143021_claude_abc123",
        "model": {"provider": "anthropic", "name": "claude-sonnet-4-20250514"},
        "created_at": "2024-01-15T14:30:21.123456",
        "review_response": {
            "summary": "전반적으로 코드 품질이 좋습니다. 몇 가지 개선사항이 있습니다.",
            "score": 8.5,
            "issues": [
                {
                    "severity": "HIGH",
                    "file_name": "src/main.py",
                    "line_number": 42,
                    "description": "잠재적인 SQL 인젝션 취약점이 있습니다.",
                    "suggestion": "parameterized query를 사용하세요.",
                },
                {
                    "severity": "MEDIUM",
                    "file_name": "src/utils.py",
                    "line_number": 15,
                    "description": "예외 처리가 너무 광범위합니다.",
                    "suggestion": "구체적인 예외 타입을 사용하세요.",
                },
                {
                    "severity": "LOW",
                    "file_name": "src/config.py",
                    "line_number": None,
                    "description": "변수명이 명확하지 않습니다.",
                    "suggestion": "더 의미있는 변수명을 사용하세요.",
                },
            ],
            "recommendations": [
                "단위 테스트를 추가하세요.",
                "코드 문서화를 개선하세요.",
                "타입 힌팅을 추가하세요.",
            ],
        },
        "status": "SUCCESS",
        "error": None,
        "prompt_version": "v2",
    }


@pytest.fixture
def temp_log_file(mock_review_log_data):
    """임시 리뷰 로그 파일을 생성하는 픽스처."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(mock_review_log_data, f, ensure_ascii=False, indent=2)
        temp_path = f.name

    yield temp_path

    # 정리
    Path(temp_path).unlink(missing_ok=True)


def capture_console_output(func, *args, **kwargs) -> str:
    """Console 출력을 캡처하는 헬퍼 함수."""
    captured_output = io.StringIO()
    console = Console(file=captured_output, width=80, force_terminal=True)

    # ReviewDisplay의 console을 임시로 교체
    original_console = func.__self__.console if hasattr(func, "__self__") else None
    if original_console:
        func.__self__.console = console

    try:
        func(*args, **kwargs)
        return captured_output.getvalue()
    finally:
        # 원래 console 복원
        if original_console:
            func.__self__.console = original_console


class TestReviewDisplay:
    """ReviewDisplay 클래스의 테스트 케이스들."""

    def setup_method(self):
        """각 테스트 메서드 실행 전 설정."""
        self.display = ReviewDisplay()

    def test_model_info_output_contains_model_name(self, review_display):
        """model_info 메서드가 모델명을 포함한 출력을 생성하는지 테스트."""
        output = capture_console_output(
            review_display.model_info,
            "claude-sonnet-4-20250514",
            "하이브리드 추론 모델로 고급 코딩 및 명령 수행 최적화",
        )

        # ANSI 색상 코드가 포함된 텍스트에서 모델명 확인
        assert "claude-sonnet-4-20250514" in output
        assert "하이브리드 추론 모델로 고급 코딩 및 명령 수행 최적화" in output
        assert "리뷰 AI 모델" in output

    def test_log_saved_output_contains_path_info(self, review_display, mock_log_path):
        """log_saved 메서드가 경로 정보를 포함한 출력을 생성하는지 테스트."""
        output = capture_console_output(review_display.log_saved, mock_log_path)

        # 저장 완료 메시지와 파일명 확인
        assert "저장 완료" in output
        assert "결과 저장" in output
        # 경로가 축약되었더라도 파일명 일부는 포함되어 있어야 함
        assert "2024-01-15_code_revi" in output  # 축약되어도 파일명 일부는 남음

    def test_review_complete_output_comprehensive(
        self, review_display, mock_model_info, mock_estimated_cost, mock_log_path
    ):
        """review_complete 메서드가 모든 정보를 포함한 출력을 생성하는지 테스트."""
        output = capture_console_output(
            review_display.review_complete,
            mock_model_info,
            mock_log_path,
            mock_estimated_cost,
        )

        # 모델 정보 확인
        assert "claude-sonnet-4-20250514" in output
        assert "하이브리드 추론 모델로 고급 코딩 및 명령 수행 최적화" in output

        # 비용 정보 확인 (달러 표시)
        assert "0.095" in output or "$" in output

        # 토큰 정보 확인 (축약된 형태)
        assert "15.4k" in output  # input tokens
        assert "3.2k" in output  # output tokens (실제 출력에서 반올림된 값)

        # 로그 정보 확인
        assert "저장" in output
        assert "코드 리뷰 완료" in output

    def test_print_review_result_with_valid_log(self):
        """유효한 로그 파일로 리뷰 결과 출력 테스트."""
        # 테스트 데이터 생성
        test_data = {
            "model": {"name": "claude-3.5-sonnet"},
            "review_response": {
                "summary": "코드 품질이 좋습니다.",
                "score": 8,
                "issues": [
                    {
                        "severity": "HIGH",
                        "file": "test.py",
                        "line_number": 10,
                        "description": "테스트 설명",
                        "suggestion": "테스트 제안",
                        "target_code": "def test():\n    pass",
                        "suggested_code": 'def test():\n    """Test function."""\n    pass',
                    }
                ],
                "recommendations": ["테스트 추천사항"],
            },
        }

        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(test_data, f, ensure_ascii=False)
            temp_path = f.name

        try:
            # use_pager=False로 설정하여 테스트에서 Pager 비활성화
            with patch("selvage.src.utils.review_display.console"):
                self.display.print_review_result(temp_path, use_pager=False)
            # 정상적으로 실행되면 성공
            assert True
        finally:
            # 임시 파일 정리
            Path(temp_path).unlink()

    def test_print_review_result_with_nonexistent_file(self):
        """존재하지 않는 파일 처리 테스트."""
        with patch("selvage.src.utils.review_display.console") as mock_console:
            self.display.print_review_result("nonexistent.json", use_pager=False)
            # 에러 메시지 출력 확인
            mock_console.error.assert_called_once()

    def test_print_review_result_with_no_issues(self, review_display):
        """이슈가 없는 경우 테스트."""
        test_data = {
            "model": {"name": "claude-3.5-sonnet"},
            "review_response": {
                "summary": "이슈가 없습니다.",
                "score": 10,
                "issues": [],
                "recommendations": [],
            },
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(test_data, f, ensure_ascii=False)
            temp_path = f.name

        try:
            with patch("selvage.src.utils.review_display.console"):
                self.display.print_review_result(temp_path, use_pager=False)
            assert True
        finally:
            Path(temp_path).unlink()

    def test_print_review_result_with_invalid_json(self, review_display):
        """잘못된 JSON 파일 처리 테스트."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write("invalid json content")
            temp_path = f.name

        try:
            with patch("selvage.src.utils.review_display.console") as mock_console:
                self.display.print_review_result(temp_path, use_pager=False)
                mock_console.error.assert_called_once()
        finally:
            Path(temp_path).unlink()

    def test_progress_review_context_manager(self, review_display):
        """progress_review 메서드가 context manager로 정상 동작하는지 테스트."""
        # context manager가 정상적으로 시작되고 종료되는지만 확인
        try:
            with review_display.progress_review("claude-sonnet-4-20250514"):
                # 실제로는 아무것도 하지 않음 (빠른 테스트를 위해)
                pass
        except Exception as e:
            pytest.fail(f"progress_review context manager failed: {e}")

    def test_show_available_models_with_mock(self, review_display):
        """show_available_models 메서드가 예외 없이 실행되는지 테스트."""
        try:
            output = capture_console_output(review_display.show_available_models)
            # 예시: 최소한 "사용 가능한 AI 모델 목록"과 같은 헤더 문자열이 포함되어 있는지 확인
            assert "사용 가능한 AI 모델 목록" in output
        except FileNotFoundError:
            # models.yml 파일이 없는 경우를 예상하고 테스트를 건너뛸 수 있음
            pytest.skip(
                "models.yml not found, skipping test for show_available_models."
            )
        except Exception as e:
            pytest.fail(
                f"show_available_models_with_mock raised an unexpected exception: {e}"
            )

    def test_format_token_count_function(self):
        """_format_token_count 함수가 올바르게 토큰 수를 포맷하는지 테스트."""
        from selvage.src.utils.review_display import _format_token_count

        # 1000 미만
        assert _format_token_count(999) == "999"
        assert _format_token_count(500) == "500"

        # 1000 이상
        assert _format_token_count(1000) == "1.0k"
        assert _format_token_count(1500) == "1.5k"
        assert _format_token_count(15420) == "15.4k"

    def test_shorten_path_function(self):
        """_shorten_path 함수가 올바르게 경로를 축약하는지 테스트."""
        from selvage.src.utils.review_display import _shorten_path

        # 짧은 경로는 그대로
        short_path = "/Users/test/file.txt"
        assert _shorten_path(short_path) == short_path

        # 긴 경로는 축약
        long_path = (
            "/Users/test/very/long/path/to/some/deep/directory/structure/file.txt"
        )
        shortened = _shorten_path(long_path)
        assert len(shortened) <= len(long_path)
        assert "file.txt" in shortened  # 파일명은 보존
        assert "..." in shortened  # 축약 표시 포함

    def test_review_display_has_console_instance(self, review_display):
        """ReviewDisplay 인스턴스가 console 속성을 가지는지 테스트."""
        assert hasattr(review_display, "console")
        assert isinstance(review_display.console, Console)

    def test_estimated_cost_with_different_formats(
        self, review_display, mock_model_info, mock_log_path
    ):
        """다양한 비용 형태로 review_complete가 동작하는지 테스트."""
        # 높은 비용
        high_cost = EstimatedCost(
            model="claude-sonnet-4-20250514",
            input_tokens=150000,
            input_cost_usd=0.45,
            output_tokens=32000,
            output_cost_usd=0.48,
            total_cost_usd=0.93,
            within_context_limit=True,
        )

        output = capture_console_output(
            review_display.review_complete, mock_model_info, mock_log_path, high_cost
        )

        # 높은 토큰 수가 k 단위로 표시되는지 확인
        assert "150.0k" in output
        assert "32.0k" in output
        assert "0.93" in output

    def test_create_syntax_block(self):
        """구문 강조 블록 생성 테스트."""
        code = "def hello():\n    print('Hello, World!')"
        syntax_block = _create_syntax_block(code, "test.py")

        # Syntax 객체가 생성되었는지 확인
        assert syntax_block is not None
        # Rich Syntax 객체의 실제 속성 확인
        assert hasattr(syntax_block, "code")
        assert hasattr(syntax_block, "lexer")
        assert syntax_block.code == code.strip()

    def test_create_syntax_block_without_filename(self):
        """파일명 없이 구문 강조 블록 생성 테스트."""
        code = "some generic code"
        syntax_block = _create_syntax_block(code)

        assert syntax_block is not None
        assert hasattr(syntax_block, "code")
        assert syntax_block.code == code.strip()

    def test_create_syntax_block_javascript(self):
        """JavaScript 구문 강조 블록 생성 테스트."""
        code = "function hello() {\n    console.log('Hello, World!');\n}"
        syntax_block = _create_syntax_block(code, "test.js")

        assert syntax_block is not None
        assert hasattr(syntax_block, "code")
        assert syntax_block.code == code.strip()


class TestHelperFunctions:
    """헬퍼 함수 테스트."""

    def test_format_severity_badge(self):
        """심각도 배지 포맷팅 테스트."""
        assert "HIGH" in _format_severity_badge("HIGH")
        assert "MEDIUM" in _format_severity_badge("MEDIUM")
        assert "LOW" in _format_severity_badge("LOW")
        assert "INFO" in _format_severity_badge("INFO")
        assert "cyan" in _format_severity_badge("UNKNOWN")

    def test_shorten_path(self):
        """경로 축약 테스트."""
        long_path = "/very/long/path/to/some/deep/directory/structure/file.py"
        shortened = _shorten_path(long_path)
        assert len(shortened) <= len(long_path)
        assert "..." in shortened or len(long_path) <= 60

    def test_load_review_log_valid_file(self):
        """유효한 로그 파일 로드 테스트."""
        test_data = {"test": "data"}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            result = _load_review_log(temp_path)
            assert result == test_data
        finally:
            Path(temp_path).unlink()

    def test_load_review_log_nonexistent_file(self):
        """존재하지 않는 파일 로드 테스트."""
        with patch("selvage.src.utils.review_display.console"):
            result = _load_review_log("nonexistent.json")
            assert result is None

    def test_create_recommendations_panel(self):
        """추천사항 패널 생성 테스트."""
        recommendations = ["추천사항 1", "추천사항 2"]
        panel = _create_recommendations_panel(recommendations)
        assert panel is not None

    def test_create_recommendations_panel_empty(self):
        """빈 추천사항 패널 생성 테스트."""
        panel = _create_recommendations_panel([])
        assert panel is not None

    def test_detect_language_from_filename(self):
        """파일명에서 언어 감지 테스트."""
        assert _detect_language_from_filename("test.py") == "python"
        assert _detect_language_from_filename("test.js") == "javascript"
        assert _detect_language_from_filename("test.java") == "java"
        assert _detect_language_from_filename("test.cpp") == "cpp"
        assert _detect_language_from_filename("test.unknown") == "text"
        assert _detect_language_from_filename("") == "text"
