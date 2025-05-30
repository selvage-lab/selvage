"""run_git_diff 함수에 대한 단위 테스트 모듈."""

import os
import subprocess
from dataclasses import dataclass

import pytest

from selvage.src.utils.git_utils import GitDiffMode, GitDiffUtility


@pytest.fixture
def git_repo(tmp_path):
    """임시 Git 저장소를 생성하고 초기 커밋을 만듭니다.

    Args:
        tmp_path: pytest의 임시 디렉터리 경로

    Returns:
        str: 생성된 git 저장소의 경로
    """
    repo_dir = tmp_path / "git-repo"
    repo_dir.mkdir()
    subprocess.run(["git", "init"], cwd=str(repo_dir), check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=str(repo_dir)
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=str(repo_dir))

    file_path = repo_dir / "file.txt"
    file_path.write_text("Initial content")

    subprocess.run(["git", "add", "."], cwd=str(repo_dir), check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"], cwd=str(repo_dir), check=True
    )

    return str(repo_dir)


def test_git_diff_utility_with_unstaged_changes(git_repo):
    """스테이징되지 않은 변경사항에 대한 diff 결과를 검증합니다."""
    file_path = os.path.join(git_repo, "file.txt")
    with open(file_path, "w") as f:
        f.write("Modified content")

    git_diff = GitDiffUtility(git_repo, mode=GitDiffMode.UNSTAGED)
    diff = git_diff.get_diff()

    assert "-Initial content" in diff
    assert "+Modified content" in diff


def test_git_diff_utility_with_staged_changes(git_repo):
    """스테이징된 변경사항에 대한 diff 결과를 검증합니다."""
    file_path = os.path.join(git_repo, "file.txt")
    with open(file_path, "w") as f:
        f.write("Staged content")
    subprocess.run(["git", "add", "file.txt"], cwd=git_repo, check=True)

    git_diff = GitDiffUtility(git_repo, mode=GitDiffMode.STAGED)
    diff = git_diff.get_diff()

    assert "-Initial content" in diff
    assert "+Staged content" in diff


def test_git_diff_utility_with_target_commit(git_repo):
    """특정 커밋과의 diff 결과를 검증합니다."""
    file_path = os.path.join(git_repo, "file.txt")
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=git_repo,
        capture_output=True,
        text=True,
        check=True,
    )
    initial_commit = result.stdout.strip()

    with open(file_path, "w") as f:
        f.write("New commit content")
    subprocess.run(["git", "add", "file.txt"], cwd=git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "Second commit"], cwd=git_repo, check=True)

    git_diff = GitDiffUtility(
        git_repo, mode=GitDiffMode.TARGET_COMMIT, target=initial_commit
    )
    diff = git_diff.get_diff()

    assert "-Initial content" in diff
    assert "+New commit content" in diff


def test_git_diff_utility_with_empty_target_commit(git_repo):
    """빈 target_commit 인자에 대한 예외 처리를 검증합니다."""
    git_diff = GitDiffUtility(git_repo, mode=GitDiffMode.TARGET_COMMIT, target="")
    diff = git_diff.get_diff()

    assert diff == ""


def test_git_diff_utility_from_args(git_repo):
    """from_args 메서드로 인스턴스 생성을 검증합니다."""

    # 테스트용 Args 클래스 정의
    @dataclass
    class MockArgs:
        repo_path: str
        staged: bool = False
        target_commit: str | None = None
        target_branch: str | None = None

    args = MockArgs(repo_path=git_repo, staged=True)

    git_diff = GitDiffUtility.from_args(args)
    assert git_diff.mode == GitDiffMode.STAGED
    assert git_diff.repo_path == git_repo
    assert git_diff.target is None
