"""완전한 testcontainers 기반 Linux 환경 E2E 테스트."""

import json

import pytest
from testcontainers.core.generic import DockerContainer

from e2e.helpers import verify_selvage_installation
from selvage.src.config import get_api_key
from selvage.src.models.model_provider import ModelProvider
from selvage.src.utils.json_extractor import JSONExtractor
from selvage.src.utils.token.models import ReviewResponse


@pytest.fixture(scope="function")
def testpypi_container():
    """TestPyPI 테스트용 사전 구성된 컨테이너 fixture (의존성 미리 설치됨)."""
    container = DockerContainer(image="selvage-testpypi:latest")
    container.with_command("bash -c 'while true; do sleep 1; done'")

    # API 키 설정
    gemini_api_key = get_api_key(ModelProvider.GOOGLE)
    if gemini_api_key:
        container.with_env("GEMINI_API_KEY", gemini_api_key)

    container.start()

    # 클래스 레벨에서 selvage 설치 (제거)
    # class_name = request.cls.__name__ if request.cls else "ModuleLevelTests"
    # print(f"Setting up selvage for {class_name}")
    # install_selvage_from_testpypi(container)

    yield container
    container.stop()


def test_selvage_installation_in_container(testpypi_container) -> None:
    """컨테이너 내에서 selvage 설치 및 기본 명령어 테스트."""
    container = testpypi_container

    # 컨테이너 상태 확인
    wrapped_container = container.get_wrapped_container()
    wrapped_container.reload()
    container_attrs = wrapped_container.attrs

    assert container_attrs["State"]["Running"], "Container should be running"
    assert container_attrs["State"]["Status"] == "running", (
        "Container status should be 'running'"
    )

    # Python 버전 확인
    exit_code, output = container.exec("python --version")
    assert exit_code == 0, "Python should be available"
    print(f"Python 버전: {output.decode().strip()}")

    verify_selvage_installation(container)

    # 기본 명령어 테스트
    exit_code, output = container.exec("selvage --help")
    assert exit_code == 0, "Selvage help command should work"
    assert b"selvage" in output.lower(), "Output should contain 'selvage'"


def test_selvage_config_in_container(testpypi_container) -> None:
    """컨테이너 내에서 selvage 설정 관리 테스트."""
    container = testpypi_container

    # 컨테이너 상태 확인
    wrapped_container = container.get_wrapped_container()
    wrapped_container.reload()
    container_attrs = wrapped_container.attrs

    assert container_attrs["State"]["Running"], "Container should be running"

    verify_selvage_installation(container)

    # 1. CONFIG_FILE 경로가 예상된 Linux 경로와 일치하는지 검증
    python_code_to_get_path = (
        "from selvage.src.config import CONFIG_FILE; print(CONFIG_FILE)"
    )
    exit_code, config_file_path_output = container.exec(
        f"python -c '{python_code_to_get_path}'"
    )
    assert exit_code == 0, "Failed to get CONFIG_FILE path from selvage.src.config"

    actual_config_file_path = config_file_path_output.decode(
        "utf-8", errors="ignore"
    ).strip()

    # Linux 환경에서 예상되는 경로와 일치하는지 검증
    # get_platform_config_dir() 함수를 직접 호출해서 예상 경로 구하기
    python_code_to_get_expected_path = "from selvage.src.utils.platform_utils import get_platform_config_dir; print(get_platform_config_dir() / 'config.ini')"
    exit_code, expected_path_output = container.exec(
        f"python -c '{python_code_to_get_expected_path}'"
    )

    if exit_code != 0:
        # 실제 오류 메시지 출력
        error_message = expected_path_output.decode("utf-8", errors="ignore").strip()
        print(f"Failed to get expected config path. Error: {error_message}")

        # 대안: 경로가 올바른 패턴인지만 확인
        assert "/.config/selvage/config.ini" in actual_config_file_path, (
            f"CONFIG_FILE path should contain '/.config/selvage/config.ini', "
            f"but got: {actual_config_file_path}"
        )
        print(f"CONFIG_FILE path validation (pattern match): {actual_config_file_path}")
    else:
        expected_config_file_path = expected_path_output.decode(
            "utf-8", errors="ignore"
        ).strip()

        assert actual_config_file_path == expected_config_file_path, (
            f"CONFIG_FILE path mismatch. Expected: {expected_config_file_path}, "
            f"Actual: {actual_config_file_path}"
        )
        print(f"CONFIG_FILE path validation (exact match): {actual_config_file_path}")

    # 설정 명령어 테스트
    exit_code, output = container.exec("selvage config list")
    assert exit_code == 0, "Config list command should work"

    # 2. 모델 설정 및 검증
    exit_code, output = container.exec("selvage config model gpt-4o")
    assert exit_code == 0, "Config model set should work"

    # 3. debug-mode 설정 테스트
    exit_code, output = container.exec("selvage config debug-mode on")
    assert exit_code == 0, "Config debug-mode on should work"

    exit_code, output = container.exec("selvage config debug-mode off")
    assert exit_code == 0, "Config debug-mode off should work"

    # 설정 확인
    exit_code, output = container.exec("selvage config list")
    assert exit_code == 0, "Config list verification should work"
    assert b"gpt-4o" in output, "Config should contain gpt-4o"

    # config 파일이 존재하는지 확인
    exit_code, output = container.exec(f"ls -l {actual_config_file_path}")
    assert exit_code == 0, f"Config file should exist at {actual_config_file_path}"

    # 5. config 파일 내용을 직접 읽어서 설정 값들이 올바르게 저장되었는지 검증
    exit_code, config_content = container.exec(f"cat {actual_config_file_path}")
    assert exit_code == 0, "Should be able to read config file content"

    config_content_str = config_content.decode("utf-8", errors="ignore")

    # INI 파일 형식에서 설정 값들 확인
    assert "[model]" in config_content_str, "Config should contain [model] section"
    assert "default_model = gpt-4o" in config_content_str, (
        "Config should contain model setting gpt-4o"
    )

    assert "[debug]" in config_content_str, "Config should contain [debug] section"
    assert "debug_mode = false" in config_content_str, (
        "Config should contain debug_mode = false setting"
    )

    print(
        f"✅ Config file validation successful!\n"
        f"📁 File location: {actual_config_file_path}\n"
        f"�� Config content:\n{config_content_str}"
    )


