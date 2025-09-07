"""
리뷰 결과를 보여주는 Streamlit 웹 인터페이스 모듈

이 모듈은 저장된 리뷰 결과를 Streamlit을 사용하여 웹 브라우저에 표시합니다.
"""

import copy
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from selvage.src.config import get_default_review_log_dir
from selvage.src.utils.base_console import console
from selvage.src.utils.review_formatter import ReviewFormatter
from selvage.src.utils.token.models import ReviewResponse


def get_default_llm_eval_data_dir() -> Path:
    """llm_eval 데이터가 저장된 data 디렉토리 경로를 반환합니다."""
    project_root = Path(__file__).resolve().parent.parent.parent
    return project_root / "llm_eval" / "results"


def get_llm_eval_data_files() -> list[Path]:
    """llm_eval 데이터 디렉토리에서 모든 파일을 가져옵니다."""
    llm_eval_data_dir = get_default_llm_eval_data_dir()
    if not llm_eval_data_dir.exists():
        return []

    llm_eval_files = list(llm_eval_data_dir.glob("*"))
    llm_eval_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return llm_eval_files


def get_review_log_files() -> list[Path]:
    """리뷰 로그 디렉토리에서 모든 리뷰 로그 파일을 가져옵니다."""
    log_dir = get_default_review_log_dir()
    if not log_dir.exists():
        return []

    log_files = list(log_dir.glob("*.json"))
    log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return log_files


def parse_date_from_filename(filename: str) -> datetime | None:
    """파일명에서 날짜 정보를 추출합니다."""
    parts = filename.split("_")

    # YYYYMMDD_HHMMSS 형식 검색
    if len(parts) >= 2:
        # 접두사에 날짜가 있는 경우: YYYYMMDD_HHMMSS_...
        if (
            parts[0].isdigit()
            and len(parts[0]) == 8
            and parts[1].isdigit()
            and len(parts[1]) == 6
        ):
            try:
                return datetime.strptime(f"{parts[0]}_{parts[1]}", "%Y%m%d_%H%M%S")
            except ValueError:
                pass

        # 접미사에 날짜가 있는 경우: ..._YYYYMMDD_HHMMSS
        if (
            parts[-2].isdigit()
            and len(parts[-2]) == 8
            and parts[-1].isdigit()
            and len(parts[-1]) == 6
        ):
            try:
                return datetime.strptime(f"{parts[-2]}_{parts[-1]}", "%Y%m%d_%H%M%S")
            except ValueError:
                pass

        # 중간에 날짜가 있는 경우
        for i in range(len(parts) - 1):
            if (
                parts[i].isdigit()
                and len(parts[i]) == 8
                and parts[i + 1].isdigit()
                and len(parts[i + 1]) == 6
            ):
                try:
                    return datetime.strptime(
                        f"{parts[i]}_{parts[i + 1]}", "%Y%m%d_%H%M%S"
                    )
                except ValueError:
                    pass

    return None


def extract_model_name_from_filename(filename: str, date_parts_count: int = 0) -> str:
    """파일명에서 모델 이름을 추출합니다."""
    parts = filename.split("_")

    if date_parts_count == 2 and len(parts) > 2:
        # 날짜 부분 제외한 나머지를 모델명으로 간주
        return "_".join(parts[2:])
    elif len(parts) > 0 and not parts[-1].isdigit():
        # 마지막 부분이 숫자가 아니면 모델명으로 간주
        return parts[-1]

    return ""


