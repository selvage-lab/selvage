"""target_code의 line_number를 계산하는 유틸리티."""

from selvage.src.utils.base_console import console
from selvage.src.utils.file_utils import read_file_lines_cached


def calculate_line_number(file_path: str, target_code: str) -> int | None:
    """파일에서 target_code의 라인 번호를 계산합니다.

    단일 라인 및 멀티라인 target_code를 모두 지원합니다.
    멀티라인의 경우 첫 번째 라인의 번호를 반환합니다.
    캐시된 파일 읽기를 사용하여 동일한 파일에 대한 반복 호출 시 성능이 최적화됩니다.

    Args:
        file_path: 검색할 파일의 경로
        target_code: 찾을 코드 문자열 (단일 라인 또는 멀티라인)

    Returns:
        int | None: 1-based 라인 번호, 찾지 못하거나 오류 시 None
    """
    if not file_path or not target_code or not target_code.strip():
        return None

    try:
        # 캐시된 파일 읽기 함수 사용
        lines = read_file_lines_cached(file_path)
        if lines is None:
            return None

        # target_code를 줄별로 분할
        target_lines = [line.strip() for line in target_code.strip().split("\n")]

        # 성능 최적화: 첫 번째 라인 후보들을 먼저 찾기
        first_target_line = target_lines[0]
        potential_starts = []
        for idx, line in enumerate(lines):
            if line.strip() == first_target_line:
                potential_starts.append(idx)

        # 후보 위치에서만 멀티라인 매칭 수행
        for start_line_idx in potential_starts:
            if start_line_idx + len(target_lines) > len(lines):
                continue

            match = True
            for i, target_line in enumerate(target_lines):
                file_line = lines[start_line_idx + i].strip()
                if target_line != file_line:
                    match = False
                    break

            if match:
                return start_line_idx + 1  # 1-based 반환

        return None

    except Exception as e:
        console.log_info(f"라인 번호 계산 중 예외 발생 ({file_path}): {str(e)}")
        return None
