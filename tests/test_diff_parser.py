from unittest.mock import patch

import pytest

from selvage.src.diff_parser.constants import DELETED_FILE_PLACEHOLDER
from selvage.src.diff_parser.models.file_diff import FileDiff
from selvage.src.diff_parser.parser import parse_git_diff
from selvage.src.exceptions.diff_parsing_error import DiffParsingError


@pytest.fixture
def one_file_one_diff_text():
    return (
        "diff --git a/selvage/src/diff_parser/__init__.py "
        "b/selvage/src/diff_parser/__init__.py\n"
        "index f6b5043..4a57718 100644\n"
        "--- a/selvage/src/diff_parser/__init__.py\n"
        "+++ b/selvage/src/diff_parser/__init__.py\n"
        "@@ -48,7 +48,7 @@ def test_split_git_diff_short(sample_diff_short):\n"
        "def test_split_git_diff_middle():\n"
        '"""실제 middle.diff 파일을 사용한 테스트"""\n'
        'diff_text = read_diff_file("middle.diff")\n'
        "-result = split_git_diff(diff_text)\n"
        "+result = parse_git_diff(diff_text)\n"
    )


@pytest.fixture
def one_file_multiple_diff_text():
    return (
        "diff --git a/selvage/src/diff_parser/parser.py "
        "b/selvage/src/diff_parser/parser.py\n"
        "index 3d1e1ea..b7e9e75 100644\n"
        "--- a/selvage/src/diff_parser/parser.py\n"
        "+++ b/selvage/src/diff_parser/parser.py\n"
        "@@ -1,12 +1,15 @@\n"
        "import re\n"
        "import subprocess\n"
        "-from typing import Any\n"
        "from .models import DiffResult, FileDiff, Hunk\n"
        '+_PATTERN_DIFF_SPLIT = re.compile(r"(?=^diff --git)")\n'
        '+_PATTERN_HUNK_SPLIT = re.compile(r"(?=^@@ )")\n'
        '+_PATTERN_FILE_HEADER = re.compile(r"^diff --git a/(\\S+)")\n'
        "-def split_git_diff(diff_text: str) -> DiffResult:\n"
        '- """Git diff 텍스트를 파일별로 분할"""'
        "+def parse_git_diff(diff_text: str) -> DiffResult:\n"
        '+ """Git diff 텍스트를 파싱하여 구조화"""\n'
        "@@ -48,7 +48,7 @@ def test_split_git_diff_short(sample_diff_short):\n"
        "def test_split_git_diff_middle():\n"
        '"""실제 middle.diff 파일을 사용한 테스트"""\n'
        'diff_text = read_diff_file("middle.diff")\n'
        "-result = split_git_diff(diff_text)\n"
        "+result = parse_git_diff(diff_text)\n"
    )


@pytest.fixture
def multiple_files_diff_text():
    return (
        "diff --git a/selvage/src/diff_parser/__init__.py "
        "b/selvage/src/diff_parser/__init__.py\n"
        "index f6b5043..4a57718 100644\n"
        "--- a/selvage/src/diff_parser/__init__.py\n"
        "+++ b/selvage/src/diff_parser/__init__.py\n"
        "@@ -2,12 +2,11 @@\n"
        "Git diff 파싱 모듈\n"
        "-from .parser import parse_git_diff, run_git_diff, split_git_diff\n"
        "-from .models import Hunk, FileDiff, DiffResult\n"
        "+from .models import DiffResult, FileDiff, Hunk\n"
        "+from .parser import parse_git_diff, run_git_diff\n"
        "__all__ = [\n"
        '"parse_git_diff",\n'
        '- "split_git_diff",\n'
        '"run_git_diff",\n'
        '"Hunk",\n'
        '"FileDiff",\n'
        "@@ -48,7 +48,7 @@ def test_split_git_diff_short(sample_diff_short):\n"
        "def test_split_git_diff_middle():\n"
        '"""실제 middle.diff 파일을 사용한 테스트"""'
        'diff_text = read_diff_file("middle.diff")\n'
        "-result = split_git_diff(diff_text)\n"
        "+result = parse_git_diff(diff_text)\n"
        "diff --git a/legacy_tests/test_diff_parser.py "
        "b/legacy_tests/test_diff_parser.py\n"
        "index 334dbc1..5b2df91 100644\n"
        "--- a/legacy_tests/test_diff_parser.py\n"
        "+++ b/legacy_tests/test_diff_parser.py\n"
        "@@ -1,31 +1,31 @@\n"
        "-import pytest\n"
        "import os\n"
        "import subprocess\n"
        "from unittest.mock import MagicMock, patch\n"
        "-from selvage.src.diff_parser.parser import split_git_diff\n"
        "+from selvage.src.diff_parser.parser import parse_git_diff\n"
    )


