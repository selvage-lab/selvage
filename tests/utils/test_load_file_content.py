"""load_file_content 함수에 대한 유닛 테스트."""

import pytest

from selvage.src.utils.file_utils import load_file_content


@pytest.fixture
def temp_repo_with_files(tmpdir) -> str:
    """테스트용 임시 저장소와 파일을 생성합니다.

    Args:
        tmpdir: pytest의 임시 디렉토리 픽스처

    Returns:
        str: 생성된 임시 저장소 경로
    """
    # 임시 저장소 디렉토리 생성
    repo_dir = tmpdir.mkdir("repo")

    # 텍스트 파일 생성
    text_file = repo_dir.join("file.txt")
    text_file.write("텍스트 파일 내용")

    # 중첩 디렉토리 및 파일 생성
    subdir = repo_dir.mkdir("subdir")
    subdir_file = subdir.join("subfile.py")
    subdir_file.write(
        "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\nprint('테스트')"
    )

    # 바이너리 파일로 간주될 파일 생성
    binary_file = repo_dir.join("image.png")
    binary_file.write("가짜 바이너리 내용")

    # 외부 디렉토리 (저장소 외부 테스트용)
    tmpdir.mkdir("outside")
    outside_file = tmpdir.join("outside/outside.txt")
    outside_file.write("저장소 외부 파일")

    return str(repo_dir)


class TestLoadFileContent:
    """load_file_content 함수에 대한 테스트 클래스."""

    def test_text_file(self, temp_repo_with_files: str) -> None:
        """텍스트 파일 로딩이 올바르게 작동하는지 테스트합니다.

        Args:
            temp_repo_with_files: 임시 저장소 경로 픽스처
        """

        content = load_file_content("file.txt", temp_repo_with_files)
        assert content == "텍스트 파일 내용"

    def test_nested_file(self, temp_repo_with_files: str) -> None:
        """중첩 디렉토리 내 파일 로딩이 올바르게 작동하는지 테스트합니다.

        Args:
            temp_repo_with_files: 임시 저장소 경로 픽스처
        """

        content = load_file_content("subdir/subfile.py", temp_repo_with_files)
        assert "print('테스트')" in content

    def test_file_not_found(self, temp_repo_with_files: str) -> None:
        """존재하지 않는 파일 로딩 시 적절한 예외가 발생하는지 테스트합니다.

        Args:
            temp_repo_with_files: 임시 저장소 경로 픽스처
        """

        with pytest.raises(FileNotFoundError) as excinfo:
            load_file_content("non_existent.txt", temp_repo_with_files)

        assert str(excinfo.value) == "File not found: non_existent.txt"

    def test_permission_error(self, temp_repo_with_files: str) -> None:
        """저장소 외부 파일 접근 시도 시 적절한 예외가 발생하는지 테스트합니다.

        Args:
            temp_repo_with_files: 임시 저장소 경로 픽스처
        """

        with pytest.raises(PermissionError) as excinfo:
            load_file_content("../outside/outside.txt", temp_repo_with_files)

        assert str(excinfo.value) == "접근 권한이 없습니다: ../outside/outside.txt"

    def test_binary_file(self, temp_repo_with_files: str) -> None:
        """제외 파일 로딩 시 적절한 메시지를 반환하는지 테스트합니다.

        Args:
            temp_repo_with_files: 임시 저장소 경로 픽스처
        """

        content = load_file_content("image.png", temp_repo_with_files)
        assert content == "[제외 파일: image.png]"
