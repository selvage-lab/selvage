"""find_project_root 함수에 대한 유닛 테스트."""

from pathlib import Path
from unittest import mock

import pytest

from selvage.src.utils.file_utils import find_project_root


@pytest.fixture
def project_structure(tmpdir):
    """TestFindProjectRoot 테스트를 위한 기본 프로젝트 구조를 생성합니다.

    Args:
        tmpdir: pytest의 임시 디렉토리 픽스처

    Returns:
        tuple[Path, Path, Path]: (project_dir, src_dir, module_file) 튜플
    """
    # 임시 디렉토리에 프로젝트 구조 생성
    project_dir = Path(tmpdir) / "project"
    src_dir = project_dir / "src" / "utils"
    src_dir.mkdir(parents=True)

    # 모듈 파일 생성
    module_file = src_dir / "file_utils.py"
    module_file.touch()

    return project_dir, src_dir, module_file


class TestFindProjectRoot:
    """find_project_root 함수에 대한 테스트 클래스."""

    def test_found_git_root(self, project_structure) -> None:
        """Git 저장소 루트를 올바르게 찾는지 테스트합니다."""
        # 테스트 전 캐시 초기화
        find_project_root.cache_clear()

        project_dir, _, module_file = project_structure

        # .git 디렉토리 생성 (프로젝트 루트 표시)
        git_dir = project_dir / ".git"
        git_dir.mkdir()

        # __file__ 값을 모킹하고 Path.cwd()도 모킹합니다.
        with (
            mock.patch("selvage.src.utils.file_utils.__file__", str(module_file)),
            mock.patch("pathlib.Path.cwd", return_value=project_dir),
        ):
            root = find_project_root()
            # 정규화된 경로로 비교
            assert root.resolve() == project_dir.resolve()

    def test_found_pyproject_root(self, project_structure) -> None:
        """pyproject.toml이 있는 루트를 올바르게 찾는지 테스트합니다."""
        # 테스트 전 캐시 초기화
        find_project_root.cache_clear()

        project_dir, _, module_file = project_structure

        # pyproject.toml 파일 생성 (프로젝트 루트 표시)
        pyproject_file = project_dir / "pyproject.toml"
        pyproject_file.touch()

        # __file__ 값을 모킹하고 Path.cwd()도 모킹합니다.
        with (
            mock.patch("selvage.src.utils.file_utils.__file__", str(module_file)),
            mock.patch("pathlib.Path.cwd", return_value=project_dir),
        ):
            root = find_project_root()
            # 정규화된 경로로 비교
            assert root.resolve() == project_dir.resolve()

    def test_root_not_found(self, project_structure) -> None:
        """프로젝트 루트를 찾지 못할 때 적절한 예외가 발생하는지 테스트합니다."""
        # 테스트 전 캐시 초기화
        find_project_root.cache_clear()

        project_dir, _, module_file = project_structure

        # exists 메서드 모킹하여 항상 False 반환하도록 설정
        with (
            mock.patch("pathlib.Path.exists", return_value=False),
            mock.patch("pathlib.Path.cwd", return_value=project_dir),
        ):
            # __file__ 값을 모킹하여 find_project_root 내부에서 올바른 시작점을 갖도록 함
            with mock.patch("selvage.src.utils.file_utils.__file__", str(module_file)):
                with pytest.raises(FileNotFoundError):
                    find_project_root()

    def test_lru_cache(self, project_structure) -> None:
        """캐싱 기능이 올바르게 작동하는지 테스트합니다."""
        # 테스트 전 캐시 초기화
        find_project_root.cache_clear()

        project_dir, _, module_file = project_structure

        # .git 디렉토리 생성
        git_dir = project_dir / ".git"
        git_dir.mkdir()

        # __file__ 값 모킹 및 Path.cwd() 모킹
        with (
            mock.patch("selvage.src.utils.file_utils.__file__", str(module_file)),
            mock.patch("pathlib.Path.cwd", return_value=project_dir),
        ):
            # 첫 번째 호출
            first_result = find_project_root()

            # .git 디렉토리 삭제 후 requirements.txt 생성
            git_dir.rmdir()
            req_file = project_dir / "requirements.txt"
            req_file.touch()

            # 두 번째 호출 (캐시된 결과가 반환되어야 함)
            second_result = find_project_root()

            # 정규화된 경로로 비교
            assert first_result.resolve() == second_result.resolve()
            assert second_result.resolve() == project_dir.resolve()

            # 캐시 초기화 후 다시 호출
            find_project_root.cache_clear()

            # 세 번째 호출 (새 결과가 반환되어야 함, 하지만 여전히 같은 디렉토리)
            # Path.cwd()는 계속 모킹된 상태이므로 project_dir을 기준으로 찾음
            third_result = find_project_root()
            assert third_result.resolve() == project_dir.resolve()
