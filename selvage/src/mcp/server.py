"""Selvage MCP 서버 구현"""

import sys
import warnings

from fastmcp import FastMCP

from selvage.src.config import set_mcp_mode
from selvage.src.mcp.tools.review_tools import register_review_tools
from selvage.src.mcp.tools.utility_tools import register_utility_tools


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

    def __init__(self, name: str = "Selvage Code Review Server") -> None:
        # MCP 환경 설정 (stdout 보호)
        _setup_mcp_environment()

        self.name = name
        self.mcp = FastMCP(name)
        self._register_tools()

    def _register_tools(self) -> None:
        """모든 MCP 도구들을 등록합니다."""
        register_review_tools(self.mcp)
        register_utility_tools(self.mcp)

    async def run(self, transport: str = "stdio") -> None:
        """
        MCP 서버를 실행합니다.

        Args:
            transport: 전송 방식 ("stdio" 또는 "sse")
        """
        if transport == "stdio":
            # show_banner=False: stdout에 배너 출력 방지 (MCP 프로토콜 보호)
            await self.mcp.run(show_banner=False)
        else:
            # HTTP/SSE 모드는 향후 구현
            raise NotImplementedError(f"Transport {transport} is not yet supported")

    def get_tools_info(self) -> dict:
        """등록된 도구들의 정보를 반환합니다."""
        return {
            "server_name": self.name,
            "transport": "stdio",
            "tools_registered": True,
            "review_tools": [
                "review_current_changes_tool",
                "review_staged_changes_tool",
                "review_against_branch_tool",
                "review_against_commit_tool",
            ],
            "utility_tools": [
                "get_available_models_tool",
                "get_review_history_tool",
                "get_review_details_tool",
                "get_server_status_tool",
                "validate_model_support_tool",
                "validate_api_key_for_provider_tool",
            ],
        }


def main_sync() -> None:
    """MCP 서버 동기 엔트리 포인트"""
    server = SelvageMCPServer()

    # 디버그 정보 출력 (stderr로 출력되어 MCP 프로토콜과 분리됨)
    print(f"Starting {server.name}...", file=sys.stderr)
    print(f"Tools info: {server.get_tools_info()}", file=sys.stderr)

    # FastMCP 서버 직접 실행 (asyncio.run 사용하지 않음)
    # show_banner=False: stdout에 배너 출력 방지 (MCP 프로토콜 보호)
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
    # 단순히 main_sync 호출 (main_sync에서 모든 event loop 처리를 담당)
    main_sync()
