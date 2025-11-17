"""
Proactive Multiturn Config 테스트 모듈.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from selvage.src.config import (
    get_proactive_multiturn_threshold,
    set_proactive_multiturn_threshold,
)


class TestProactiveMultiturnConfig(unittest.TestCase):
    """Proactive Multiturn threshold 설정 테스트 클래스."""

    def setUp(self) -> None:
        """테스트 시작 전 설정."""
        # 임시 설정 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "config.ini"

        # CONFIG_DIR과 CONFIG_FILE을 임시 디렉토리로 패치
        self.patcher_dir = patch("selvage.src.config.CONFIG_DIR", Path(self.temp_dir))
        self.patcher_file = patch("selvage.src.config.CONFIG_FILE", self.config_file)
        self.patcher_dir.start()
        self.patcher_file.start()

    def tearDown(self) -> None:
        """테스트 완료 후 정리."""
        self.patcher_dir.stop()
        self.patcher_file.stop()

        # 임시 파일 정리
        if self.config_file.exists():
            self.config_file.unlink()
        if Path(self.temp_dir).exists():
            Path(self.temp_dir).rmdir()

    def test_get_default_threshold(self) -> None:
        """기본 threshold 값 확인 테스트."""
        # When: 설정이 없는 경우 기본값 가져오기
        threshold = get_proactive_multiturn_threshold()

        # Then: 기본값 200,000 반환
        self.assertEqual(threshold, 200000)

    def test_set_and_get_threshold(self) -> None:
        """threshold 설정 및 조회 테스트."""
        # Given: 새로운 threshold 값
        new_threshold = 150000

        # When: threshold 설정
        with patch("selvage.src.utils.base_console.console"):
            result = set_proactive_multiturn_threshold(new_threshold)

        # Then: 설정 성공 및 값 확인
        self.assertTrue(result)
        self.assertEqual(get_proactive_multiturn_threshold(), new_threshold)

    def test_set_threshold_negative_value(self) -> None:
        """음수 threshold 설정 시 에러 테스트."""
        # Given: 음수 threshold
        invalid_threshold = -1000

        # When: 음수 threshold 설정 시도
        with patch("selvage.src.utils.base_console.console"):
            result = set_proactive_multiturn_threshold(invalid_threshold)

        # Then: 설정 실패
        self.assertFalse(result)

    def test_set_threshold_zero_value(self) -> None:
        """0 threshold 설정 시 에러 테스트."""
        # Given: 0 threshold
        invalid_threshold = 0

        # When: 0 threshold 설정 시도
        with patch("selvage.src.utils.base_console.console"):
            result = set_proactive_multiturn_threshold(invalid_threshold)

        # Then: 설정 실패
        self.assertFalse(result)

    def test_set_threshold_large_value(self) -> None:
        """큰 threshold 값 설정 테스트."""
        # Given: 큰 threshold 값 (1백만)
        large_threshold = 1000000

        # When: 큰 값 설정
        with patch("selvage.src.utils.base_console.console"):
            result = set_proactive_multiturn_threshold(large_threshold)

        # Then: 설정 성공
        self.assertTrue(result)
        self.assertEqual(get_proactive_multiturn_threshold(), large_threshold)

    def test_threshold_persistence(self) -> None:
        """threshold 설정 영속성 테스트."""
        # Given: threshold 설정
        test_threshold = 200000
        with patch("selvage.src.utils.base_console.console"):
            set_proactive_multiturn_threshold(test_threshold)

        # When: 설정 파일 다시 로드
        saved_threshold = get_proactive_multiturn_threshold()

        # Then: 저장된 값과 동일
        self.assertEqual(saved_threshold, test_threshold)

    def test_get_threshold_with_corrupted_config(self) -> None:
        """손상된 설정 파일에서 threshold 조회 테스트."""
        # Given: 손상된 설정 파일
        self.config_file.write_text("invalid config content!@#$%", encoding="utf-8")

        # When: threshold 조회
        threshold = get_proactive_multiturn_threshold()

        # Then: 기본값 반환
        self.assertEqual(threshold, 200000)


if __name__ == "__main__":
    unittest.main()
