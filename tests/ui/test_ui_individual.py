#!/usr/bin/env python3
"""ReviewDisplay UI 개별 테스트 스크립트.

특정 UI 요소만 빠르게 테스트할 수 있습니다.

실행 전 권장 사항:
    1. 개발 모드로 패키지 설치: pip install -e .
    2. 또는 PYTHONPATH 환경변수 설정: export PYTHONPATH="$PWD:$PYTHONPATH"
"""

import argparse
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
    mock_model_info: ModelInfoDict = {
        "full_name": "Claude 3.5 Sonnet",
        "aliases": ["claude-3.5-sonnet", "claude"],
        "description": "코드 분석과 리뷰에 특화된 고성능 AI 모델",
        "provider": ModelProvider.CLAUDE,
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

    mock_estimated_cost = EstimatedCost(
        model="claude-3.5-sonnet",
        input_tokens=15420,
        input_cost_usd=0.046,
        output_tokens=3250,
        output_cost_usd=0.049,
        total_cost_usd=0.095,
        within_context_limit=True,
    )

    mock_log_path = str(
        Path.home()
        / "Development"
        / "my-project"
        / "review_logs"
        / "2024-01-15_code_review_claude.md"
    )

    return mock_model_info, mock_estimated_cost, mock_log_path


def test_model_info():
    """모델 정보 UI만 테스트합니다."""
    display = ReviewDisplay()
    display.model_info(
        model_name="Claude 3.5 Sonnet",
        description="코드 분석과 리뷰에 특화된 고성능 AI 모델",
    )


def test_log_saved():
    """로그 저장 완료 UI만 테스트합니다."""
    display = ReviewDisplay()
    _, _, mock_log_path = create_mock_data()
    display.log_saved(mock_log_path)


def test_review_complete():
    """리뷰 완료 통합 UI만 테스트합니다."""
    display = ReviewDisplay()
    mock_model_info, mock_estimated_cost, mock_log_path = create_mock_data()

    display.review_complete(
        model_info=mock_model_info,
        log_path=mock_log_path,
        estimated_cost=mock_estimated_cost,
    )


def test_progress_review():
    """리뷰 진행 상황 UI만 테스트합니다."""
    display = ReviewDisplay()

    print("진행률 UI 테스트 (3초간 표시)")
    with display.progress_review(model="Claude 3.5 Sonnet"):
        time.sleep(3)


def test_show_available_models():
    """사용 가능한 모델 목록 UI만 테스트합니다."""
    display = ReviewDisplay()
    display.show_available_models()


def main():
    """지정된 UI 요소만 테스트합니다."""
    parser = argparse.ArgumentParser(description="ReviewDisplay UI 개별 테스트")
    parser.add_argument(
        "test_type",
        choices=["model_info", "log_saved", "review_complete", "progress", "models"],
        help="테스트할 UI 요소 선택",
    )

    args = parser.parse_args()

    print(f"🎨 ReviewDisplay UI 테스트: {args.test_type}")
    print("=" * 50)

    try:
        if args.test_type == "model_info":
            test_model_info()
        elif args.test_type == "log_saved":
            test_log_saved()
        elif args.test_type == "review_complete":
            test_review_complete()
        elif args.test_type == "progress":
            test_progress_review()
        elif args.test_type == "models":
            test_show_available_models()

        print("\n✅ 테스트 완료!")

    except KeyboardInterrupt:
        print("\n❌ 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")


if __name__ == "__main__":
    main()
