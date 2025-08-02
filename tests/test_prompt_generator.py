"""프롬프트 생성기 테스트"""

import json
from unittest.mock import patch

import pytest

from selvage.src.context_extractor.line_range import LineRange
from selvage.src.diff_parser.models.diff_result import DiffResult
from selvage.src.diff_parser.models.file_diff import FileDiff
from selvage.src.diff_parser.models.hunk import Hunk
from selvage.src.utils.prompts.models import (
    ContextType,
    FileContextInfo,
    ReviewPromptWithFileContent,
    SystemPrompt,
    UserPromptWithFileContent,
)
from selvage.src.utils.prompts.prompt_generator import PromptGenerator
from selvage.src.utils.token.models import ReviewRequest


@pytest.fixture
def review_request() -> ReviewRequest:
    return ReviewRequest(
        diff_content=(
            "diff --git a/file.py b/file.py\n"
            "index 1234..5678 100644\n"
            "--- a/file.py\n"
            "+++ b/file.py\n"
            "@@ -1,3 +1,4 @@\n"
            "+print('Hello')\n"
            " print('World')\n"
        ),
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
                            change_line=LineRange(start_line=1, end_line=2),
                        )
                    ],
                    language="python",
                    additions=1,
                    deletions=0,
                    line_count=10,  # 전체 파일이 10줄이라고 가정
                )
            ]
        ),
        model="gpt-4o-mini",
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
                            change_line=LineRange(start_line=1, end_line=2),
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
                            change_line=LineRange(start_line=12, end_line=12),
                        ),
                    ],
                    language="python",
                    additions=2,
                    deletions=0,
                    line_count=15,  # 전체 파일이 15줄이라고 가정
                )
            ]
        ),
        model="gpt-4o-mini",
        repo_path=".",
    )


class TestPromptGenerator:
    """프롬프트 생성기 테스트 클래스"""

    @patch('selvage.src.utils.prompts.prompt_generator.SmartContextUtils.use_smart_context')
    @patch('selvage.src.utils.prompts.prompt_generator.ContextExtractor')
    @patch.object(
        PromptGenerator,
        "_get_code_review_system_prompt",
        return_value="Mock system prompt",
    )
    def test_create_code_review_prompt(
        self, mock_system_prompt, mock_context_extractor, mock_use_smart_context,
        review_request: ReviewRequest
    ):
        """코드 리뷰 프롬프트 생성 테스트 - SMART_CONTEXT 시나리오"""
        # Given
        mock_use_smart_context.return_value = True
        mock_extractor_instance = mock_context_extractor.return_value
        mock_extractor_instance.extract_contexts.return_value = ["smart context from file.py"]
        
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
        
        # file_context는 FileContextInfo 타입이어야 함
        assert isinstance(user_prompt.file_context, FileContextInfo)
        
        # mock 설정으로 인해 smart context가 생성될 것
        assert user_prompt.file_context.context_type == ContextType.SMART_CONTEXT
        expected_description = "AST-based context extraction"
        assert user_prompt.file_context.description == expected_description
        assert user_prompt.file_context.context == "smart context from file.py"

        # 4. 포맷된 Hunk 검증
        assert len(user_prompt.formatted_hunks) == 1
        hunk = user_prompt.formatted_hunks[0]
        assert hunk.hunk_idx == "1"
        assert hunk.after_code_start_line_number == 1
        assert "print('World')" in hunk.before_code
        assert "print('Hello')" in hunk.after_code

    @patch('selvage.src.utils.prompts.prompt_generator.SmartContextUtils.use_smart_context')
    @patch('selvage.src.utils.prompts.prompt_generator.ContextExtractor')
    @patch.object(
        PromptGenerator,
        "_get_code_review_system_prompt",
        return_value="Mock system prompt",
    )
    def test_review_prompt_to_messages_conversion(
        self, mock_system_prompt, mock_context_extractor, mock_use_smart_context,
        review_request: ReviewRequest
    ):
        """ReviewPromptWithFileContent에서 메시지 변환 테스트 - SMART_CONTEXT JSON"""
        # Given
        mock_use_smart_context.return_value = True
        mock_extractor_instance = mock_context_extractor.return_value
        mock_extractor_instance.extract_contexts.return_value = ["smart context for json test"]
        
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
        
        # file_context가 변경되었으므로 새로운 JSON 구조 확인
        assert "file_context" in content
        file_context = content["file_context"]
        assert isinstance(file_context, dict)
        
        # FileContextInfo.to_dict() 결과 검증
        assert "context" in file_context
        assert "context_type" in file_context
        assert "description" in file_context
        
        # 실제 동작에서는 context_type이 다를 수 있으므로 여러 경우 허용
        # 하지만 값은 정확한 enum 값이어야 함
        assert file_context["context_type"] in ["smart_context", "fallback_context", "full_context"]
        
        # mock 설정으로 인해 smart_context가 생성됨
        assert file_context["context_type"] == "smart_context"
        expected_desc = "AST-based context extraction"
        assert file_context["description"] == expected_desc
        assert file_context["context"] == "smart context for json test"

        # 5. 포맷된 Hunk 검증
        assert len(content["formatted_hunks"]) == 1
        hunk = content["formatted_hunks"][0]
        assert hunk["hunk_idx"] == "1"
        assert "print('World')" in hunk["before_code"]
        assert "print('Hello')" in hunk["after_code"]
        assert hunk["after_code_start_line_number"] == 1

    @patch('selvage.src.utils.prompts.prompt_generator.SmartContextUtils.use_smart_context')
    @patch.object(
        PromptGenerator,
        "_get_code_review_system_prompt",
        return_value="Multi hunk review system prompt",
    )
    def test_create_code_review_prompt_multiple_hunks(
        self,
        mock_system_prompt,
        mock_use_smart_context,
        multi_hunk_review_request: ReviewRequest,
    ):
        """여러 hunk가 있는 경우 코드 리뷰 프롬프트 생성 테스트 - FULL_CONTEXT 시나리오"""
        # Given
        mock_use_smart_context.return_value = False  # FULL_CONTEXT 시나리오
        
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
        
        # file_context는 FileContextInfo 타입이어야 함
        assert isinstance(user_prompt.file_context, FileContextInfo)
        
        # mock 설정으로 인해 FULL_CONTEXT가 생성될 것
        assert user_prompt.file_context.context_type == ContextType.FULL_CONTEXT
        expected_description = "Complete file content"
        assert user_prompt.file_context.description == expected_description
        assert user_prompt.file_context.context == "file content"

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


