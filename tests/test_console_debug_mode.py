"""Console 디버그 모드 기능 테스트"""

from unittest.mock import patch, Mock
import pytest

from selvage.src.utils.base_console import console


class TestConsoleDebugMode:
    """Console 디버그 모드 기능 테스트"""

    def test_is_debug_mode_method_exists(self):
        """is_debug_mode 메서드가 존재하는지 테스트"""
        assert hasattr(console, 'is_debug_mode')
        assert callable(console.is_debug_mode)

    @patch('selvage.src.config.get_default_debug_mode')
    def test_is_debug_mode_returns_config_value_when_available(self, mock_get_debug_mode):
        """config 모듈이 있을 때 get_default_debug_mode() 값을 반환하는지 테스트"""
        # get_default_debug_mode()가 True를 반환하도록 설정
        mock_get_debug_mode.return_value = True
        
        result = console.is_debug_mode()
        
        assert result is True
        mock_get_debug_mode.assert_called_once()

    @patch('selvage.src.config.get_default_debug_mode')
    def test_is_debug_mode_returns_false_when_config_returns_false(self, mock_get_debug_mode):
        """get_default_debug_mode()가 False일 때 False를 반환하는지 테스트"""
        # get_default_debug_mode()가 False를 반환하도록 설정
        mock_get_debug_mode.return_value = False
        
        result = console.is_debug_mode()
        
        assert result is False
        mock_get_debug_mode.assert_called_once()

    def test_is_debug_mode_exception_handling_coverage(self):
        """예외 처리가 제대로 구현되어 있는지 확인하는 테스트"""
        # is_debug_mode 메서드에 try-except가 있는지 확인
        import inspect
        source = inspect.getsource(console.is_debug_mode)
        assert 'try:' in source
        assert 'except' in source
        assert 'ImportError' in source
        assert 'return False' in source

    @patch('selvage.src.config.get_default_debug_mode')
    def test_is_debug_mode_handles_config_exception(self, mock_get_debug_mode):
        """get_default_debug_mode() 호출 시 예외 발생하면 False 반환하는지 테스트"""
        # get_default_debug_mode()가 예외를 발생시키도록 설정
        mock_get_debug_mode.side_effect = Exception("Config error")
        
        result = console.is_debug_mode()
        
        # 예외가 발생해도 False를 반환해야 함
        assert result is False
        mock_get_debug_mode.assert_called_once()