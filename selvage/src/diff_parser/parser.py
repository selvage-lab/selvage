import re

from selvage.src.exceptions.diff_parsing_error import DiffParsingError
from selvage.src.utils import load_file_content

from .models import DiffResult, FileDiff, Hunk

_PATTERN_DIFF_SPLIT = re.compile(r"(?=^diff --git)", flags=re.MULTILINE)
_PATTERN_HUNK_SPLIT = re.compile(r"(?=^@@ )", flags=re.MULTILINE)
_PATTERN_FILE_HEADER = re.compile(r"^diff --git a/(\S+) b/(\S+)", flags=re.MULTILINE)
_DELETED_FILE_PLACEHOLDER = "삭제된 파일"
_DELETED_FILE_PATTERN = re.compile(r"^--- a/.*\n^\+\+\+ /dev/null$", flags=re.MULTILINE)


def _parse_single_file_diff(raw_diff: str, repo_path: str) -> FileDiff | None:
    """단일 파일 diff 텍스트를 파싱하여 FileDiff 객체를 반환합니다.

    Args:
        raw_diff (str): 단일 파일에 대한 git diff 텍스트.
        repo_path (str): Git 저장소 경로.

    Returns:
        FileDiff | None: 파싱된 FileDiff 객체 또는 파싱할 수 없는 경우 None.
    """
    if not raw_diff.strip():
        return None

    header_match = _PATTERN_FILE_HEADER.search(raw_diff)
    if not header_match:
        return None
    filename = header_match.group(2)

    hunks_text = _PATTERN_HUNK_SPLIT.split(raw_diff)
    hunk_list = [
        Hunk.from_hunk_text(h) for h in hunks_text if h.lstrip().startswith("@@")
    ]

    file_content: str | None
    if _is_deleted_file(raw_diff):
        file_content = _DELETED_FILE_PLACEHOLDER
    else:
        try:
            file_content = load_file_content(filename, repo_path)
        except (FileNotFoundError, PermissionError) as e:
            # 파일 읽기 실패 시, 오류 메시지를 content로 사용하고 파싱은 계속 진행
            file_content = f"[파일 읽기 오류: {filename} ({e.__class__.__name__})]"
        except Exception as e:
            # 기타 예외 발생 시에도 오류 메시지를 content로 사용
            file_content = (
                f"[파일 처리 중 예기치 않은 오류: {filename} ({e.__class__.__name__})]"
            )

    parsed_diff = FileDiff(
        filename=filename, file_content=file_content, hunks=hunk_list
    )
    parsed_diff.detect_language()
    parsed_diff.calculate_changes()
    parsed_diff.calculate_line_count()
    return parsed_diff


def parse_git_diff(diff_text: str, repo_path: str) -> DiffResult:
    """Git diff 텍스트를 파싱하여 구조화된 DiffResult 객체를 반환합니다.

    Args:
        diff_text (str): git diff 명령어의 출력 텍스트
        repo_path (str): Git 저장소 경로

    Returns:
        DiffResult: Git diff 결과를 나타내는 객체

    Raises:
        DiffParsingError: diff가 비어있거나 유효하지 않은 형식인 경우
    """
    if not diff_text:
        raise DiffParsingError("빈 diff가 제공되었습니다.")

    file_diffs = _PATTERN_DIFF_SPLIT.split(diff_text)
    result = DiffResult()

    for raw_diff in file_diffs:
        file_diff = _parse_single_file_diff(raw_diff, repo_path)
        if file_diff:
            result.files.append(file_diff)

    if not result.files:
        raise DiffParsingError("유효하지 않은 diff 형식입니다.")

    return result


def _is_deleted_file(raw_diff: str) -> bool:
    """파일이 삭제된 경우 True를 반환합니다.

    Git diff에서 삭제된 파일은 diff 헤더에 '+++ /dev/null' 패턴이 있습니다.
    단순 문자열 포함 여부가 아닌 정규표현식으로 헤더 패턴을 확인합니다.
    """
    return bool(_DELETED_FILE_PATTERN.search(raw_diff))