def determine_file_format(file_path: Path) -> str:
    """파일의 형식을 결정합니다."""
    file_suffix = file_path.suffix.lstrip(".").lower()

    if not file_suffix:
        # 확장자 없는 파일 처리
        try:
            # llm_eval 디렉토리 내 파일인지 확인
            llm_eval_dir = get_default_llm_eval_data_dir().resolve()
            file_parent = file_path.parent.resolve()

            is_in_llm_eval_dir = str(file_parent).startswith(str(llm_eval_dir))

            # 파일명에 날짜 형식이 있는지 확인
            parts = file_path.stem.split("_")
            has_date_format = (
                len(parts) >= 2
                and parts[0].isdigit()
                and len(parts[0]) == 8
                and parts[1].isdigit()
                and len(parts[1]) == 6
            )

            if is_in_llm_eval_dir or has_date_format:
                return "json"
            return "txt"
        except Exception as e:
            console.error(
                f"Error occurred while determining file format: {e}", exception=e
            )
            return "txt"

    return file_suffix if file_suffix in ["json", "log", "html", "txt"] else "txt"


def get_file_info(file: Path) -> dict[str, Any]:
    """파일 정보를 가져옵니다."""
    mtime = datetime.fromtimestamp(file.stat().st_mtime)
    size = file.stat().st_size
    size_str = f"{size / 1024:.1f}KB" if size >= 1024 else f"{size}B"

    # 날짜 추출
    date_candidate = parse_date_from_filename(file.stem)
    if date_candidate is None:
        date_candidate = mtime
        date_parts_count = 0
    else:
        date_parts_count = 2

    # 모델명 추출
    model_name_candidate = extract_model_name_from_filename(file.stem, date_parts_count)

    # 파일 형식 결정
    file_format = determine_file_format(file)

    # repo_path 추출 (JSON 파일인 경우)
    repo_path = None
    if file_format == "json":
        repo_path = extract_repo_path_from_file(file)

    return {
        "path": file,
        "name": file.name,
        "model": model_name_candidate,
        "date": date_candidate,
        "mtime": mtime,
        "size": size,
        "size_str": size_str,
        "format": file_format,
        "repo_path": repo_path,
    }


def get_uploaded_file_info(uploaded_file: UploadedFile, content: str) -> dict[str, Any]:
    """업로드된 파일 정보를 가져옵니다."""
    upload_time = datetime.now()
    size = len(content.encode("utf-8"))
    size_str = f"{size / 1024:.1f}KB" if size >= 1024 else f"{size}B"

    # 파일명에서 확장자 추출
    file_name = uploaded_file.name
    file_stem = Path(file_name).stem
    file_suffix = Path(file_name).suffix.lstrip(".").lower()

    # 날짜 추출
    date_candidate = parse_date_from_filename(file_stem)
    if date_candidate is None:
        date_candidate = upload_time
        date_parts_count = 0
    else:
        date_parts_count = 2

    # 모델명 추출
    model_name_candidate = extract_model_name_from_filename(file_stem, date_parts_count)

    # 파일 형식 결정
    file_format = (
        file_suffix if file_suffix in ["json", "log", "html", "txt"] else "txt"
    )

    # repo_path 추출 (JSON 파일인 경우)
    repo_path = None
    if file_format == "json":
        try:
            json_data = json.loads(content)
            repo_path = json_data.get("repo_path")
        except json.JSONDecodeError:
            repo_path = None

    return {
        "path": None,  # 업로드 파일은 실제 경로가 없음
        "name": file_name,
        "model": model_name_candidate,
        "date": date_candidate,
        "mtime": upload_time,
        "size": size,
        "size_str": size_str,
        "format": file_format,
        "repo_path": repo_path,
        "content": content,  # 업로드된 파일의 내용
        "is_uploaded": True,  # 업로드 파일 구분용
    }


def display_file_info(file_info: dict[str, Any]) -> None:
    """파일 정보를 화면에 표시합니다."""
    col1, col2, col3 = st.columns(3)
    with col1:
        # 파일명과 프로젝트명 표시
        file_display = f"**파일명**: {file_info['name']}"
        if "repo_path" in file_info and file_info["repo_path"]:
            project_display = format_repo_path_display(file_info["repo_path"])
            file_display += f" `({project_display})`"
        st.markdown(file_display)
    with col2:
        st.markdown(f"**날짜**: {file_info['date'].strftime('%Y-%m-%d %H:%M')}")
    with col3:
        st.markdown(f"**크기**: {file_info['size_str']}")