def test_selvage_review_workflow_in_container(
    testpypi_container, capfd, realistic_code_samples
) -> None:
    """컨테이너 내에서 Git workflow와 selvage 통합 테스트."""
    container = testpypi_container

    # 컨테이너 상태 확인
    wrapped_container = container.get_wrapped_container()
    wrapped_container.reload()
    container_attrs = wrapped_container.attrs

    assert container_attrs["State"]["Running"], "Container should be running"

    verify_selvage_installation(container)

    # 모델을 gemini-2.5-flash로 설정
    exit_code, output = container.exec("selvage config model gemini-2.5-flash")
    assert exit_code == 0, "Model configuration should succeed"

    # 현실적인 프로덕션 코드 샘플로 초기 파일 생성
    initial_code = realistic_code_samples["initial_code"]
    problematic_code = realistic_code_samples["problematic_code"]

    # 전체 Git 워크플로우를 하나의 스크립트로 실행
    workflow_script = f"""#!/bin/bash
set -e

# 테스트용 Git repository 생성 및 설정
mkdir -p /tmp/test_repo
cd /tmp/test_repo
git init
git config user.email test@example.com
git config user.name 'Test User'

# 초기 파일 생성 및 커밋
cat > user_api_client.py << 'INITIAL_EOF'
{initial_code}
INITIAL_EOF

git add user_api_client.py
git commit -m 'feat: Add UserApiClient for user management system'

# 문제가 있는 코드로 수정 및 스테이징
cat > user_api_client.py << 'PROBLEMATIC_EOF'
{problematic_code}
PROBLEMATIC_EOF

git add user_api_client.py

echo "Git workflow completed successfully"
"""

    # 워크플로우 스크립트를 파일로 저장하고 실행
    exit_code, output = container.exec(
        'bash -c \'cat > /tmp/workflow.sh << "SCRIPT_EOF"\n#!/bin/bash\nset -e\n\n# 테스트용 Git repository 생성 및 설정\nmkdir -p /tmp/test_repo\ncd /tmp/test_repo\ngit init\ngit config user.email test@example.com\ngit config user.name "Test User"\n\n# 초기 파일 생성 및 커밋\ncat > user_api_client.py << "INITIAL_EOF"\n'
        + initial_code
        + '\nINITIAL_EOF\n\ngit add user_api_client.py\ngit commit -m "feat: Add UserApiClient for user management system"\n\n# 문제가 있는 코드로 수정 및 스테이징\ncat > user_api_client.py << "PROBLEMATIC_EOF"\n'
        + problematic_code
        + '\nPROBLEMATIC_EOF\n\ngit add user_api_client.py\n\necho "Git workflow completed successfully"\nSCRIPT_EOF\''
    )
    assert exit_code == 0, "Workflow script creation should succeed"

    # 스크립트 실행 권한 설정 및 실행
    exit_code, output = container.exec(
        "bash -c 'chmod +x /tmp/workflow.sh && /tmp/workflow.sh'"
    )
    if exit_code != 0:
        print(
            f"Workflow script failed. Output: {output.decode('utf-8', errors='ignore')}"
        )
    assert exit_code == 0, (
        f"Git workflow should succeed. Output: {output.decode('utf-8', errors='ignore')}"
    )

    # 리뷰 결과 JSON 파일 경로 가져오기
    exit_code, config_dir_output = container.exec(
        "bash -c 'python -c \"from selvage.src.config import get_default_review_log_dir; print(get_default_review_log_dir())\"'"
    )
    assert exit_code == 0, "Should be able to get review log directory"
    review_log_dir = config_dir_output.decode("utf-8", errors="ignore").strip()

    # 애플리케이션이 review_log_dir를 생성하므로 명시적 생성 로직 제거
    # exit_code, output = container.exec(f"bash -c 'mkdir -p \"{review_log_dir}\"'")
    # assert exit_code == 0, "Review log directory creation failed"

    # API 키를 환경변수로 설정하여 selvage review --staged 실행
    exit_code, output = container.exec(
        "bash -c 'cd /tmp/test_repo && selvage review --staged'"
    )
    if exit_code != 0:
        print(
            f"Selvage review failed. Output: {output.decode('utf-8', errors='ignore')}"
        )
    assert exit_code == 0, (
        f"Selvage review should succeed with valid API key. Output: {output.decode('utf-8', errors='ignore')}"
    )

    # 리뷰 로그 디렉토리에서 JSON 파일 확인
    exit_code, json_files = container.exec(
        f"bash -c 'find {review_log_dir} -name \"*.json\" -type f | head -5'"
    )
    assert exit_code == 0, "Should be able to list JSON files"

    json_files_list = json_files.decode("utf-8", errors="ignore").strip()
    # print(f"DEBUG: Found JSON files output: {json_files!r}") # 디버그 로그 제거
    # print(f"DEBUG: Parsed JSON files list: {json_files_list!r}") # 디버그 로그 제거
    assert json_files_list, "Should have at least one JSON review result file"

    # 가장 최근 JSON 파일의 내용 확인
    latest_json_file = json_files_list.split("\n")[0]
    # print(f"DEBUG: Latest JSON file: {latest_json_file!r}") # 디버그 로그 제거
    exit_code, json_content = container.exec(f"bash -c 'cat \"{latest_json_file}\"'")
    assert exit_code == 0, (
        f"Should be able to read JSON file content. File: {latest_json_file}, Error: {json_content.decode('utf-8', errors='ignore')}"
    )

    json_content_str = json_content.decode("utf-8", errors="ignore")

    # JSONExtractor를 사용한 JSON 검증 - 전체 파일 내용을 바로 검증
    json_data = json.loads(json_content_str)
    assert "review_response" in json_data, (
        "JSON file should contain 'review_response' field"
    )

    # review_response가 None이 아닌 경우에만 ReviewResponse 모델로 검증
    validated_response = None
    if json_data["review_response"] is not None:
        validated_response = JSONExtractor.validate_and_parse_json(
            json.dumps(json_data["review_response"]), ReviewResponse
        )
        assert validated_response is not None, (
            "review_response should be valid ReviewResponse model"
        )

    # 리뷰 결과 정보 준비
    review_summary = "리뷰 내용을 확인할 수 없음"
    if validated_response and validated_response.summary:
        review_summary = (
            validated_response.summary[:200] + "..."
            if len(validated_response.summary) > 200
            else validated_response.summary
        )

    # 상세 정보 구성
    success_message = (
        f"\n{'=' * 60}\n"
        f"리뷰 결과가 성공적으로 저장되었습니다!\n"
        f"파일 위치: {latest_json_file}\n"
        f"리뷰 요약: {review_summary}\n"
        f"JSON 구조: {list(json_data.keys())}\n"
        f"RAW_JSON:\n{json.dumps(json_data.get('review_response'), indent=2, ensure_ascii=False)}\n"
    )

    # 리뷰 이슈 정보 추가
    if validated_response and validated_response.issues:
        issues_count = len(validated_response.issues)
        success_message += f"🔍 발견된 이슈 개수: {issues_count}\n"

        # 첫 번째 이슈 미리보기
        if issues_count > 0:
            first_issue = validated_response.issues[0]
            success_message += f"🔸 첫 번째 이슈: {first_issue.type} - {first_issue.description[:100]}...\n"

    success_message += f"{'=' * 60}\n"

    # 출력을 강제로 flush하여 pytest에서도 보이도록 함
    with capfd.disabled():
        print(success_message)

    # 항상 성공하는 assert이지만 메시지로 정보 전달
    assert True, success_message
