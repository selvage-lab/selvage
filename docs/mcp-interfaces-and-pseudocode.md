# Selvage MCP 모드 - 인터페이스 및 수도 코드

## 1. 핵심 인터페이스 설계

### 1.1 MCP 응답 모델 정의

```python
# selvage/src/mcp/models/responses.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ReviewResult(BaseModel):
    """코드 리뷰 결과 응답 모델"""
    success: bool = Field(description="리뷰 성공 여부")
    review_content: Optional[str] = Field(None, description="리뷰 내용 (Markdown 형식)")
    summary: Optional[str] = Field(None, description="리뷰 요약")
    estimated_cost: float = Field(0.0, description="예상 비용 (USD)")
    model_used: str = Field(description="사용된 AI 모델")
    files_reviewed: List[str] = Field(default_factory=list, description="리뷰된 파일 목록")
    log_id: Optional[str] = Field(None, description="로그 ID")
    log_path: Optional[str] = Field(None, description="로그 파일 경로")
    timestamp: datetime = Field(default_factory=datetime.now, description="리뷰 완료 시간")
    error_message: Optional[str] = Field(None, description="에러 메시지 (실패 시)")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ModelInfo(BaseModel):
    """AI 모델 정보"""
    name: str = Field(description="모델 이름")
    provider: str = Field(description="프로바이더 (openai, anthropic, google, openrouter)")
    display_name: str = Field(description="표시용 이름")
    description: str = Field(description="모델 설명")
    cost_per_1k_tokens: float = Field(description="1000토큰당 비용 (USD)")
    max_tokens: int = Field(description="최대 토큰 수")
    supports_function_calling: bool = Field(default=False, description="함수 호출 지원 여부")

class ReviewHistoryItem(BaseModel):
    """리뷰 히스토리 항목"""
    log_id: str = Field(description="로그 ID")
    timestamp: datetime = Field(description="리뷰 시간")
    model: str = Field(description="사용된 모델")
    files_count: int = Field(description="리뷰된 파일 수")
    status: str = Field(description="리뷰 상태 (SUCCESS, FAILED)")
    cost: float = Field(description="실제 비용 (USD)")
    review_type: str = Field(description="리뷰 타입 (current, staged, branch, commit)")
    target: Optional[str] = Field(None, description="타겟 브랜치 또는 커밋 (해당되는 경우)")

class ServerStatus(BaseModel):
    """MCP 서버 상태"""
    running: bool = Field(description="서버 실행 여부")
    port: Optional[int] = Field(None, description="서버 포트")
    host: Optional[str] = Field(None, description="서버 호스트")
    start_time: Optional[datetime] = Field(None, description="서버 시작 시간")
    version: str = Field(description="Selvage 버전")
    tools_count: int = Field(description="등록된 도구 수")
```

### 1.2 MCP 도구 인터페이스

```python
# selvage/src/mcp/tools/review_tools.py
from typing import Optional
from mcp.server.fastmcp import FastMCP
from ..models.responses import ReviewResult

def register_review_tools(mcp: FastMCP) -> None:
    """리뷰 관련 MCP 도구들을 등록합니다."""

    @mcp.tool()
    def review_current_changes(
        model: str,
        repo_path: str = "."
    ) -> ReviewResult:
        """
        현재 작업 디렉토리의 unstaged 변경사항을 AI로 코드 리뷰합니다.

        Args:
            model: 사용할 AI 모델 (예: claude-sonnet-4, gpt-4o)
            repo_path: Git 저장소 경로 (기본값: 현재 디렉토리)

        Returns:
            ReviewResult: 리뷰 결과 및 메타데이터
        """
        # 구현 로직 (아래 수도 코드 참조)
        pass

    @mcp.tool()
    def review_staged_changes(
        model: str,
        repo_path: str = "."
    ) -> ReviewResult:
        """
        스테이징 영역의 변경사항을 AI로 코드 리뷰합니다.

        Args:
            model: 사용할 AI 모델
            repo_path: Git 저장소 경로

        Returns:
            ReviewResult: 리뷰 결과 및 메타데이터
        """
        pass

    @mcp.tool()
    def review_against_branch(
        model: str,
        target_branch: str,
        repo_path: str = "."
    ) -> ReviewResult:
        """
        현재 브랜치와 지정된 브랜치 간의 차이점을 AI로 코드 리뷰합니다.

        Args:
            model: 사용할 AI 모델
            target_branch: 비교할 브랜치명 (예: main, develop)
            repo_path: Git 저장소 경로

        Returns:
            ReviewResult: 리뷰 결과 및 메타데이터
        """
        pass

    @mcp.tool()
    def review_against_commit(
        model: str,
        target_commit: str,
        repo_path: str = "."
    ) -> ReviewResult:
        """
        지정된 커밋부터 HEAD까지의 변경사항을 AI로 코드 리뷰합니다.

        Args:
            model: 사용할 AI 모델
            target_commit: 기준 커밋 해시 (예: abc1234)
            repo_path: Git 저장소 경로

        Returns:
            ReviewResult: 리뷰 결과 및 메타데이터
        """
        pass
```