@pytest.fixture
def new_file_review_request() -> ReviewRequest:
    """새로 생성된 파일에 대한 review_request fixture"""
    return ReviewRequest(
        diff_content=(
            "diff --git a/new_file.py b/new_file.py\n"
            "index 0000000..abc1234 100644\n"
            "--- /dev/null\n"
            "+++ b/new_file.py\n"
            "@@ -0,0 +1,3 @@\n"
            "+def hello():\n"
            "+    print('Hello')\n"
            "+    return True\n"
        ),
        file_paths=["new_file.py"],
        processed_diff=DiffResult(
            files=[
                FileDiff(
                    filename="new_file.py",
                    file_content=(
                        "def hello():\n    print('Hello')\n    return True\n"
                    ),
                    hunks=[
                        Hunk(
                            header="@@ -0,0 +1,3 @@",
                            content=(
                                "+def hello():\n+    print('Hello')\n+    return True\n"
                            ),
                            before_code="",
                            after_code=(
                                "def hello():\n    print('Hello')\n    return True\n"
                            ),
                            start_line_original=0,
                            line_count_original=0,
                            start_line_modified=1,
                            line_count_modified=3,
                            change_line=LineRange(start_line=1, end_line=3),
                        )
                    ],
                    language="python",
                    additions=3,
                    deletions=0,
                    line_count=3,  # 새 파일은 전체 라인 수가 추가된 라인 수와 같음
                )
            ]
        ),
        model="gpt-4o-mini",
        repo_path=".",
    )