def parse_json_content(content: str) -> dict[str, Any]:
    """JSON 문자열을 파싱합니다."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {}


def parse_prompt_content(prompt_list: list) -> list:
    """프롬프트 데이터의 content 필드를 파싱합니다."""
    if not isinstance(prompt_list, list):
        return prompt_list

    parsed_list = []
    for item in prompt_list:
        item_copy = copy.deepcopy(item)
        if (
            isinstance(item_copy, dict)
            and "content" in item_copy
            and isinstance(item_copy["content"], str)
        ):
            try:
                item_copy["content"] = json.loads(item_copy["content"])
            except json.JSONDecodeError:
                pass
        parsed_list.append(item_copy)

    return parsed_list


def display_json_field_in_expander(
    key: str, value: dict[str, Any] | list | None
) -> None:
    """JSON 필드를 접을 수 있는 expander로 표시합니다."""
    if not value:  # None이거나 빈 값
        with st.expander(f"{key} 내용 보기", expanded=False):
            st.write("내용 없음")
        return

    with st.expander(f"{key} 내용 보기", expanded=False):
        if key == "prompt" and isinstance(value, list):
            parsed_value = parse_prompt_content(value)
            st.json(parsed_value, expanded=True)
        else:
            st.json(value, expanded=True)


def display_review_result_raw_json(json_data: dict[str, Any]) -> None:
    """리뷰 결과의 원본 JSON을 표시합니다."""
    st.markdown("## 원본 JSON 데이터")
    data_to_display = copy.deepcopy(json_data)

    # 주요 필드를 expander로 표시
    target_keys = ["prompt", "review_request", "review_response"]
    for key in target_keys:
        if key in data_to_display:
            display_json_field_in_expander(key, data_to_display.pop(key))

    # 나머지 데이터 표시
    if data_to_display:
        st.markdown("---")
        st.markdown("### 원본 데이터")
        st.json(json_data, expanded=False)


def filter_failed_test_cases(test_cases: list) -> tuple[list, int]:
    """실패한 테스트 케이스만 필터링합니다."""
    if not isinstance(test_cases, list):
        return [], 0

    filtered_cases = []

    for tc in test_cases:
        if not isinstance(tc, dict) or tc.get("success") is not False:
            continue

        tc_copy = copy.deepcopy(tc)

        # metricsData 내부에서 실패한 항목만 필터링
        if "metricsData" in tc_copy and isinstance(tc_copy["metricsData"], list):
            filtered_metrics = [
                m
                for m in tc_copy["metricsData"]
                if isinstance(m, dict) and m.get("success") is False
            ]
            tc_copy["metricsData"] = filtered_metrics or []

        filtered_cases.append(tc_copy)

    return filtered_cases, len(filtered_cases)


def parse_test_case_inputs(test_cases: list) -> None:
    """테스트 케이스의 입력 필드를 파싱합니다."""
    if not isinstance(test_cases, list):
        return

    for test_case in test_cases:
        if not isinstance(test_case, dict):
            continue

        # input 필드 처리
        if "input" in test_case and isinstance(test_case["input"], str):
            try:
                parsed_input = json.loads(test_case["input"])
                if isinstance(parsed_input, list):
                    parsed_input = parse_prompt_content(parsed_input)
                test_case["input"] = parsed_input
            except json.JSONDecodeError:
                pass

        # actualOutput 필드 처리
        if "actualOutput" in test_case and isinstance(test_case["actualOutput"], str):
            try:
                test_case["actualOutput"] = json.loads(test_case["actualOutput"])
            except json.JSONDecodeError:
                pass


def display_llm_eval_results(json_data: dict[str, Any]) -> None:
    """llm_eval 결과를 표시합니다."""
    st.markdown("## llm_eval 결과 내용")

    # 데이터 복사
    display_data = copy.deepcopy(json_data)

    # 테스트 케이스 수 계산
    test_cases = (
        display_data.get("testCases", []) if isinstance(display_data, dict) else []
    )
    num_total_cases = len(test_cases) if isinstance(test_cases, list) else 0

    # 필터링 컨트롤
    col_checkbox, col_count = st.columns([0.8, 0.2])
    with col_checkbox:
        filter_failed_tests = st.checkbox(
            "실패한 테스트 케이스만 보기 (success=false)",
            key="llm_eval_filter_checkbox",
        )

    # 필터링 적용
    num_displayed_cases = num_total_cases
    if (
        filter_failed_tests
        and isinstance(display_data, dict)
        and "testCases" in display_data
    ):
        filtered_cases, num_displayed_cases = filter_failed_test_cases(
            display_data["testCases"]
        )
        display_data["testCases"] = filtered_cases
        count_caption_text = (
            f"(표시: {num_displayed_cases} / 총: {num_total_cases}건, 실패만)"
        )
    else:
        count_caption_text = f"(총 {num_total_cases}건)"

    with col_count:
        st.caption(count_caption_text)

    # 입력 필드 파싱
    if isinstance(display_data, dict) and "testCases" in display_data:
        parse_test_case_inputs(display_data["testCases"])

    # 결과 표시
    st.json(display_data, expanded=False)


def display_review_result(json_data: dict[str, Any]) -> None:
    """리뷰 결과를 HTML로 표시합니다."""
    if "review_response" not in json_data or not json_data["review_response"]:
        st.warning("리뷰 응답 데이터가 없습니다.")
        return

    try:
        review_response = ReviewResponse.model_validate(json_data["review_response"])
        formatter = ReviewFormatter()
        content = formatter.to_markdown(review_response)
        st.markdown(content)
    except Exception as e:
        st.error(f"리뷰 응답 데이터 처리 중 오류 발생: {e}")
        st.json(json_data["review_response"], expanded=False)


def load_and_display_file_content(file_path: Path) -> None:
    """파일 내용을 로드하고 표시합니다."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        file_format = determine_file_format(file_path)

        if file_format == "json":
            json_data = parse_json_content(content)
            if not json_data:
                st.error("유효하지 않은 JSON 형식입니다.")
                st.text(content)
                return

            view_type = st.session_state.get("view_type")

            if view_type == "리뷰 결과":
                if "show_raw_json" not in st.session_state:
                    st.session_state.show_raw_json = False

                show_raw_json = st.checkbox(
                    "원본 JSON 데이터 보기", key="show_raw_json"
                )

                if show_raw_json:
                    display_review_result_raw_json(json_data)
                else:
                    display_review_result(json_data)

            elif view_type == "llm_eval 결과":
                display_llm_eval_results(json_data)
        else:
            # 텍스트 파일은 그대로 표시
            st.text(content)

    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {str(e)}")


