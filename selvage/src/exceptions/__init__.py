"""
예외 클래스들을 정의하는 패키지입니다.
"""

from selvage.src.exceptions.api_key_not_found_error import APIKeyNotFoundError
from selvage.src.exceptions.context_extraction_error import (
    ContextExtractionError,
    TreeSitterError,
    UnsupportedLanguageError,
)
from selvage.src.exceptions.context_limit_exceeded_error import (
    ContextLimitExceededError,
)
from selvage.src.exceptions.diff_parsing_error import DiffParsingError
from selvage.src.exceptions.invalid_api_key_error import InvalidAPIKeyError
from selvage.src.exceptions.invalid_model_provider_error import (
    InvalidModelProviderError,
)
from selvage.src.exceptions.llm_gateway_error import LLMGatewayError
from selvage.src.exceptions.unsupported_model_error import UnsupportedModelError
from selvage.src.exceptions.unsupported_provider_error import UnsupportedProviderError

__all__ = [
    "LLMGatewayError",
    "APIKeyNotFoundError",
    "InvalidModelProviderError",
    "UnsupportedModelError",
    "UnsupportedProviderError",
    "DiffParsingError",
    "ContextLimitExceededError",
    "InvalidAPIKeyError",
    "ContextExtractionError",
    "UnsupportedLanguageError",
    "TreeSitterError",
]
