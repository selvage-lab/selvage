"""get_file_path 함수에 대한 유닛 테스트."""

import os
import tempfile

import pytest

from selvage.src.utils.file_utils import get_file_path


class TestGetFilePath:
    """get_file_path 함수에 대한 테스트 클래스."""

    @pytest.mark.parametrize(
        "filename, repo_path, expected_result, should_raise",
        [
            # 성공 케이스
            ("file.txt", "/tmp/repo", "/tmp/repo/file.txt", False),
            ("subdir/file.py", "/tmp/repo", "/tmp/repo/subdir/file.py", False),
            ("deep/nested/path/file.md", "/tmp/repo", 
             "/tmp/repo/deep/nested/path/file.md", False),
            ("", "/tmp/repo", "/tmp/repo", False),  # 빈 문자열 (저장소 루트)
            (".", "/tmp/repo", "/tmp/repo", False),  # 저장소 루트 접근
            
            # 실패 케이스 (PermissionError)
            ("../outside.txt", "/tmp/repo", None, True),  # Path traversal
            ("../../etc/passwd", "/tmp/repo", None, True),  # 심각한 path traversal
            ("../../../root/.ssh/id_rsa", "/tmp/repo", None, True),  
            ("subdir/../../../outside.txt", "/tmp/repo", None, True),
            ("/etc/passwd", "/tmp/repo", None, True),  # 절대 경로
            ("/root/.bashrc", "/tmp/repo", None, True),
        ]
    )
    def test_get_file_path(
        self, 
        filename: str, 
        repo_path: str, 
        expected_result: str | None, 
        should_raise: bool
    ) -> None:
        """다양한 파일 경로에 대해 get_file_path의 동작을 테스트합니다.
        
        Args:
            filename: 테스트할 파일 경로
            repo_path: 저장소 루트 경로
            expected_result: 예상되는 절대 경로 결과
            should_raise: PermissionError가 발생해야 하는지 여부
        """
        if should_raise:
            with pytest.raises(PermissionError) as exc_info:
                get_file_path(filename, repo_path)
            
            assert "접근 권한이 없습니다" in str(exc_info.value)
            assert filename in str(exc_info.value)
        else:
            result = get_file_path(filename, repo_path)
            
            # 결과 검증
            assert result == expected_result
            assert os.path.isabs(result)
            
            # 저장소 경로 내부에 있는지 확인
            abs_repo_path = os.path.abspath(repo_path)
            assert (
                result.startswith(abs_repo_path + os.sep) 
                or result == abs_repo_path
            )

    def test_relative_repo_path(self) -> None:
        """상대 경로로 주어진 repo_path에 대해서도 올바르게 동작하는지 테스트합니다."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                relative_repo = "test_repo"
                os.makedirs(relative_repo, exist_ok=True)
                
                result = get_file_path("file.txt", relative_repo)
                expected = os.path.abspath(
                    os.path.join(relative_repo, "file.txt")
                )
                
                assert result == expected
                assert os.path.isabs(result)
            finally:
                os.chdir(original_cwd)

    def test_edge_cases(self) -> None:
        """Windows 스타일 경로와 유니코드 파일명 등 엣지 케이스를 테스트합니다."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = temp_dir
            abs_repo_path = os.path.abspath(repo_path)
            
            # Windows 스타일 경로 구분자
            result1 = get_file_path("subdir\\file.txt", repo_path)
            assert os.path.isabs(result1)
            assert (
                result1.startswith(abs_repo_path + os.sep)
                or result1 == abs_repo_path
            )
            
            # 유니코드 파일명
            filename = "한글파일.txt"
            result2 = get_file_path(filename, repo_path)
            expected = os.path.abspath(os.path.join(repo_path, filename))
            assert result2 == expected
            assert result2.startswith(abs_repo_path + os.sep)