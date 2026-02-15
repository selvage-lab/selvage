"""DelegatedContextStore 유닛 테스트"""

import json
import time

from selvage.src.mcp.context_store import DelegatedContextStore


class TestDelegatedContextStore:
    """DelegatedContextStore 클래스 테스트"""

    def test_save_and_load_metadata(self, tmp_path) -> None:
        """저장 후 메타데이터 로드 테스트"""
        store = DelegatedContextStore(store_dir=tmp_path)
        data = {
            'system_prompt': 'You are a code reviewer...',
            'review_targets': [
                {'role': 'user', 'content': '{"file_name": "app.py"}'},
            ],
            'output_format': {'type': 'json_schema'},
            'metadata': {'files_count': 1},
            'file_list': ['app.py'],
        }

        context_id = store.save(data)

        assert context_id.startswith('ctx-')
        loaded = store.load_metadata(context_id)
        assert loaded is not None
        assert loaded['system_prompt'] == 'You are a code reviewer...'
        assert loaded['file_list'] == ['app.py']
        assert 'created_at' in loaded

    def test_save_creates_json_file(self, tmp_path) -> None:
        """save가 JSON 파일을 생성하는지 테스트"""
        store = DelegatedContextStore(store_dir=tmp_path)
        context_id = store.save({'review_targets': []})

        file_path = tmp_path / f'{context_id}.json'
        assert file_path.exists()

        content = json.loads(file_path.read_text(encoding='utf-8'))
        assert 'created_at' in content

    def test_load_file_context_found(self, tmp_path) -> None:
        """파일 컨텍스트 정상 조회 테스트"""
        store = DelegatedContextStore(store_dir=tmp_path)
        data = {
            'review_targets': [
                {'role': 'user', 'content': '{"file_name": "app.py", "diff": "..."}'},
                {'role': 'user', 'content': '{"file_name": "utils.py", "diff": "..."}'},
            ],
        }
        context_id = store.save(data)

        result = store.load_file_context(context_id, 'app.py')

        assert result is not None
        assert result['role'] == 'user'
        assert 'app.py' in result['content']

    def test_load_file_context_not_found(self, tmp_path) -> None:
        """존재하지 않는 파일 조회 시 None 반환 테스트"""
        store = DelegatedContextStore(store_dir=tmp_path)
        context_id = store.save({
            'review_targets': [
                {'role': 'user', 'content': '{"file_name": "app.py"}'},
            ],
        })

        result = store.load_file_context(context_id, 'nonexistent.py')

        assert result is None

    def test_load_file_context_invalid_context_id(self, tmp_path) -> None:
        """잘못된 context_id로 조회 시 None 반환 테스트"""
        store = DelegatedContextStore(store_dir=tmp_path)

        result = store.load_file_context('ctx-invalid-12345678', 'app.py')

        assert result is None

    def test_load_metadata_invalid_context_id(self, tmp_path) -> None:
        """잘못된 context_id로 메타데이터 조회 시 None 반환 테스트"""
        store = DelegatedContextStore(store_dir=tmp_path)

        result = store.load_metadata('ctx-invalid-12345678')

        assert result is None

    def test_cleanup_expired(self, tmp_path) -> None:
        """만료된 컨텍스트 파일 정리 테스트"""
        store = DelegatedContextStore(store_dir=tmp_path)

        # 만료된 파일 생성 (오래된 mtime 설정)
        old_file = tmp_path / 'ctx-old-12345678.json'
        old_file.write_text('{}')
        old_mtime = time.time() - 7200  # 2시간 전
        import os
        os.utime(old_file, (old_mtime, old_mtime))

        # 최신 파일 생성
        store.save({'review_targets': []})

        deleted = store.cleanup_expired(ttl_minutes=60)

        assert deleted == 1
        assert not old_file.exists()
        # 최신 파일은 남아있어야 함
        remaining = list(tmp_path.glob('ctx-*.json'))
        assert len(remaining) == 1

    def test_cleanup_expired_no_expired(self, tmp_path) -> None:
        """만료 파일 없을 때 삭제 수 0 반환 테스트"""
        store = DelegatedContextStore(store_dir=tmp_path)
        store.save({'review_targets': []})

        deleted = store.cleanup_expired(ttl_minutes=60)

        assert deleted == 0

    def test_context_id_format(self, tmp_path) -> None:
        """context_id 형식 테스트"""
        store = DelegatedContextStore(store_dir=tmp_path)
        context_id = store.save({'review_targets': []})

        parts = context_id.split('-')
        assert parts[0] == 'ctx'
        assert parts[1].isdigit()  # unix timestamp
        assert len(parts[2]) == 8  # uuid hex[:8]

    def test_save_does_not_mutate_input(self, tmp_path) -> None:
        """save()가 입력 dict를 변이시키지 않는지 테스트"""
        store = DelegatedContextStore(store_dir=tmp_path)
        data = {'review_targets': [], 'metadata': {}}
        original_keys = set(data.keys())

        store.save(data)

        assert set(data.keys()) == original_keys
        assert 'created_at' not in data

    def test_path_traversal_rejected(self, tmp_path) -> None:
        """경로 순회 공격 시도가 차단되는지 테스트"""
        store = DelegatedContextStore(store_dir=tmp_path)

        assert store.load_metadata('../../etc/passwd') is None
        assert store.load_file_context('../secret', 'file.py') is None
        assert store.load_metadata('ctx-notanumber-abcd1234') is None

    def test_valid_context_id_accepted(self, tmp_path) -> None:
        """유효한 context_id 형식이 허용되는지 테스트"""
        store = DelegatedContextStore(store_dir=tmp_path)

        assert store._validate_context_id('ctx-1770967425-82244dea')
        assert store._validate_context_id('ctx-0-00000000')

    def test_invalid_context_id_rejected(self, tmp_path) -> None:
        """유효하지 않은 context_id 형식이 거부되는지 테스트"""
        store = DelegatedContextStore(store_dir=tmp_path)

        assert not store._validate_context_id('')
        assert not store._validate_context_id('ctx-abc-12345678')
        assert not store._validate_context_id('ctx-123-1234567')  # hex 7자리
        assert not store._validate_context_id('ctx-123-123456789')  # hex 9자리
        assert not store._validate_context_id('../../etc/passwd')
        assert not store._validate_context_id('ctx-123-ZZZZZZZZ')  # 비-hex 문자

    def test_corrupted_json_returns_none(self, tmp_path) -> None:
        """손상된 JSON 파일 로드 시 None 반환 테스트"""
        store = DelegatedContextStore(store_dir=tmp_path)

        corrupted_file = tmp_path / 'ctx-1234567890-abcdef01.json'
        corrupted_file.write_text('{ invalid json content', encoding='utf-8')

        result = store.load_metadata('ctx-1234567890-abcdef01')

        assert result is None