```python
# selvage/src/mcp/tools/utility_tools.py
from typing import List, Optional, Dict, Any
from mcp.server.fastmcp import FastMCP
from ..models.responses import ModelInfo, ReviewHistoryItem, ServerStatus

def register_utility_tools(mcp: FastMCP) -> None:
    """유틸리티 MCP 도구들을 등록합니다."""

    @mcp.tool()
    def get_available_models() -> List[ModelInfo]:
        """
        Selvage에서 사용 가능한 AI 모델 목록을 조회합니다.

        Returns:
            List[ModelInfo]: 사용 가능한 모델들의 정보
        """
        pass

    @mcp.tool()
    def get_review_history(
        limit: int = 10,
        repo_path: str = ".",
        model_filter: Optional[str] = None
    ) -> List[ReviewHistoryItem]:
        """
        최근 코드 리뷰 히스토리를 조회합니다.

        Args:
            limit: 조회할 히스토리 개수 (최대 50)
            repo_path: Git 저장소 경로
            model_filter: 특정 모델로 필터링 (선택적)

        Returns:
            List[ReviewHistoryItem]: 리뷰 히스토리 목록
        """
        pass

    @mcp.tool()
    def get_review_details(
        log_id: str
    ) -> Dict[str, Any]:
        """
        특정 리뷰의 상세 정보를 조회합니다.

        Args:
            log_id: 조회할 리뷰의 로그 ID

        Returns:
            Dict[str, Any]: 리뷰 상세 정보 (프롬프트, 응답, 메타데이터 포함)
        """
        pass

    @mcp.tool()
    def get_server_status() -> ServerStatus:
        """
        MCP 서버의 현재 상태를 조회합니다.

        Returns:
            ServerStatus: 서버 상태 정보
        """
        pass

    @mcp.tool()
    def validate_model_config(
        model: str
    ) -> Dict[str, Any]:
        """
        지정된 모델의 설정과 API 키를 검증합니다.

        Args:
            model: 검증할 모델명

        Returns:
            Dict[str, Any]: 검증 결과 (유효성, 에러 메시지 등)
        """
        pass
```

## 2. 핵심 로직 수도 코드

### 2.1 리뷰 도구 구현 로직

```python
# selvage/src/mcp/tools/review_tools.py (구현부)

from ...cli import get_diff_content, _perform_new_review
from ...src.diff_parser.parser import parse_git_diff
from ...src.models.review_request import ReviewRequest
from ...src.utils.logging.review_log_manager import ReviewLogManager
from ...src.config import get_api_key, get_model_info
from ...src.models.model_provider import ModelProvider

def _execute_review_workflow(
    model: str,
    repo_path: str,
    staged: bool = False,
    target_commit: Optional[str] = None,
    target_branch: Optional[str] = None
) -> ReviewResult:
    """공통 리뷰 워크플로우 실행"""

    try:
        # 1. 모델 및 API 키 검증
        model_info = get_model_info(model)
        if not model_info:
            return ReviewResult(
                success=False,
                model_used=model,
                error_message=f"지원되지 않는 모델입니다: {model}"
            )

        provider = model_info.get("provider")
        api_key = get_api_key(provider)
        if not api_key:
            return ReviewResult(
                success=False,
                model_used=model,
                error_message=f"{provider} API 키가 설정되지 않았습니다."
            )

        # 2. Git diff 추출
        diff_content = get_diff_content(
            repo_path=repo_path,
            staged=staged,
            target_commit=target_commit,
            target_branch=target_branch
        )

        if not diff_content:
            return ReviewResult(
                success=False,
                model_used=model,
                error_message="리뷰할 변경사항이 없습니다."
            )

        # 3. Diff 파싱 및 리뷰 요청 생성
        diff_result = parse_git_diff(diff_content, repo_path)
        review_request = ReviewRequest(
            diff_content=diff_content,
            processed_diff=diff_result,
            file_paths=[file.filename for file in diff_result.files],
            model=model,
            repo_path=repo_path
        )

        # 4. 리뷰 수행
        review_response, estimated_cost = _perform_new_review(review_request)

        # 5. 로그 저장
        log_id = ReviewLogManager.generate_log_id(model)
        log_path = ReviewLogManager.save(
            review_prompt=None,  # 필요시 생성
            review_request=review_request,
            review_response=review_response,
            status="SUCCESS",
            log_id=log_id,
            estimated_cost=estimated_cost
        )

        # 6. 결과 반환
        return ReviewResult(
            success=True,
            review_content=review_response.content,
            summary=_generate_summary(review_response.content),
            estimated_cost=estimated_cost.total_cost,
            model_used=model,
            files_reviewed=[f.filename for f in diff_result.files],
            log_id=log_id,
            log_path=log_path
        )

    except Exception as e:
        return ReviewResult(
            success=False,
            model_used=model,
            error_message=f"리뷰 중 오류가 발생했습니다: {str(e)}"
        )

def _generate_summary(review_content: str) -> str:
    """리뷰 내용에서 요약 생성"""
    # 간단한 요약 생성 로직
    lines = review_content.split('\n')
    summary_lines = []

    for line in lines[:10]:  # 첫 10줄에서 요약 추출
        if line.strip() and not line.startswith('#'):
            summary_lines.append(line.strip())
            if len(summary_lines) >= 3:
                break

    return ' '.join(summary_lines)[:200] + "..." if summary_lines else "리뷰 완료"

# 실제 도구 구현
def register_review_tools(mcp: FastMCP) -> None:

    @mcp.tool()
    def review_current_changes(model: str, repo_path: str = ".") -> ReviewResult:
        return _execute_review_workflow(
            model=model,
            repo_path=repo_path,
            staged=False
        )

    @mcp.tool()
    def review_staged_changes(model: str, repo_path: str = ".") -> ReviewResult:
        return _execute_review_workflow(
            model=model,
            repo_path=repo_path,
            staged=True
        )

    @mcp.tool()
    def review_against_branch(model: str, target_branch: str, repo_path: str = ".") -> ReviewResult:
        return _execute_review_workflow(
            model=model,
            repo_path=repo_path,
            target_branch=target_branch
        )

    @mcp.tool()
    def review_against_commit(model: str, target_commit: str, repo_path: str = ".") -> ReviewResult:
        return _execute_review_workflow(
            model=model,
            repo_path=repo_path,
            target_commit=target_commit
        )
```

