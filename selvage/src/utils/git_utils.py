import subprocess
from enum import Enum
from pathlib import Path

from selvage.src.utils.base_console import console


class GitDiffMode(str, Enum):
    """git diff 동작 모드 열거형"""

    STAGED = "staged"
    TARGET_COMMIT = "target_commit"
    TARGET_BRANCH = "target_branch"
    UNSTAGED = "unstaged"


class GitDiffUtility:
    """Git diff 관련 작업을 위한 유틸리티 클래스"""

    def __init__(
        self,
        repo_path: str,
        mode: GitDiffMode = GitDiffMode.UNSTAGED,
        target: str | None = None,
    ) -> None:
        """GitDiffUtility 초기화

        Args:
            repo_path (str): Git 저장소 경로
            mode (GitDiffMode): diff 동작 모드
            target (str | None): mode에 따른 대상 (commit hash 또는 branch 이름)

        Raises:
            ValueError: 저장소 경로가 유효하지 않은 경우
        """
        self.repo_path = repo_path
        self.mode = mode
        self.target = target

        # 경로 유효성 검증
        path = Path(repo_path)
        if not path.exists() or not (path / ".git").exists():
            raise ValueError(f"오류: 유효한 Git 저장소 경로를 지정하세요: {repo_path}")

    @classmethod
    def from_args(cls, args) -> "GitDiffUtility":
        """명령줄 인수에서 GitDiffUtility 인스턴스를 생성합니다.

        Args:
            args: 명령줄 인수 객체 (repo_path, staged, target_commit, target_branch 속성 포함)

        Returns:
            GitDiffUtility: 초기화된 유틸리티 인스턴스

        Raises:
            ValueError: 저장소 경로가 유효하지 않은 경우
        """
        mode = GitDiffMode.UNSTAGED
        target = None

        if getattr(args, "staged", False):
            mode = GitDiffMode.STAGED
        elif getattr(args, "target_commit", None):
            mode = GitDiffMode.TARGET_COMMIT
            target = args.target_commit
        elif getattr(args, "target_branch", None):
            mode = GitDiffMode.TARGET_BRANCH
            target = args.target_branch

        return cls(repo_path=str(Path(args.repo_path)), mode=mode, target=target)

    def get_diff(self) -> str:
        """Git diff 명령을 실행하고 결과를 반환합니다.

        Returns:
            str: git diff 명령의 출력
        """
        cmd = ["git", "-C", self.repo_path, "diff", "--unified=5"]

        if self.mode == GitDiffMode.STAGED:
            cmd.append("--cached")
        elif self.mode == GitDiffMode.TARGET_COMMIT:
            if not self.target or not self.target.strip():
                console.error("오류: commit 값이 비어있습니다.")
                return ""
            cmd.append(f"{self.target}..HEAD")
        elif self.mode == GitDiffMode.TARGET_BRANCH:
            if not self.target or not self.target.strip():
                console.error("오류: branch 값이 비어있습니다.")
                return ""
            cmd.append(f"{self.target}..HEAD")

        try:
            process_result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, encoding="utf-8"
            )
            return process_result.stdout
        except subprocess.CalledProcessError as e:
            console.error(
                f"Git diff 명령 실행 중 오류 발생: {e}\n실행된 명령어: {' '.join(cmd)}",
                exception=e,
            )
            return ""
        except Exception as e:
            console.error(
                f"Git diff 처리 중 예상치 못한 오류 발생: {e}\n실행된 명령어: {' '.join(cmd)}",
                exception=e,
            )
            return ""
