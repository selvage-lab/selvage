"""tree-sitter를 사용한 코드 파싱 테스트"""

import os
from pathlib import Path

from tree_sitter_language_pack import get_language, get_parser


def test_tree_sitter_parsing():
    """tree-sitter를 사용해서 Python 코드를 파싱하고 결과를 출력합니다."""

    # 1. Python 언어와 파서 가져오기
    try:
        language = get_language("python")
        parser = get_parser("python")
        print("Python 언어와 파서 로딩 성공!")
    except Exception as err:
        print(f"언어/파서 로딩 실패: {err}")
        return

    # 2. SCM 쿼리 파일 읽기
    query_path = Path(
        "selvage/resources/queries/tree-sitter-language-pack/python-tags.scm"
    )
    if not query_path.exists():
        print(f"쿼리 파일을 찾을 수 없습니다: {query_path}")
        return

    query_scm = query_path.read_text()
    print(f"SCM 쿼리 로딩 완료:\n{query_scm}")
    print("-" * 50)

    # 3. 테스트 파일 읽기
    test_file_path = Path("tests/test_sample_class.py")
    if not test_file_path.exists():
        print(f"테스트 파일을 찾을 수 없습니다: {test_file_path}")
        return

    code = test_file_path.read_text()
    print(f"테스트 파일 로딩 완료: {test_file_path}")
    print("-" * 50)

    # 4. 코드 파싱
    try:
        tree = parser.parse(bytes(code, "utf-8"))
        print("코드 파싱 완료!")
    except Exception as err:
        print(f"코드 파싱 실패: {err}")
        return

    # 5. 쿼리 실행
    try:
        query = language.query(query_scm)
        captures = query.captures(tree.root_node)
        print("쿼리 실행 완료!")
        print("-" * 50)
    except Exception as err:
        print(f"쿼리 실행 실패: {err}")
        return

    # 6. 캡처 결과 출력
    print("=== CAPTURE 결과 ===")
    print(f"캡처 타입: {type(captures)}")
    print(f"캡처 개수: {len(captures) if hasattr(captures, '__len__') else 'Unknown'}")
    print()

    # captures가 딕셔너리인지 리스트인지 확인
    if isinstance(captures, dict):
        print("캡처 결과가 딕셔너리 형태입니다:")
        for tag, nodes in captures.items():
            print(f"\n태그: {tag}")
            print(f"노드 개수: {len(nodes)}")
            for i, node in enumerate(nodes):
                text = node.text.decode("utf-8") if node.text else "None"
                start_line = node.start_point[0] + 1  # 1-based line number
                print(f"  [{i + 1}] 라인 {start_line}: '{text}'")
    else:
        print("캡처 결과가 리스트 형태입니다:")
        for i, (node, tag) in enumerate(captures):
            text = node.text.decode("utf-8") if node.text else "None"
            start_line = node.start_point[0] + 1  # 1-based line number
            print(f"[{i + 1}] 태그: {tag}, 라인 {start_line}: '{text}'")

    # 7. 추가 분석 실행
    analyze_captures_by_type(captures)

    print("\n" + "=" * 50)
    print("파싱 테스트 완료!")


def analyze_captures_by_type(captures):
    """캡처 결과를 타입별로 분류해서 분석합니다."""
    print("\n=== 타입별 분석 ===")

    if isinstance(captures, dict):
        # tree-sitter-language-pack 스타일
        definitions = []
        references = []

        for tag, nodes in captures.items():
            for node in nodes:
                text = node.text.decode("utf-8") if node.text else "None"
                line = node.start_point[0] + 1

                if "definition" in tag:
                    definitions.append((tag, text, line))
                elif "reference" in tag:
                    references.append((tag, text, line))

        print(f"정의(Definitions): {len(definitions)}개")
        for tag, text, line in definitions:
            # 긴 텍스트는 첫 줄만 표시
            display_text = text.split("\n")[0] if "\n" in text else text
            if len(display_text) > 50:
                display_text = display_text[:47] + "..."
            print(f"  {tag} - 라인 {line}: {display_text}")

        print(f"\n참조(References): {len(references)}개")
        for tag, text, line in references:
            display_text = text.split("\n")[0] if "\n" in text else text
            if len(display_text) > 50:
                display_text = display_text[:47] + "..."
            print(f"  {tag} - 라인 {line}: {display_text}")
    else:
        # 기본 tree-sitter 스타일
        for node, tag in captures:
            text = node.text.decode("utf-8") if node.text else "None"
            line = node.start_point[0] + 1
            display_text = text.split("\n")[0] if "\n" in text else text
            if len(display_text) > 50:
                display_text = display_text[:47] + "..."
            print(f"  {tag} - 라인 {line}: {display_text}")


if __name__ == "__main__":
    # 현재 디렉토리를 프로젝트 루트로 변경
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)

    test_tree_sitter_parsing()