### 2.2 유틸리티 도구 구현 로직

```python
# selvage/src/mcp/tools/utility_tools.py (구현부)

from ...src.model_config import load_models_config
from ...src.utils.logging.review_log_manager import ReviewLogManager
from ...src.config import get_api_key
import json
import os
from pathlib import Path

def register_utility_tools(mcp: FastMCP) -> None:

    @mcp.tool()
    def get_available_models() -> List[ModelInfo]:
        try:
            models_config = load_models_config()
            model_list = []

            for model_name, model_data in models_config.items():
                model_list.append(ModelInfo(
                    name=model_name,
                    provider=model_data.get("provider", "unknown"),
                    display_name=model_data.get("display_name", model_name),
                    description=model_data.get("description", ""),
                    cost_per_1k_tokens=model_data.get("cost_per_1k_tokens", 0.0),
                    max_tokens=model_data.get("max_tokens", 4096),
                    supports_function_calling=model_data.get("supports_function_calling", False)
                ))

            return model_list
        except Exception as e:
            return []

    @mcp.tool()
    def get_review_history(
        limit: int = 10,
        repo_path: str = ".",
        model_filter: Optional[str] = None
    ) -> List[ReviewHistoryItem]:
        try:
            # 제한값 검증
            limit = min(max(1, limit), 50)

            # 로그 디렉토리에서 히스토리 조회
            log_dir = ReviewLogManager.get_log_directory()
            history = []

            # JSON 로그 파일들 스캔
            for log_file in sorted(Path(log_dir).glob("*.json"), reverse=True):
                if len(history) >= limit:
                    break

                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        log_data = json.load(f)

                    # 모델 필터링
                    if model_filter and log_data.get("model") != model_filter:
                        continue

                    history.append(ReviewHistoryItem(
                        log_id=log_data.get("log_id", log_file.stem),
                        timestamp=log_data.get("timestamp"),
                        model=log_data.get("model", "unknown"),
                        files_count=len(log_data.get("file_paths", [])),
                        status=log_data.get("status", "UNKNOWN"),
                        cost=log_data.get("estimated_cost", {}).get("total_cost", 0.0),
                        review_type=_determine_review_type(log_data),
                        target=log_data.get("target")
                    ))
                except Exception:
                    continue

            return history
        except Exception:
            return []

    @mcp.tool()
    def get_review_details(log_id: str) -> Dict[str, Any]:
        try:
            log_path = ReviewLogManager.find_log_by_id(log_id)
            if not log_path or not os.path.exists(log_path):
                return {"error": "로그를 찾을 수 없습니다."}

            with open(log_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)

            # 민감한 정보 제거
            safe_data = {
                "log_id": log_data.get("log_id"),
                "timestamp": log_data.get("timestamp"),
                "model": log_data.get("model"),
                "status": log_data.get("status"),
                "file_paths": log_data.get("file_paths", []),
                "estimated_cost": log_data.get("estimated_cost", {}),
                "review_response": log_data.get("review_response", {}),
                "error": log_data.get("error")
            }

            return safe_data
        except Exception as e:
            return {"error": f"로그 조회 중 오류: {str(e)}"}

    @mcp.tool()
    def get_server_status() -> ServerStatus:
        # 서버 상태 정보 수집
        from selvage.__version__ import __version__

        return ServerStatus(
            running=True,  # MCP 서버가 실행 중이므로 True
            port=None,     # MCP는 stdio 기반이므로 포트 없음
            host=None,
            start_time=None,  # 서버 시작 시간 추적 필요시 구현
            version=__version__,
            tools_count=6  # 현재 등록된 도구 수
        )

    @mcp.tool()
    def validate_model_config(model: str) -> Dict[str, Any]:
        try:
            model_info = get_model_info(model)
            if not model_info:
                return {
                    "valid": False,
                    "error": f"지원되지 않는 모델: {model}",
                    "suggestion": "get_available_models 도구로 사용 가능한 모델을 확인하세요."
                }

            provider = model_info.get("provider")
            api_key = get_api_key(provider)

            return {
                "valid": bool(api_key),
                "model": model,
                "provider": provider,
                "api_key_set": bool(api_key),
                "error": f"{provider} API 키가 설정되지 않았습니다." if not api_key else None,
                "suggestion": f"export {provider.upper()}_API_KEY=your_key" if not api_key else None
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"검증 중 오류: {str(e)}"
            }

def _determine_review_type(log_data: Dict[str, Any]) -> str:
    """로그 데이터에서 리뷰 타입 결정"""
    if log_data.get("staged"):
        return "staged"
    elif log_data.get("target_commit"):
        return "commit"
    elif log_data.get("target_branch"):
        return "branch"
    else:
        return "current"
```

### 2.3 MCP 서버 메인 로직 (출력 관리 통합)

