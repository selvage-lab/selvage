"""MCP 서버 통합 도구 등록 테스트"""

from unittest.mock import patch


class TestUnifiedToolRegistration:
    """모든 도구가 항상 등록되는지 테스트"""

    @patch("selvage.src.mcp.server._setup_mcp_environment")
    def test_all_tools_always_registered(self, _mock_setup) -> None:
        """context + review + utility 도구가 모두 등록되는지 확인"""
        from selvage.src.mcp.server import SelvageMCPServer

        server = SelvageMCPServer()
        info = server.get_tools_info()

        assert len(info["context_tools"]) == 2
        assert "get_review_context" in info["context_tools"]
        assert "get_file_review_context" in info["context_tools"]

        assert len(info["review_tools"]) == 1
        assert "review_changes" in info["review_tools"]

        assert len(info["utility_tools"]) == 6

    @patch("selvage.src.mcp.server._setup_mcp_environment")
    def test_no_mode_parameter(self, _mock_setup) -> None:
        """SelvageMCPServer()에 mode 파라미터 없이 정상 생성"""
        from selvage.src.mcp.server import SelvageMCPServer

        server = SelvageMCPServer()
        assert server.name == "Selvage Code Review Server"

    @patch("selvage.src.mcp.server._setup_mcp_environment")
    def test_get_tools_info_no_mode_field(self, _mock_setup) -> None:
        """get_tools_info에 mode 필드가 없는지 확인"""
        from selvage.src.mcp.server import SelvageMCPServer

        server = SelvageMCPServer()
        info = server.get_tools_info()

        assert "mode" not in info

    @patch("selvage.src.mcp.server._setup_mcp_environment")
    def test_utility_tools_always_registered(self, _mock_setup) -> None:
        """utility 도구 6개가 등록되는지 확인"""
        from selvage.src.mcp.server import SelvageMCPServer

        server = SelvageMCPServer()
        info = server.get_tools_info()

        expected_utility_tools = [
            "get_available_models",
            "get_review_history",
            "get_review_details",
            "get_server_status",
            "validate_model_support",
            "validate_api_key_for_provider",
        ]
        assert info["utility_tools"] == expected_utility_tools
