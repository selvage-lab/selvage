import os

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".go": "go",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".md": "markdown",
    ".json": "json",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".sh": "shell",
    ".bash": "shell",
    ".sql": "sql",
}


def detect_language_from_filename(filename: str) -> str:
    """파일 확장자를 기반으로 언어를 감지합니다.

    Args:
        filename: 언어를 감지할 파일의 이름입니다.

    Returns:
        감지된 언어를 나타내는 문자열입니다. 알려지지 않은 확장자의 경우 'text'를 반환합니다.
    """
    _, ext = os.path.splitext(filename)
    return SUPPORTED_EXTENSIONS.get(ext.lower(), "text")