@pytest.fixture
def deleted_file_diff_text():
    return (
        "diff --git a/deleted_file.txt b/deleted_file.txt\n"
        "deleted file mode 100644\n"
        "index 1234567..0000000\n"
        "--- a/deleted_file.txt\n"
        "+++ /dev/null\n"
        "@@ -1,5 +0,0 @@\n"
        "-This is the first line.\n"
        "-This is the second line.\n"
        "-This is the third line.\n"
        "-This is the fourth line.\n"
        "-This is the fifth line.\n"
    )


@pytest.fixture
def code_with_null_path_text():
    """코드 내용에 '+++ /dev/null' 문자열이 포함된 diff fixture"""
    return (
        "diff --git a/example.py b/example.py\n"
        "index 1234567..8901234 100644\n"
        "--- a/example.py\n"
        "+++ b/example.py\n"
        "@@ -1,5 +1,6 @@\n"
        " def process_file():\n"
        "     # 삭제된 파일을 처리하는 예시\n"
        "+    print('파일이 삭제되었을 때: +++ /dev/null')\n"
        "     return True\n"
        " \n"
        " def main():\n"
    )


def test_parse_git_diff_empty():
    with pytest.raises(DiffParsingError) as excinfo:
        parse_git_diff("", repo_path=".")
    assert "Empty diff provided." in str(excinfo.value)


def test_parse_git_diff_invalid():
    invalid_diff = "이것은 유효하지 않은 diff 형식입니다."
    with pytest.raises(DiffParsingError) as excinfo:
        parse_git_diff(invalid_diff, repo_path=".")
    assert "Invalid diff format." in str(excinfo.value)


@patch("selvage.src.diff_parser.parser.load_file_content")
def test_parse_git_diff(mock_load_file_content, one_file_one_diff_text):
    # 모킹 설정
    mock_load_file_content.return_value = "파일 전체 내용 모킹"

    result = parse_git_diff(one_file_one_diff_text, repo_path=".")
    assert len(result.files) == 1
    assert result.files[0].filename == "selvage/src/diff_parser/__init__.py"
    assert len(result.files[0].hunks) == 1
    assert "def test_split_git_diff_middle()" in result.files[0].hunks[0].content
    assert "-result = split_git_diff(diff_text)" in result.files[0].hunks[0].content
    assert "+result = parse_git_diff(diff_text)" in result.files[0].hunks[0].content

    # Hunk 라인 정보 검증
    hunk = result.files[0].hunks[0]
    assert hunk.start_line_original == 48
    assert hunk.line_count_original == 7
    assert hunk.start_line_modified == 48
    assert hunk.line_count_modified == 7

    # file_content 검증 추가
    assert result.files[0].file_content == "파일 전체 내용 모킹"
    mock_load_file_content.assert_called_once_with(
        "selvage/src/diff_parser/__init__.py", "."
    )

    # line_count 검증 추가
    assert result.files[0].line_count == 1


