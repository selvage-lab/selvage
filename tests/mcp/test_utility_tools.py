"""MCP 유틸리티 도구 테스트"""

from unittest.mock import Mock, patch

import pytest


class TestUtilityToolsRegistration:
    """MCP 유틸리티 도구 등록 테스트"""

    def test_register_utility_tools_function_exists(self) -> None:
        """register_utility_tools 함수가 존재해야 함"""
        try:
            from selvage.src.mcp.tools.utility_tools import register_utility_tools

            assert callable(register_utility_tools)
        except ImportError:
            pytest.skip("utility_tools not implemented yet")

    @patch("selvage.src.mcp.tools.utility_tools.FastMCP")
    def test_register_utility_tools_registers_all_tools(
        self, mock_fastmcp: Mock
    ) -> None:
        """register_utility_tools가 모든 도구를 등록해야 함"""
        try:
            from selvage.src.mcp.tools.utility_tools import register_utility_tools
        except ImportError:
            pytest.skip("utility_tools not implemented yet")

        mock_mcp_instance = Mock()
        mock_fastmcp.return_value = mock_mcp_instance

        register_utility_tools(mock_mcp_instance)

        # tool 데코레이터가 6번 호출되어야 함 (6개 유틸리티 도구)
        assert mock_mcp_instance.tool.call_count == 6


class TestGetAvailableModels:
    """get_available_models 도구 테스트"""

    def test_get_available_models_function_exists(self) -> None:
        """get_available_models 함수가 존재해야 함"""
        try:
            from selvage.src.mcp.tools.utility_tools import get_available_models

            assert callable(get_available_models)
        except ImportError:
            pytest.skip("get_available_models not implemented yet")

    @patch("selvage.src.mcp.tools.utility_tools.ModelConfig")
    def test_get_available_models_returns_model_list(
        self, mock_config_class: Mock
    ) -> None:
        """get_available_models가 ModelInfo 리스트를 반환해야 함"""
        try:
            from selvage.src.mcp.tools.utility_tools import get_available_models
        except ImportError:
            pytest.skip("get_available_models not implemented yet")

        from selvage.src.mcp.models.responses import ModelInfo

        # Mock 설정
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        mock_config.get_all_models_config.return_value = {
            "claude-sonnet-4.5-20250929": {
                "name": "claude-sonnet-4.5-20250929",
                "provider": "anthropic",
                "display_name": "Claude Sonnet 4",
                "description": "High-performance reasoning model",
                "cost_per_1k_tokens": 0.003,
                "max_tokens": 200000,
                "supports_function_calling": True,
            },
            "gpt-4o": {
                "name": "gpt-4o",
                "provider": "openai",
                "display_name": "GPT-4o",
                "description": "OpenAI's latest model",
                "cost_per_1k_tokens": 0.005,
                "max_tokens": 128000,
                "supports_function_calling": True,
            },
        }

        # 실행
        result = get_available_models()

        # 검증
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(model, ModelInfo) for model in result)
        assert result[0].name == "claude-sonnet-4.5-20250929"
        assert result[1].name == "gpt-4o"


class TestGetReviewHistory:
    """get_review_history 도구 테스트"""

    def test_get_review_history_function_exists(self) -> None:
        """get_review_history 함수가 존재해야 함"""
        try:
            from selvage.src.mcp.tools.utility_tools import get_review_history

            assert callable(get_review_history)
        except ImportError:
            pytest.skip("get_review_history not implemented yet")

    @patch("selvage.src.mcp.tools.utility_tools.ReviewLogManager")
    def test_get_review_history_returns_history_list(
        self, mock_log_manager: Mock
    ) -> None:
        """get_review_history가 ReviewHistoryItem 리스트를 반환해야 함"""
        try:
            from selvage.src.mcp.tools.utility_tools import get_review_history
        except ImportError:
            pytest.skip("get_review_history not implemented yet")

        from datetime import datetime

        from selvage.src.mcp.models.responses import ReviewHistoryItem

        # Mock 설정
        mock_log_manager.get_recent_logs.return_value = [
            {
                "log_id": "log-123",
                "timestamp": datetime.now().isoformat(),
                "model": "claude-sonnet-4.5-20250929",
                "files_count": 3,
                "status": "SUCCESS",
                "cost": 0.05,
                "review_type": "current",
                "target": None,
            },
            {
                "log_id": "log-456",
                "timestamp": datetime.now().isoformat(),
                "model": "gpt-4o",
                "files_count": 5,
                "status": "SUCCESS",
                "cost": 0.10,
                "review_type": "branch",
                "target": "main",
            },
        ]

        # 실행
        result = get_review_history(limit=10, repo_path=".", model_filter=None)

        # 검증
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, ReviewHistoryItem) for item in result)
        assert result[0].log_id == "log-123"
        assert result[1].log_id == "log-456"

    def test_get_review_history_parameter_validation(self) -> None:
        """get_review_history 파라미터 검증 테스트"""
        try:
            from selvage.src.mcp.tools.utility_tools import get_review_history
        except ImportError:
            pytest.skip("get_review_history not implemented yet")

        # limit 파라미터는 기본값이 있음
        with patch(
            "selvage.src.mcp.tools.utility_tools.ReviewLogManager"
        ) as mock_log_manager:
            mock_log_manager.get_recent_logs.return_value = []
            result = get_review_history()
            assert isinstance(result, list)


