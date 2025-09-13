"""ReviewFormatter 테스트 모듈."""

from unittest.mock import patch

import pytest

from selvage.src.utils.review_formatter import ReviewFormatter
from selvage.src.utils.token.models import ReviewIssue, ReviewResponse


@pytest.fixture
def complex_review_response() -> ReviewResponse:
    """복잡한 형태의 ReviewResponse 객체를 생성하는 픽스처입니다.

    Returns:
        ReviewResponse: 테스트용 복잡한 리뷰 응답 객체
    """
    return ReviewResponse(
        issues=[
            ReviewIssue(
                type="버그",
                line_number=10,
                file="main.py",
                description="잠재적인 널 참조 오류",
                suggestion="None 체크 추가",
                severity="error",
                target_code="data = user.get_data()",
                suggested_code="if user is not None:\n    data = user.get_data()\nelse:\n    data = None",
            ),
            ReviewIssue(
                type="성능",
                line_number=25,
                file="utils.py",
                description="비효율적인 루프 사용",
                suggestion="리스트 컴프리헨션 사용",
                severity="warning",
                target_code="result = []\nfor item in items:\n    result.append(item.value)",
                suggested_code="result = [item.value for item in items]",
            ),
        ],
        summary="코드에 몇 가지 개선이 필요합니다.",
        score=7.5,
        recommendations=["변수명 명확히 하기", "주석 추가하기"],
    )


def test_formatter_to_markdown(complex_review_response: ReviewResponse) -> None:
    """ReviewFormatter의 to_markdown 메서드를 테스트합니다.

    Args:
        complex_review_response: 테스트용 복잡한 리뷰 응답 객체
    """
    # 마크다운 형식 변환 테스트
    formatter = ReviewFormatter()
    markdown = formatter.to_markdown(complex_review_response)

    # 기본 구조 검증
    assert "# 코드 리뷰 결과" in markdown
    assert "## 요약" in markdown
    assert "코드에 몇 가지 개선이 필요합니다." in markdown
    assert "**점수**: 7.5/10" in markdown

    # 이슈 검증
    assert "## 발견된 이슈" in markdown
    assert "### 1. 🛑 버그" in markdown
    assert "**파일**: `main.py`, **라인**: 10" in markdown
    assert "잠재적인 널 참조 오류" in markdown
    assert "None 체크 추가" in markdown

    # 코드 블록 검증
    assert "```python\ndata = user.get_data()\n```" in markdown
    assert (
        "```python\nif user is not None:\n    data = user.get_data()\nelse:\n    data = None\n```"
        in markdown
    )

    # 두 번째 이슈 검증
    assert "### 2. ⚠️ 성능" in markdown

    # 권장사항 검증
    assert "## 권장사항" in markdown
    assert "1. 변수명 명확히 하기" in markdown
    assert "2. 주석 추가하기" in markdown


def test_formatter_to_html(complex_review_response: ReviewResponse) -> None:
    """ReviewFormatter의 to_html 메서드를 테스트합니다.

    Args:
        complex_review_response: 테스트용 복잡한 리뷰 응답 객체
    """
    # HTML 형식 변환 테스트
    formatter = ReviewFormatter()
    html = formatter.to_html(complex_review_response)

    # 기본 구조 검증
    assert "<!DOCTYPE html>" in html
    assert "<title>코드 리뷰 결과</title>" in html
    assert "<h1>코드 리뷰 결과</h1>" in html

    # 요약 및 점수 검증
    assert "<h2>요약</h2>" in html
    assert "<p>코드에 몇 가지 개선이 필요합니다.</p>" in html
    assert "<p><strong>점수</strong>: 7.5/10</p>" in html

    # 이슈 및 코드 블록 검증
    assert "<div class='issue error'>" in html
    assert "<pre><code class='language-python'>" in html  # 언어 클래스 명시
    assert (
        html.count("<pre><code class='language-python'>") == 4
    )  # main.py와 utils.py 모두 python으로 감지되므로 총 4개

    # CSS 스타일 포함 검증
    assert "<style>" in html


def test_formatter_empty_review() -> None:
    """ReviewFormatter가 빈 리뷰 응답을 올바르게 처리하는지 테스트합니다."""
    # 빈 리뷰 응답 테스트
    empty_review = ReviewResponse(
        issues=[], summary="No issues found.", score=10.0, recommendations=[]
    )

    formatter = ReviewFormatter()
    markdown = formatter.to_markdown(empty_review)

    assert "# 코드 리뷰 결과" in markdown
    assert "## 요약" in markdown
    assert "No issues found." in markdown
    assert "**점수**: 10.0/10" in markdown
    assert "## 발견된 이슈" not in markdown  # 이슈가 없으므로 섹션이 없어야 함
    assert "## 권장사항" not in markdown  # 권장사항이 없으므로 섹션이 없어야 함


# format 메서드에 대한 테스트 추가
def test_formatter_format_markdown(complex_review_response: ReviewResponse) -> None:
    """format 메서드가 마크다운 형식으로 올바르게 변환하는지 테스트합니다.

    Args:
        complex_review_response: 테스트용 복잡한 리뷰 응답 객체
    """
    formatter = ReviewFormatter()

    # format 메서드 호출 (기본값: markdown)
    markdown_result = formatter.format(complex_review_response)

    # to_markdown 메서드의 결과와 비교
    expected_result = formatter.to_markdown(complex_review_response)
    assert markdown_result == expected_result


def test_formatter_format_html(complex_review_response: ReviewResponse) -> None:
    """format 메서드가 HTML 형식으로 올바르게 변환하는지 테스트합니다.

    Args:
        complex_review_response: 테스트용 복잡한 리뷰 응답 객체
    """
    formatter = ReviewFormatter()

    # format 메서드 호출 (html 형식 지정)
    html_result = formatter.format(complex_review_response, output_format="html")

    # to_html 메서드의 결과와 비교
    expected_result = formatter.to_html(complex_review_response)
    assert html_result == expected_result


def test_formatter_format_invalid() -> None:
    """format 메서드가 지원하지 않는 형식에 대해 예외를 발생시키는지 테스트합니다."""
    formatter = ReviewFormatter()
    review = ReviewResponse(issues=[], summary="테스트용 리뷰", recommendations=[])

    # 지원하지 않는 형식으로 호출시 ValueError 발생 확인
    with pytest.raises(ValueError) as excinfo:
        formatter.format(review, output_format="json")

    # 예외 메시지 검증
    assert "Unsupported output format" in str(excinfo.value)


# 모킹을 사용한 format 메서드 테스트
def test_formatter_format_calls_correct_method(
    complex_review_response: ReviewResponse,
) -> None:
    """format 메서드가 출력 형식에 따라 올바른 메서드를 호출하는지 테스트합니다.

    Args:
        complex_review_response: 테스트용 복잡한 리뷰 응답 객체
    """
    formatter = ReviewFormatter()

    # to_markdown 메서드 모킹
    with patch.object(formatter, "to_markdown") as mock_to_markdown:
        formatter.format(complex_review_response)
        # to_markdown이 호출되었는지 확인
        mock_to_markdown.assert_called_once_with(complex_review_response)

    # to_html 메서드 모킹
    with patch.object(formatter, "to_html") as mock_to_html:
        formatter.format(complex_review_response, output_format="html")
        # to_html이 호출되었는지 확인
        mock_to_html.assert_called_once_with(complex_review_response)