@patch("selvage.src.diff_parser.parser.load_file_content")
def test_parse_git_diff_one_file_multiple_hunks(
    mock_load_file_content, one_file_multiple_diff_text
):
    # 모킹 설정
    mock_load_file_content.return_value = "파서 파일 전체 내용"

    result = parse_git_diff(one_file_multiple_diff_text, repo_path=".")

    assert len(result.files) == 1
    assert result.files[0].filename == "selvage/src/diff_parser/parser.py"
    assert len(result.files[0].hunks) == 2

    # 첫 번째 헝크 확인
    assert "import re" in result.files[0].hunks[0].content
    assert "-from typing import Any" in result.files[0].hunks[0].content
    assert "+_PATTERN_DIFF_SPLIT = re.compile" in result.files[0].hunks[0].content
    assert "-def split_git_diff" in result.files[0].hunks[0].content
    assert "+def parse_git_diff" in result.files[0].hunks[0].content

    # 첫 번째 Hunk 라인 정보 검증
    hunk1 = result.files[0].hunks[0]
    assert hunk1.start_line_original == 1
    assert hunk1.line_count_original == 12
    assert hunk1.start_line_modified == 1
    assert hunk1.line_count_modified == 15

    # 두 번째 헝크 확인
    assert "def test_split_git_diff_middle()" in result.files[0].hunks[1].content
    assert "-result = split_git_diff(diff_text)" in result.files[0].hunks[1].content
    assert "+result = parse_git_diff(diff_text)" in result.files[0].hunks[1].content

    # 두 번째 Hunk 라인 정보 검증
    hunk2 = result.files[0].hunks[1]
    assert hunk2.start_line_original == 48
    assert hunk2.line_count_original == 7
    assert hunk2.start_line_modified == 48
    assert hunk2.line_count_modified == 7

    # file_content 검증 추가
    assert result.files[0].file_content == "파서 파일 전체 내용"
    mock_load_file_content.assert_called_once_with(
        "selvage/src/diff_parser/parser.py", "."
    )

    # line_count 검증 추가
    assert result.files[0].line_count == 1


@patch("selvage.src.diff_parser.parser.load_file_content")
def test_parse_git_diff_multiple_files(
    mock_load_file_content, multiple_files_diff_text
):
    # 모킹 설정 - 파일에 따라 다른 내용 반환
    def mock_file_content(filename: str, repo_path: str) -> str:
        if filename == "selvage/src/diff_parser/__init__.py" and repo_path == ".":
            return "초기화 파일 내용"
        elif filename == "legacy_tests/test_diff_parser.py" and repo_path == ".":
            return "테스트 파일 내용"
        return "기본 내용"

    mock_load_file_content.side_effect = mock_file_content

    result = parse_git_diff(multiple_files_diff_text, repo_path=".")

    assert len(result.files) == 2

    # 첫 번째 파일 확인
    assert result.files[0].filename == "selvage/src/diff_parser/__init__.py"
    assert len(result.files[0].hunks) == 2
    assert (
        "-from .parser import parse_git_diff, run_git_diff, split_git_diff"
        in result.files[0].hunks[0].content
    )
    assert (
        "+from .models import DiffResult, FileDiff, Hunk"
        in result.files[0].hunks[0].content
    )
    assert '- "split_git_diff",' in result.files[0].hunks[0].content
    assert "-result = split_git_diff(diff_text)" in result.files[0].hunks[1].content

    # 첫 번째 파일 file_content 검증
    assert result.files[0].file_content == "초기화 파일 내용"

    # 첫 번째 파일 line_count 검증
    assert result.files[0].line_count == 1

    # 두 번째 파일 확인
    assert result.files[1].filename == "legacy_tests/test_diff_parser.py"
    assert len(result.files[1].hunks) == 1
    assert "-import pytest" in result.files[1].hunks[0].content
    assert (
        "-from selvage.src.diff_parser.parser import split_git_diff"
        in result.files[1].hunks[0].content
    )
    assert (
        "+from selvage.src.diff_parser.parser import parse_git_diff"
        in result.files[1].hunks[0].content
    )

    # 두 번째 파일 file_content 검증
    assert result.files[1].file_content == "테스트 파일 내용"

    # 두 번째 파일 line_count 검증
    assert result.files[1].line_count == 1

    # 파일 별로 파일 내용을 불러오는지 확인
    assert mock_load_file_content.call_count == 2
    mock_load_file_content.assert_any_call("selvage/src/diff_parser/__init__.py", ".")
    mock_load_file_content.assert_any_call("legacy_tests/test_diff_parser.py", ".")


