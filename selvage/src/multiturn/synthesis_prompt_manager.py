"""합성 프롬프트 관리 모듈"""

import importlib.resources

from selvage.src.config import get_default_language


class SynthesisPromptManager:
    """합성 프롬프트 관리 전용 클래스"""

    def get_summary_synthesis_prompt(self) -> str:
        """Summary 전용 합성 프롬프트 로드"""
        file_ref = importlib.resources.files(
            "selvage.resources.prompt.synthesis"
        ).joinpath("summary_synthesis_prompt.txt")
        with importlib.resources.as_file(file_ref) as file_path:
            base_prompt = file_path.read_text(encoding="utf-8")

        user_language = get_default_language()
        return base_prompt.replace("{{LANGUAGE}}", user_language)

    def get_recommendation_synthesis_prompt(self) -> str:
        """Recommendations 전용 합성 프롬프트 로드"""
        file_ref = importlib.resources.files(
            "selvage.resources.prompt.synthesis"
        ).joinpath("recommendation_synthesis_prompt.txt")
        with importlib.resources.as_file(file_ref) as file_path:
            base_prompt = file_path.read_text(encoding="utf-8")

        user_language = get_default_language()
        return base_prompt.replace("{{LANGUAGE}}", user_language)

    def get_system_prompt_for_task(self, task: str) -> str:
        """작업 타입에 따른 시스템 프롬프트 반환"""
        if task == "summary_synthesis":
            return self.get_summary_synthesis_prompt()
        elif task == "recommendation_synthesis":
            return self.get_recommendation_synthesis_prompt()
        else:
            raise ValueError(f"지원하지 않는 작업 타입: {task}")
