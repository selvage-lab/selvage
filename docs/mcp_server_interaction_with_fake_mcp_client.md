### FakeMcpClient 예시로 보는 MCP Server 상호작용

이 문서는 FakeMcpClient 예시 코드를 통해 MCP Server와의 상호작용 흐름(connect → initialize → tools/list → tools/call)을 설명합니다. 서버는 `python -m selvage.src.mcp.server`로 stdio 기반 실행을 가정합니다.

#### 예시 코드 (async)

```python
import sys
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class FakeMcpClient:
    """테스트용 간단 MCP 클라이언트 (stdio)."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout
        self.session: ClientSession | None = None
        self._exit_stack: AsyncExitStack | None = None
        self.initialized = False

    async def connect(self) -> None:
        """서버 프로세스를 stdio로 띄우고 연결합니다."""
        server = StdioServerParameters(
            command=sys.executable,
            args=["-m", "selvage.src.mcp.server"],
        )

        self._exit_stack = AsyncExitStack()
        read, write = await self._exit_stack.enter_async_context(stdio_client(server))
        self.session = ClientSession(read, write)

    async def initialize(self) -> dict[str, Any]:
        if not self.session:
            await self.connect()
        result = await self.session.initialize()
        self.initialized = True
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": result.protocol_version,
                "capabilities": result.capabilities.model_dump(),
                "serverInfo": result.server_info.model_dump() if result.server_info else {},
            },
        }

    async def list_tools(self) -> dict[str, Any]:
        if not self.session or not self.initialized:
            raise RuntimeError("먼저 initialize()를 호출하세요")
        result = await self.session.list_tools()
        return {
            "jsonrpc": "2.0",
            "id": 2,
            "result": {"tools": [t.model_dump() for t in result.tools]},
        }

    async def call_tool(self, name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.session or not self.initialized:
            raise RuntimeError("먼저 initialize()를 호출하세요")
        res = await self.session.call_tool(name, args or {})
        return {
            "jsonrpc": "2.0",
            "id": 3,
            "result": {"content": [c.model_dump() for c in res.content]},
        }

    async def stop(self) -> None:
        self.session = None
        if self._exit_stack is not None:
            await self._exit_stack.aclose()
            self._exit_stack = None
        self.initialized = False
```

#### 사용 예시

```python
import asyncio

from docs.fake_mcp_client import FakeMcpClient  # 파일 경로에 맞게 조정


async def main() -> None:
    client = FakeMcpClient()
    try:
        await client.connect()

        init = await client.initialize()
        print("initialize:", init)

        tools = await client.list_tools()
        print("tools:", [t["name"] for t in tools["result"]["tools"]])

        # 예: 서버 상태 조회 도구 호출
        call_res = await client.call_tool("get_server_status_tool")
        print("call result:", call_res)
    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

#### 핵심 포인트

- 연결은 `stdio_client(StdioServerParameters)`로 생성된 `(read, write)` 스트림을 `ClientSession`에 넘겨 구성합니다.
- `initialize()`로 프로토콜 협상 후 `list_tools()`/`call_tool()`을 호출합니다.
- 테스트에서는 같은 Task에서 종료가 수행되도록 `try/finally`를 권장합니다.
