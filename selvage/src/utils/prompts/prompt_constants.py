"""시스템 프롬프트에서 사용되는 상수 및 옵션 규칙들을 정의하는 모듈"""


def get_entirely_new_content_rule() -> str:
    """새로 추가된 파일 또는 전면 재작성된 파일에 대한 규칙을 반환합니다.

    Returns:
        str: 새로 추가된 파일 처리 규칙 문자열
    """
    return (
        "9. **Newly Added or Completely Rewritten Files**: "
        "When `file_context.context` contains a message starting with "
        '"NEWLY ADDED OR COMPLETELY REWRITTEN FILE", treat the '
        "`after_code` as the entire file content. In this case, "
        "`before_code` should be ignored and `file_context.context` "
        "contains only an informational message, not actual code."
    )