```python
# selvage/src/mcp/server.py

import asyncio
import sys
from typing import Optional
from mcp.server.fastmcp import FastMCP
from .tools.review_tools import register_review_tools
from .tools.utility_tools import register_utility_tools
from selvage.src.config import set_mcp_mode  # MCP 모드 관리 추가

class SelvageMCPServer:
    """Selvage MCP 서버 메인 클래스"""

    def __init__(self, name: str = "Selvage Code Review Server"):
        # MCP 모드 활성화 (프로세스 시작시 한번만)
        # 이후 모든 BaseConsole은 자동으로 stderr 사용
        set_mcp_mode(True)

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
            transport: 전송 방식 (기본: stdio)
        """
        try:
            await self.mcp.run(transport)
        except KeyboardInterrupt:
            # stderr로 출력 (MCP 모드에서 안전)
            print("\\nMCP 서버를 종료합니다.", file=sys.stderr)
        except Exception as e:
            print(f"MCP 서버 오류: {e}", file=sys.stderr)
            raise

# 서버 실행 함수
async def start_mcp_server(name: Optional[str] = None) -> None:
    """MCP 서버를 시작합니다."""
    server = SelvageMCPServer(name or "Selvage Code Review Server")
    await server.run()

# CLI에서 직접 호출할 수 있는 동기 함수
def run_mcp_server_sync(name: Optional[str] = None) -> None:
    """동기적으로 MCP 서버를 실행합니다."""
    asyncio.run(start_mcp_server(name))
```

### 2.4 CLI 통합 로직

```python
# selvage/cli.py에 추가할 내용

import subprocess
import signal
import os
import time
from pathlib import Path

# MCP 서버 프로세스 관리
MCP_PID_FILE = Path.home() / ".selvage" / "mcp_server.pid"

@cli.group()
def mcp():
    """MCP (Model Context Protocol) 서버 관리"""
    pass

@mcp.command()
@click.option("--port", default=3000, help="MCP 서버 포트 (현재는 stdio 모드만 지원)")
@click.option("--host", default="localhost", help="MCP 서버 호스트")
@click.option("--daemon", is_flag=True, help="백그라운드에서 서버 실행")
def start(port: int, host: str, daemon: bool):
    """MCP 서버를 시작합니다."""

    # 이미 실행 중인지 확인
    if _is_mcp_server_running():
        console.warning("MCP 서버가 이미 실행 중입니다.")
        return

    if daemon:
        # 백그라운드 실행
        _start_mcp_server_daemon()
        console.success("MCP 서버가 백그라운드에서 시작되었습니다.")
    else:
        # 포그라운드 실행
        console.info("MCP 서버를 시작합니다... (Ctrl+C로 종료)")
        from .src.mcp.server import run_mcp_server_sync
        run_mcp_server_sync()

@mcp.command()
def stop():
    """실행 중인 MCP 서버를 중지합니다."""

    if not _is_mcp_server_running():
        console.warning("실행 중인 MCP 서버가 없습니다.")
        return

    if _stop_mcp_server():
        console.success("MCP 서버를 중지했습니다.")
    else:
        console.error("MCP 서버 중지에 실패했습니다.")

@mcp.command()
def status():
    """MCP 서버 상태를 확인합니다."""

    if _is_mcp_server_running():
        pid = _get_mcp_server_pid()
        uptime = _get_server_uptime(pid)
        console.success(f"MCP 서버가 실행 중입니다. (PID: {pid}, 업타임: {uptime})")
    else:
        console.info("MCP 서버가 실행되지 않습니다.")

@mcp.command()
def logs():
    """MCP 서버 로그를 확인합니다."""

    log_file = Path.home() / ".selvage" / "mcp_server.log"
    if log_file.exists():
        console.info(f"MCP 서버 로그: {log_file}")
        # 최근 50줄 출력
        with open(log_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-50:]:
                print(line.rstrip())
    else:
        console.warning("MCP 서버 로그 파일이 없습니다.")

# 헬퍼 함수들
def _is_mcp_server_running() -> bool:
    """MCP 서버가 실행 중인지 확인"""
    if not MCP_PID_FILE.exists():
        return False

    try:
        with open(MCP_PID_FILE, 'r') as f:
            pid = int(f.read().strip())

        # 프로세스가 실제로 존재하는지 확인
        os.kill(pid, 0)
        return True
    except (ValueError, OSError):
        # PID 파일 삭제
        MCP_PID_FILE.unlink(missing_ok=True)
        return False

def _get_mcp_server_pid() -> Optional[int]:
    """실행 중인 MCP 서버의 PID 반환"""
    if MCP_PID_FILE.exists():
        try:
            with open(MCP_PID_FILE, 'r') as f:
                return int(f.read().strip())
        except ValueError:
            pass
    return None

def _start_mcp_server_daemon() -> bool:
    """백그라운드에서 MCP 서버 시작"""
    try:
        # 로그 디렉토리 생성
        log_dir = Path.home() / ".selvage"
        log_dir.mkdir(exist_ok=True)

        # 백그라운드 프로세스 시작
        log_file = log_dir / "mcp_server.log"
        with open(log_file, 'a') as f:
            process = subprocess.Popen(
                [sys.executable, "-m", "selvage.src.mcp.server"],
                stdout=f,
                stderr=subprocess.STDOUT,
                start_new_session=True
            )

        # PID 저장
        with open(MCP_PID_FILE, 'w') as f:
            f.write(str(process.pid))

        return True
    except Exception as e:
        console.error(f"MCP 서버 시작 실패: {e}")
        return False

def _stop_mcp_server() -> bool:
    """MCP 서버 중지"""
    pid = _get_mcp_server_pid()
    if not pid:
        return False

    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)  # 정상 종료 대기

        # 프로세스가 여전히 실행 중이면 강제 종료
        try:
            os.kill(pid, 0)
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass  # 이미 종료됨

        # PID 파일 삭제
        MCP_PID_FILE.unlink(missing_ok=True)
        return True
    except OSError:
        return False

def _get_server_uptime(pid: int) -> str:
    """서버 업타임 계산"""
    try:
        stat_file = f"/proc/{pid}/stat"
        if os.path.exists(stat_file):
            with open(stat_file, 'r') as f:
                stats = f.read().split()
                start_time = int(stats[21])  # 프로세스 시작 시간

            # 업타임 계산 (간단한 구현)
            with open("/proc/uptime", 'r') as f:
                system_uptime = float(f.read().split()[0])

            process_uptime = system_uptime - (start_time / 100)  # jiffies to seconds
            return f"{int(process_uptime // 60)}분 {int(process_uptime % 60)}초"
    except Exception:
        pass

    return "알 수 없음"
```

