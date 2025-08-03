"""Java Annotation 관련 ContextExtractor 테스트 케이스."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import ContextExtractor, LineRange


class TestAnnotatedExtraction:
    """Annotation이 포함된 클래스/메서드 추출 테스트."""

    @pytest.fixture
    def annotated_file_content(self) -> str:
        """Annotation이 포함된 테스트용 샘플 파일 내용을 반환합니다."""
        file_path = Path(__file__).parent / "SampleAnnotatedClass.java"
        return file_path.read_text(encoding="utf-8")

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Java용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("java")

    def test_entity_annotation_extraction(
        self,
        extractor: ContextExtractor,
        annotated_file_content: str,
    ) -> None:
        """@Entity가 붙은 클래스 추출 시 annotation 포함 테스트."""
        # UserInfo 클래스의 name 필드 라인
        changed_ranges = [LineRange(22, 23)]  # private String name; 라인
        contexts = extractor.extract_contexts(annotated_file_content, changed_ranges)

        # 정확한 추출 결과 검증 - import와 annotation이 포함되어야 함
        all_context = "\n".join(contexts)

        # annotation이 포함되어 있는지 확인
        assert "@Entity" in all_context
        assert "@Component" in all_context
        assert "private String name;" in all_context

    def test_method_with_override_annotation(
        self,
        extractor: ContextExtractor,
        annotated_file_content: str,
    ) -> None:
        """@Override annotation이 붙은 메서드 추출 테스트."""
        # toString 메서드 내부 변경
        changed_ranges = [LineRange(49, 50)]  # return 문 라인
        contexts = extractor.extract_contexts(annotated_file_content, changed_ranges)

        all_context = "\n".join(contexts)

        # @Override annotation이 포함되어 있는지 확인
        assert "@Override" in all_context
        assert "public String toString()" in all_context
        assert "return String.format" in all_context

    def test_multiple_annotations(
        self,
        extractor: ContextExtractor,
        annotated_file_content: str,
    ) -> None:
        """여러 annotation이 붙은 메서드 추출 테스트."""
        # isConnected 메서드 내부 변경 (다중 annotation)
        changed_ranges = [LineRange(203, 203)]  # return true 라인
        contexts = extractor.extract_contexts(annotated_file_content, changed_ranges)

        all_context = "\n".join(contexts)

        # 다중 annotation이 모두 포함되어 있는지 확인
        assert "@Async" in all_context
        assert "@Transactional" in all_context
        assert "@Cacheable" in all_context
        assert "public boolean isConnected()" in all_context

    def test_annotated_method_extraction(
        self,
        extractor: ContextExtractor,
        annotated_file_content: str,
    ) -> None:
        """@Async, @Transactional annotation이 붙은 메서드 추출 테스트."""
        # processUserData 메서드 내부 변경
        changed_ranges = [LineRange(216, 220)]  # 메서드 본문
        contexts = extractor.extract_contexts(annotated_file_content, changed_ranges)

        all_context = "\n".join(contexts)

        # annotation과 메서드가 올바르게 추출되었는지 확인
        assert "@Async" in all_context
        assert "@Transactional" in all_context
        assert "processUserData" in all_context
        assert "@Valid UserInfo userInfo" in all_context
        assert "Map<String, Object> result" in all_context
