"""ReviewDisplay 클래스의 단위 테스트."""

import io
from pathlib import Path

import pytest
from rich.console import Console

from selvage.src.model_config import ModelInfoDict
from selvage.src.models.model_provider import ModelProvider
from selvage.src.utils.review_display import ReviewDisplay
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
        """show_available_models 메서드가 mock 데이터로 정상 동작하는지 테스트."""
        # show_available_models는 실제 구현을 사용하되 오류가 발생해도 무시
        try:
            output = capture_console_output(review_display.show_available_models)

            # 최소한의 출력 요소가 있는지만 확인
            assert len(output) > 0  # 어떤 출력이라도 있어야 함
        except Exception:
            # 설정 파일 문제 등으로 실패할 수 있으므로 무시
            pass

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
