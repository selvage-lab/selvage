"""Kotlin Annotation 관련 ContextExtractor 테스트 케이스."""

from __future__ import annotations

from pathlib import Path

import pytest

from selvage.src.context_extractor import ContextExtractor, LineRange


class TestAnnotatedExtraction:
    """Annotation이 포함된 클래스/메서드 추출 테스트."""

    @pytest.fixture
    def annotated_file_path(self) -> Path:
        """Annotation이 포함된 테스트용 샘플 파일 경로를 반환합니다."""
        return Path(__file__).parent / "SampleAnnotatedClass.kt"

    @pytest.fixture
    def extractor(self) -> ContextExtractor:
        """Kotlin용 ContextExtractor 인스턴스를 반환합니다."""
        return ContextExtractor("kotlin")

    def test_entity_annotation_extraction(
        self,
        extractor: ContextExtractor,
        annotated_file_path: Path,
    ) -> None:
        """@Entity가 붙은 data class 추출 시 annotation 포함 테스트."""
        # UserInfo data class의 name 필드 라인
        changed_ranges = [LineRange(21, 21)]  # val name: String 라인
        contexts = extractor.extract_contexts(annotated_file_path, changed_ranges)

        all_context = "\n".join(contexts)

        # annotation이 포함되어 있는지 확인
        assert "@Entity" in all_context
        assert "@Component" in all_context
        assert "data class UserInfo" in all_context
        assert "val name: String" in all_context

    def test_method_with_deprecated_annotation(
        self,
        extractor: ContextExtractor,
        annotated_file_path: Path,
    ) -> None:
        """@Deprecated annotation이 붙은 메서드 추출 테스트."""
        # getDisplayName 메서드 내부 변경
        changed_ranges = [LineRange(38, 39)]  # return 문 라인
        contexts = extractor.extract_contexts(annotated_file_path, changed_ranges)

        all_context = "\n".join(contexts)

        # @Deprecated와 @JvmOverloads annotation이 포함되어 있는지 확인
        assert "@JvmOverloads" in all_context
        assert "@Deprecated" in all_context
        assert "fun getDisplayName" in all_context
        assert 'prefix: String = ""' in all_context

    def test_multiple_annotations(
        self,
        extractor: ContextExtractor,
        annotated_file_path: Path,
    ) -> None:
        """여러 annotation이 붙은 메서드 추출 테스트."""
        # isConnected 메서드 내부 변경 (다중 annotation)
        changed_ranges = [LineRange(195, 195)]  # return true 라인
        contexts = extractor.extract_contexts(annotated_file_path, changed_ranges)

        all_context = "\n".join(contexts)

        # 다중 annotation이 모두 포함되어 있는지 확인
        assert "@Async" in all_context
        assert "@Transactional" in all_context
        assert "@Cacheable" in all_context
        assert "fun isConnected()" in all_context

    def test_jvm_annotated_method_extraction(
        self,
        extractor: ContextExtractor,
        annotated_file_path: Path,
    ) -> None:
        """@JvmOverloads annotation이 붙은 메서드 추출 테스트."""
        # processUserData 메서드 선언부
        changed_ranges = [LineRange(205, 205)]  # 메서드 선언부
        contexts = extractor.extract_contexts(annotated_file_path, changed_ranges)

        all_context = "\n".join(contexts)

        # annotation과 메서드가 올바르게 추출되었는지 확인
        assert "@Async" in all_context
        assert "@Transactional" in all_context
        assert "@JvmOverloads" in all_context
        assert "processUserData" in all_context
        assert "@Valid userInfo: UserInfo" in all_context
        assert "includeEmail: Boolean = true" in all_context
