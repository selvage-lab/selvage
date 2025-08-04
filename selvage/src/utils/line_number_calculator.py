"""target_code의 line_number를 계산하는 유틸리티."""

from pathlib import Path


class LineNumberCalculator:
    """target_code를 파일에서 찾아서 line_number를 계산하는 클래스."""

    @staticmethod
    def calculate_line_number(file_path: str, target_code: str) -> int | None:
        """파일에서 target_code의 라인 번호를 계산합니다.

        단일 라인 및 멀티라인 target_code를 모두 지원합니다.
        멀티라인의 경우 첫 번째 라인의 번호를 반환합니다.

        Args:
            file_path: 검색할 파일의 경로
            target_code: 찾을 코드 문자열 (단일 라인 또는 멀티라인)

        Returns:
            int | None: 1-based 라인 번호, 찾지 못하면 None

        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
            OSError: 파일 읽기 오류가 발생한 경우
        """
        if not file_path or not target_code:
            return None

        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

            with open(file_path_obj, encoding="utf-8") as file:
                lines = file.readlines()

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

        except FileNotFoundError:
            raise
        except Exception as e:
            raise OSError(f"파일 읽기 오류: {e}") from e
