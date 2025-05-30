"""프롬프트 생성기 테스트"""

import json
from unittest.mock import patch

import pytest

from selvage.src.diff_parser.models.diff_result import DiffResult
from selvage.src.diff_parser.models.file_diff import FileDiff
from selvage.src.diff_parser.models.hunk import Hunk
from selvage.src.utils.prompts.models import (
    ReviewPrompt,
    ReviewPromptWithFileContent,
    SystemPrompt,
    UserPrompt,
    UserPromptWithFileContent,
)
from selvage.src.utils.prompts.prompt_generator import PromptGenerator
from selvage.src.utils.token.models import ReviewRequest


@pytest.fixture
def review_request() -> ReviewRequest:
    return ReviewRequest(
        diff_content="diff --git a/file.py b/file.py\nindex 1234..5678 100644\n--- a/file.py\n+++ b/file.py\n@@ -1,3 +1,4 @@\n+print('Hello')\n print('World')\n",
        file_paths=["file.py"],
        processed_diff=DiffResult(
            files=[
                FileDiff(
                    filename="file.py",
                    file_content="file content",
                    hunks=[
                        Hunk(
                            header="@@ -1,3 +1,4 @@",
                            content="+print('Hello')\n print('World')\n",
                            before_code="print('World')\n",
                            after_code="print('Hello')\nprint('World')\n",
                            start_line_original=1,
                            line_count_original=3,
                            start_line_modified=1,
                            line_count_modified=4,
                        )
                    ],
                    language="python",
                )
            ]
        ),
        model="gpt-4o-mini",
        use_full_context=True,
        repo_path=".",
    )


@pytest.fixture
def diff_only_review_request() -> ReviewRequest:
    """use_full_context가 False인 review_request fixture"""
    return ReviewRequest(
        diff_content="diff --git a/file.py b/file.py\nindex 1234..5678 100644\n--- a/file.py\n+++ b/file.py\n@@ -1,3 +1,4 @@\n+print('Hello')\n print('World')\n",
        file_paths=["file.py"],
        processed_diff=DiffResult(
            files=[
                FileDiff(
                    filename="file.py",
                    file_content="file content",
                    hunks=[
                        Hunk(
                            header="@@ -1,3 +1,4 @@",
                            content="+print('Hello')\n print('World')\n",
                            before_code="print('World')\n",
                            after_code="print('Hello')\nprint('World')\n",
                            start_line_original=1,
                            line_count_original=3,
                            start_line_modified=1,
                            line_count_modified=4,
                        )
                    ],
                    language="python",
                )
            ]
        ),
        model="gpt-4o-mini",
        use_full_context=False,
        repo_path=".",
    )


@pytest.fixture
def multi_hunk_review_request() -> ReviewRequest:
    """여러 개의 hunk가 포함된 review_request fixture"""
    return ReviewRequest(
        diff_content="diff --git a/file.py b/file.py\n...",
        file_paths=["file.py"],
        processed_diff=DiffResult(
            files=[
                FileDiff(
                    filename="file.py",
                    file_content="file content",
                    hunks=[
                        Hunk(
                            header="@@ -1,3 +1,4 @@",
                            content="+print('Hello')\n print('World')\n",
                            before_code="print('World')\n",
                            after_code="print('Hello')\nprint('World')\n",
                            start_line_original=1,
                            line_count_original=3,
                            start_line_modified=1,
                            line_count_modified=4,
                        ),
                        Hunk(
                            header="@@ -10,3 +11,4 @@",
                            content=" print('Debug')\n+print('Log')\n print('Info')\n",
                            before_code="print('Debug')\nprint('Info')\n",
                            after_code="print('Debug')\nprint('Log')\nprint('Info')\n",
                            start_line_original=10,
                            line_count_original=3,
                            start_line_modified=11,
                            line_count_modified=4,
                        ),
                    ],
                    language="python",
                )
            ]
        ),
        model="gpt-4o-mini",
        use_full_context=True,
        repo_path=".",
    )


@pytest.fixture
def multi_hunk_diff_only_review_request() -> ReviewRequest:
    """여러 개의 hunk가 포함되고 use_full_context가 False인 review_request fixture"""
    return ReviewRequest(
        diff_content="diff --git a/file.py b/file.py\n...",
        file_paths=["file.py"],
        processed_diff=DiffResult(
            files=[
                FileDiff(
                    filename="file.py",
                    file_content="file content",
                    hunks=[
                        Hunk(
                            header="@@ -1,3 +1,4 @@",
                            content="+print('Hello')\n print('World')\n",
                            before_code="print('World')\n",
                            after_code="print('Hello')\nprint('World')\n",
                            start_line_original=1,
                            line_count_original=3,
                            start_line_modified=1,
                            line_count_modified=4,
                        ),
                        Hunk(
                            header="@@ -10,3 +11,4 @@",
                            content=" print('Debug')\n+print('Log')\n print('Info')\n",
                            before_code="print('Debug')\nprint('Info')\n",
                            after_code="print('Debug')\nprint('Log')\nprint('Info')\n",
                            start_line_original=10,
                            line_count_original=3,
                            start_line_modified=11,
                            line_count_modified=4,
                        ),
                    ],
                    language="python",
                )
            ]
        ),
        model="gpt-4o-mini",
        use_full_context=False,
        repo_path=".",
    )


