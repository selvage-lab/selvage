"""
에러 패턴 기반 파서 모듈

실제 수집된 LLM provider 에러 데이터를 기반으로 구성된 패턴을 사용하여
에러를 분석하고 구조화된 정보를 추출합니다.
"""

import importlib.resources
import json
import re
from typing import Any, NamedTuple

import yaml


class TokenInfo(NamedTuple):
    """토큰 정보를 담는 클래스"""

    actual_tokens: int | None = None
    max_tokens: int | None = None


class ErrorParsingResult(NamedTuple):
    """에러 파싱 결과를 담는 클래스"""

    error_type: str
    error_code: str | None = None
    http_status_code: int | None = None
    token_info: TokenInfo | None = None
    matched_pattern: str | None = None
    additional_token_info: dict[str, Any] = {}


class ErrorPatternParser:
    """에러 패턴을 사용하여 에러를 파싱하는 클래스"""

    def __init__(self) -> None:
        """
        Args:
            patterns_file: 패턴 설정 파일 경로. None인 경우 패키지 리소스에서 로드
        """
        self._patterns: dict[str, Any] | None = None
        self._load_patterns()

    def _load_patterns(self) -> None:
        """패턴 설정 파일을 로드합니다."""
        try:
            # importlib.resources를 사용하여 패키지 리소스에서 로드
            file_ref = importlib.resources.files("selvage.resources").joinpath(
                "error_patterns.yml"
            )
            content = file_ref.read_text(encoding="utf-8")
            self._patterns = yaml.safe_load(content)
        except FileNotFoundError as e:
            msg = "패키지 리소스에서 error_patterns.yml을 찾을 수 없습니다"
            raise FileNotFoundError(msg) from e
        except yaml.YAMLError as e:
            raise ValueError(f"패턴 설정 파일 파싱 실패: {e}") from e

    def parse_error(self, provider: str, error: Exception) -> ErrorParsingResult:
        """
        에러를 분석하여 구조화된 정보를 추출합니다.

        Args:
            provider: LLM 프로바이더 이름
                ('openai', 'anthropic', 'google', 'openrouter')
            error: 분석할 에러 객체

        Returns:
            ErrorParsingResult: 파싱된 에러 정보
        """
        if not self._patterns:
            return ErrorParsingResult(error_type="parse_error")

        provider_patterns = self._patterns.get("providers", {}).get(provider, {})
        if not provider_patterns:
            return ErrorParsingResult(error_type="api_error")

        # OpenRouter의 경우 실제 JSON 응답에서 메시지 추출
        if provider == "openrouter":
            error_message = self._extract_openrouter_message(error)
        else:
            error_message = str(error)

        error_attrs = self._extract_error_attributes(error)

        # 패턴 우선순위에 따라 정렬
        patterns = provider_patterns.get("patterns", {})
        priorities = self._patterns.get("pattern_priorities", {})

        sorted_patterns = sorted(
            patterns.items(), key=lambda x: priorities.get(x[0], 0), reverse=True
        )

        # 각 패턴에 대해 매칭 시도
        for pattern_name, pattern_config in sorted_patterns:
            result = self._try_match_pattern(
                pattern_name, pattern_config, error_message, error_attrs
            )
            if result:
                return result

        # 매칭되는 패턴이 없는 경우 기본값 반환
        return ErrorParsingResult(error_type="api_error", additional_token_info={})

    def _extract_error_attributes(self, error: Exception) -> dict[str, Any]:
        """에러 객체에서 속성들을 추출합니다."""
        attrs = {}

        # HTTP 상태 코드 추출
        # (Anthropic: status_code 직접, OpenAI: response.status_code)
        if hasattr(error, "status_code"):
            attrs["http_status_code"] = error.status_code
        elif hasattr(error, "response") and hasattr(error.response, "status_code"):
            attrs["http_status_code"] = error.response.status_code

        # 에러 코드 추출 (여러 가지 방식 지원)
        if hasattr(error, "type"):
            attrs["error_code"] = error.type
        elif hasattr(error, "code"):
            attrs["error_code"] = error.code

        # Anthropic 에러에서 body 추출
        if hasattr(error, "body") and isinstance(error.body, dict):
            attrs["error_body"] = error.body
            if "error" in error.body and isinstance(error.body["error"], dict):
                error_info = error.body["error"]
                attrs["error_code"] = error_info.get("type", attrs.get("error_code"))

        # OpenAI 에러에서 response 추출
        if hasattr(error, "response"):
            try:
                response_data = error.response.json()
                if "error" in response_data and isinstance(
                    response_data["error"], dict
                ):
                    error_info = response_data["error"]
                    attrs["error_code"] = error_info.get(
                        "code", attrs.get("error_code")
                    )
            except (AttributeError, ValueError):
                pass

        return attrs

    def _extract_openrouter_message(self, error: Exception) -> str:
        """OpenRouter HTTPStatusError에서 실제 JSON 응답 메시지를 추출합니다."""
        try:
            # HTTPStatusError에서 response.text 추출 시도
            if hasattr(error, "response") and hasattr(error.response, "text"):
                response_text = error.response.text
                response_data = json.loads(response_text)

                # OpenRouter 응답 구조: {"error": {"message": "실제 메시지"}}
                if isinstance(response_data, dict) and "error" in response_data:
                    error_info = response_data["error"]
                    if isinstance(error_info, dict) and "message" in error_info:
                        return error_info["message"]

        except (AttributeError, json.JSONDecodeError, KeyError):
            pass

        # 추출 실패 시 기본 에러 메시지 반환
        return str(error)

    def _try_match_pattern(
        self,
        pattern_name: str,
        pattern_config: dict[str, Any],
        error_message: str,
        error_attrs: dict[str, Any],
    ) -> ErrorParsingResult | None:
        """특정 패턴과 에러 매칭을 시도합니다."""
        match_score = 0
        max_score = 0

        # 키워드 매칭 (선택적)
        keywords = pattern_config.get("keywords", [])
        if keywords:
            max_score += 1
            if any(keyword in error_message for keyword in keywords):
                match_score += 1

        # 에러 코드 매칭 (선택적)
        error_codes = pattern_config.get("error_codes", [])
        if error_codes:
            max_score += 1
            if error_attrs.get("error_code") in error_codes:
                match_score += 1

        # HTTP 상태 코드 매칭 (선택적)
        http_status_codes = pattern_config.get("http_status_codes", [])
        if http_status_codes:
            max_score += 1
            if error_attrs.get("http_status_code") in http_status_codes:
                match_score += 1

        # 메시지 패턴 매칭 (선택적이지만 점수가 높음)
        message_patterns = pattern_config.get("message_patterns", [])
        if message_patterns:
            max_score += 2  # 메시지 패턴은 더 높은 가중치
            for pattern_info in message_patterns:
                if isinstance(pattern_info, dict) and "regex" in pattern_info:
                    regex = pattern_info["regex"]
                    if re.search(regex, error_message):
                        match_score += 2
                        break

        # 매칭 조건: 점수가 있어야 하고, 키워드나 메시지 패턴 중 하나는 매칭되어야 함
        # 단, api_error 패턴은 catch-all이므로 예외
        if pattern_name == "api_error":
            # api_error는 항상 매칭 (catch-all)
            pass
        elif pattern_name == "context_limit_exceeded":
            # context_limit_exceeded는 메시지 패턴이 반드시 매칭되어야 함
            message_patterns = pattern_config.get("message_patterns", [])
            if message_patterns:
                message_matched = False
                for pattern_info in message_patterns:
                    if isinstance(pattern_info, dict) and "regex" in pattern_info:
                        regex = pattern_info["regex"]
                        if re.search(regex, error_message):
                            message_matched = True
                            break
                if not message_matched:
                    return None
            else:
                # 메시지 패턴이 정의되지 않은 context_limit_exceeded 패턴은 매칭 불가
                return None
        elif max_score == 0:
            # 매칭 조건이 없는 패턴은 매칭 안 함
            return None
        elif match_score == 0:
            # 매칭 조건이 있지만 하나도 매칭 안 됨
            return None

        # 메시지 패턴에서 토큰 정보 추출
        token_info, additional_token_info = self._extract_token_info(
            pattern_config, error_message
        )

        return ErrorParsingResult(
            error_type=pattern_config.get("error_type", "api_error"),
            error_code=error_attrs.get("error_code"),
            http_status_code=error_attrs.get("http_status_code"),
            token_info=token_info,
            matched_pattern=pattern_name,
            additional_token_info=additional_token_info,
        )

    def _extract_token_info(
        self, pattern_config: dict[str, Any], error_message: str
    ) -> tuple[TokenInfo | None, dict[str, Any]]:
        """메시지 패턴에서 토큰 정보를 추출합니다."""
        message_patterns = pattern_config.get("message_patterns", [])
        additional_token_info = {}

        for pattern_info in message_patterns:
            if isinstance(pattern_info, dict) and "regex" in pattern_info:
                regex = pattern_info["regex"]
                extract_config = pattern_info.get("extract_tokens", {})

                match = re.search(regex, error_message)
                if match:
                    token_info, additional = self._parse_token_groups(
                        match, extract_config
                    )
                    additional_token_info.update(additional)
                    return token_info, additional_token_info

        return None, additional_token_info

    def _parse_token_groups(
        self, match: re.Match, extract_config: dict[str, int]
    ) -> tuple[TokenInfo, dict[str, Any]]:
        """정규표현식 매치에서 토큰 수를 추출합니다."""
        actual_tokens = None
        max_tokens = None
        additional_info = {}

        # 실제 토큰 수 추출
        if "actual_tokens" in extract_config:
            group_idx = extract_config["actual_tokens"]
            try:
                token_str = match.group(group_idx)
                actual_tokens = self._clean_and_parse_number(token_str)
            except (IndexError, ValueError):
                pass

        # 최대 토큰 수 추출
        if "max_tokens" in extract_config:
            group_idx = extract_config["max_tokens"]
            try:
                token_str = match.group(group_idx)
                max_tokens = self._clean_and_parse_number(token_str)
            except (IndexError, ValueError):
                pass

        # 추가 토큰 정보 추출 (max_tokens_param, total_limit 등)
        for field_name, group_idx in extract_config.items():
            if field_name not in ["actual_tokens", "max_tokens"]:
                try:
                    token_str = match.group(group_idx)
                    additional_info[field_name] = self._clean_and_parse_number(
                        token_str
                    )
                except (IndexError, ValueError):
                    pass

        return TokenInfo(
            actual_tokens=actual_tokens, max_tokens=max_tokens
        ), additional_info

    def _clean_and_parse_number(self, number_str: str) -> int:
        """숫자 문자열에서 쉼표를 제거하고 정수로 변환합니다."""
        clean_str = number_str.replace(",", "")
        return int(clean_str)

    def get_supported_providers(self) -> list[str]:
        """지원되는 프로바이더 목록을 반환합니다."""
        if not self._patterns:
            return []
        return list(self._patterns.get("providers", {}).keys())

    def get_pattern_info(
        self, provider: str, pattern_name: str
    ) -> dict[str, Any] | None:
        """특정 프로바이더의 패턴 정보를 반환합니다."""
        if not self._patterns:
            return None

        provider_patterns = self._patterns.get("providers", {}).get(provider, {})
        return provider_patterns.get("patterns", {}).get(pattern_name)