@pytest.fixture
def rewritten_file_review_request() -> ReviewRequest:
    """파일이 재작성된 경우에 대한 review_request fixture"""
    return ReviewRequest(
        diff_content=(
            "diff --git a/rewritten.py b/rewritten.py\n"
            "index abc1234..def5678 100644\n"
            "--- a/rewritten.py\n"
            "+++ b/rewritten.py\n"
            "@@ -1,5 +1,3 @@\n"
            "-old_function()\n"
            "-old_code()\n"
            "-legacy()\n"
            "-deprecated()\n"
            "-unused()\n"
            "+def new_function():\n"
            "+    return 'Rewritten'\n"
            "+    print('Done')\n"
        ),
        file_paths=["rewritten.py"],
        processed_diff=DiffResult(
            files=[
                FileDiff(
                    filename="rewritten.py",
                    file_content=(
                        "def new_function():\n"
                        "    return 'Rewritten'\n"
                        "    print('Done')\n"
                    ),
                    hunks=[
                        Hunk(
                            header="@@ -1,5 +1,3 @@",
                            content=(
                                "-old_function()\n"
                                "-old_code()\n"
                                "-legacy()\n"
                                "-deprecated()\n"
                                "-unused()\n"
                                "+def new_function():\n"
                                "+    return 'Rewritten'\n"
                                "+    print('Done')\n"
                            ),
                            before_code=(
                                "old_function()\n"
                                "old_code()\n"
                                "legacy()\n"
                                "deprecated()\n"
                                "unused()\n"
                            ),
                            after_code=(
                                "def new_function():\n"
                                "    return 'Rewritten'\n"
                                "    print('Done')\n"
                            ),
                            start_line_original=1,
                            line_count_original=5,
                            start_line_modified=1,
                            line_count_modified=3,
                            change_line=LineRange(start_line=1, end_line=3),
                        )
                    ],
                    language="python",
                    additions=3,
                    deletions=5,
                    line_count=3,  # 파일 재작성: 전체 라인 수가 추가된 라인 수와 같음
                )
            ]
        ),
        model="gpt-4o-mini",
        repo_path=".",
    )


class TestPromptGeneratorNewFileAndRewrite:
    """새 파일 생성 및 파일 재작성 케이스 테스트"""

    @patch('selvage.src.utils.prompts.prompt_generator.SmartContextUtils.use_smart_context')
    @patch.object(
        PromptGenerator,
        "_get_code_review_system_prompt",
        return_value="New file review system prompt",
    )
    def test_create_code_review_prompt_new_file(
        self, mock_system_prompt, mock_use_smart_context, new_file_review_request: ReviewRequest
    ):
        """새로 생성된 파일에 대한 FULL_CONTEXT 특별 메시지 시나리오 테스트"""
        # Given - SmartContextUtils mock으로 False 설정하여 FULL_CONTEXT 플로우로 진입
        mock_use_smart_context.return_value = False
        
        generator = PromptGenerator()

        # When
        review_prompt = generator.create_code_review_prompt(new_file_review_request)

        # Then
        # 1. ReviewPromptWithFileContent 구조 검증
        assert isinstance(review_prompt, ReviewPromptWithFileContent)
        assert len(review_prompt.user_prompts) == 1

        # 2. 새 파일의 경우 FULL_CONTEXT 특별 메시지 검증
        user_prompt = review_prompt.user_prompts[0]
        assert user_prompt.file_name == "new_file.py"
        
        # file_context 구조에 맞게 검증
        assert isinstance(user_prompt.file_context, FileContextInfo)
        
        # 새 파일에 대한 FULL_CONTEXT 특별 메시지 검증
        assert user_prompt.file_context.context_type == ContextType.FULL_CONTEXT
        expected_description = "Complete file content"
        assert user_prompt.file_context.description == expected_description
        
        # 특별 메시지 내용 검증
        expected_message = (
            "NEWLY ADDED OR COMPLETELY REWRITTEN FILE: This file is either "
            "newly created or completely rewritten. The file_context "
            "contains only this informational message. The complete file "
            "content is available in the after_code field of "
            "formatted_hunks. before_code will be empty and should be "
            "ignored."
        )
        assert user_prompt.file_context.context == expected_message

        # 3. hunks는 여전히 존재해야 함 (after_code에 전체 파일 내용 포함)
        assert len(user_prompt.formatted_hunks) == 1
        hunk = user_prompt.formatted_hunks[0]
        assert "def hello():" in hunk.after_code
        assert "print('Hello')" in hunk.after_code
        assert "return True" in hunk.after_code

    @patch.object(
        PromptGenerator,
        "_get_code_review_system_prompt",
        return_value="Rewritten file review system prompt",
    )
    def test_create_code_review_prompt_rewritten_file(
        self, mock_system_prompt, rewritten_file_review_request: ReviewRequest
    ):
        """파일이 재작성된 경우 file_content가 비워지는지 테스트"""
        # Given
        generator = PromptGenerator()

        # When
        review_prompt = generator.create_code_review_prompt(
            rewritten_file_review_request
        )

        # Then
        # 1. ReviewPromptWithFileContent 구조 검증
        assert isinstance(review_prompt, ReviewPromptWithFileContent)
        assert len(review_prompt.user_prompts) == 1

        # 2. 파일 재작성의 경우 file_context 검증
        user_prompt = review_prompt.user_prompts[0]
        assert user_prompt.file_name == "rewritten.py"
        
        # file_context 구조에 맞게 검증
        assert isinstance(user_prompt.file_context, FileContextInfo)
        
        # 재작성 파일의 경우 여러 시나리오가 가능:
        # 1. 스마트 컨텍스트 추출 성공 -> SMART_CONTEXT
        # 2. 스마트 컨텍스트 실패 -> FALLBACK_CONTEXT  
        # 3. entirely_new_content 조건 만족 -> FULL_CONTEXT with special message
        assert user_prompt.file_context.context_type in [
            ContextType.SMART_CONTEXT, 
            ContextType.FALLBACK_CONTEXT,
            ContextType.FULL_CONTEXT
        ]
        
        # 컨텍스트에 파일 관련 내용이 포함되어야 함
        context = user_prompt.file_context.context
        if user_prompt.file_context.context_type == ContextType.FULL_CONTEXT:
            # 특별 메시지가 있는 경우
            assert "NEWLY ADDED OR COMPLETELY REWRITTEN FILE" in context
        else:
            # 일반적인 컨텍스트 추출이 된 경우 (파일 내용 포함)
            assert "def new_function" in context or "new_function" in context
        
        # description이 적절히 설정되어야 함
        assert len(user_prompt.file_context.description) > 0

        # 3. hunks는 여전히 존재해야 함 (before_code와 after_code 모두 포함)
        assert len(user_prompt.formatted_hunks) == 1
        hunk = user_prompt.formatted_hunks[0]
        assert "old_function()" in hunk.before_code
        assert "def new_function():" in hunk.after_code
        assert "return 'Rewritten'" in hunk.after_code

    def test_new_file_condition_validation(
        self, new_file_review_request: ReviewRequest
    ):
        """새 파일 생성 조건 검증"""
        file_diff = new_file_review_request.processed_diff.files[0]

        # 새 파일 생성 조건: line_count == additions
        assert file_diff.line_count == file_diff.additions
        assert file_diff.line_count == 3
        assert file_diff.additions == 3
        assert file_diff.deletions == 0

    def test_rewritten_file_condition_validation(
        self, rewritten_file_review_request: ReviewRequest
    ):
        """파일 재작성 조건 검증"""
        file_diff = rewritten_file_review_request.processed_diff.files[0]

        # 파일 재작성 조건: line_count == additions (but deletions > 0)
        assert file_diff.line_count == file_diff.additions
        assert file_diff.line_count == 3
        assert file_diff.additions == 3
        assert file_diff.deletions == 5  # 기존 내용이 삭제됨


