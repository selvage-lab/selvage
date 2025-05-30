"""End-to-End 테스트를 위한 pytest 설정 및 fixture들."""

import pytest


def pytest_configure(config):
    """pytest 설정을 구성합니다. E2E 테스트용 마커들을 등록합니다."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
    config.addinivalue_line(
        "markers", "container: marks tests that require Docker containers"
    )
    config.addinivalue_line(
        "markers", "error_scenario: marks tests that test error handling scenarios"
    )
    config.addinivalue_line(
        "markers", "workflow: marks tests that simulate realistic developer workflows"
    )
    config.addinivalue_line(
        "markers", "cross_platform: marks tests that should run on multiple platforms"
    )


# E2E 테스트에서는 필터링을 무효화
def pytest_ignore_collect(collection_path, config):
    """E2E 테스트에서는 전역 필터링을 무시합니다."""
    # E2E 테스트 실행시에는 아무것도 필터링하지 않음
    return False


@pytest.fixture
def realistic_code_samples():
    """실제 프로덕션에서 사용할 만한 현실적인 코드 샘플들을 제공합니다."""
    return {
        "initial_code": '''"""API 클라이언트 모듈 - 사용자 관리 시스템"""
import json
from typing import Optional, Dict, Any

class UserApiClient:
    """사용자 관리 API 클라이언트"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = None
    
    def authenticate(self) -> bool:
        """API 인증을 수행합니다."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        # 인증 로직 구현 필요
        return True
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """사용자 정보를 조회합니다."""
        if not self.authenticate():
            return None
        
        # API 호출 로직
        response_data = {"id": user_id, "name": "Test User"}
        return response_data
    
    def create_user(self, user_data: Dict[str, Any]) -> bool:
        """새 사용자를 생성합니다."""
        if not user_data.get("email"):
            raise ValueError("이메일은 필수입니다")
        
        # 사용자 생성 로직
        return True
''',
        "problematic_code": '''"""API 클라이언트 모듈 - 사용자 관리 시스템 (문제 버전)"""
import json
from typing import Optional, Dict, Any

class UserApiClient:
    """사용자 관리 API 클라이언트"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = None
    
    def authenticate(self) -> bool:
        """API 인증을 수행합니다."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        # TODO: 실제 인증 로직 구현 필요
        return True
    
    def get_user(self, user_id):  # 타입 힌트 누락
        """사용자 정보를 조회합니다."""
        # 인증 검사 없음 (보안 문제)
        response_data = {"id": user_id, "name": "Test User"}
        return response_data
    
    def create_user(self, user_data: Dict[str, Any]) -> bool:
        """새 사용자를 생성합니다."""
        # 입력 검증 없음 (잠재적 버그)
        return True
    
    def delete_user(self, user_id: int) -> bool:
        """사용자를 삭제합니다."""
        # 위험: 소프트 삭제가 아닌 하드 삭제
        # 로그 없음, 예외 처리 없음
        return True
    
    def get_user(self, user_id: int) -> str:  # 중복 함수 정의 (기존 함수 덮어씀)
        """사용자 정보를 문자열로 반환합니다."""
        return f"User: {user_id}"
''',
        "security_issue_code": '''"""보안 취약점이 있는 코드 샘플"""
import os
import subprocess

class ConfigManager:
    def __init__(self):
        self.config = {}
    
    def load_config(self, config_file: str) -> None:
        """설정 파일을 로드합니다."""
        # 위험: 파일 경로 검증 없음
        with open(config_file, 'r') as f:
            exec(f.read())  # 매우 위험한 코드 실행
    
    def execute_command(self, cmd: str) -> str:
        """시스템 명령어를 실행합니다."""
        # 위험: 입력 검증 없는 shell injection 가능
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout
    
    def get_secret(self, key: str) -> str:
        """환경 변수에서 비밀값을 가져옵니다."""
        secret = os.getenv(key)
        if not secret:
            print(f"Warning: {key} not found")  # 민감 정보 로깅
        return secret or "default_secret"  # 기본값 사용 (보안 위험)
''',
    }
