# 테스트 실행 가이드

## 기본 테스트 실행

### 빠른 테스트 (통합 테스트 제외)

```bash
# 기본 테스트 실행 - 통합 테스트는 자동 스킵
pytest ./tests

# 특정 디렉토리만 테스트
pytest ./tests/context_extractor/
pytest ./tests/utils/
```

### 통합 테스트 포함 실행

```bash
# 모든 테스트 실행 (통합 테스트 포함)
pytest ./tests --integration

# 특정 마커만 실행
pytest ./tests -m integration  # 통합 테스트만
pytest ./tests -m "not integration"  # 통합 테스트 제외
```

## 마커 설명

- **`integration`**: 통합 테스트 (외부 API 호출, 외부 서비스 등) - `--integration` 옵션 필요
- **`slow`**: 실행 시간이 오래 걸리는 테스트
- **`unit`**: 단위 테스트 (격리된 컴포넌트 테스트)

## 테스트 실행 예시

### 개발 중 빠른 피드백

```bash
# 통합 테스트 없이 빠른 테스트
pytest ./tests -v -m "not integration"
```

### 배포 전 전체 테스트

```bash
# 모든 테스트 실행 (통합 테스트 포함)
pytest ./tests --integration -v
```

### 특정 기능 테스트

```bash
# 컨텍스트 추출기만 테스트
pytest ./tests/context_extractor/ -v

# LLM 게이트웨이만 테스트 (통합 테스트 포함)
pytest ./tests/llm_gateway/ --integration -v
```

### 병렬 실행 (속도 향상)

```bash
# 병렬로 테스트 실행 (pytest-xdist 필요)
pytest ./tests --integration -n auto
```

## 주의사항

1. **`--integration` 옵션 없이 실행**: 통합 테스트는 자동으로 스킵됩니다.
2. **API 키 설정**: `--integration` 옵션으로 실행할 때는 적절한 API 키가 환경변수에 설정되어 있어야 합니다.
3. **비용 발생**: 통합 테스트는 실제 API를 호출하므로 비용이 발생할 수 있습니다.
4. **네트워크 의존성**: 인터넷 연결이 필요합니다.

## 환경변수 설정

통합 테스트를 실행하기 전에 필요한 환경변수를 설정하세요:

```bash
# OpenAI
export OPENAI_API_KEY="your-api-key"

# Anthropic
export ANTHROPIC_API_KEY="your-api-key"

# Google
export GEMINI_API_KEY="your-api-key"

# OpenRouter
export OPENROUTER_API_KEY="your-api-key"
```
