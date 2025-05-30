"""is_ignore_file 함수에 대한 유닛 테스트."""

import pytest

from selvage.src.utils.file_utils import is_ignore_file


class TestIsIgnoreFile:
    """is_ignore_file 함수에 대한 테스트 클래스."""

    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("test.exe", True),
            ("image.png", True),
            ("archive.zip", True),
            ("document.pdf", True),
            ("music.mp3", True),
        ],
    )
    def test_binary_extension(self, filename: str, expected: bool) -> None:
        """바이너리 확장자를 가진 파일에 대해 올바르게 판단하는지 테스트합니다.

        Args:
            filename: 테스트할 파일명
            expected: 예상 결과 (True: 무시해야 할 파일)
        """
        assert is_ignore_file(filename) == expected

    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("code.py", False),
            ("doc.txt", False),
            ("config.json", False),
            ("index.html", False),
            ("script.js", False),
        ],
    )
    def test_text_extension(self, filename: str, expected: bool) -> None:
        """텍스트 확장자를 가진 파일에 대해 올바르게 판단하는지 테스트합니다.

        Args:
            filename: 테스트할 파일명
            expected: 예상 결과 (False: 무시하지 않아도 되는 파일)
        """
        assert is_ignore_file(filename) == expected

    @pytest.mark.parametrize(
        "filename,expected",
        [
            (".DS_Store", True),
            ("gradlew", True),
            (".env", True),
            (".gitignore", True),
            ("gradle-wrapper.properties", True),
        ],
    )
    def test_ignore_filename(self, filename: str, expected: bool) -> None:
        """무시해야 할 특수 파일명에 대해 올바르게 판단하는지 테스트합니다.

        Args:
            filename: 테스트할 파일명
            expected: 예상 결과 (True: 무시해야 할 파일)
        """
        assert is_ignore_file(filename) == expected

    @pytest.mark.parametrize(
        "filepath,expected",
        [
            ("/path/to/image.jpg", True),
            ("src/main/resources/config.json", False),
            ("../project/gradlew", True),
            ("C:\\Users\\user\\Documents\\file.txt", False),
            ("/var/www/html/.env.local", True),
        ],
    )
    def test_with_path(self, filepath: str, expected: bool) -> None:
        """경로가 포함된 파일명에 대해 올바르게 판단하는지 테스트합니다.

        Args:
            filepath: 테스트할 파일 경로
            expected: 예상 결과
        """
        assert is_ignore_file(filepath) == expected
