"""
파일 조작 및 프로젝트 관련 유틸리티 함수들입니다.
"""

import os
from functools import lru_cache
from pathlib import Path

from selvage.src.utils.base_console import console

"""파일 관련 유틸리티 함수와 상수"""

# 제외할 바이너리/비텍스트 파일 확장자 목록
BINARY_EXTENSIONS = {
    # 실행 파일 및 라이브러리
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
    ".o",
    ".obj",
    ".a",
    ".lib",
    # 압축 파일
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".jar",
    ".war",
    ".ear",
    ".aar",
    # 이미지 파일
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".ico",
    ".webp",
    # 비디오/오디오 파일
    ".mp3",
    ".mp4",
    ".wav",
    ".avi",
    ".mov",
    ".mkv",
    ".flac",
    ".ogg",
    # 문서 파일
    ".pdf",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".xls",
    ".xlsx",
    # 기타 바이너리 파일
    ".class",
    ".pyc",
    ".pyo",
    ".db",
    ".sqlite",
    ".dat",
}

# 바이너리 파일 이름 목록
BINARY_FILENAMES = {
    "gradlew",
    "gradle-wrapper.jar",
    "mvnw",
    "mvnw.cmd",
    ".DS_Store",
    "gradle-wrapper.properties",
    "gradlew.bat",
}

# 무시할 텍스트 파일 이름 목록
IGNORE_FILENAMES = {
    ".gitignore",
    ".gitmodules",
    ".gitconfig",
    ".git",
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
    ".env.development.local",
    ".env.production.local",
    "e2e-cross-platform.yml.disabled",
    "e2e-cross-platform.yml",
}


def is_ignore_file(filename: str) -> bool:
    """파일명이나 확장자를 기준으로 무시해야 할 파일인지 확인합니다.

    Args:
        filename (str): 확인할 파일 경로

    Returns:
        bool: 무시해야 할 파일이면 True, 아니면 False
    """
    import os.path

    # 확장자 또는 파일명으로 무시해야 할 파일 확인
    _, ext = os.path.splitext(filename.lower())
    base_name = os.path.basename(filename)

    return (
        ext in BINARY_EXTENSIONS
        or base_name in BINARY_FILENAMES
        or base_name in IGNORE_FILENAMES
    )


def get_file_path(filename: str, repo_path: str) -> str:
    """저장소 내부의 안전한 절대 파일 경로를 반환합니다.

    Path traversal 공격을 방지하기 위해 파일 경로가 지정된 저장소
    경로 내부에 있는지 확인하고, 검증된 절대 경로를 반환합니다.

    Args:
        filename (str): 대상 파일 경로 (상대 경로)
        repo_path (str): 저장소 루트 경로

    Returns:
        str: 검증된 절대 파일 경로

    Raises:
        PermissionError: 저장소 외부 파일 접근 시도 시
    """
    # 파일 경로 완성 및 보안 검사
    abs_repo_path = os.path.abspath(repo_path)
    # filename이 repo_path에 대한 상대 경로라고 가정합니다.
    # 악의적인 filename (예: "../../../etc/passwd")을 방지합니다.
    prospective_path = os.path.join(abs_repo_path, filename)
    abs_file_path = os.path.abspath(prospective_path)

    # resolved_path가 resolved_repo_path로 시작하는지 확인합니다.
    # os.sep을 추가하여 "/foo/bar"와 "/foo/barbaz" 같은 경우를 구분합니다.
    if (
        not abs_file_path.startswith(abs_repo_path + os.sep)
        and abs_file_path != abs_repo_path
    ):
        raise PermissionError(f"접근 권한이 없습니다: {filename}")

    return abs_file_path


def load_file_content(filename: str, repo_path: str) -> str:
    """파일 전체 내용을 읽어옵니다. 지정된 저장소 경로를 기준으로 파일을 찾습니다.

    Args:
        filename (str): 읽을 파일 경로
        repo_path (str): 저장소 경로

    Returns:
        str: 파일 내용

    Raises:
        FileNotFoundError: 파일을 찾을 수 없는 경우
        PermissionError: 저장소 외부의 파일에 접근하려고 시도한 경우
    """
    try:
        # 보안 검사를 통한 안전한 파일 경로 획득
        file_path = get_file_path(filename, repo_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {filename}")

        # 무시해야 할 파일인지 확인 (파일 확장자 및 이름 기준)
        if is_ignore_file(
            filename
        ):  # is_ignore_file은 같은 파일 내에 있으므로 바로 사용
            return f"[제외 파일: {filename}]"

        # UTF-8로 파일 읽기 시도
        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # 인코딩 오류 시 바이너리 파일로 간주
            return f"[인코딩 오류로 읽을 수 없는 파일: {filename}]"

    except (FileNotFoundError, PermissionError) as e:
        # FileNotFoundError와 PermissionError는 그대로 다시 발생시킴
        console.error(f"파일 접근 오류: {str(e)}", exception=e)
        raise e
    except Exception as e:
        # 그 외 예외는 좀 더 구체적인 메시지와 함께 Exception으로 다시 발생시킴
        console.error(f"파일 처리 오류: {str(e)}", exception=e)
        import traceback

        error_msg = f"파일 '{filename}' 읽기 오류: {str(e)}\\n{traceback.format_exc()}"
        raise Exception(error_msg) from e


@lru_cache(maxsize=1)
def find_project_root() -> Path:
    """프로젝트 루트 디렉토리를 찾습니다.

    일반적인 프로젝트 식별 파일(예: .git, pyproject.toml, setup.py)이 있는
    상위 디렉토리를 찾습니다.

    Returns:
        Path: 프로젝트 루트 경로
    """
    current_dir = Path.cwd()

    # 프로젝트 루트 식별자 파일 목록
    root_identifiers = [
        ".git",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
    ]

    while True:
        if any((current_dir / identifier).exists() for identifier in root_identifiers):
            return current_dir
        if current_dir.parent == current_dir:
            break
        current_dir = current_dir.parent
    raise FileNotFoundError(
        f"프로젝트 루트 디렉토리를 찾을 수 없습니다. 탐색 완료 경로: {current_dir}"
    )
