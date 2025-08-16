"""리뷰 프로세스 관련 UI 표시를 위한 모듈."""

import json
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
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
    """경로를 축약된 형태로 표시합니다."""
    import os

    # 홈 디렉토리 축약
    path = path.replace(str(Path.home()), "~")

    # 경로가 너무 길면 가운데를 생략
    if len(path) > 60:
        parts = path.split(os.sep)
        if len(parts) > 3:
            # 앞 2개와 뒤 1개만 남기고 ...으로 생략
            shortened = os.sep.join(parts[:2] + ["..."] + parts[-1:])
            return shortened

    return path


def _load_review_log(log_path: str) -> dict | None:
    """리뷰 로그 파일을 로드합니다."""
    try:
        with open(log_path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        console.error(f"리뷰 로그 파일을 읽을 수 없습니다: {log_path}")
        return None


def _format_severity_badge(severity: str) -> str:
    """심각도 배지를 생성합니다."""
    severity_upper = severity.upper()
    if severity_upper == "HIGH":
        return "[bold red]HIGH[/bold red]"
    elif severity_upper == "MEDIUM":
        return "[bold yellow]MEDIUM[/bold yellow]"
    elif severity_upper == "LOW":
        return "[bold blue]LOW[/bold blue]"
    else:
        return "[bold cyan]INFO[/bold cyan]"


def _detect_language_from_filename(filename: str) -> str:
    """파일명에서 프로그래밍 언어를 추론합니다."""
    if not filename:
        return "text"

    ext = Path(filename).suffix.lower()
    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".php": "php",
        ".rb": "ruby",
        ".go": "go",
        ".rs": "rust",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".sql": "sql",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
        ".sass": "sass",
        ".json": "json",
        ".xml": "xml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".md": "markdown",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "zsh",
        ".fish": "fish",
    }

    return language_map.get(ext, "text")


def _create_syntax_block(code: str, filename: str = "") -> Syntax:
    """코드 블록을 구문 강조와 함께 생성합니다."""
    language = _detect_language_from_filename(filename)

    return Syntax(
        code.strip(),
        language,
        theme="monokai",
        line_numbers=True,
        word_wrap=True,
        background_color="default",
    )