## 3. 사용 예시 시나리오

### 3.1 Claude Code에서 사용

#### 연동 설정

**1. MCP 서버 추가 (Claude Code CLI 사용)**

```bash
# selvage MCP 서버 추가
claude mcp add selvage uvx selvage mcp start

# 환경변수와 함께 추가
claude mcp add selvage \
  -e ANTHROPIC_API_KEY=your_anthropic_key \
  -e OPENAI_API_KEY=your_openai_key \
  -e GEMINI_API_KEY=your_gemini_key \
  -- uvx selvage mcp start
```

**2. 수동 설정 (~/.claude.json)**

```json
{
  "mcpServers": {
    "selvage": {
      "command": "uvx",
      "args": ["selvage", "mcp", "start"],
      "env": {
        "OPENROUTER_API_KEY": "your_openrouter_key"
      }
    }
  }
}
```

**3. 설정 확인**

```bash
# MCP 서버 목록 확인
claude mcp list

# selvage 서버 상태 확인
claude mcp get selvage
```

#### 사용 예시

```bash
# 2. Claude Code에서 사용
사용자: "현재 변경사항을 코드 리뷰해줘"

Claude Code:
- tool: review_current_changes
- parameters: {"model": "claude-sonnet-4", "repo_path": "."}
- result: 구조화된 리뷰 결과 반환

# 3. 추가 요청
사용자: "main 브랜치와 비교해서 리뷰해줘"

Claude Code:
- tool: review_against_branch
- parameters: {"model": "claude-sonnet-4", "target_branch": "main", "repo_path": "."}
```

### 3.2 Cursor에서 사용

#### 연동 설정

**1. mcp.json 설정 파일 수정**

Cursor의 MCP 설정 파일 경로: `~/.cursor/mcp.json`

```json
{
  "mcpServers": {
    "selvage": {
      "command": "uvx",
      "args": ["selvage", "mcp", "start"],
      "env": {
        "OPENROUTER_API_KEY": "your_openrouter_key"
      }
    }
  }
}
```

**2. 로컬 패키지로 개발 중인 경우**

```json
{
  "mcpServers": {
    "selvage-dev": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/selvage",
        "run",
        "python",
        "-m",
        "selvage.src.mcp.server"
      ],
      "env": {
        "OPENROUTER_API_KEY": "your_openrouter_key"
      }
    }
  }
}
```

**3. 특정 프로젝트 경로 지정**

```json
{
  "mcpServers": {
    "selvage-project": {
      "command": "uvx",
      "args": ["selvage", "mcp", "start"],
      "env": {
        "OPENROUTER_API_KEY": "your_openrouter_key"
      }
    }
  }
}
```

#### 사용 예시

```bash
# Cursor에서 MCP 연동 후
사용자: "스테이징된 변경사항에 대해 리뷰 받고 싶어"

Cursor:
- MCP call: review_staged_changes
- parameters: {"model": "claude-sonnet-4", "repo_path": "."}
- 결과 분석 후 추가 제안
- 코드 개선 방향 제시

# 히스토리 조회 예시
사용자: "최근 5개 리뷰 히스토리를 보여줘"

Cursor:
- MCP call: get_review_history
- parameters: {"limit": 5, "repo_path": "."}
- 리뷰 히스토리 테이블 형식으로 표시
```

### 3.3 일반적인 MCP 클라이언트 연동

#### 표준 MCP 설정 형식

**1. stdio transport 방식 (권장)**

```json
{
  "mcpServers": {
    "selvage": {
      "type": "stdio",
      "command": "uvx",
      "args": ["selvage", "mcp", "start"],
      "env": {
        "OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}"
      }
    }
  }
}
```

**2. 환경변수 직접 전달**

```json
{
  "mcpServers": {
    "selvage": {
      "command": "uvx",
      "args": ["selvage", "mcp", "start"],
      "env": {
        "OPENROUTER_API_KEY": "sk-or-v1-..."
      }
    }
  }
}
```

#### 다양한 설치 방식

**1. PyPI에서 직접 설치**

```bash
# uvx로 자동 설치 및 실행
uvx selvage mcp start

# uv tool로 설치 후 실행
uv tool install selvage
uv tool run selvage mcp start
```

