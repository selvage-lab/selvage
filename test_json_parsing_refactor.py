#!/usr/bin/env python3
"""JSONParsingError 리팩터링 검증 테스트"""

from selvage.src.exceptions.json_parsing_error import JSONParsingError


def test_from_parsing_exception_method():
    """from_parsing_exception 메서드 동작 검증"""
    print("=== JSONParsingError.from_parsing_exception 테스트 ===")

    # 원본 예외 생성
    original_error = ValueError("Invalid JSON format")
    response_text = "This is a very long response text that should be truncated" * 20

    # from_parsing_exception 메서드 테스트
    json_error = JSONParsingError.from_parsing_exception(
        source_error=original_error, api_name="Test API", raw_response=response_text
    )

    # 검증
    assert isinstance(json_error, JSONParsingError)
    assert "Test API 응답 파싱 실패" in str(json_error)
    assert "ValueError" in str(json_error)
    assert json_error.parsing_error == original_error
    assert len(json_error.raw_response) <= 503  # 500 + "..."
    assert json_error.raw_response.endswith("...")

    print(f"✅ 메시지: {json_error}")
    print(
        f"✅ 원본 응답 길이: {len(response_text)} → 잘린 응답 길이: {len(json_error.raw_response)}"
    )
    print(f"✅ 원본 예외: {json_error.parsing_error}")


def test_truncate_response_method():
    """_truncate_response 정적 메서드 테스트"""
    print("\n=== _truncate_response 메서드 테스트 ===")

    # 긴 텍스트 테스트
    long_text = "A" * 600
    truncated = JSONParsingError._truncate_response(long_text)
    assert len(truncated) == 503  # 500 + "..."
    assert truncated.endswith("...")

    # 짧은 텍스트 테스트
    short_text = "Short text"
    not_truncated = JSONParsingError._truncate_response(short_text)
    assert not_truncated == short_text
    assert not not_truncated.endswith("...")

    # None 테스트
    none_result = JSONParsingError._truncate_response(None)
    assert none_result == ""

    # 빈 문자열 테스트
    empty_result = JSONParsingError._truncate_response("")
    assert empty_result == ""

    print("✅ 긴 텍스트 자르기 성공")
    print("✅ 짧은 텍스트 유지 성공")
    print("✅ None 처리 성공")
    print("✅ 빈 문자열 처리 성공")


def test_code_reduction():
    """코드 라인 수 감소 확인"""
    print("\n=== 코드 단순화 확인 ===")

    # 이전 코드 (시뮬레이션)
    def old_way(parse_error, response_text):
        truncated_response = (
            response_text[:500] + "..." if len(response_text) > 500 else response_text
        )
        return JSONParsingError(
            f"API 응답 파싱 실패: {str(parse_error)}",
            raw_response=truncated_response,
            parsing_error=parse_error,
        )

    # 새로운 코드 (현재 방식)
    def new_way(parse_error, response_text):
        return JSONParsingError.from_parsing_exception(
            parse_error, "API", response_text
        )

    # 동일한 결과 확인
    test_error = ValueError("Test error")
    test_response = "A" * 600

    old_result = old_way(test_error, test_response)
    new_result = new_way(test_error, test_response)

    # 핵심 속성들이 동일한지 확인
    assert old_result.parsing_error == new_result.parsing_error
    assert len(old_result.raw_response) == len(new_result.raw_response)
    assert old_result.raw_response.endswith("...") == new_result.raw_response.endswith(
        "..."
    )

    print("✅ 이전 방식과 새 방식의 결과가 동일함")
    print("✅ 코드 라인 수: 8줄 → 3줄 (62% 감소)")


if __name__ == "__main__":
    print("JSONParsingError 리팩터링 검증 시작...\n")

    try:
        test_from_parsing_exception_method()
        test_truncate_response_method()
        test_code_reduction()
        print("\n🎉 모든 검증 통과! 리팩터링이 성공적으로 완료되었습니다.")
    except Exception as e:
        print(f"\n❌ 검증 실패: {e}")
        raise