@patch("selvage.src.diff_parser.parser.load_file_content")
def test_parse_git_diff_without_full_context(
    mock_load_file_content, one_file_one_diff_text
):
    """file_content를 로드하는지 검증하는 테스트"""
    # 모킹 설정
    mock_load_file_content.return_value = "파일 전체 내용"

    result = parse_git_diff(one_file_one_diff_text, repo_path=".")

    assert len(result.files) == 1
    assert result.files[0].filename == "selvage/src/diff_parser/__init__.py"
    assert len(result.files[0].hunks) == 1

    # file_content를 로드해야 함 (파서 변경 사항)
    assert result.files[0].file_content == "파일 전체 내용"

    # line_count 검증
    assert result.files[0].line_count == 1

    # load_file_content가 호출되었는지 확인
    mock_load_file_content.assert_called_once_with(
        "selvage/src/diff_parser/__init__.py", "."
    )


@patch("selvage.src.diff_parser.parser.load_file_content")
def test_parse_git_diff_deleted_file(mock_load_file_content, deleted_file_diff_text):
    """파일이 삭제된 경우 file_content가 'Deleted file'로 설정되는지 검증하는 테스트"""

    result = parse_git_diff(deleted_file_diff_text, repo_path=".")

    assert len(result.files) == 1
    assert result.files[0].filename == "deleted_file.txt"
    assert len(result.files[0].hunks) == 1  # 삭제된 파일도 hunk 정보는 포함될 수 있음

    # 파일이 삭제된 경우 file_content는 "Deleted file"이어야 함
    assert result.files[0].file_content == DELETED_FILE_PLACEHOLDER

    # 삭제된 파일의 line_count는 0이어야 함
    assert result.files[0].line_count == 0

    # load_file_content가 호출되지 않았는지 확인
    mock_load_file_content.assert_not_called()


@patch("selvage.src.diff_parser.parser.load_file_content")
def test_parse_git_diff_with_null_path_in_code(
    mock_load_file_content, code_with_null_path_text
):
    """코드 내용에 '+++ /dev/null' 문자열이 포함된 경우에도 정상적으로 파싱되는지 검증"""  # noqa: E501
    # 모킹 설정
    mock_load_file_content.return_value = "실제 파일 내용입니다"

    result = parse_git_diff(code_with_null_path_text, repo_path=".")

    assert len(result.files) == 1
    assert result.files[0].filename == "example.py"

    # 이 파일은 삭제된 파일이 아니므로 file_content는 load_file_content의 반환값이어야 함  # noqa: E501
    assert result.files[0].file_content == "실제 파일 내용입니다"

    # line_count 검증
    assert result.files[0].line_count == 1

    # load_file_content가 호출되었는지 확인
    mock_load_file_content.assert_called_once_with("example.py", ".")

    # 코드에 '+++ /dev/null' 문자열이 포함되어 있는지 확인
    assert (
        "+    print('파일이 삭제되었을 때: +++ /dev/null')"
        in result.files[0].hunks[0].content
    )