class TestGetReviewDetails:
    """get_review_details 도구 테스트"""

    def test_get_review_details_function_exists(self) -> None:
        """get_review_details 함수가 존재해야 함"""
        try:
            from selvage.src.mcp.tools.utility_tools import get_review_details

            assert callable(get_review_details)
        except ImportError:
            pytest.skip("get_review_details not implemented yet")

    @patch("selvage.src.mcp.tools.utility_tools.ReviewLogManager")
    def test_get_review_details_returns_review_details_result(
        self, mock_log_manager: Mock
    ) -> None:
        """get_review_details가 ReviewDetailsResult를 반환해야 함"""
        try:
            from selvage.src.mcp.tools.utility_tools import get_review_details
        except ImportError:
            pytest.skip("get_review_details not implemented yet")

        from selvage.src.mcp.models.responses import ReviewDetailsResult

        # Mock 설정
        mock_log_manager.load_log.return_value = {
            "log_id": "log-123",
            "review_request": {"model": "claude-sonnet-4.5-20250929", "repo_path": "."},
            "review_response": {"content": "Good code quality"},
            "estimated_cost": {"total_cost": 0.05},
            "timestamp": "2024-01-01T00:00:00",
            "status": "SUCCESS",
        }

        # 실행
        result = get_review_details("log-123")

        # 검증
        assert isinstance(result, ReviewDetailsResult)
        assert result.success is True
        assert result.data is not None
        assert result.data["content"] == "Good code quality"
        assert result.error_message is None

    def test_get_review_details_requires_log_id(self) -> None:
        """get_review_details가 log_id 파라미터를 필요로 해야 함"""
        try:
            from selvage.src.mcp.tools.utility_tools import get_review_details
        except ImportError:
            pytest.skip("get_review_details not implemented yet")

        with pytest.raises(TypeError):
            get_review_details()  # log_id 누락


class TestGetServerStatus:
    """get_server_status 도구 테스트"""

    def test_get_server_status_function_exists(self) -> None:
        """get_server_status 함수가 존재해야 함"""
        try:
            from selvage.src.mcp.tools.utility_tools import get_server_status

            assert callable(get_server_status)
        except ImportError:
            pytest.skip("get_server_status not implemented yet")

    def test_get_server_status_returns_server_status(self) -> None:
        """get_server_status가 ServerStatus를 반환해야 함"""
        try:
            from selvage.src.mcp.tools.utility_tools import get_server_status
        except ImportError:
            pytest.skip("get_server_status not implemented yet")

        from selvage.src.mcp.models.responses import ServerStatus

        # 실행
        result = get_server_status()

        # 검증
        assert isinstance(result, ServerStatus)
        assert result.running is True
        assert isinstance(result.version, str)
        assert isinstance(result.tools_count, int)


class TestValidateModelSupport:
    """validate_model_support 도구 테스트"""

    def test_validate_model_support_function_exists(self) -> None:
        """validate_model_support 함수가 존재해야 함"""
        from selvage.src.mcp.tools.utility_tools import validate_model_support

        assert callable(validate_model_support)

    @patch("selvage.src.mcp.tools.utility_tools.get_model_info")
    def test_validate_model_support_valid_model(
        self, mock_get_model_info: Mock
    ) -> None:
        """validate_model_support가 유효한 모델에 대해 올바른 결과를 반환해야 함"""
        from selvage.src.mcp.tools.utility_tools import validate_model_support
        from selvage.src.mcp.models.responses import ModelValidationResult

        # Mock 설정
        mock_get_model_info.return_value = {
            "provider": "anthropic",
            "name": "claude-sonnet-4.5-20250929",
        }

        # 실행
        result = validate_model_support("claude-sonnet-4.5-20250929")

        # 검증
        assert isinstance(result, ModelValidationResult)
        assert result.valid is True
        assert result.model == "claude-sonnet-4.5-20250929"
        assert result.provider == "Anthropic"

    @patch("selvage.src.mcp.tools.utility_tools.get_model_info")
    def test_validate_model_support_invalid_model(
        self, mock_get_model_info: Mock
    ) -> None:
        """validate_model_support가 무효한 모델에 대해 올바른 결과를 반환해야 함"""
        from selvage.src.mcp.tools.utility_tools import validate_model_support
        from selvage.src.mcp.models.responses import ModelValidationResult

        # Mock 설정
        mock_get_model_info.return_value = None

        # 실행
        result = validate_model_support("invalid-model")

        # 검증
        assert isinstance(result, ModelValidationResult)
        assert result.valid is False
        assert result.error_message is not None


