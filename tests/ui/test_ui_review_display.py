#!/usr/bin/env python3

"""리뷰 표시 UI 테스트 - 새로운 통합 API 사용"""

import json
import tempfile
import time

from selvage.src.utils.review_display import ReviewDisplay


def test_enhanced_progress_review():
    """새로운 enhanced_progress_review 컨텍스트 매니저 테스트."""
    print("\n" + "=" * 60)
    print("6. Enhanced Progress Review 테스트 (새로운 패턴)")
    print("=" * 60)

    display = ReviewDisplay()

    print("새로운 enhanced_progress_review 시나리오를 시뮬레이션합니다.")
    print("단계별 진행 상황:")

    # 새로운 컨텍스트 매니저 패턴 사용
    with display.enhanced_progress_review("Claude Sonnet-4") as progress:
        # 1단계: 일반 리뷰 시뮬레이션
        print("  1️⃣ 일반 코드 리뷰 진행 중...")
        time.sleep(3)

        # 2단계: 컨텍스트 제한 감지 시뮬레이션
        print("  ⚠️ 컨텍스트 제한 초과 감지!")

        # 3단계: UI 연속성을 유지하면서 멀티턴 모드로 전환
        print("  🔄 멀티턴 모드로 부드럽게 전환 (UI 연속성 유지)")
        progress.transition_to_multiturn(
            "Context limit reached! Processing in long context mode..."
        )

        # 4단계: Multiturn review 처리 시뮬레이션
        time.sleep(4)

        # 5단계: 정상 완료
        print("  ✅ 리뷰 완료")
        progress.complete()

    print("  🎯 테스트 완료: 새로운 패턴으로 UI 연속성을 유지하며 동작했습니다!")


def test_progress_review():
    """기존 progress_review 메서드 테스트."""
    print("\n" + "=" * 60)
    print("5. Progress Review 컨텍스트 매니저 테스트")
    print("=" * 60)

    display = ReviewDisplay()

    with display.progress_review(model="Claude 3.5 Sonnet"):
        print("  📊 리뷰 진행 상황 표시 중...")
        time.sleep(3)
        print("  ✅ 리뷰 처리 완료")

    print("  🎯 progress_review 컨텍스트 매니저 정상 동작 완료!")


def test_print_review_result():
    """리뷰 결과 출력 UI 테스트."""
    print("\n" + "=" * 60)
    print("8. 리뷰 결과 출력 테스트")
    print("=" * 60)

    display = ReviewDisplay()

    # 샘플 데이터 생성
    sample_data = {
        "model": {
            "name": "claude-3-5-sonnet-20241022",
            "description": "Claude 3.5 Sonnet",
        },
        "review_response": {
            "summary": "전반적으로 잘 작성된 코드입니다. 몇 가지 개선사항이 있습니다.",
            "score": 8,
            "issues": [
                {
                    "severity": "medium",
                    "file": "example.py",
                    "line_number": 15,
                    "description": "변수명이 명확하지 않습니다.",
                    "suggestion": "더 의미있는 변수명을 사용하세요.",
                    "target_code": "x = calculate()",
                    "suggested_code": "result = calculate()",
                }
            ],
            "recommendations": [
                "타입 힌팅을 추가하면 코드 가독성이 향상됩니다.",
                "단위 테스트를 추가하는 것을 권장합니다.",
            ],
        },
    }

    # 임시 파일 생성 및 테스트
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as temp_file:
        json.dump(sample_data, temp_file, ensure_ascii=False, indent=2)
        temp_log_path = temp_file.name

    try:
        print(f"임시 로그 파일 생성: {temp_log_path}")
        print("리뷰 결과 출력 중...")
        print("-" * 60)

        # use_pager=False로 설정하여 터미널에 직접 출력
        display.print_review_result(temp_log_path, use_pager=False)

    finally:
        # 임시 파일 정리
        import os

        try:
            os.unlink(temp_log_path)
            print(f"\n임시 파일 삭제 완료: {temp_log_path}")
        except FileNotFoundError:
            pass

    print("  🎯 리뷰 결과 출력 테스트 완료!")


def main():
    """모든 UI 테스트를 실행합니다."""
    print("=" * 60)
    print("🎨 Selvage UI 테스트 시작 (새로운 통합 API)")
    print("=" * 60)

    try:
        test_progress_review()
        input("\n다음 테스트로 계속하려면 Enter를 누르세요...")

        test_enhanced_progress_review()
        input("\n다음 테스트로 계속하려면 Enter를 누르세요...")

        test_print_review_result()

        print("\n" + "=" * 60)
        print("✅ 모든 UI 테스트가 완료되었습니다!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n❌ 테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 테스트 중 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    main()
