"""ReviewLogManager 테스트"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from selvage.src.utils.logging.review_log_manager import ReviewLogManager


class TestReviewLogManager:
    """ReviewLogManager 테스트 클래스"""

    @pytest.fixture
    def temp_log_dir(self):
        """임시 로그 디렉토리 픽스처"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def sample_log_data(self):
        """샘플 로그 데이터 픽스처"""
        return {
            "id": "test-log-id-123",
            "model": {"provider": "openai", "name": "gpt-4"},
            "created_at": "2024-01-15T10:30:00",
            "status": "SUCCESS",
            "repo_path": "/test/repo",
            "total_cost": 0.05,
            "token_info": {"input_tokens": 1000, "output_tokens": 500},
            "review_request": {
                "model": "gpt-4",
                "repo_path": "/test/repo",
                "diff_mode": "current",
            },
            "review_response": {"summary": "Test review"},
            "prompt": [],
            "error": None,
            "prompt_version": "v4",
        }

    def create_sample_log_file(self, log_dir: Path, log_data: dict, filename: str):
        """샘플 로그 파일 생성"""
        log_file = log_dir / f"{filename}.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        return log_file

    def test_get_recent_logs_empty_directory(self, temp_log_dir):
        """빈 디렉토리에서 get_recent_logs 테스트"""
        with patch(
            "selvage.src.utils.logging.review_log_manager.get_default_review_log_dir",
            return_value=temp_log_dir,
        ):
            result = ReviewLogManager.get_recent_logs(repo_path="ALL")
            assert result == []

    def test_get_recent_logs_basic(self, temp_log_dir, sample_log_data):
        """기본 get_recent_logs 테스트"""
        # 샘플 로그 파일 생성
        self.create_sample_log_file(
            temp_log_dir, sample_log_data, "20240115_103000_gpt-4_review_log"
        )

        with patch(
            "selvage.src.utils.logging.review_log_manager.get_default_review_log_dir",
            return_value=temp_log_dir,
        ):
            result = ReviewLogManager.get_recent_logs(limit=10, repo_path="ALL")
            assert len(result) == 1
            assert result[0]["log_id"] == "test-log-id-123"
            assert result[0]["model"] == "gpt-4"
            assert result[0]["status"] == "SUCCESS"
            assert result[0]["cost"] == 0.05
            assert result[0]["files_count"] == 0  # 기본값

    def test_get_recent_logs_with_limit(self, temp_log_dir, sample_log_data):
        """limit 파라미터로 get_recent_logs 테스트"""
        # 여러 로그 파일 생성
        for i in range(5):
            log_data = sample_log_data.copy()
            log_data["id"] = f"test-log-id-{i}"
            log_data["created_at"] = f"2024-01-15T10:3{i}:00"
            self.create_sample_log_file(
                temp_log_dir, log_data, f"20240115_1030{i}0_gpt-4_review_log"
            )

        with patch(
            "selvage.src.utils.logging.review_log_manager.get_default_review_log_dir",
            return_value=temp_log_dir,
        ):
            result = ReviewLogManager.get_recent_logs(limit=3, repo_path="ALL")
            assert len(result) == 3
            # 최신 순으로 정렬되어야 함
            assert result[0]["log_id"] == "test-log-id-4"
            assert result[1]["log_id"] == "test-log-id-3"
            assert result[2]["log_id"] == "test-log-id-2"

    def test_get_recent_logs_with_model_filter(self, temp_log_dir, sample_log_data):
        """model_filter 파라미터로 get_recent_logs 테스트"""
        # 다른 모델로 로그 파일 생성
        claude_log = sample_log_data.copy()
        claude_log["id"] = "claude-log-id"
        claude_log["model"] = {"provider": "anthropic", "name": "claude-sonnet-4"}
        self.create_sample_log_file(
            temp_log_dir, claude_log, "20240115_103000_claude-sonnet-4_review_log"
        )

        gpt_log = sample_log_data.copy()
        gpt_log["id"] = "gpt-log-id"
        self.create_sample_log_file(
            temp_log_dir, gpt_log, "20240115_103100_gpt-4_review_log"
        )

        with patch(
            "selvage.src.utils.logging.review_log_manager.get_default_review_log_dir",
            return_value=temp_log_dir,
        ):
            # Claude 모델 필터링
            result = ReviewLogManager.get_recent_logs(
                model_filter="claude-sonnet-4", repo_path="ALL"
            )
            assert len(result) == 1
            assert result[0]["log_id"] == "claude-log-id"

            # GPT 모델 필터링
            result = ReviewLogManager.get_recent_logs(
                model_filter="gpt-4", repo_path="ALL"
            )
            assert len(result) == 1
            assert result[0]["log_id"] == "gpt-log-id"

    def test_get_recent_logs_with_repo_path_filter(self, temp_log_dir, sample_log_data):
        """repo_path 파라미터로 get_recent_logs 테스트"""
        # 다른 repo_path로 로그 파일 생성
        repo1_log = sample_log_data.copy()
        repo1_log["id"] = "repo1-log-id"
        repo1_log["repo_path"] = "/test/repo1"
        self.create_sample_log_file(
            temp_log_dir, repo1_log, "20240115_103000_gpt-4_review_log"
        )

        repo2_log = sample_log_data.copy()
        repo2_log["id"] = "repo2-log-id"
        repo2_log["repo_path"] = "/test/repo2"
        self.create_sample_log_file(
            temp_log_dir, repo2_log, "20240115_103100_gpt-4_review_log"
        )

        with patch(
            "selvage.src.utils.logging.review_log_manager.get_default_review_log_dir",
            return_value=temp_log_dir,
        ):
            # repo1 필터링
            result = ReviewLogManager.get_recent_logs(repo_path="/test/repo1")
            assert len(result) == 1
            assert result[0]["log_id"] == "repo1-log-id"

    def test_get_recent_logs_with_none_repo_path(self, temp_log_dir, sample_log_data):
        """repo_path=None일 때 현재 프로젝트 자동 필터링 테스트"""
        current_project_log = sample_log_data.copy()
        current_project_log["id"] = "current-project-log"
        current_project_log["repo_path"] = "/Users/demin_coder/Dev/selvage"
        self.create_sample_log_file(
            temp_log_dir, current_project_log, "20240115_103000_gpt-4_review_log"
        )

        other_project_log = sample_log_data.copy()
        other_project_log["id"] = "other-project-log"
        other_project_log["repo_path"] = "/test/other-project"
        self.create_sample_log_file(
            temp_log_dir, other_project_log, "20240115_103100_gpt-4_review_log"
        )

        with (
            patch(
                "selvage.src.utils.logging.review_log_manager.get_default_review_log_dir",
                return_value=temp_log_dir,
            ),
            patch(
                "selvage.src.utils.logging.review_log_manager.find_project_root",
                return_value=Path("/Users/demin_coder/Dev/selvage"),
            ),
        ):
            # repo_path=None (기본값) - 현재 프로젝트만 조회
            result = ReviewLogManager.get_recent_logs()
            assert len(result) == 1
            assert result[0]["log_id"] == "current-project-log"

    def test_get_recent_logs_with_all_repo_path(self, temp_log_dir, sample_log_data):
        """repo_path="ALL"일 때 모든 프로젝트 로그 조회 테스트"""
        project1_log = sample_log_data.copy()
        project1_log["id"] = "project1-log"
        project1_log["repo_path"] = "/test/project1"
        self.create_sample_log_file(
            temp_log_dir, project1_log, "20240115_103000_gpt-4_review_log"
        )

        project2_log = sample_log_data.copy()
        project2_log["id"] = "project2-log"
        project2_log["repo_path"] = "/test/project2"
        self.create_sample_log_file(
            temp_log_dir, project2_log, "20240115_103100_gpt-4_review_log"
        )

        with patch(
            "selvage.src.utils.logging.review_log_manager.get_default_review_log_dir",
            return_value=temp_log_dir,
        ):
            # repo_path="ALL" - 모든 프로젝트 로그 조회
            result = ReviewLogManager.get_recent_logs(repo_path="ALL")
            assert len(result) == 2
            log_ids = {item["log_id"] for item in result}
            assert log_ids == {"project1-log", "project2-log"}

    def test_get_recent_logs_project_root_not_found(
        self, temp_log_dir, sample_log_data
    ):
        """find_project_root 실패 시 현재 디렉토리 사용 테스트"""
        current_dir_log = sample_log_data.copy()
        current_dir_log["id"] = "current-dir-log"
        # 현재 작업 디렉토리를 repo_path로 사용
        current_dir_log["repo_path"] = str(Path.cwd())
        self.create_sample_log_file(
            temp_log_dir, current_dir_log, "20240115_103000_gpt-4_review_log"
        )

        with (
            patch(
                "selvage.src.utils.logging.review_log_manager.get_default_review_log_dir",
                return_value=temp_log_dir,
            ),
            patch(
                "selvage.src.utils.logging.review_log_manager.find_project_root",
                side_effect=FileNotFoundError("프로젝트 루트를 찾을 수 없습니다"),
            ),
        ):
            # find_project_root 실패 시 현재 디렉토리 사용
            result = ReviewLogManager.get_recent_logs()
            assert len(result) == 1
            assert result[0]["log_id"] == "current-dir-log"

    def test_load_log_success(self, temp_log_dir, sample_log_data):
        """load_log 성공 테스트"""
        log_file = self.create_sample_log_file(
            temp_log_dir, sample_log_data, "20240115_103000_gpt-4_review_log"
        )

        with patch(
            "selvage.src.utils.logging.review_log_manager.get_default_review_log_dir",
            return_value=temp_log_dir,
        ):
            result = ReviewLogManager.load_log("test-log-id-123")
            assert result == sample_log_data

    def test_load_log_not_found(self, temp_log_dir):
        """load_log 파일 없음 테스트"""
        with patch(
            "selvage.src.utils.logging.review_log_manager.get_default_review_log_dir",
            return_value=temp_log_dir,
        ):
            with pytest.raises(FileNotFoundError):
                ReviewLogManager.load_log("non-existent-log-id")

    def test_load_log_invalid_json(self, temp_log_dir):
        """load_log 잘못된 JSON 테스트"""
        # 잘못된 JSON 파일 생성
        log_file = temp_log_dir / "20240115_103000_gpt-4_review_log.json"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("invalid json content")

        # JSON 파일에 log_id 추가 (실제로는 파싱 실패할 예정)
        with patch(
            "selvage.src.utils.logging.review_log_manager.get_default_review_log_dir",
            return_value=temp_log_dir,
        ):
            with pytest.raises(json.JSONDecodeError):
                ReviewLogManager.load_log("any-log-id")

    def test_get_recent_logs_timestamp_parsing(self, temp_log_dir, sample_log_data):
        """timestamp 파싱 테스트"""
        # ISO 형식 timestamp
        iso_log = sample_log_data.copy()
        iso_log["id"] = "iso-log-id"
        iso_log["created_at"] = "2024-01-15T10:30:00"
        self.create_sample_log_file(
            temp_log_dir, iso_log, "20240115_103000_gpt-4_review_log"
        )

        # Z suffix timestamp
        z_log = sample_log_data.copy()
        z_log["id"] = "z-log-id"
        z_log["created_at"] = "2024-01-15T10:30:00Z"
        self.create_sample_log_file(
            temp_log_dir, z_log, "20240115_103100_gpt-4_review_log"
        )

        with patch(
            "selvage.src.utils.logging.review_log_manager.get_default_review_log_dir",
            return_value=temp_log_dir,
        ):
            result = ReviewLogManager.get_recent_logs(repo_path="ALL")
            assert len(result) == 2
            # timestamp가 datetime 객체로 변환되어야 함
            for item in result:
                assert "timestamp" in item
                assert isinstance(item["timestamp"], str)

    def test_get_recent_logs_files_count_extraction(
        self, temp_log_dir, sample_log_data
    ):
        """files_count 추출 테스트"""
        # review_request에 files 정보가 있는 경우
        log_with_files = sample_log_data.copy()
        log_with_files["id"] = "files-log-id"
        log_with_files["review_request"]["files"] = ["file1.py", "file2.py", "file3.py"]
        self.create_sample_log_file(
            temp_log_dir, log_with_files, "20240115_103000_gpt-4_review_log"
        )

        with patch(
            "selvage.src.utils.logging.review_log_manager.get_default_review_log_dir",
            return_value=temp_log_dir,
        ):
            result = ReviewLogManager.get_recent_logs(repo_path="ALL")
            assert len(result) == 1
            assert result[0]["files_count"] == 3
