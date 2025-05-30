"""JSON 추출을 위한 유틸리티 함수들"""

import json
import re
from typing import TypeVar

import pydantic
from pydantic import BaseModel

from selvage.src.utils.base_console import console

JSON_PATTERN = r"\{[\s\S]*\}"
T = TypeVar("T", bound=BaseModel)


class JSONExtractor:
    """JSON 추출을 위한 유틸리티 클래스"""

    @staticmethod
    def validate_and_parse_json(json_str: str, target_model: type[T]) -> T | None:
        """JSON 문자열을 검증하고 지정된 모델로 파싱합니다.

        Args:
            json_str: JSON 문자열
            target_model: 파싱할 대상 모델 클래스

        Returns:
            Any | None: 파싱된 객체 또는 None
        """
        try:
            json_matches = re.findall(JSON_PATTERN, json_str)

            structured_response = None
            for json_text in json_matches:
                try:
                    # JSON 유효성 검사
                    json.loads(json_text)
                    structured_response = target_model.model_validate_json(json_text)
                    break
                except (json.JSONDecodeError, ValueError, pydantic.ValidationError):
                    console.error(f"JSON 파싱 오류: {str(json_text)}")
                    continue

            if structured_response is None:
                console.warning("입력 문자열에서 유효한 JSON을 찾을 수 없습니다.")
                return None
        except Exception as parse_error:
            console.error(f"파싱 오류: {str(parse_error)}", exception=parse_error)
            console.error(f"원본 응답: {json_str}")
            return None
        return structured_response
