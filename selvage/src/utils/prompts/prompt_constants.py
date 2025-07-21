"""시스템 프롬프트에서 사용되는 상수 및 옵션 규칙들을 정의하는 모듈"""


def get_entirely_new_content_rule() -> str:
    """새로 추가된 파일 또는 전면 재작성된 파일에 대한 규칙을 반환합니다.
    
    Returns:
        str: 새로 추가된 파일 처리 규칙 문자열
    """
    return (
        "10. **Newly Added or Completely Rewritten Files**: "
        "When `file_content` is contains a message like "
        "\"This file is newly added or completely rewritten\", "
        "treat the `after_code` as the entire file content "
        "(in this case, `before_code` and `file_content` are "
        "empty and should be ignored)."
    )