def display_uploaded_file_content(file_info: dict[str, Any]) -> None:
    """업로드된 파일 내용을 표시합니다."""
    content = file_info.get("content", "")
    file_format = file_info.get("format", "txt")

    if file_format == "json":
        json_data = parse_json_content(content)
        if not json_data:
            st.error("유효하지 않은 JSON 형식입니다.")
            st.text(content)
            return

        view_type = st.session_state.get("view_type")

        if view_type == "리뷰 결과":
            if "show_raw_json_uploaded" not in st.session_state:
                st.session_state.show_raw_json_uploaded = False

            show_raw_json = st.checkbox(
                "원본 JSON 데이터 보기", key="show_raw_json_uploaded"
            )

            if show_raw_json:
                display_review_result_raw_json(json_data)
            else:
                display_review_result(json_data)

        elif view_type == "llm_eval 결과":
            display_llm_eval_results(json_data)
    else:
        # 텍스트 파일은 그대로 표시
        st.text(content)


def sort_file_infos(
    file_infos: list[dict[str, Any]], sort_option: str
) -> list[dict[str, Any]]:
    """파일 정보 목록을 정렬합니다."""
    if sort_option == "최신순":
        file_infos.sort(key=lambda x: x["date"], reverse=True)
    elif sort_option == "오래된순":
        file_infos.sort(key=lambda x: x["date"])
    return file_infos


