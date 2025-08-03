"""프롬프트 생성기"""

import importlib.resources

from selvage.src.config import get_default_language
from selvage.src.context_extractor.context_extractor import ContextExtractor
from selvage.src.context_extractor.fallback_context_extractor import (
    FallbackContextExtractor,
)
from selvage.src.exceptions import UnsupportedLanguageError
from selvage.src.utils.base_console import console
from selvage.src.utils.file_utils import is_ignore_file
from selvage.src.utils.smart_context_utils import SmartContextUtils
from selvage.src.utils.token.models import ReviewRequest

from .models import (
    FileContextInfo,
    ReviewPromptWithFileContent,
    SystemPrompt,
    UserPromptWithFileContent,
)
from .prompt_constants import get_entirely_new_content_rule

PROMPT_PATH = "selvage.resources.prompt"
PROMPT_FILE_NAME = "code_review_system_prompt"
VERSION = "v3"


class PromptGenerator:
    """프롬프트 생성기 클래스"""

    @classmethod
    def _get_code_review_system_prompt(
        cls, is_include_entirely_new_content: bool
    ) -> str:
        """코드 리뷰 시스템 프롬프트를 불러옵니다.

        Returns:
            str: 코드 리뷰 시스템 프롬프트
        """
        try:
            file_ref = importlib.resources.files(f"{PROMPT_PATH}.{VERSION}").joinpath(
                f"{PROMPT_FILE_NAME}_{VERSION}.txt"
            )
            with importlib.resources.as_file(file_ref) as file_path:
                prompt_content = file_path.read_text(encoding="utf-8")

                # 템플릿 변수 처리
                language = get_default_language()
                prompt_content = prompt_content.replace("{{LANGUAGE}}", language)
                prompt_content = prompt_content.replace(
                    "{{IS_INCLUDE_ENTIRELY_NEW_CONTENT}}",
                    "true" if is_include_entirely_new_content else "false",
                )

                prompt_content = prompt_content.replace(
                    "{{ENTIRELY_NEW_CONTENT_RULE}}",
                    get_entirely_new_content_rule()
                    if is_include_entirely_new_content
                    else "",
                )

                return prompt_content
        except Exception as e:
            error_message = (
                f"시스템 프롬프트 파일을 찾을 수 없습니다 "
                f"(경로: '{PROMPT_PATH}.{VERSION}/{PROMPT_FILE_NAME}_{VERSION}.txt'). "
                f"원본 오류: {e}"
            )
            console.error(error_message, exception=e)
            raise FileNotFoundError(error_message) from e

    def create_code_review_prompt(
        self, review_request: ReviewRequest
    ) -> ReviewPromptWithFileContent:
        """코드 리뷰 요청으로부터 파일 내용을 포함한 프롬프트를 생성합니다.

        Args:
            review_request: 리뷰 요청 객체

        Returns:
            ReviewPromptWithFileContent: 생성된 파일 내용 포함 리뷰 프롬프트 객체
        """
        system_prompt_content = self._get_code_review_system_prompt(
            is_include_entirely_new_content=review_request.is_include_entirely_new_content()
        )

        # 시스템 프롬프트 생성
        system_prompt = SystemPrompt(role="system", content=system_prompt_content)
        user_prompts: list[UserPromptWithFileContent] = []

        for file in review_request.processed_diff.files:
            # 바이너리 파일인지 먼저 확인
            if is_ignore_file(file.filename):
                # 바이너리 파일은 처리하지 않고 건너뜁니다
                continue

            try:
                # 파일 컨텍스트 생성
                if SmartContextUtils.use_smart_context(file):
                    try:
                        contexts = ContextExtractor(file.language).extract_contexts(
                            file.file_content, [hunk.change_line for hunk in file.hunks]
                        )
                        file_context = FileContextInfo.create_smart_context(contexts)
                    except Exception as e:
                        if not isinstance(e, UnsupportedLanguageError):
                            # UnsupportedLanguageError가 아닌 다른 예외일 때만 경고
                            console.warning(f"컨텍스트 추출 실패, fall back 사용: {e}")

                        # 모든 예외에 대해 공통적으로 fall back 로직을 실행합니다.
                        contexts = FallbackContextExtractor().extract_contexts(
                            file.file_content, [hunk.change_line for hunk in file.hunks]
                        )
                        file_context = FileContextInfo.create_fallback_context(contexts)
                elif not file.file_content:
                    console.warning(f"파일 내용이 없습니다. 파일 경로: {file.filename}")
                    file_context = FileContextInfo.create_full_context("")
                elif file.is_entirely_new_content():
                    content = (
                        "NEWLY ADDED OR COMPLETELY REWRITTEN FILE: This file is either "
                        "newly created or completely rewritten. The file_context "
                        "contains only this informational message. The complete file "
                        "content is available in the after_code field of "
                        "formatted_hunks. before_code will be empty and should be "
                        "ignored."
                    )
                    file_context = FileContextInfo.create_full_context(content)
                else:
                    file_context = FileContextInfo.create_full_context(
                        file.file_content
                    )

                # user_prompt 생성
                user_prompt = UserPromptWithFileContent(
                    file_name=file.filename,
                    file_context=file_context,
                    hunks=file.hunks,
                    language=file.language,
                )
                user_prompts.append(user_prompt)

            except FileNotFoundError:
                # 파일을 찾을 수 없는 경우도 건너뜁니다
                continue

        review_prompt_with_file_content = ReviewPromptWithFileContent(
            system_prompt=system_prompt,
            user_prompts=user_prompts,
        )

        return review_prompt_with_file_content
