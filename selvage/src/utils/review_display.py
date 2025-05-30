"""리뷰 프로세스 관련 UI 표시를 위한 모듈."""

import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from selvage.src.utils.base_console import console

if TYPE_CHECKING:
    from selvage.src.model_config import ModelInfoDict
    from selvage.src.utils.token.models import EstimatedCost


def _format_token_count(count: int) -> str:
    """토큰 수를 축약된 형태로 포맷팅합니다."""
    if count >= 1000:
        return f"{count / 1000:.1f}k"
    return str(count)


def _shorten_path(path: str) -> str:
    """긴 파일 경로를 축약합니다."""
    import os

    # 홈 디렉토리를 ~ 로 표시
    simplified = path.replace(os.path.expanduser("~"), "~")

    # 경로가 너무 긴 경우 중간 부분 생략
    if len(simplified) > 60:  # 더 짧게 제한
        parts = simplified.split("/")
        if len(parts) > 3:
            filename = parts[-1]
            # 파일명도 너무 긴 경우 축약
            if len(filename) > 30:
                name, ext = os.path.splitext(filename)
                filename = f"{name[:20]}...{ext}"

            start = "/".join(parts[:2])  # ~/Library 등
            return f"{start}/.../{filename}"

    return simplified


class ReviewDisplay:
    """리뷰 프로세스 관련 UI 표시를 관리하는 클래스."""

    def __init__(self) -> None:
        """디스플레이 인스턴스를 초기화합니다."""
        self.console = Console()

    def model_info(self, model_name: str, description: str) -> None:
        """모델 정보를 Panel로 출력합니다."""
        content = f"[bold cyan]{model_name}[/bold cyan]\n[dim]{description}[/dim]"

        panel = Panel.fit(
            content,
            title="[bold]리뷰 AI 모델[/bold]",
            border_style="cyan",
        )
        self.console.print(panel)

    def log_saved(self, log_path: str) -> None:
        """리뷰 로그 저장 완료 메시지를 Panel로 출력합니다."""

        # 경로를 간단하게 표시 (홈 디렉토리는 ~ 로 표시)
        simplified_path = _shorten_path(log_path)

        # Panel 내용 구성
        content = f"[bold green]저장 완료[/bold green]\n[dim]{simplified_path}[/dim]"

        panel = Panel.fit(
            content,
            title="[bold]결과 저장[/bold]",
            border_style="green",
        )
        self.console.print(panel)

    def review_complete(
        self,
        model_info: "ModelInfoDict",
        log_path: str,
        estimated_cost: "EstimatedCost",
    ) -> None:
        """리뷰 완료 결과를 통합된 Panel로 출력합니다."""
        # 토큰 정보를 축약된 형태로 표시
        token_info = f"{_format_token_count(estimated_cost.input_tokens)} → {_format_token_count(estimated_cost.output_tokens)} tokens"

        # 경로를 간단하게 표시
        simplified_path = _shorten_path(log_path)

        # 통합 Panel 내용 구성
        content = f"""[bold cyan]모델:[/bold cyan] [white]{model_info["full_name"]}[/white]
[dim]{model_info["description"]}[/dim]

[bold yellow]비용:[/bold yellow] [white]{estimated_cost.total_cost_usd}[/white] [dim]({token_info})[/dim]
[dim]※ 추정 비용이므로 각 AI 서비스에서 정확한 비용을 확인하세요.[/dim]

[bold green]저장:[/bold green] [white]{simplified_path}[/white]"""

        panel = Panel(
            Align.center(content),
            title="[bold]코드 리뷰 완료[/bold]",
            border_style="cyan",
            width=80,
            padding=(1, 2),
        )

        self.console.print(panel)

    @contextmanager
    def progress_review(self, model: str) -> Generator[None, None, None]:
        """코드 리뷰 진행 상황을 통합된 Panel로 표시합니다."""
        # Progress 설정 (퍼센트 표시 제거)
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            transient=False,
        )

        task = progress.add_task("코드 분석 및 리뷰 생성 중...", total=100)

        # Panel 내용 구성
        def make_panel() -> Panel:
            # 텍스트 컴포넌트들
            title = Text("Selvage : 코드 마감까지 탄탄하게!", style="bold cyan")
            model_info = Text(f"모델: {model}", style="dim")

            # Group으로 컴포넌트들 조합
            content = Group(
                Align.center(title),
                Text(""),  # 빈 줄
                Align.center(model_info),
                Text(""),  # 빈 줄
                progress,
            )

            return Panel(
                content,
                title="[bold]코드 리뷰 진행 중[/bold]",
                border_style="blue",
                width=70,
                padding=(1, 2),
            )

        # Live 표시로 실시간 업데이트
        with Live(
            make_panel(), refresh_per_second=10, console=self.console, transient=True
        ) as live:
            # 백그라운드에서 물결치는 진행률 업데이트
            stop_progress = threading.Event()

            def update_progress():
                step = 0
                while not stop_progress.is_set():
                    # 톱니파 패턴: 0에서 100까지 갔다가 다시 0에서 시작
                    cycle_length = 50  # 한 사이클의 길이 (조절 가능)
                    progress_value = (step % cycle_length) * (100 / cycle_length)
                    progress.update(task, completed=progress_value)
                    live.update(make_panel())

                    step += 1
                    time.sleep(0.1)

            progress_thread = threading.Thread(target=update_progress)
            progress_thread.start()

            try:
                yield
            finally:
                stop_progress.set()
                progress_thread.join()
                # 완료 시에는 100%로 설정하고 잠시 보여준 후 사라지게 함
                progress.update(task, completed=100)
                live.update(make_panel())
                time.sleep(0.5)  # 완료 상태를 잠시 보여줌
                # Live가 종료되면서 Panel이 자동으로 사라짐

    def show_available_models(self) -> None:
        """사용 가능한 모든 AI 모델을 가독성 있게 표시합니다."""
        from selvage.src.model_config import ModelConfig
        from selvage.src.models.model_provider import ModelProvider

        try:
            model_config = ModelConfig()
            all_models_config = model_config.get_all_models_config()

            if not all_models_config:
                console.error("모델 설정을 로드할 수 없습니다.")
                return

            # 제목 출력
            self.console.print("\n[bold cyan]사용 가능한 AI 모델 목록[/bold cyan]\n")

            # 프로바이더별로 그룹화
            providers_data = {}
            for model_key, model_info in all_models_config.items():
                provider = model_info["provider"]
                if provider not in providers_data:
                    providers_data[provider] = []
                providers_data[provider].append((model_key, model_info))

            # 각 프로바이더별로 테이블 생성
            for provider in [
                ModelProvider.OPENAI,
                ModelProvider.ANTHROPIC,
                ModelProvider.GOOGLE,
            ]:
                if provider not in providers_data:
                    continue

                # 프로바이더별 테이블 생성
                table = Table(
                    title=f"[bold]{provider.get_display_name()}[/bold]",
                    show_header=True,
                    header_style="bold magenta",
                    border_style="blue",
                )
                table.add_column("모델명", style="cyan", no_wrap=True)
                table.add_column("별칭", style="green")
                table.add_column("설명", style="white")
                table.add_column("컨텍스트", style="yellow", justify="right")

                # 모델 정보 추가
                for model_key, model_info in providers_data[provider]:
                    aliases = ", ".join(model_info.get("aliases", []))
                    description = model_info.get("description", "")
                    context_limit = f"{model_info.get('context_limit', 0):,}"

                    table.add_row(
                        model_key,
                        aliases if aliases else "-",
                        description,
                        context_limit,
                    )

                self.console.print(table)
                self.console.print()  # 빈 줄 추가

            # 사용법 안내
            self.console.print(
                "[dim]사용법: [/dim][bold]selvage review --model <모델명 또는 별칭>[/bold]"
            )
            self.console.print(
                "[dim]기본 모델 설정: [/dim][bold]selvage config model <모델명>[/bold]"
            )

        except Exception as e:
            console.error(
                f"모델 목록을 가져오는 중 오류가 발생했습니다: {str(e)}", exception=e
            )


# 전역 리뷰 디스플레이 인스턴스
review_display = ReviewDisplay()
