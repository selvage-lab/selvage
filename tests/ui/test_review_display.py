#!/usr/bin/env python3
"""ReviewDisplay UI 테스트 스크립트.

실제 API 호출 없이 ReviewDisplay의 모든 UI 요소를 확인할 수 있습니다.

실행 전 권장 사항:
    1. 개발 모드로 패키지 설치: pip install -e .
    2. 또는 PYTHONPATH 환경변수 설정: export PYTHONPATH="$PWD:$PYTHONPATH"
"""

import sys
import time
from pathlib import Path

# 패키지가 설치되지 않은 경우에만 경로 추가 (후순위 방법)
try:
    from selvage.src.model_config import ModelInfoDict
except ImportError:
    # 개발 환경에서 패키지가 설치되지 않은 경우에만 사용
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from selvage.src.model_config import ModelInfoDict

from selvage.src.models.model_provider import ModelProvider
from selvage.src.utils.review_display import ReviewDisplay
from selvage.src.utils.token.models import EstimatedCost


def create_mock_data():
    """테스트용 Mock 데이터를 생성합니다."""

    # Mock 모델 정보 (올바른 ModelInfoDict 구조)
    mock_model_info: ModelInfoDict = {
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

    # Mock 비용 정보 (실제 EstimatedCost 클래스 사용)
    mock_estimated_cost = EstimatedCost(
        model="claude-sonnet-4-20250514",
        input_tokens=15420,
        input_cost_usd=0.046,
        output_tokens=3250,
        output_cost_usd=0.049,
        total_cost_usd=0.095,
        within_context_limit=True,
    )

    # Mock 경로
    mock_log_path = str(
        Path.home()
        / "Development"
        / "my-project"
        / "review_logs"
        / "2024-01-15_code_review_claude.md"
    )

    return mock_model_info, mock_estimated_cost, mock_log_path


def test_model_info():
    """모델 정보 UI 테스트."""
    print("\n" + "=" * 60)
    print("1. 모델 정보 UI 테스트")
    print("=" * 60)

    display = ReviewDisplay()
    display.model_info(
        model_name="Claude 3.5 Sonnet",
        description="코드 분석과 리뷰에 특화된 고성능 AI 모델",
    )


def test_log_saved():
    """로그 저장 완료 UI 테스트."""
    print("\n" + "=" * 60)
    print("2. 로그 저장 완료 UI 테스트")
    print("=" * 60)

    display = ReviewDisplay()
    _, _, mock_log_path = create_mock_data()
    display.log_saved(mock_log_path)


def test_review_complete():
    """리뷰 완료 통합 UI 테스트."""
    print("\n" + "=" * 60)
    print("3. 리뷰 완료 통합 UI 테스트")
    print("=" * 60)

    display = ReviewDisplay()
    mock_model_info, mock_estimated_cost, mock_log_path = create_mock_data()

    display.review_complete(
        model_info=mock_model_info,
        log_path=mock_log_path,
        estimated_cost=mock_estimated_cost,
    )


def test_progress_review():
    """리뷰 진행 상황 UI 테스트."""
    print("\n" + "=" * 60)
    print("4. 리뷰 진행 상황 UI 테스트 (5초간 표시)")
    print("=" * 60)

    display = ReviewDisplay()

    with display.progress_review(model="Claude 3.5 Sonnet"):
        # 실제 리뷰 대신 5초 대기
        time.sleep(5)


def test_show_available_models():
    """사용 가능한 모델 목록 UI 테스트."""
    print("\n" + "=" * 60)
    print("5. 사용 가능한 모델 목록 UI 테스트")
    print("=" * 60)

    display = ReviewDisplay()
    display.show_available_models()


def main():
    """모든 UI 테스트를 실행합니다."""
    print("ReviewDisplay UI 테스트 시작")
    print("=" * 60)
    print("각 UI 요소를 순차적으로 테스트합니다.")
    print("실제 API 호출은 없으므로 비용이 발생하지 않습니다.")

    try:
        # 개별 테스트 실행
        test_model_info()
        input("\n다음 테스트로 계속하려면 Enter를 누르세요...")

        test_log_saved()
        input("\n다음 테스트로 계속하려면 Enter를 누르세요...")

        test_review_complete()
        input("\n다음 테스트로 계속하려면 Enter를 누르세요...")

        test_progress_review()
        input("\n다음 테스트로 계속하려면 Enter를 누르세요...")

        test_show_available_models()

        print("\n" + "=" * 60)
        print("✅ 모든 UI 테스트가 완료되었습니다!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n❌ 테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 테스트 중 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    main()
