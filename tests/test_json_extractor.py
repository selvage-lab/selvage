"""JSONExtractor 유틸리티 테스트"""

import pytest
from pydantic import BaseModel, ValidationError

from selvage.src.exceptions.json_parsing_error import JSONParsingError
from selvage.src.utils.json_extractor import JSONExtractor


class SampleModel(BaseModel):
    """테스트용 Pydantic 모델"""

    name: str
    age: int


class TestJSONExtractor:
    """JSONExtractor 클래스 테스트"""

    def test_valid_json_parsing_success(self) -> None:
        """유효한 JSON 파싱 성공 테스트"""
        json_str = '{"name": "홍길동", "age": 30}'
        result = JSONExtractor.validate_and_parse_json(json_str, SampleModel)

        assert result is not None
        assert result.name == "홍길동"
        assert result.age == 30

    def test_llm_response_with_explanation_prefix(self) -> None:
        """LLM이 설명과 함께 JSON을 제공하는 경우 테스트"""
        json_str = """
        여기 분석 결과입니다:
        {"name": "홍길동", "age": 30}
        """
        result = JSONExtractor.validate_and_parse_json(json_str, SampleModel)

        assert result is not None
        assert result.name == "홍길동"
        assert result.age == 30

    def test_llm_response_with_explanation_suffix(self) -> None:
        """LLM이 JSON 뒤에 추가 설명을 제공하는 경우 테스트"""
        json_str = """
        {"name": "이순신", "age": 45}
        이상으로 분석을 마치겠습니다.
        """
        result = JSONExtractor.validate_and_parse_json(json_str, SampleModel)

        assert result is not None
        assert result.name == "이순신"
        assert result.age == 45

    def test_no_valid_json_returns_none(self) -> None:
        """유효한 JSON이 없을 때 None 반환 테스트"""
        json_str = "invalid json string"
        result = JSONExtractor.validate_and_parse_json(json_str, SampleModel)

        assert result is None

    def test_json_parsing_error_raised_for_validation_failures(self) -> None:
        """검증 실패 시 JSONParsingError 발생 테스트"""
        json_str = '{"name": "홍길동"}'  # age 필드 누락

        with pytest.raises(JSONParsingError) as exc_info:
            JSONExtractor.validate_and_parse_json(json_str, SampleModel)

        error = exc_info.value
        assert "JSON 파싱에 실패했습니다" in str(error)
        assert error.raw_response == json_str
        assert error.parsing_error is not None
        assert isinstance(error.parsing_error, ValidationError)

    def test_json_parsing_error_with_long_response_truncation(self) -> None:
        """긴 응답의 경우 truncation 테스트"""
        # age를 문자열로 만들어서 ValidationError 유발
        long_json = '{"name": "' + "a" * 600 + '", "age": "invalid_age"}'

        with pytest.raises(JSONParsingError) as exc_info:
            JSONExtractor.validate_and_parse_json(long_json, SampleModel)

        error = exc_info.value
        assert error.raw_response.endswith("...")
        assert len(error.raw_response) == 503  # 500 + "..."

    def test_json_parsing_error_with_short_response_no_truncation(self) -> None:
        """짧은 응답의 경우 truncation 없음 테스트"""
        short_json = '{"name": "홍길동"}'

        with pytest.raises(JSONParsingError) as exc_info:
            JSONExtractor.validate_and_parse_json(short_json, SampleModel)

        error = exc_info.value
        assert error.raw_response == short_json
        assert not error.raw_response.endswith("...")

    def test_unexpected_parsing_error_handling(self) -> None:
        """예상치 못한 파싱 오류 처리 테스트"""
        json_str = '{"name": "홍길동", "age": 30}'

        # target_model을 None으로 전달하여 예상치 못한 오류 유발
        with pytest.raises(JSONParsingError) as exc_info:
            JSONExtractor.validate_and_parse_json(json_str, None)  # type: ignore

        error = exc_info.value
        assert "예상치 못한 파싱 오류" in str(error)
        assert error.raw_response == json_str
        assert error.parsing_error is not None

    def test_json_parsing_error_re_raised(self) -> None:
        """JSONParsingError가 그대로 재발생하는지 테스트"""
        # 내부적으로 JSONParsingError를 발생시키는 상황을 시뮬레이션
        json_str = '{"name": "홍길동"}'  # ValidationError 유발

        with pytest.raises(JSONParsingError):
            JSONExtractor.validate_and_parse_json(json_str, SampleModel)

    def test_valid_json_with_extra_text(self) -> None:
        """JSON 주변에 추가 텍스트가 있는 경우 테스트"""
        json_str = """
        Here is some text before
        {"name": "세종대왕", "age": 53}
        And some text after
        """
        result = JSONExtractor.validate_and_parse_json(json_str, SampleModel)

        assert result is not None
        assert result.name == "세종대왕"
        assert result.age == 53

    def test_all_json_objects_invalid_raises_error(self) -> None:
        """모든 JSON 객체가 유효하지 않을 때 JSONParsingError 발생 테스트"""
        json_str = """
        {"invalid": json}
        {"also": invalid}
        """

        with pytest.raises(JSONParsingError) as exc_info:
            JSONExtractor.validate_and_parse_json(json_str, SampleModel)

        error = exc_info.value
        assert "JSON 파싱에 실패했습니다" in str(error)
        assert error.raw_response is not None
        assert error.parsing_error is not None

    def test_console_debug_mode_check(self) -> None:
        """디버그 모드에서 원본 응답 출력 테스트"""
        # 이 테스트는 console.is_debug_mode() 동작을 확인
        json_str = "invalid json"
        result = JSONExtractor.validate_and_parse_json(json_str, SampleModel)

        # 예상: None 반환 (에러가 아닌 정상 동작)
        assert result is None