def extract_repo_path_from_file(file_path: Path) -> str | None:
    """JSON 파일에서 repo_path를 추출합니다."""
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("repo_path")
    except Exception as e:
        console.error(f"Error extracting repo_path from file {file_path}: {e}")
        return None


def get_unique_repo_paths(files: list[Path]) -> list[str]:
    """모든 파일에서 고유한 repo_path 목록을 반환합니다."""
    repo_paths = set()
    has_none_repo_path = False

    for file_path in files:
        repo_path = extract_repo_path_from_file(file_path)
        if repo_path:
            repo_paths.add(repo_path)
        else:
            has_none_repo_path = True

    # None인 repo_path가 있으면 "미분류" 카테고리 추가
    sorted_paths = sorted(repo_paths)
    if has_none_repo_path:
        sorted_paths.append("__UNCATEGORIZED__")  # 특별한 키값 사용

    return sorted_paths


def filter_files_by_repo_path(files: list[Path], selected_repo_path: str) -> list[Path]:
    """선택된 repo_path에 해당하는 파일들만 필터링합니다."""
    if not selected_repo_path:
        return files

    filtered_files = []
    for file_path in files:
        repo_path = extract_repo_path_from_file(file_path)

        # 미분류 카테고리 선택 시 repo_path가 None인 파일들 반환
        if selected_repo_path == "__UNCATEGORIZED__":
            if repo_path is None:
                filtered_files.append(file_path)
        elif repo_path == selected_repo_path:
            filtered_files.append(file_path)

    return filtered_files


def format_repo_path_display(repo_path: str | None) -> str:
    """repo_path를 화면 표시용으로 포맷팅합니다."""
    if repo_path is None:
        return "미분류 프로젝트"
    elif repo_path == ".":
        return "현재 프로젝트 (.)"
    elif repo_path == "__UNCATEGORIZED__":
        return "미분류 프로젝트"
    return repo_path