class TestPromptGenerator:
    """프롬프트 생성기 테스트 클래스"""

    @patch.object(
        PromptGenerator,
        "_get_code_review_system_prompt",
        return_value="Mock system prompt",
    )
    def test_create_code_review_prompt(
        self, mock_system_prompt, review_request: ReviewRequest
    ):
        """코드 리뷰 프롬프트 생성 테스트 (use_full_context=True)"""
        # Given
        generator = PromptGenerator()

        # When
        review_prompt = generator.create_code_review_prompt(review_request)

        # Then
        # 1. ReviewPromptWithFileContent 구조 검증
        assert isinstance(review_prompt, ReviewPromptWithFileContent)
        assert isinstance(review_prompt.system_prompt, SystemPrompt)
        assert len(review_prompt.user_prompts) == 1
        assert isinstance(review_prompt.user_prompts[0], UserPromptWithFileContent)

        # 2. SystemPrompt 필드 검증
        assert review_prompt.system_prompt.role == "system"
        assert review_prompt.system_prompt.content == "Mock system prompt"

        # 3. UserPromptWithFileContent 필드 검증
        user_prompt = review_prompt.user_prompts[0]
        assert user_prompt.file_name == "file.py"
        assert user_prompt.file_content == "file content"

        # 4. 포맷된 Hunk 검증
        assert len(user_prompt.formatted_hunks) == 1
        hunk = user_prompt.formatted_hunks[0]
        assert hunk.hunk_idx == "1"
        assert hunk.after_code_start_line_number == 1
        assert "print('World')" in hunk.before_code
        assert "print('Hello')" in hunk.after_code

    @patch.object(
        PromptGenerator,
        "_get_code_review_system_prompt",
        return_value="Mock system prompt for diff only",
    )
    def test_create_code_review_prompt_with_diff_only(
        self, mock_system_prompt, diff_only_review_request: ReviewRequest
    ):
        """코드 리뷰 프롬프트 생성 테스트 (use_full_context=False)"""
        # Given
        generator = PromptGenerator()

        # When
        review_prompt = generator.create_code_review_prompt(diff_only_review_request)

        # Then
        # 1. ReviewPrompt 구조 검증
        assert isinstance(review_prompt, ReviewPrompt)
        assert isinstance(review_prompt.system_prompt, SystemPrompt)
        assert len(review_prompt.user_prompts) == 1
        assert isinstance(review_prompt.user_prompts[0], UserPrompt)

        # 2. SystemPrompt 필드 검증
        assert review_prompt.system_prompt.role == "system"
        assert review_prompt.system_prompt.content == "Mock system prompt for diff only"

        # 3. UserPrompt 모든 필드 검증
        user_prompt = review_prompt.user_prompts[0]
        assert user_prompt.hunk_idx == "1"
        assert user_prompt.file_name == "file.py"
        assert user_prompt.language == "python"
        assert user_prompt.after_code_start_line_number == 1

        # before_code와 after_code 검증 - 이스케이프된 포맷 검증
        assert "```python\n" in user_prompt.before_code
        assert "```python\n" in user_prompt.after_code
        assert user_prompt.before_code.endswith("\n```")
        assert user_prompt.after_code.endswith("\n```")

        # 원본 코드와 수정된 코드 내용 검증
        assert "print('World')" in user_prompt.before_code
        assert "print('Hello')\nprint('World')" in user_prompt.after_code

    @patch.object(
        PromptGenerator,
        "_get_code_review_system_prompt",
        return_value="Mock system prompt",
    )
    def test_review_prompt_to_messages_conversion(
        self, mock_system_prompt, review_request: ReviewRequest
    ):
        """ReviewPromptWithFileContent에서 메시지 변환 테스트 (use_full_context=True)"""
        # Given
        generator = PromptGenerator()

        review_prompt = generator.create_code_review_prompt(review_request)

        # When
        messages = review_prompt.to_messages()

        # Then
        # 1. 메시지 구조 검증
        assert len(messages) == 2

        # 2. 시스템 메시지 검증
        system_message = messages[0]
        assert system_message["role"] == "system"
        assert "Mock system prompt" in system_message["content"]

        # 3. 사용자 메시지 검증
        user_message = messages[1]
        assert user_message["role"] == "user"

        # 4. 사용자 메시지 내용(JSON) 파싱 및 검증
        content = json.loads(user_message["content"])
        assert content["file_name"] == "file.py"
        assert content["file_content"] == "file content"

        # 5. 포맷된 Hunk 검증
        assert len(content["formatted_hunks"]) == 1
        hunk = content["formatted_hunks"][0]
        assert hunk["hunk_idx"] == "1"
        assert "print('World')" in hunk["before_code"]
        assert "print('Hello')" in hunk["after_code"]
        assert hunk["after_code_start_line_number"] == 1

    @patch.object(
        PromptGenerator,
        "_get_code_review_system_prompt",
        return_value="Mock system prompt for diff only",
    )
    def test_diff_only_review_prompt_to_messages_conversion(
        self, mock_system_prompt, diff_only_review_request: ReviewRequest
    ):
        """ReviewPrompt에서 메시지 변환 테스트 (use_full_context=False)"""
        # Given
        generator = PromptGenerator()

        review_prompt = generator.create_code_review_prompt(diff_only_review_request)

        # When
        messages = review_prompt.to_messages()

        # Then
        # 1. 메시지 구조 검증
        assert len(messages) == 2

        # 2. 시스템 메시지 검증
        system_message = messages[0]
        assert system_message["role"] == "system"
        assert "Mock system prompt for diff only" in system_message["content"]

        # 3. 사용자 메시지 검증
        user_message = messages[1]
        assert user_message["role"] == "user"

        # 4. 사용자 메시지 내용(JSON) 파싱 및 검증
        content = json.loads(user_message["content"])
        assert content["hunk_idx"] == "1"
        assert content["file_name"] == "file.py"
        assert "print('World')" in content["before_code"]
        assert "print('Hello')" in content["after_code"]
        assert content["after_code_start_line_number"] == 1
        assert content["language"] == "python"

    @patch.object(
        PromptGenerator,
        "_get_code_review_system_prompt",
        return_value="Multi hunk review system prompt",
    )
    def test_create_code_review_prompt_multiple_hunks(
        self,
        mock_system_prompt,
        multi_hunk_review_request: ReviewRequest,
    ):
        """여러 hunk가 있는 경우 코드 리뷰 프롬프트 생성 테스트 (use_full_context=True)"""
        # Given
        generator = PromptGenerator()

        # When
        review_prompt = generator.create_code_review_prompt(multi_hunk_review_request)

        # Then
        # 1. ReviewPromptWithFileContent 구조 검증
        assert isinstance(review_prompt, ReviewPromptWithFileContent)
        assert isinstance(review_prompt.system_prompt, SystemPrompt)
        assert len(review_prompt.user_prompts) == 1
        assert isinstance(review_prompt.user_prompts[0], UserPromptWithFileContent)

        # 2. SystemPrompt 필드 검증
        assert review_prompt.system_prompt.role == "system"
        assert review_prompt.system_prompt.content == "Multi hunk review system prompt"

        # 3. UserPromptWithFileContent 필드 검증
        user_prompt = review_prompt.user_prompts[0]
        assert user_prompt.file_name == "file.py"
        assert user_prompt.file_content == "file content"

        # 4. 포맷된 Hunk 검증
        assert len(user_prompt.formatted_hunks) == 2

        # 첫 번째 hunk 검증
        first_hunk = user_prompt.formatted_hunks[0]
        assert first_hunk.hunk_idx == "1"
        assert first_hunk.after_code_start_line_number == 1
        assert "print('World')" in first_hunk.before_code
        assert "print('Hello')" in first_hunk.after_code

        # 두 번째 hunk 검증
        second_hunk = user_prompt.formatted_hunks[1]
        assert second_hunk.hunk_idx == "2"
        assert second_hunk.after_code_start_line_number == 11
        assert "print('Debug')" in second_hunk.before_code
        assert "print('Log')" in second_hunk.after_code
        assert "print('Info')" in second_hunk.after_code

    @patch.object(
        PromptGenerator,
        "_get_code_review_system_prompt",
        return_value="Multi hunk diff only review system prompt",
    )
    def test_create_code_review_prompt_multiple_hunks_with_diff_only(
        self, mock_system_prompt, multi_hunk_diff_only_review_request: ReviewRequest
    ):
        """여러 hunk가 있고 use_full_context=False인 경우 코드 리뷰 프롬프트 생성 테스트"""
        # Given
        generator = PromptGenerator()

        # When
        review_prompt = generator.create_code_review_prompt(
            multi_hunk_diff_only_review_request
        )

        # Then
        # 1. ReviewPrompt 구조 검증
        assert isinstance(review_prompt, ReviewPrompt)
        assert isinstance(review_prompt.system_prompt, SystemPrompt)
        assert len(review_prompt.user_prompts) == 2

        # 2. SystemPrompt 필드 검증
        assert review_prompt.system_prompt.role == "system"
        assert (
            review_prompt.system_prompt.content
            == "Multi hunk diff only review system prompt"
        )

        # 3. UserPrompt 모든 필드 검증
        # 첫 번째 hunk 검증
        first_prompt = review_prompt.user_prompts[0]
        assert first_prompt.hunk_idx == "1"
        assert first_prompt.file_name == "file.py"
        assert first_prompt.after_code_start_line_number == 1
        assert "print('World')" in first_prompt.before_code
        assert "print('Hello')" in first_prompt.after_code

        # 두 번째 hunk 검증
        second_prompt = review_prompt.user_prompts[1]
        assert second_prompt.hunk_idx == "2"
        assert second_prompt.file_name == "file.py"
        assert second_prompt.after_code_start_line_number == 11
        assert "print('Debug')" in second_prompt.before_code
        assert "print('Log')" in second_prompt.after_code
        assert "print('Info')" in second_prompt.after_code
