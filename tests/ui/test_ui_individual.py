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
    from selvage.src.models.model_provider import ModelProvider
    from selvage.src.utils.review_display import ReviewDisplay
    from selvage.src.utils.token.models import EstimatedCost
except ImportError:
    # 개발 환경에서 패키지가 설치되지 않은 경우에만 사용
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from selvage.src.models.model_provider import ModelProvider
    from selvage.src.utils.review_display import ReviewDisplay
    from selvage.src.utils.token.models import EstimatedCost

# ModelInfoDict 타입 힌팅을 위한 간단한 타입 정의 (yaml 의존성 없이)
from typing import Any

ModelInfoDict = dict[str, Any]


def create_mock_data():
    """테스트용 Mock 데이터를 생성합니다."""
    mock_model_info: ModelInfoDict = {
        "full_name": "Claude 3.5 Sonnet",
        "aliases": ["claude-3.5-sonnet", "claude"],
        "description": "코드 분석과 리뷰에 특화된 고성능 AI 모델",
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


def test_updatable_progress():
    """업데이트 가능한 진행 상황 UI 테스트 - 다양한 상황별 종료 메서드 시연."""
    display = ReviewDisplay()

    print("업데이트 가능한 진행률 UI 테스트 - 상황별 종료 메서드 시연")

    # 시나리오 1: 정상 완료
    print("\n1. 정상 완료 시나리오")
    progress1 = display.create_updatable_progress("Claude Sonnet-4")
    progress1.start()
    time.sleep(2)
    progress1.update_message("리뷰 완료 중...")
    time.sleep(1)
    progress1.stop()  # 정상 완료

    # 시나리오 2: 전환 상황
    print("\n2. Long context 전환 시나리오")
    progress2 = display.create_updatable_progress("gpt-5.2-codex")
    progress2.start()
    time.sleep(2)
    progress2.update_message("컨텍스트 한계 초과 감지!")
    time.sleep(1)
    progress2.stop()  # 전환용 종료

    # 시나리오 3: 에러 상황
    print("\n3. 에러 발생 시나리오")
    progress3 = display.create_updatable_progress("Gemini-2.5-Pro")
    progress3.start()
    time.sleep(2)
    progress3.update_message("API 오류 발생...")
    time.sleep(1)
    progress3.stop()  # 에러 종료

    print("\n✅ 모든 상황별 종료 메서드 테스트 완료")


def test_long_context_transition():
    """실제 CLI에서 발생하는 Long context review 전환을 완전히 재현합니다."""
    print("🎯 실제 multiturn review 전환 시나리오 재현")
    print("실제 CLI 코드와 동일한 방식으로 진행됩니다...")

    # 실제 CLI의 _perform_new_review 함수와 동일한 방식
    display = ReviewDisplay()

    # 1. 업데이트 가능한 진행 상황 표시 시작 (CLI와 동일)
    progress = display.create_updatable_progress("kimi-k2.5")  # 실제 사용한 모델명
    progress.start()

    try:
        # 2. 일반 리뷰 시뮬레이션 (정상적인 처리 중)
        time.sleep(3)

        # 3. 컨텍스트 제한 에러 감지 시뮬레이션
        # 실제 CLI에서 error_response.is_context_limit_error()가 True일 때와 동일

        # 4. 전환용 종료 - 화면 clear하여 깔끔하게 정리
        progress.stop()

        # 5. 새로운 progress 인스턴스 생성 (깨끗한 화면에서 시작)
        multiturn_progress = display.create_updatable_progress("kimi-k2.5")
        multiturn_progress.start()
        multiturn_progress.update_message(
            "Context limit reached! Processing in long context mode..."
        )

        # 6. Multiturn review 처리 시뮬레이션
        time.sleep(4)

        # 7. 완료
        multiturn_progress.complete()

    except Exception:
        # progress 또는 multiturn_progress 중 활성화된 것을 에러로 종료
        try:
            if "multiturn_progress" in locals():
                multiturn_progress.stop()
            else:
                progress.stop()
        except:
            pass
        raise

    print("\n✅ 실제 multiturn review 전환과 동일한 UI 재현 완료")


def test_multiple_transitions():
    """여러 단계의 진행 상황 변화를 테스트 - 실제 전환 시나리오 포함."""
    display = ReviewDisplay()

    print("다단계 진행 상황 변화 테스트 - 실제 전환 시나리오 포함")

    try:
        # 1단계: 일반 리뷰 시작
        progress = display.create_updatable_progress("Claude Sonnet-4")
        progress.start()

        stages_normal = [
            ("코드 분석 및 리뷰 생성 중...", 2),
            ("대용량 파일 처리 중...", 2),
            ("컨텍스트 제한 초과 감지됨", 1),
        ]

        for i, (message, duration) in enumerate(stages_normal, 1):
            print(f"   {i}/{len(stages_normal)}: {message}")
            progress.update_message(message)
            time.sleep(duration)

        # 2단계: 전환 상황 - 기존 progress 종료
        print("   🔄 Context 한계 초과! 전환 중...")
        progress.stop()  # 전환용 종료

        # 3단계: 새로운 multiturn progress 시작
        multiturn_progress = display.create_updatable_progress("Claude Sonnet-4")
        multiturn_progress.start()
        multiturn_progress.update_message("Long context review로 전환합니다...")
        time.sleep(2)

        stages_multiturn = [
            ("프롬프트 분할 처리 중... (1/3)", 2),
            ("프롬프트 분할 처리 중... (2/3)", 2),
            ("프롬프트 분할 처리 중... (3/3)", 2),
            ("결과 통합 중...", 1),
        ]

        for i, (message, duration) in enumerate(stages_multiturn, 4):
            print(f"   {i}/{len(stages_normal) + len(stages_multiturn)}: {message}")
            multiturn_progress.update_message(message)
            time.sleep(duration)

        # 4단계: 정상 완료
        multiturn_progress.complete()
        print("✅ 다단계 진행 상황 변화 테스트 완료")

    except Exception:
        # 에러 발생 시 적절한 progress 종료
        try:
            if "multiturn_progress" in locals():
                multiturn_progress.stop()
            else:
                progress.stop()
        except:
            pass
        raise


def test_cli_exact_reproduction():
    """CLI의 _perform_new_review 함수 로직을 정확히 재현합니다."""
    print("🔄 CLI _perform_new_review 함수 로직 정확 재현")
    print("selvage/cli.py:357-377 새로운 방식으로 수정된 코드")

    from selvage.src.utils.review_display import ReviewDisplay

    # CLI에서와 동일한 방식
    display = ReviewDisplay()
    progress = display.create_updatable_progress("kimi-k2.5")
    progress.start()

    try:
        # 일반 리뷰 처리 시뮬레이션 (review_result 생성까지)
        time.sleep(2)

        # 컨텍스트 제한 에러 시뮬레이션
        # CLI 코드: if error_response.is_context_limit_error():
        simulate_context_limit_error = True

        if simulate_context_limit_error:
            # 전환용 종료 - 화면 clear하여 깔끔하게 정리
            progress.stop()

            # 새로운 progress 인스턴스 생성 (깨끗한 화면에서 시작)
            multiturn_progress = display.create_updatable_progress("kimi-k2.5")
            multiturn_progress.start()
            multiturn_progress.update_message(
                "Context limit reached! Processing in long context mode..."
            )

            try:
                # MultiturnReviewExecutor.execute_multiturn_review() 시뮬레이션
                time.sleep(5)
                multiturn_progress.complete()  # 정상 완료
                print("✅ 상황별 종료 메서드로 깔끔하게 처리 완료")
                return
            except Exception:
                multiturn_progress.stop()  # 에러 발생 시
                raise

        # 정상 완료 (에러가 없는 경우)
        progress.complete()

    except Exception:
        progress.stop()  # 예상치 못한 에러 시
        raise


def test_show_available_models():
    """사용 가능한 모델 목록 UI만 테스트합니다."""
    display = ReviewDisplay()
    display.show_available_models()


def main():
    """지정된 UI 요소만 테스트합니다."""
    parser = argparse.ArgumentParser(description="ReviewDisplay UI 개별 테스트")
    parser.add_argument(
        "test_type",
        choices=[
            "model_info",
            "log_saved",
            "review_complete",
            "progress",
            "updatable_progress",
            "long_context",
            "multi_transitions",
            "cli_exact",
            "models",
        ],
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
        elif args.test_type == "updatable_progress":
            test_updatable_progress()
        elif args.test_type == "long_context":
            test_long_context_transition()
        elif args.test_type == "multi_transitions":
            test_multiple_transitions()
        elif args.test_type == "cli_exact":
            test_cli_exact_reproduction()
        elif args.test_type == "models":
            test_show_available_models()

        print("\n✅ 테스트 완료!")

    except KeyboardInterrupt:
        print("\n❌ 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")


if __name__ == "__main__":
    main()
