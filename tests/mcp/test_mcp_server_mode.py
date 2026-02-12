"""MCP 서버 모드별 도구 등록 테스트"""

import os
from unittest.mock import patch

import pytest

from selvage.src.mcp.server import _has_any_api_key


class TestServerModeToolRegistration:
    """서버 모드에 따른 도구 등록 테스트"""

    @patch("selvage.src.mcp.server._setup_mcp_environment")
    @patch.dict(os.environ, {}, clear=True)
    def test_auto_mode_without_api_keys(self, _mock_setup) -> None:
        """auto 모드 + API 키 없음 -> context 도구만 등록"""
        from selvage.src.mcp.server import SelvageMCPServer

        server = SelvageMCPServer(mode="auto")
        info = server.get_tools_info()

        assert "get_review_context" in info["context_tools"]
        assert info["review_tools"] == []

    @patch("selvage.src.mcp.server._setup_mcp_environment")
    @patch.dict(
        os.environ,
        {"ANTHROPIC_API_KEY": "test-key"},
        clear=False,
    )
    def test_auto_mode_with_api_key(self, _mock_setup) -> None:
        """auto 모드 + API 키 있음 -> 모든 도구 등록"""
        from selvage.src.mcp.server import SelvageMCPServer

        server = SelvageMCPServer(mode="auto")
        info = server.get_tools_info()

        assert len(info["review_tools"]) == 4
        assert "get_review_context" in info["context_tools"]

    @patch("selvage.src.mcp.server._setup_mcp_environment")
    def test_agent_mode(self, _mock_setup) -> None:
        """agent 모드 -> context 도구만 등록"""
        from selvage.src.mcp.server import SelvageMCPServer

        server = SelvageMCPServer(mode="agent")
        info = server.get_tools_info()

        assert info["review_tools"] == []
        assert "get_review_context" in info["context_tools"]

    @patch("selvage.src.mcp.server._setup_mcp_environment")
    def test_independent_mode(self, _mock_setup) -> None:
        """independent 모드 -> review 도구만 등록"""
        from selvage.src.mcp.server import SelvageMCPServer

        server = SelvageMCPServer(mode="independent")
        info = server.get_tools_info()

        assert len(info["review_tools"]) == 4
        assert info["context_tools"] == []

    @patch("selvage.src.mcp.server._setup_mcp_environment")
    def test_default_mode_is_auto(self, _mock_setup) -> None:
        """기본 모드는 auto"""
        from selvage.src.mcp.server import SelvageMCPServer

        server = SelvageMCPServer()
        assert server.mode == "auto"

    def test_invalid_mode_raises_error(self) -> None:
        """잘못된 모드는 ValueError 발생"""
        from selvage.src.mcp.server import SelvageMCPServer

        with pytest.raises(ValueError, match="Invalid mode"):
            SelvageMCPServer(mode="invalid")

    @patch("selvage.src.mcp.server._setup_mcp_environment")
    def test_get_tools_info_includes_mode(self, _mock_setup) -> None:
        """get_tools_info에 mode 필드가 포함되는지 테스트"""
        from selvage.src.mcp.server import SelvageMCPServer

        server = SelvageMCPServer(mode="agent")
        info = server.get_tools_info()

        assert info["mode"] == "agent"

    @patch("selvage.src.mcp.server._setup_mcp_environment")
    def test_utility_tools_always_registered(self, _mock_setup) -> None:
        """utility 도구는 모든 모드에서 등록"""
        from selvage.src.mcp.server import SelvageMCPServer

        for mode in ("auto", "agent", "independent"):
            server = SelvageMCPServer(mode=mode)
            info = server.get_tools_info()
            assert len(info["utility_tools"]) == 6


class TestHasAnyApiKey:
    """API 키 존재 여부 확인 함수 테스트"""

    @patch.dict(os.environ, {}, clear=True)
    def test_no_api_keys(self) -> None:
        assert _has_any_api_key() is False

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}, clear=True)
    def test_anthropic_key_only(self) -> None:
        assert _has_any_api_key() is True

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test"}, clear=True)
    def test_openrouter_key_only(self) -> None:
        assert _has_any_api_key() is True

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test"}, clear=True)
    def test_openai_key_only(self) -> None:
        assert _has_any_api_key() is True

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test"}, clear=True)
    def test_gemini_key_only(self) -> None:
        assert _has_any_api_key() is True