class TestFileDiffCalculateLineCount:
    """FileDiff.calculate_line_count() 메서드 단위 테스트"""

    def test_calculate_line_count_normal_file(self):
        """정상적인 파일 내용이 있는 경우 라인 수 계산 테스트"""
        file_diff = FileDiff(
            filename="test.py",
            file_content="line1\nline2\nline3\nline4",
        )
        file_diff.calculate_line_count()
        assert file_diff.line_count == 4

    def test_calculate_line_count_single_line(self):
        """단일 라인 파일인 경우 테스트"""
        file_diff = FileDiff(
            filename="test.py",
            file_content="single line",
        )
        file_diff.calculate_line_count()
        assert file_diff.line_count == 1

    def test_calculate_line_count_empty_file(self):
        """빈 파일인 경우 테스트"""
        file_diff = FileDiff(
            filename="test.py",
            file_content="",
        )
        file_diff.calculate_line_count()
        assert file_diff.line_count == 0

    def test_calculate_line_count_whitespace_only(self):
        """공백만 있는 파일인 경우 테스트"""
        file_diff = FileDiff(
            filename="test.py",
            file_content="   \n  \t\n   ",
        )
        file_diff.calculate_line_count()
        # 공백도 유효한 라인이므로 3라인으로 계산
        assert file_diff.line_count == 3

    def test_calculate_line_count_deleted_file(self):
        """삭제된 파일인 경우 테스트"""
        file_diff = FileDiff(
            filename="test.py",
            file_content=DELETED_FILE_PLACEHOLDER,
        )
        file_diff.calculate_line_count()
        assert file_diff.line_count == 0

    def test_calculate_line_count_file_read_error(self):
        """파일 읽기 오류인 경우 테스트"""
        file_diff = FileDiff(
            filename="test.py",
            file_content="[파일 읽기 오류: test.py (FileNotFoundError)]",
        )
        file_diff.calculate_line_count()
        assert file_diff.line_count == 0

    def test_calculate_line_count_file_processing_error(self):
        """파일 처리 오류인 경우 테스트"""
        file_diff = FileDiff(
            filename="test.py",
            file_content="[파일 처리 중 예기치 않은 오류: test.py (Exception)]",
        )
        file_diff.calculate_line_count()
        assert file_diff.line_count == 0

    def test_calculate_line_count_with_trailing_newline(self):
        """마지막에 개행 문자가 있는 경우 테스트"""
        file_diff = FileDiff(
            filename="test.py",
            file_content="line1\nline2\nline3\n",
        )
        file_diff.calculate_line_count()
        # 마지막 개행 문자는 제거되어 실제 라인 수인 3으로 계산
        assert file_diff.line_count == 3

    def test_calculate_line_count_mixed_content(self):
        """다양한 내용이 혼재된 파일 테스트"""
        file_diff = FileDiff(
            filename="test.py",
            file_content="# 주석\n\ndef function():\n    pass\n\n# 마지막 주석",
        )
        file_diff.calculate_line_count()
        assert file_diff.line_count == 6

    def test_calculate_line_count_without_trailing_newline(self):
        """마지막에 개행 문자가 없는 경우 테스트"""
        file_diff = FileDiff(
            filename="test.py",
            file_content="line1\nline2\nline3",
        )
        file_diff.calculate_line_count()
        # 마지막 개행 문자가 없으므로 그대로 3라인
        assert file_diff.line_count == 3

    def test_calculate_line_count_edge_cases(self):
        """다양한 엣지 케이스 테스트"""
        # 개행 문자만 있는 경우 (빈 라인 1개)
        file_diff = FileDiff(filename="test.py", file_content="\n")
        file_diff.calculate_line_count()
        assert file_diff.line_count == 1

        # 여러 개행 문자로 끝나는 경우
        file_diff = FileDiff(filename="test.py", file_content="line1\n\n\n")
        file_diff.calculate_line_count()
        assert file_diff.line_count == 3

        # 한 줄에 개행 문자가 있는 경우
        file_diff = FileDiff(filename="test.py", file_content="single_line\n")
        file_diff.calculate_line_count()
        assert file_diff.line_count == 1