**2. GitHub에서 개발 버전 설치**

```json
{
  "mcpServers": {
    "selvage-dev": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/your-org/selvage.git",
        "selvage",
        "mcp",
        "start"
      ]
    }
  }
}
```

**3. 로컬 개발 환경**

```json
{
  "mcpServers": {
    "selvage-local": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/selvage",
        "run",
        "python",
        "-m",
        "selvage.src.mcp.server"
      ]
    }
  }
}
```

#### 고급 설정 옵션

**1. 특정 모델 기본값 설정**

```json
{
  "mcpServers": {
    "selvage": {
      "command": "uvx",
      "args": ["selvage", "mcp", "start"],
      "env": {
        "SELVAGE_DEFAULT_MODEL": "claude-sonnet-4",
        "SELVAGE_DEFAULT_LANGUAGE": "ko",
        "OPENROUTER_API_KEY": "your_openrouter_key"
      }
    }
  }
}
```

**2. 디버그 모드 활성화**

```json
{
  "mcpServers": {
    "selvage-debug": {
      "command": "uvx",
      "args": ["selvage", "mcp", "start"],
      "env": {
        "SELVAGE_DEBUG_MODE": "true",
        "SELVAGE_LOG_LEVEL": "DEBUG",
        "ANTHROPIC_API_KEY": "your_key"
      }
    }
  }
}
```

#### 연동 확인 방법

**1. MCP 서버 상태 확인**

```bash
# 서버 프로세스 확인
ps aux | grep selvage

# 로그 확인 (디버그 모드 시)
tail -f ~/.selvage/logs/selvage.log
```

**2. 사용 가능한 도구 확인**
대부분의 MCP 클라이언트에서 사용 가능한 도구 목록:

- `review_current_changes` - 현재 변경사항 리뷰
- `review_staged_changes` - 스테이징된 변경사항 리뷰
- `review_against_branch` - 브랜치 간 차이점 리뷰
- `review_against_commit` - 커밋 간 차이점 리뷰
- `get_available_models` - 사용 가능한 AI 모델 목록
- `get_review_history` - 리뷰 히스토리 조회
- `get_server_status` - 서버 상태 조회
- `validate_model_config` - 모델 설정 검증

## 4. MCP 모드 출력 관리

### 4.1 문제점 분석

MCP 서버에서는 stdin/stdout이 프로토콜 통신에 사용되므로, 일반적인 출력을 stdout으로 하면 안 됩니다.

**현재 selvage의 출력 방식**:

- Rich Console: 기본적으로 stdout 사용
- Python Logger: stderr 사용 (안전)

### 4.2 읽기 전용 MCP 모드 관리

```python
# selvage/src/config.py에 추가

# MCP 모드 전역 상태
_MCP_MODE = False
_mcp_mode_set = False

def set_mcp_mode(enabled: bool) -> None:
    """MCP 모드를 설정합니다. 프로세스당 한번만 설정 가능합니다.

    Args:
        enabled: MCP 모드 활성화 여부

    Raises:
        RuntimeError: 이미 MCP 모드가 설정된 경우
    """
    global _MCP_MODE, _mcp_mode_set

    if _mcp_mode_set:
        raise RuntimeError("MCP mode can only be set once per process")

    _MCP_MODE = enabled
    _mcp_mode_set = True

def is_mcp_mode() -> bool:
    """현재 MCP 모드 여부를 반환합니다.

    Returns:
        bool: MCP 모드 활성화 여부
    """
    return _MCP_MODE

def get_mcp_mode_status() -> dict[str, bool]:
    """MCP 모드 상태 정보를 반환합니다 (디버깅용).

    Returns:
        dict: MCP 모드 상태 정보
    """
    return {
        "mcp_mode": _MCP_MODE,
        "mcp_mode_set": _mcp_mode_set
    }
```

### 4.3 BaseConsole 수정

```python
# selvage/src/utils/base_console.py 수정

import sys
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from rich.console import Console
from rich.status import Status

from selvage.src.utils.logging import get_logger
from selvage.src.config import is_mcp_mode  # 추가

class BaseConsole:
    """기본 콘솔 출력 및 로깅을 관리하는 클래스."""

    def __init__(self) -> None:
        """콘솔 인스턴스를 초기화합니다."""
        # MCP 모드에 따른 조건부 출력 스트림 설정
        if is_mcp_mode():
            # MCP 모드: 모든 출력을 stderr로 (프로토콜 안전성)
            self.console = Console(file=sys.stderr)
        else:
            # 일반 모드: stdout 사용 (파이프라인 호환성)
            self.console = Console()

        self.logger = get_logger(__name__)

    # 나머지 메서드는 동일...
```

### 4.4 장점 및 특징

**장점**:

1. **기존 코드 최소 변경**: BaseConsole만 수정하면 됨
2. **안전성**: 한번 설정 후 변경 불가로 예측 가능한 동작
3. **성능**: 런타임 오버헤드 최소화
4. **호환성**: CLI 모드와 MCP 모드 모두 지원

**특징**:

- MCP 서버 프로세스는 시작부터 종료까지 stderr 사용
- 일반 CLI 명령어는 기존대로 stdout 사용하여 파이프라인 호환성 유지
- 테스트 환경에서도 안전하게 격리 가능

### 4.5 테스트 방법

