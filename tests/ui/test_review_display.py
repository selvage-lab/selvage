#!/usr/bin/env python3
"""ReviewDisplay UI 테스트 스크립트.

실제 API 호출 없이 ReviewDisplay의 모든 UI 요소를 확인할 수 있습니다.

실행 전 권장 사항:
    1. 개발 모드로 패키지 설치: pip install -e .
    2. 또는 PYTHONPATH 환경변수 설정: export PYTHONPATH="$PWD:$PYTHONPATH"
"""

import json
import sys
import tempfile
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


def create_sample_log_data():
    """print_review_result 테스트용 샘플 로그 데이터를 생성합니다."""
    return {
        "model": {
            "name": "Claude 3.5 Sonnet",
            "version": "claude-sonnet-3.5-20241022",
            "provider": "Anthropic",
        },
        "review_response": {
            "summary": "전반적으로 잘 작성된 코드입니다. 몇 가지 개선사항과 잠재적 이슈가 발견되었습니다.",
            "score": 8,
            "issues": [
                {
                    "severity": "HIGH",
                    "file": "src/calculator.py",
                    "line_number": 15,
                    "description": "Zero division 에러가 발생할 수 있습니다. 분모가 0인 경우에 대한 예외 처리가 필요합니다.",
                    "suggestion": "try-except 블록을 사용하여 ZeroDivisionError를 처리하고, 적절한 에러 메시지를 반환하세요.",
                    "target_code": "def divide(a, b):\n    return a / b",
                    "suggested_code": "def divide(a, b):\n    try:\n        return a / b\n    except ZeroDivisionError:\n        raise ValueError('Division by zero is not allowed')",
                },
                {
                    "severity": "MEDIUM",
                    "file": "src/utils.py",
                    "line_number": 23,
                    "description": "변수명이 명확하지 않습니다. 더 의미있는 이름을 사용하는 것이 좋습니다.",
                    "suggestion": "단일 문자 변수명 대신 설명적인 변수명을 사용하세요.",
                    "target_code": "for i in x:\n    result += i",
                    "suggested_code": "for item in items:\n    result += item",
                },
                {
                    "severity": "LOW",
                    "file": "src/main.py",
                    "line_number": 5,
                    "description": "불필요한 import문이 있습니다.",
                    "suggestion": "사용하지 않는 import문을 제거하세요.",
                    "target_code": "import os\nimport sys\nimport json  # 사용하지 않음",
                    "suggested_code": "import os\nimport sys",
                },
            ],
            "recommendations": [
                "단위 테스트 코드를 추가하여 코드의 신뢰성을 높이세요.",
                "타입 힌팅을 추가하여 코드의 가독성과 유지보수성을 향상시키세요.",
                "docstring을 추가하여 함수와 클래스의 역할을 명확히 하세요.",
                "에러 로깅 시스템을 도입하여 디버깅을 용이하게 하세요.",
            ],
        },
        "timestamp": "2024-01-15T10:30:00Z",
        "git_commit": "abc123def456",
        "files_reviewed": ["src/calculator.py", "src/utils.py", "src/main.py"],
    }


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


def test_print_review_result():
    """리뷰 결과 출력 UI 테스트."""
    print("\n" + "=" * 60)
    print("6. 리뷰 결과 출력 UI 테스트")
    print("=" * 60)

    display = ReviewDisplay()

    # 임시 로그 파일 생성
    sample_data = create_sample_log_data()

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
        except OSError:
            pass


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