class TestPromptGeneratorTemplateProcessing:
    """프롬프트 생성기의 템플릿 변수 처리 테스트"""

    def test_get_code_review_system_prompt_with_entirely_new_content_true(self):
        """is_include_entirely_new_content=True일 때 ENTIRELY_NEW_CONTENT_RULE 포함"""
        # Given
        generator = PromptGenerator()

        # When
        system_prompt = generator._get_code_review_system_prompt(
            is_include_entirely_new_content=True
        )

        # Then
        assert "{{LANGUAGE}}" not in system_prompt
        assert "{{ENTIRELY_NEW_CONTENT_RULE}}" not in system_prompt
        assert "10. **Newly Added or Completely Rewritten Files**" in system_prompt
        assert "treat the `after_code` as the entire file content" in system_prompt

    def test_get_code_review_system_prompt_with_entirely_new_content_false(self):
        """is_include_entirely_new_content=False일 때 ENTIRELY_NEW_CONTENT_RULE 제외"""
        # Given
        generator = PromptGenerator()

        # When
        system_prompt = generator._get_code_review_system_prompt(
            is_include_entirely_new_content=False
        )

        # Then
        assert "{{LANGUAGE}}" not in system_prompt
        assert "{{ENTIRELY_NEW_CONTENT_RULE}}" not in system_prompt
        assert "10. **Newly Added or Completely Rewritten Files**" not in system_prompt
        assert "treat the `after_code` as the entire file content" not in system_prompt

    def test_template_variable_replacement_completeness(self):
        """모든 템플릿 변수가 올바르게 치환되는지 확인"""
        # Given
        generator = PromptGenerator()

        # When - is_include_entirely_new_content=True 케이스
        system_prompt_with_rule = generator._get_code_review_system_prompt(
            is_include_entirely_new_content=True
        )

        # When - is_include_entirely_new_content=False 케이스
        system_prompt_without_rule = generator._get_code_review_system_prompt(
            is_include_entirely_new_content=False
        )

        # Then - 템플릿 변수가 남아있지 않아야 함
        template_variables = [
            "{{LANGUAGE}}",
            "{{ENTIRELY_NEW_CONTENT_RULE}}",
        ]

        for template_var in template_variables:
            assert template_var not in system_prompt_with_rule
            assert template_var not in system_prompt_without_rule

    def test_system_prompt_difference_with_rule_parameter(self):
        """is_include_entirely_new_content 파라미터에 따른 시스템 프롬프트 차이 검증"""
        # Given
        generator = PromptGenerator()

        # When
        prompt_with_rule = generator._get_code_review_system_prompt(
            is_include_entirely_new_content=True
        )
        prompt_without_rule = generator._get_code_review_system_prompt(
            is_include_entirely_new_content=False
        )

        # Then
        # 1. 두 프롬프트는 달라야 함
        assert prompt_with_rule != prompt_without_rule

        # 2. rule이 포함된 버전이 더 길어야 함
        assert len(prompt_with_rule) > len(prompt_without_rule)

        # 3. rule이 포함된 버전에서 rule 제거하면 rule이 없는 버전과 유사해야 함
        rule_text = (
            "10. **Newly Added or Completely Rewritten Files**: "
            "When `file_context.context` contains a message starting with "
            '"NEWLY ADDED OR COMPLETELY REWRITTEN FILE", treat the '
            "`after_code` as the entire file content. In this case, "
            "`before_code` should be ignored and `file_context.context` "
            "contains only an informational message, not actual code."
        )
        prompt_with_rule_cleaned = prompt_with_rule.replace(rule_text, "")
        assert prompt_with_rule_cleaned.strip() == prompt_without_rule.strip()


