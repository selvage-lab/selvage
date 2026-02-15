"""Selvage MCP 서버 구현"""

import sys
import warnings

from fastmcp import FastMCP

from selvage.src.config import set_mcp_mode
from selvage.src.mcp.tools.context_tools import register_context_tools
from selvage.src.mcp.tools.review_tools import register_review_tools
from selvage.src.mcp.tools.utility_tools import (
    UTILITY_TOOL_NAMES,
    register_utility_tools,
    set_total_tools_count,
)


def _setup_mcp_environment() -> None:
    """MCP 환경을 설정합니다.

    stdout에 출력되는 모든 것을 차단하고, 로깅과 경고를 stderr로 리다이렉트합니다.
    """
    # MCP 모드 활성화 (가장 먼저 설정)
    set_mcp_mode(True)

    # 콘솔 인스턴스 재설정 (MCP 모드 반영)
    from selvage.src.utils.base_console import reset_console

    reset_console()

    # warnings를 stderr로 강제 리다이렉트
    warnings.showwarning = lambda msg, cat, _fn, _ln, _file=None, _line=None: print(
        f"{cat.__name__}: {msg}", file=sys.stderr
    )


class SelvageMCPServer:
    """Selvage MCP 서버 메인 클래스"""

    def __init__(
        self,
        name: str = "Selvage Code Review Server",
    ) -> None:
        # MCP 환경 설정 (stdout 보호)
        _setup_mcp_environment()

        self.name = name
        self.mcp = FastMCP(name)
        self._registered_review_tools: list[str] = []
        self._registered_context_tools: list[str] = []
        self._register_tools()

    def _register_tools(self) -> None:
        """MCP 도구들을 등록합니다."""
        register_context_tools(self.mcp)
        self._registered_context_tools = [
            "get_review_context",
            "get_file_review_context",
        ]

        register_review_tools(self.mcp)
        self._registered_review_tools = [
            "review_changes",
        ]

        register_utility_tools(self.mcp)

        total_count = (
            len(self._registered_review_tools)
            + len(self._registered_context_tools)
            + len(UTILITY_TOOL_NAMES)
        )
        set_total_tools_count(total_count)

    async def run(self, transport: str = "stdio") -> None:
        """MCP 서버를 실행합니다."""
        if transport == "stdio":
            await self.mcp.run(show_banner=False)
        else:
            raise NotImplementedError(f"Transport {transport} is not yet supported")

    def get_tools_info(self) -> dict:
        """등록된 도구들의 정보를 반환합니다."""
        return {
            "server_name": self.name,
            "transport": "stdio",
            "tools_registered": True,
            "review_tools": self._registered_review_tools,
            "context_tools": self._registered_context_tools,
            "utility_tools": list(UTILITY_TOOL_NAMES),
        }


def main_sync() -> None:
    """MCP 서버 동기 엔트리 포인트"""
    server = SelvageMCPServer()

    print(f"Starting {server.name}...", file=sys.stderr)
    print(f"Tools info: {server.get_tools_info()}", file=sys.stderr)

    try:
        server.mcp.run(show_banner=False)
    except KeyboardInterrupt:
        print("Server stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main_sync()


def run_server() -> None:
    """서버를 실행합니다 (외부 호출용)"""
    main_sync()


_dev_app: FastMCP | None = None


def __getattr__(name: str) -> FastMCP:
    """fastmcp dev 호환을 위한 모듈 레벨 lazy attribute (PEP 562).

    fastmcp dev는 모듈에서 mcp, server, app 변수를 찾는다.
    _setup_mcp_environment 없이 가볍게 FastMCP만 생성하여
    set_mcp_mode 중복 호출 문제를 회피한다.
    인스턴스는 캐싱하여 매 접근 시 재생성하지 않는다.
    """
    global _dev_app
    if name in ("mcp", "app"):
        if _dev_app is None:
            _dev_app = FastMCP("Selvage Code Review Server")
            register_context_tools(_dev_app)
            register_review_tools(_dev_app)
            register_utility_tools(_dev_app)
        return _dev_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
