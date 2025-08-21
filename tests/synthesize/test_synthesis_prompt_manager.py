"""SynthesisPromptManager 테스트"""

from unittest.mock import patch

import pytest

from selvage.src.multiturn.synthesis_prompt_manager import SynthesisPromptManager


class TestSynthesisPromptManager:
    """SynthesisPromptManager 클래스 테스트"""

    @pytest.fixture
    def prompt_manager(self) -> SynthesisPromptManager:
        """SynthesisPromptManager 인스턴스 생성"""
        return SynthesisPromptManager()

    def test_get_summary_synthesis_prompt(self, prompt_manager: SynthesisPromptManager) -> None:
        """Summary 합성 프롬프트 로드 테스트"""
        # When: Summary 합성 프롬프트 로드
        prompt = prompt_manager.get_summary_synthesis_prompt()

        # Then: 프롬프트가 정상적으로 로드되어야 함
        assert prompt is not None
        assert len(prompt) > 0
        assert isinstance(prompt, str)

    def test_get_recommendation_synthesis_prompt(self, prompt_manager: SynthesisPromptManager) -> None:
        """Recommendation 합성 프롬프트 로드 테스트"""
        # When: Recommendation 합성 프롬프트 로드
        prompt = prompt_manager.get_recommendation_synthesis_prompt()

        # Then: 프롬프트가 정상적으로 로드되어야 함
        assert prompt is not None
        assert len(prompt) > 0
        assert isinstance(prompt, str)

    def test_get_system_prompt_for_task_summary(self, prompt_manager: SynthesisPromptManager) -> None:
        """작업별 시스템 프롬프트 반환 - Summary 테스트"""
        # When: Summary 작업에 대한 시스템 프롬프트 조회
        prompt = prompt_manager.get_system_prompt_for_task("summary_synthesis")

        # Then: Summary 합성 프롬프트와 동일해야 함
        expected_prompt = prompt_manager.get_summary_synthesis_prompt()
        assert prompt == expected_prompt

    def test_get_system_prompt_for_task_recommendation(self, prompt_manager: SynthesisPromptManager) -> None:
        """작업별 시스템 프롬프트 반환 - Recommendation 테스트"""
        # When: Recommendation 작업에 대한 시스템 프롬프트 조회
        prompt = prompt_manager.get_system_prompt_for_task("recommendation_synthesis")

        # Then: Recommendation 합성 프롬프트와 동일해야 함
        expected_prompt = prompt_manager.get_recommendation_synthesis_prompt()
        assert prompt == expected_prompt

    def test_get_system_prompt_for_task_invalid(self, prompt_manager: SynthesisPromptManager) -> None:
        """작업별 시스템 프롬프트 반환 - 잘못된 작업 타입 테스트"""
        # When & Then: 지원하지 않는 작업 타입으로 호출 시 예외 발생
        with pytest.raises(ValueError, match="지원하지 않는 작업 타입"):
            prompt_manager.get_system_prompt_for_task("invalid_task")

    @patch("selvage.src.multiturn.synthesis_prompt_manager.get_default_language")
    def test_language_replacement_korean(self, mock_get_language) -> None:
        """한국어 설정 시 언어 치환 테스트"""
        # Given: 한국어 설정
        mock_get_language.return_value = "Korean"
        prompt_manager = SynthesisPromptManager()

        # When: 프롬프트 로드
        summary_prompt = prompt_manager.get_summary_synthesis_prompt()
        recommendation_prompt = prompt_manager.get_recommendation_synthesis_prompt()

        # Then: 언어 치환이 정상적으로 이루어져야 함
        assert "Korean" in summary_prompt
        assert "Korean" in recommendation_prompt

    @patch("selvage.src.multiturn.synthesis_prompt_manager.get_default_language")
    def test_language_replacement_english(self, mock_get_language) -> None:
        """영어 설정 시 언어 치환 테스트"""
        # Given: 영어 설정
        mock_get_language.return_value = "English"
        prompt_manager = SynthesisPromptManager()

        # When: 프롬프트 로드
        summary_prompt = prompt_manager.get_summary_synthesis_prompt()
        recommendation_prompt = prompt_manager.get_recommendation_synthesis_prompt()

        # Then: 언어 치환이 정상적으로 이루어져야 함
        assert "English" in summary_prompt
        assert "English" in recommendation_prompt