def app() -> None:
    """Streamlit 앱 메인 함수"""
    st.set_page_config(
        page_title="Selvage - 코드 리뷰 결과",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("코드 리뷰 결과")

    # 결과 디렉토리 표시
    review_log_dir = get_default_review_log_dir()
    st.sidebar.markdown(f"**리뷰 로그 저장 위치**: {review_log_dir}")
    st.sidebar.markdown(
        f"**llm_eval 결과 저장 위치**: {get_default_llm_eval_data_dir()}"
    )

    # 결과 선택
    view_type = st.sidebar.selectbox(
        "보기 유형:",
        [
            "리뷰 결과",
            "llm_eval 결과",
        ],
        index=0,
    )

    # 뷰 타입 세션 저장
    st.session_state.view_type = view_type

    # 파일 선택 방식 탭
    tab1, tab2 = st.sidebar.tabs(["💾 저장된 파일", "📁 파일 업로드"])

    selected_file_info = None

    with tab1:
        # 기존 파일 목록 가져오기
        if view_type == "리뷰 결과":
            all_files = get_review_log_files()
            if not all_files:
                st.info("저장된 리뷰 로그가 없습니다.")
                st.markdown("""
                ### 리뷰 생성 방법
                
                터미널에서 다음 명령어를 실행하여 코드 리뷰를 생성하세요:
                ```bash
                selvage review
                ```
                
                자세한 사용법은 README.md 파일을 참조하세요.
                """)
                return

            # 프로젝트(repo_path) 선택 - 최상위 카테고리
            unique_repo_paths = get_unique_repo_paths(all_files)
            if unique_repo_paths:
                # repo_path 표시용 옵션 생성
                repo_path_options = {
                    format_repo_path_display(path): path for path in unique_repo_paths
                }

                selected_display_path = st.selectbox(
                    "📁 프로젝트 선택:",
                    ["전체 프로젝트"] + list(repo_path_options.keys()),
                    index=0,
                    key="stored_project_select",
                )

                # 선택된 repo_path로 파일 필터링
                if selected_display_path == "전체 프로젝트":
                    files = all_files
                    st.markdown(f"**표시 중**: 전체 프로젝트 ({len(all_files)}개 파일)")
                else:
                    selected_repo_path = repo_path_options[selected_display_path]
                    files = filter_files_by_repo_path(all_files, selected_repo_path)
                    st.markdown(
                        f"**표시 중**: {selected_display_path} ({len(files)}개 파일)"
                    )
            else:
                files = all_files
                st.markdown(f"**표시 중**: 전체 파일 ({len(all_files)}개)")
        else:  # llm_eval 결과
            files = get_llm_eval_data_files()
            if not files:
                st.info("저장된 llm_eval 결과가 없습니다.")
                return

        # 파일 목록 정보 생성
        file_infos = [get_file_info(f) for f in files]

        # 정렬 옵션
        sort_option = st.selectbox(
            "정렬 기준:", ["최신순", "오래된순"], index=0, key="stored_sort_select"
        )

        # 정렬 적용
        file_infos = sort_file_infos(file_infos, sort_option)

        # 선택 가능한 파일 옵션 생성
        file_options = {
            f"{info['name']} ({info['date'].strftime('%Y-%m-%d %H:%M')})": info
            for info in file_infos
        }

        # 파일 선택 위젯
        if file_options:
            selected_file_name = st.selectbox(
                "파일 선택:",
                list(file_options.keys()),
                index=0,
                key="stored_file_select",
            )
            selected_file_info = file_options[selected_file_name]

    with tab2:
        # 파일 업로드 기능
        uploaded_file = st.file_uploader(
            "파일을 선택하세요",
            type=["json", "log", "txt", "html"],
            help="JSON, LOG, TXT, HTML 형식의 파일을 업로드할 수 있습니다.",
            key="file_uploader",
        )

        if uploaded_file is not None:
            try:
                # 파일 내용 읽기
                content = uploaded_file.read().decode("utf-8")

                # 업로드된 파일 정보 생성
                uploaded_file_info = get_uploaded_file_info(uploaded_file, content)

                st.success(
                    f"파일 '{uploaded_file.name}'이 성공적으로 업로드되었습니다."
                )
                st.markdown(f"**파일 크기**: {uploaded_file_info['size_str']}")

                # 업로드된 파일을 선택된 파일로 설정
                selected_file_info = uploaded_file_info

            except Exception as e:
                st.error(f"파일 업로드 중 오류가 발생했습니다: {str(e)}")

    # 선택된 파일 정보와 내용 표시
    if selected_file_info:
        display_file_info(selected_file_info)

        # 업로드된 파일인지 확인하여 적절한 함수 호출
        if selected_file_info.get("is_uploaded", False):
            display_uploaded_file_content(selected_file_info)
        else:
            load_and_display_file_content(selected_file_info["path"])


def run_app() -> None:
    """Streamlit 앱을 실행합니다."""
    import subprocess

    file_path = os.path.abspath(__file__)
    port = os.environ.get("STREAMLIT_SERVER_PORT", "8501")

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        file_path,
        "--server.headless",
        "true",
        "--browser.serverAddress",
        "localhost",
        "--server.port",
        port,
    ]

    # 보안을 위해 shell=False를 명시적으로 지정
    # cmd는 하드코딩된 안전한 값들로 구성됨 (Streamlit 실행용)
    subprocess.run(cmd, check=False, shell=False)  # noqa: S603


# Streamlit 앱으로 직접 실행될 경우
if __name__ == "__main__":
    app()