class TestValidateApiKeyForProvider:
    """validate_api_key_for_provider 도구 테스트"""

    def test_validate_api_key_for_provider_function_exists(self) -> None:
        """validate_api_key_for_provider 함수가 존재해야 함"""
        from selvage.src.mcp.tools.utility_tools import validate_api_key_for_provider

        assert callable(validate_api_key_for_provider)

    @patch("selvage.src.mcp.tools.utility_tools.has_openrouter_api_key")
    @patch("selvage.src.mcp.tools.utility_tools.get_api_key")
    @patch("selvage.src.mcp.tools.utility_tools.get_model_info")
    def test_validate_api_key_for_provider_valid_key(
        self, mock_get_model_info: Mock, mock_get_api_key: Mock, mock_has_openrouter: Mock
    ) -> None:
        """validate_api_key_for_provider가 유효한 API 키에 대해 올바른 결과를 반환해야 함"""
        from selvage.src.mcp.tools.utility_tools import validate_api_key_for_provider
        from selvage.src.mcp.models.responses import ApiKeyValidationResult

        # Mock 설정
        mock_get_model_info.return_value = {
            "provider": "anthropic",
            "name": "claude-sonnet-4.5-20250929",
        }
        mock_has_openrouter.return_value = False  # OpenRouter 키 없음
        mock_get_api_key.return_value = "test-api-key"

        # 실행
        result = validate_api_key_for_provider("claude-sonnet-4.5-20250929")

        # 검증
        assert isinstance(result, ApiKeyValidationResult)
        assert result.valid is True
        assert result.provider == "Anthropic"
        assert result.api_key_configured is True

    @patch("selvage.src.mcp.tools.utility_tools.has_openrouter_api_key")
    @patch("selvage.src.mcp.tools.utility_tools.get_api_key")
    @patch("selvage.src.mcp.tools.utility_tools.get_model_info")
    def test_validate_api_key_for_provider_missing_key(
        self, mock_get_model_info: Mock, mock_get_api_key: Mock, mock_has_openrouter: Mock
    ) -> None:
        """validate_api_key_for_provider가 누락된 API 키에 대해 올바른 결과를 반환해야 함"""
        from selvage.src.mcp.tools.utility_tools import validate_api_key_for_provider
        from selvage.src.mcp.models.responses import ApiKeyValidationResult

        # Mock 설정
        mock_get_model_info.return_value = {
            "provider": "anthropic",
            "name": "claude-sonnet-4.5-20250929",
        }
        mock_has_openrouter.return_value = False  # OpenRouter 키 없음
        mock_get_api_key.return_value = None

        # 실행
        result = validate_api_key_for_provider("claude-sonnet-4.5-20250929")

        # 검증
        assert isinstance(result, ApiKeyValidationResult)
        assert result.valid is False
        assert result.api_key_configured is False
        assert result.error_message is not None

    def test_validate_api_key_for_provider_invalid_model(self) -> None:
        """validate_api_key_for_provider가 무효한 모델에 대해 올바른 결과를 반환해야 함"""
        from selvage.src.mcp.tools.utility_tools import validate_api_key_for_provider
        from selvage.src.mcp.models.responses import ApiKeyValidationResult

        # 실행
        result = validate_api_key_for_provider("invalid-model")

        # 검증
        assert isinstance(result, ApiKeyValidationResult)
        assert result.valid is False
        assert result.error_message is not None

    @patch("selvage.src.mcp.tools.utility_tools.has_openrouter_api_key")
    @patch("selvage.src.mcp.tools.utility_tools.get_api_key")
    @patch("selvage.src.mcp.tools.utility_tools.get_model_info")
    def test_validate_api_key_for_provider_openrouter_first(
        self, mock_get_model_info: Mock, mock_get_api_key: Mock, mock_has_openrouter: Mock
    ) -> None:
        """OpenRouter 키가 있으면 OpenRouter를 우선 사용해야 함"""
        from selvage.src.mcp.tools.utility_tools import validate_api_key_for_provider
        from selvage.src.mcp.models.responses import ApiKeyValidationResult

        # Mock 설정
        mock_get_model_info.return_value = {
            "provider": "anthropic",  # 원래 프로바이더는 anthropic
            "name": "claude-sonnet-4.5-20250929",
        }
        mock_has_openrouter.return_value = True  # OpenRouter 키 있음
        mock_get_api_key.return_value = "openrouter-api-key"

        # 실행
        result = validate_api_key_for_provider("claude-sonnet-4.5-20250929")

        # 검증
        assert isinstance(result, ApiKeyValidationResult)
        assert result.valid is True
        assert result.provider == "OpenRouter"  # anthropic이 아닌 OpenRouter 사용
        assert result.api_key_configured is True


class TestUtilityToolsIntegration:
    """MCP 유틸리티 도구 통합 테스트"""

    def test_utility_tools_import_existing_functions(self) -> None:
        """기존 selvage 함수들을 올바르게 import할 수 있는지 테스트"""
        import subprocess
        import sys

        script = """
try:
    from selvage.src.model_config import get_model_info, ModelConfig
    from selvage.src.config import get_api_key
    from selvage.src.utils.logging.review_log_manager import ReviewLogManager
    print("import_success")
except ImportError as e:
    print(f"import_error: {e}")
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == "import_success"
