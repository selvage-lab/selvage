"""OpenRouter HTTP 클라이언트

OpenRouter API와의 HTTP 통신을 담당하는 클라이언트를 제공합니다.
"""

import json
from typing import Any

import httpx

from selvage.src.exceptions.json_parsing_error import JSONParsingError
from selvage.src.models.error_pattern_parser import (
    ErrorParsingResult,
    ErrorPatternParser,
)
from selvage.src.models.model_provider import ModelProvider
from selvage.src.utils.base_console import console

# OpenRouter API 요청 파라미터 타입
RequestParams = dict[str, Any]


class OpenRouterHTTPClient:
    """OpenRouter API를 위한 사용자 정의 HTTP 클라이언트"""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.error_parser = ErrorPatternParser()
        self.base_url = "https://openrouter.ai/api/v1"
        self.client = httpx.Client(
            timeout=httpx.Timeout(60.0),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://selvage.me",
                "X-Title": "Selvage",
            },
        )

    def create_completion(self, **params: RequestParams) -> dict[str, Any]:
        """OpenRouter API에 요청을 보내고 응답을 반환합니다.

        Args:
            **params: OpenRouter API 요청 파라미터 (RequestParams 타입)

        Returns:
            dict[str, Any]: API 응답 데이터
        """
        url = f"{self.base_url}/chat/completions"

        try:
            response = self.client.post(url, json=params)
            response.raise_for_status()

            # JSON 파싱 시도
            try:
                return response.json()
            except json.JSONDecodeError as json_error:  # JSON 파싱 에러
                console.error(
                    f"OpenRouter API 응답이 유효한 JSON이 아닙니다: {json_error}"
                )
                if console.is_debug_mode():
                    console.error(f"응답 상태코드: {response.status_code}")
                    console.error(f"응답 헤더: {response.headers}")
                    console.error(f"응답 내용 (처음 1000자): {response.text[:1000]}")

                # JSON 파싱 에러도 에러 패턴 분석으로 처리
                try:
                    error_result = self.error_parser.parse_error(
                        ModelProvider.OPENROUTER, json_error
                    )
                    self._handle_structured_error(error_result)
                except Exception as parse_error:
                    console.debug(f"JSON 파싱 에러 패턴 분석 실패: {parse_error}")

                raise JSONParsingError.from_parsing_exception(
                    json_error,
                    "OpenRouter API 응답이 유효한 JSON이 아닙니다",
                    response.text,
                ) from json_error
        except httpx.HTTPStatusError as e:
            error_detail = "응답 내용 없음"
            try:
                if hasattr(e.response, "text"):
                    error_detail = e.response.text
            except Exception as inner_e:
                console.debug(f"응답 텍스트 추출 실패: {inner_e}")

            console.error(f"OpenRouter API 호출 오류: {e}")
            console.error(f"응답 내용: {error_detail}")

            # 에러 패턴 분석을 통한 구조화된 에러 처리
            try:
                error_result = self.error_parser.parse_error(
                    ModelProvider.OPENROUTER, e
                )
                self._handle_structured_error(error_result)
            except Exception as parse_error:
                console.debug(f"에러 패턴 분석 실패: {parse_error}")

            raise
        except httpx.RequestError as e:
            console.error(f"OpenRouter API 네트워크 오류: {e}")
            raise

    def _handle_structured_error(self, error_result: ErrorParsingResult) -> None:
        """구조화된 에러 결과를 기반으로 사용자 친화적인 메시지를 출력합니다."""
        if error_result.error_type == "byok_required":
            console.error("\n[BYOK 필수 모델 감지]")
            console.error(
                "이 모델은 OpenRouter에서 BYOK(Bring Your Own Key)가 필요합니다."
            )
            console.error("해결 방법:")
            console.error(
                "1. OpenRouter BYOK 설정: https://openrouter.ai/settings/integrations"
            )
            console.error("2. OPENAI_API_KEY 환경변수 설정하여 직접 OpenAI 사용")

            # 대안 모델 제안 (패턴에서 추출된 경우)
            if error_result.additional_token_info:
                alt1 = error_result.additional_token_info.get("alternative_model_1")
                alt2 = error_result.additional_token_info.get("alternative_model_2")
                if alt1 or alt2:
                    console.error("3. 대안 모델 사용:")
                    if alt1:
                        console.error(f"   - {alt1}")
                    if alt2:
                        console.error(f"   - {alt2}")

        elif error_result.error_type == "context_limit_exceeded":
            console.error("\n[컨텍스트 한계 초과]")
            if error_result.token_info:
                if error_result.token_info.max_tokens:
                    console.error(
                        f"최대 토큰 수: {error_result.token_info.max_tokens:,}"
                    )
                if error_result.token_info.actual_tokens:
                    console.error(
                        f"요청된 토큰 수: {error_result.token_info.actual_tokens:,}"
                    )

    def close(self) -> None:
        """HTTP 클라이언트 연결을 명시적으로 종료합니다."""
        if hasattr(self, "client") and not self.client.is_closed:
            self.client.close()

    def __enter__(self) -> "OpenRouterHTTPClient":
        """컨텍스트 매니저 진입점"""
        return self

    def __exit__(
        self, exc_type: type | None, exc_val: Exception | None, exc_tb: object | None
    ) -> None:
        """컨텍스트 매니저 종료점 - 리소스 정리"""
        self.close()
