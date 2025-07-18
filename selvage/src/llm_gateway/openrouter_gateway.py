"""
OpenRouter 게이트웨이 구현입니다.

이 파일은 기존 import 경로 호환성을 위해 유지됩니다.
실제 구현은 openrouter 패키지 내부로 이동되었습니다.
"""

# 기존 import 경로 호환성을 위한 re-export
from selvage.src.llm_gateway.openrouter import OpenRouterGateway

__all__ = ["OpenRouterGateway"]
