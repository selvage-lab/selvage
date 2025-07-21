"""OpenRouter HTTP 클라이언트

OpenRouter API와의 HTTP 통신을 담당하는 클라이언트를 제공합니다.
"""

from typing import Any

import httpx

from selvage.src.utils.base_console import console


class OpenRouterHTTPClient:
    """OpenRouter API를 위한 사용자 정의 HTTP 클라이언트"""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.client = httpx.Client(
            timeout=httpx.Timeout(60.0),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    def create_completion(self, **params: Any) -> dict[str, Any]:
        """OpenRouter API에 요청을 보내고 응답을 반환합니다."""
        url = f"{self.base_url}/chat/completions"

        try:
            response = self.client.post(url, json=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            console.error(f"OpenRouter API 호출 오류: {e}")
            raise
        except httpx.RequestError as e:
            console.error(f"OpenRouter API 네트워크 오류: {e}")
            raise

    def close(self) -> None:
        """HTTP 클라이언트 연결을 명시적으로 종료합니다."""
        if hasattr(self, "client") and not self.client.is_closed:
            self.client.close()

    def __enter__(self) -> "OpenRouterHTTPClient":
        """컨텍스트 매니저 진입점"""
        return self

    def __exit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: object | None) -> None:
        """컨텍스트 매니저 종료점 - 리소스 정리"""
        self.close()