```python
# 테스트 코드 예시
def test_mcp_mode_console_output():
    """MCP 모드에서 console 출력이 stderr로 가는지 테스트"""
    from selvage.src.config import set_mcp_mode
    from selvage.src.utils.base_console import BaseConsole
    import sys

    # MCP 모드 설정
    set_mcp_mode(True)

    # Console 생성 후 확인
    console = BaseConsole()
    assert console.console.file == sys.stderr

    # 중복 설정 시 에러 확인
    with pytest.raises(RuntimeError):
        set_mcp_mode(False)

def test_normal_mode_console_output():
    """일반 모드에서 console 출력이 stdout으로 가는지 테스트"""
    from selvage.src.utils.base_console import BaseConsole
    import sys

    # 일반 모드 (MCP 모드 설정 안함)
    console = BaseConsole()
    assert console.console.file == sys.stdout
```

### 4.6 구현 순서

1. **config.py에 MCP 모드 관리 함수 추가**
2. **BaseConsole.py 수정**: `is_mcp_mode()` 조건부 로직 추가
3. **MCP 서버 구현**: `SelvageMCPServer.__init__()`에서 `set_mcp_mode(True)` 호출
4. **CLI 명령어 추가**: 기존 2.4 섹션의 CLI 통합 로직 활용
5. **테스트 작성**: MCP 모드와 일반 모드 동작 검증

## 5. 테스트 및 호환성 전략

### 5.1 단위 테스트 전략

#### Tool 호출 테스트

```python
# tests/test_mcp_tools.py
import pytest
from unittest.mock import Mock, patch
from selvage.src.mcp.tools.review_tools import register_review_tools
from selvage.src.mcp.models.responses import ReviewResult

class TestMCPReviewTools:
    """MCP 리뷰 도구 단위 테스트"""

    def test_review_current_changes_parameter_validation(self):
        """파라미터 검증 테스트"""
        # 필수 파라미터 누락 시 에러
        with pytest.raises(ValueError):
            review_current_changes(model="")

        # 잘못된 모델명 시 에러
        with pytest.raises(ValueError):
            review_current_changes(model="invalid-model")

    @patch('selvage.src.mcp.tools.review_tools._execute_review_workflow')
    def test_review_current_changes_pipeline_execution(self, mock_workflow):
        """파이프라인 실행 테스트"""
        # Mock 설정
        mock_result = ReviewResult(
            success=True,
            review_content="Test review content",
            model_used="claude-sonnet-4",
            files_reviewed=["test.py"]
        )
        mock_workflow.return_value = mock_result

        # 실행
        result = review_current_changes(
            model="claude-sonnet-4",
            repo_path="/test/repo"
        )

        # 검증
        assert result.success is True
        assert result.model_used == "claude-sonnet-4"
        mock_workflow.assert_called_once()

    def test_review_result_summary_conversion(self):
        """요약 변환 테스트"""
        review_content = """
        # Code Review

        ## Issues Found
        1. Missing error handling
        2. Unused import

        ## Suggestions
        - Add try-catch blocks
        """

        summary = _generate_summary(review_content)
        assert len(summary) <= 200
        assert "error handling" in summary.lower()
```

#### StdIO Transport 테스트

```python
# tests/test_mcp_transport.py
import json
import pytest
from selvage.src.mcp.server import SelvageMCPServer

class TestMCPTransport:
    """MCP StdIO Transport 형식 테스트"""

    def test_tool_call_input_format(self):
        """도구 호출 입력 형식 스냅샷 테스트"""
        expected_input = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "tools/call",
            "params": {
                "name": "review_current_changes",
                "arguments": {
                    "model": "claude-sonnet-4",
                    "repo_path": "."
                }
            }
        }

        # 입력 형식 검증
        assert "jsonrpc" in expected_input
        assert expected_input["method"] == "tools/call"
        assert "arguments" in expected_input["params"]

    def test_tool_response_output_format(self):
        """도구 응답 출력 형식 스냅샷 테스트"""
        response = {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "success": True,
                            "review_content": "Test review",
                            "model_used": "claude-sonnet-4"
                        })
                    }
                ]
            }
        }

        # 출력 형식 검증
        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        assert "content" in response["result"]
```

### 5.2 통합 테스트 전략

#### 가짜 MCP 클라이언트 테스트

```python
# tests/integration/test_mcp_integration.py
import asyncio
import json
from unittest.mock import AsyncMock
from selvage.src.mcp.server import SelvageMCPServer

class MockMCPClient:
    """테스트용 가짜 MCP 클라이언트"""

    def __init__(self):
        self.received_messages = []
        self.server = None

    async def connect_to_server(self, server: SelvageMCPServer):
        """서버에 연결"""
        self.server = server

    async def call_tool(self, tool_name: str, arguments: dict):
        """도구 호출"""
        request = {
            "jsonrpc": "2.0",
            "id": "test-1",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        # 서버로 요청 전송 (시뮬레이션)
        response = await self._simulate_server_call(request)
        self.received_messages.append(response)
        return response

    async def _simulate_server_call(self, request):
        """서버 호출 시뮬레이션"""
        # 실제 구현에서는 stdio를 통해 통신
        return {
            "jsonrpc": "2.0",
            "id": request["id"],
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": "Mock review result"
                    }
                ]
            }
        }

class TestMCPIntegration:
    """MCP 통합 테스트"""

    @pytest.mark.asyncio
    async def test_full_review_workflow(self):
        """전체 리뷰 워크플로우 테스트"""
        # 설정
        client = MockMCPClient()
        server = SelvageMCPServer()

        await client.connect_to_server(server)

        # 도구 호출
        response = await client.call_tool(
            "review_current_changes",
            {
                "model": "claude-sonnet-4",
                "repo_path": "/test/repo"
            }
        )

        # 검증
        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        assert len(client.received_messages) == 1

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """에러 처리 워크플로우 테스트"""
        client = MockMCPClient()

        # 잘못된 파라미터로 호출
        response = await client.call_tool(
            "review_current_changes",
            {
                "model": "",  # 빈 모델명
                "repo_path": "/nonexistent"
            }
        )

        # 에러 응답 검증
        assert "error" in response or response["result"]["content"][0]["text"].find("error") != -1
```