def _create_recommendations_panel(recommendations: list) -> Panel:
    """추천사항을 패널로 생성합니다."""
    if not recommendations:
        content = "[dim]추천사항이 없습니다.[/dim]"
    else:
        content_lines = []
        for i, rec in enumerate(recommendations, 1):
            content_lines.append(f"[bold cyan]{i}.[/bold cyan] {rec}")
        content = "\n".join(content_lines)

    return Panel(
        content,
        title="[bold green]추천사항[/bold green]",
        border_style="green",
        padding=(1, 2),
    )


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
        token_info = (
            f"{_format_token_count(estimated_cost.input_tokens)} → "
            f"{_format_token_count(estimated_cost.output_tokens)} tokens"
        )

        # 경로를 간단하게 표시
        simplified_path = _shorten_path(log_path)

        # 통합 Panel 내용 구성
        content = (
            f"[bold cyan]모델:[/bold cyan] [white]{model_info['full_name']}[/white]\n"
            f"[dim]{model_info['description']}[/dim]\n\n"
            f"[bold yellow]비용:[/bold yellow] "
            f"[white]{estimated_cost.total_cost_usd}[/white] "
            f"[dim]({token_info})[/dim]\n"
            f"[dim]※ 추정 비용이므로 각 AI 서비스에서 정확한 비용을 "
            f"확인하세요.[/dim]\n\n"
            f"[bold green]저장:[/bold green] [white]{simplified_path}[/white]"
        )

        panel = Panel(
            Align.center(content),
            title="[bold]코드 리뷰 완료[/bold]",
            border_style="cyan",
            width=80,
            padding=(1, 2),
        )

        self.console.print(panel)

    def print_review_result(self, log_path: str, use_pager: bool = True) -> None:
        """리뷰 결과를 터미널에 출력합니다."""

        log_data = _load_review_log(log_path)
        if not log_data:
            return

        review_response = log_data.get("review_response")
        if not review_response:
            console.error("리뷰 응답 데이터가 없습니다.")
            return

        model_info = log_data.get("model", {})
        model_name = model_info.get("name", "Unknown")

        # 요약 정보 패널
        summary = review_response.get("summary", "")
        score = review_response.get("score")
        issues = review_response.get("issues", [])
        recommendations = review_response.get("recommendations", [])

        # 요약 패널 생성
        summary_content = f"[bold cyan]모델:[/bold cyan] {model_name}\n\n"
        summary_content += (
            f"[bold yellow]전체 점수:[/bold yellow] {score}/10\n\n" if score else ""
        )
        summary_content += f"[bold red]발견된 이슈:[/bold red] {len(issues)}개\n\n"
        summary_content += (
            f"[bold green]추천사항:[/bold green] {len(recommendations)}개\n\n"
        )

        if summary:
            summary_content += f"[bold white]요약:[/bold white]\n{summary}"

        summary_panel = Panel(
            summary_content,
            title="[bold]리뷰 결과 요약[/bold]",
            border_style="cyan",
            padding=(1, 2),
        )

        # 출력 함수 정의
        def _print_content() -> None:
            # 요약 패널 출력
            self.console.print(summary_panel)
            self.console.print()

            # 이슈 정보 출력
            if issues:
                self.console.print("[bold cyan]이슈 상세 정보[/bold cyan]\n")
                for i, issue in enumerate(issues, 1):
                    severity = issue.get("severity", "INFO").upper()
                    # file과 file_name 둘 다 확인
                    file_name = issue.get("file") or issue.get("file_name", "")
                    line_number = issue.get("line_number", "")
                    description = issue.get("description", "")
                    suggestion = issue.get("suggestion", "")
                    target_code = issue.get("target_code", "")
                    suggested_code = issue.get("suggested_code", "")

                    # 이슈 내용 구성 (항목 간 간격 증가)
                    issue_content = f"[bold]심각도:[/bold] {severity}\n\n"
                    issue_content += f"[bold]파일:[/bold] {file_name}"
                    if line_number:
                        issue_content += f" (라인 {line_number})"
                    issue_content += f"\n\n[bold]설명:[/bold]\n{description}"

                    if suggestion:
                        issue_content += f"\n\n[bold]제안:[/bold]\n{suggestion}"

                    border_style = (
                        "red"
                        if severity == "HIGH"
                        else "yellow"
                        if severity == "MEDIUM"
                        else "blue"
                    )

                    issue_panel = Panel(
                        issue_content,
                        title=f"[bold]{i}. {severity}[/bold]",
                        border_style=border_style,
                        padding=(1, 2),
                    )
                    self.console.print(issue_panel)

                    # 코드 블록이 있는 경우 별도 패널로 출력
                    if target_code or suggested_code:
                        if target_code:
                            self.console.print()
                            current_syntax = _create_syntax_block(
                                target_code, file_name
                            )
                            current_panel = Panel(
                                current_syntax,
                                title="[bold red]현재 코드[/bold red]",
                                border_style="red",
                                padding=(0, 1),
                            )
                            self.console.print(current_panel)

                        if suggested_code:
                            self.console.print()
                            suggested_syntax = _create_syntax_block(
                                suggested_code, file_name
                            )
                            suggested_panel = Panel(
                                suggested_syntax,
                                title="[bold green]개선된 코드[/bold green]",
                                border_style="green",
                                padding=(0, 1),
                            )
                            self.console.print(suggested_panel)

                    self.console.print()  # 이슈 사이 간격
            else:
                self.console.print("[bold green]발견된 이슈가 없습니다![/bold green]")

            # 추천사항 출력
            if recommendations:
                self.console.print()
                rec_panel = _create_recommendations_panel(recommendations)
                self.console.print(rec_panel)

        # Pager 사용 여부에 따라 출력
        if use_pager:
            # Pager로 출력 (스크롤링 가능)
            with self.console.pager(styles=True):
                _print_content()
        else:
            # 직접 출력 (테스트용)
            _print_content()

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
        ) as _:
            # 백그라운드에서 물결치는 진행률 업데이트
            stop_progress = threading.Event()

            def update_progress() -> None:
                step = 0
                while not stop_progress.is_set():
                    # 톱니파 패턴: 0에서 100까지 갔다가 다시 0에서 시작
                    cycle_length = 50  # 한 사이클의 길이 (조절 가능)
                    progress_value = (step % cycle_length) * (100 / cycle_length)
                    progress.update(task, completed=progress_value)

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
                time.sleep(0.5)  # 완료 상태를 잠시 보여줌
                # Live가 종료된 후에도 Panel이 잠시 유지됩니다.

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
                ModelProvider.OPENROUTER,
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
                "[dim]사용법: [/dim][bold]selvage review --model "
                "<모델명 또는 별칭>[/bold]"
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