class TestPromptGeneratorContextTypes:
    """PromptGenerator의 각 ContextType별 명확한 시나리오 테스트"""

    @patch('selvage.src.utils.prompts.prompt_generator.SmartContextUtils.use_smart_context')
    @patch('selvage.src.utils.prompts.prompt_generator.ContextExtractor')
    @patch.object(
        PromptGenerator,
        "_get_code_review_system_prompt",
        return_value="Mock system prompt",
    )
    def test_smart_context_scenario(
        self, mock_system_prompt, mock_context_extractor, mock_use_smart_context,
        review_request: ReviewRequest
    ):
        """SMART_CONTEXT 시나리오 테스트: 스마트 컨텍스트 추출 성공"""
        # Given
        mock_use_smart_context.return_value = True
        mock_extractor_instance = mock_context_extractor.return_value
        mock_extractor_instance.extract_contexts.return_value = ["extracted context"]
        
        generator = PromptGenerator()

        # When
        review_prompt = generator.create_code_review_prompt(review_request)

        # Then
        assert len(review_prompt.user_prompts) == 1
        user_prompt = review_prompt.user_prompts[0]
        
        # 정확한 ContextType 검증
        assert user_prompt.file_context.context_type == ContextType.SMART_CONTEXT
        
        # 정확한 description 검증
        expected_description = "AST-based context extraction"
        assert user_prompt.file_context.description == expected_description
        
        # context 내용 검증
        assert user_prompt.file_context.context == "extracted context"

    @patch('selvage.src.utils.prompts.prompt_generator.SmartContextUtils.use_smart_context')
    @patch('selvage.src.utils.prompts.prompt_generator.ContextExtractor')
    @patch('selvage.src.utils.prompts.prompt_generator.FallbackContextExtractor')
    @patch.object(
        PromptGenerator,
        "_get_code_review_system_prompt",
        return_value="Mock system prompt",
    )
    def test_fallback_context_scenario(
        self, mock_system_prompt, mock_fallback_extractor, 
        mock_context_extractor, mock_use_smart_context,
        review_request: ReviewRequest
    ):
        """FALLBACK_CONTEXT 시나리오 테스트: 스마트 컨텍스트 추출 실패"""
        # Given
        mock_use_smart_context.return_value = True
        mock_extractor_instance = mock_context_extractor.return_value
        mock_extractor_instance.extract_contexts.side_effect = Exception("Context extraction failed")
        
        mock_fallback_instance = mock_fallback_extractor.return_value
        mock_fallback_instance.extract_contexts.return_value = ["fallback context"]
        
        generator = PromptGenerator()

        # When
        review_prompt = generator.create_code_review_prompt(review_request)

        # Then
        assert len(review_prompt.user_prompts) == 1
        user_prompt = review_prompt.user_prompts[0]
        
        # 정확한 ContextType 검증
        assert user_prompt.file_context.context_type == ContextType.FALLBACK_CONTEXT
        
        # 정확한 description 검증
        expected_description = "Text-based context extraction (AST fallback)"
        assert user_prompt.file_context.description == expected_description
        
        # context 내용 검증
        assert user_prompt.file_context.context == "fallback context"

    @patch('selvage.src.utils.prompts.prompt_generator.SmartContextUtils.use_smart_context')
    @patch.object(
        PromptGenerator,
        "_get_code_review_system_prompt",
        return_value="Mock system prompt",
    )
    def test_full_context_entirely_new_content_scenario(
        self, mock_system_prompt, mock_use_smart_context,
        new_file_review_request: ReviewRequest
    ):
        """FULL_CONTEXT (특별 메시지) 시나리오 테스트: 전체 새로운 내용"""
        # Given
        mock_use_smart_context.return_value = False
        # new_file_review_request는 is_entirely_new_content() == True 조건을 만족
        
        generator = PromptGenerator()

        # When
        review_prompt = generator.create_code_review_prompt(new_file_review_request)

        # Then
        assert len(review_prompt.user_prompts) == 1
        user_prompt = review_prompt.user_prompts[0]
        
        # 정확한 ContextType 검증
        assert user_prompt.file_context.context_type == ContextType.FULL_CONTEXT
        
        # 정확한 description 검증
        expected_description = "Complete file content"
        assert user_prompt.file_context.description == expected_description
        
        # 특별 메시지 검증
        assert "NEWLY ADDED OR COMPLETELY REWRITTEN FILE" in user_prompt.file_context.context

    @patch('selvage.src.utils.prompts.prompt_generator.SmartContextUtils.use_smart_context')
    @patch.object(
        PromptGenerator,
        "_get_code_review_system_prompt",
        return_value="Mock system prompt",
    )
    def test_full_context_regular_content_scenario(
        self, mock_system_prompt, mock_use_smart_context,
        review_request: ReviewRequest
    ):
        """FULL_CONTEXT (일반) 시나리오 테스트: 일반 파일 내용"""
        # Given
        mock_use_smart_context.return_value = False
        
        generator = PromptGenerator()

        # When
        review_prompt = generator.create_code_review_prompt(review_request)

        # Then
        assert len(review_prompt.user_prompts) == 1
        user_prompt = review_prompt.user_prompts[0]
        
        # 정확한 ContextType 검증
        assert user_prompt.file_context.context_type == ContextType.FULL_CONTEXT
        
        # 정확한 description 검증
        expected_description = "Complete file content"
        assert user_prompt.file_context.description == expected_description
        
        # 파일 내용 검증 (픽스쳐의 file_content와 일치해야 함)
        assert user_prompt.file_context.context == "file content"


class TestPromptConstants:
    """prompt_constants.py 모듈의 함수 테스트"""

    def test_get_entirely_new_content_rule(self):
        """get_entirely_new_content_rule 함수 출력 검증"""
        from selvage.src.utils.prompts.prompt_constants import (
            get_entirely_new_content_rule,
        )

        # When
        rule = get_entirely_new_content_rule()

        # Then
        assert isinstance(rule, str)
        assert len(rule) > 0
        assert "10. **Newly Added or Completely Rewritten Files**" in rule
        assert "treat the `after_code` as the entire file content" in rule
        assert "NEWLY ADDED OR COMPLETELY REWRITTEN FILE" in rule

    def test_get_entirely_new_content_rule_consistency(self):
        """get_entirely_new_content_rule 함수의 일관성 검증"""
        from selvage.src.utils.prompts.prompt_constants import (
            get_entirely_new_content_rule,
        )

        # When - 여러 번 호출
        rule1 = get_entirely_new_content_rule()
        rule2 = get_entirely_new_content_rule()
        rule3 = get_entirely_new_content_rule()

        # Then - 항상 동일한 결과 반환
        assert rule1 == rule2 == rule3