### 5.3 호환성 체크리스트

#### MCP 클라이언트 버전 호환성

```python
# tests/compatibility/test_mcp_compatibility.py

class TestMCPCompatibility:
    """MCP 클라이언트 호환성 테스트"""

    def test_cursor_mcp_version_compatibility(self):
        """Cursor MCP 버전 호환성"""
        # Cursor에서 지원하는 MCP 스펙 버전
        supported_versions = ["1.0", "1.1", "1.2"]

        for version in supported_versions:
            # 각 버전별 호환성 확인
            assert self._check_version_compatibility(version)

    def test_claude_code_mcp_compatibility(self):
        """Claude Code MCP 호환성"""
        # Claude Code 특정 요구사항 확인
        assert self._check_claude_code_requirements()

    def test_large_diff_multiturn_handling(self):
        """대용량 diff 멀티턴 처리 확인"""
        # 대용량 diff 시나리오
        large_diff = "+" * 100000  # 100KB 이상의 diff

        # 멀티턴 처리 흐름 확인
        result = self._process_large_diff(large_diff)
        assert result["multiturn_used"] is True
        assert len(result["chunks"]) > 1

    def _check_version_compatibility(self, version: str) -> bool:
        """버전 호환성 확인"""
        # 실제 구현에서는 MCP 스펙 버전별 테스트
        return True

    def _check_claude_code_requirements(self) -> bool:
        """Claude Code 요구사항 확인"""
        # Tool 이름 규칙, 파라미터 형식 등 확인
        return True

    def _process_large_diff(self, diff: str) -> dict:
        """대용량 diff 처리 시뮬레이션"""
        return {
            "multiturn_used": len(diff) > 50000,
            "chunks": [diff[i:i+50000] for i in range(0, len(diff), 50000)]
        }
```

### 5.4 성능 및 안정성 테스트

#### 동시 요청 처리 테스트

```python
# tests/performance/test_mcp_performance.py
import asyncio
import pytest
from concurrent.futures import ThreadPoolExecutor

class TestMCPPerformance:
    """MCP 성능 테스트"""

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self):
        """동시 도구 호출 처리 테스트"""
        # 10개의 동시 요청
        tasks = []
        for i in range(10):
            task = asyncio.create_task(
                self._call_review_tool(f"request-{i}")
            )
            tasks.append(task)

        # 모든 요청 완료 대기
        results = await asyncio.gather(*tasks)

        # 모든 요청이 성공적으로 처리되었는지 확인
        assert len(results) == 10
        assert all(result["success"] for result in results)

    async def _call_review_tool(self, request_id: str):
        """리뷰 도구 호출"""
        # 시뮬레이션된 도구 호출
        await asyncio.sleep(0.1)  # 네트워크 지연 시뮬레이션
        return {"success": True, "request_id": request_id}

    def test_memory_usage_under_load(self):
        """부하 상황에서 메모리 사용량 테스트"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # 100개의 리뷰 요청 처리
        for i in range(100):
            self._simulate_review_processing()

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # 메모리 증가량이 허용 범위 내인지 확인 (예: 100MB 이하)
        assert memory_increase < 100 * 1024 * 1024

    def _simulate_review_processing(self):
        """리뷰 처리 시뮬레이션"""
        # 메모리 사용량 테스트를 위한 시뮬레이션
        dummy_data = "x" * 1000  # 1KB 데이터
        return len(dummy_data)
```

### 5.5 테스트 실행 가이드

#### 테스트 명령어

```bash
# 전체 MCP 테스트 실행
pytest tests/test_mcp* -v

# 단위 테스트만 실행
pytest tests/test_mcp_tools.py tests/test_mcp_transport.py -v

# 통합 테스트 실행
pytest tests/integration/test_mcp_integration.py -v

# 호환성 테스트 실행
pytest tests/compatibility/test_mcp_compatibility.py -v

# 성능 테스트 실행
pytest tests/performance/test_mcp_performance.py -v

# 커버리지와 함께 실행
pytest tests/test_mcp* --cov=selvage.src.mcp --cov-report=html
```

#### CI/CD 통합

```yaml
# .github/workflows/mcp-tests.yml
name: MCP Tests

on: [push, pull_request]

jobs:
  mcp-tests:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install -e .[dev]
        pip install pytest-asyncio pytest-cov

    - name: Run MCP unit tests
      run: pytest tests/test_mcp* -v

    - name: Run MCP integration tests
      run: pytest tests/integration/test_mcp* -v

    - name: Run compatibility tests
      run: pytest tests/compatibility/test_mcp* -v
```

이러한 인터페이스와 수도 코드를 바탕으로 실제 구현을 진행할 수 있습니다.
