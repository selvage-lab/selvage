# CR-18: Multiturn Review 실행 로직 구현 명세서

## 📋 개요

Linear CR-18 이슈에 따라 LLM의 context limit를 초과하는 경우 프롬프트를 분할하여 병렬 처리하는 Multiturn Review 기능을 구현합니다.

**주요 목표:**
- Context limit 초과 시 자동으로 프롬프트 분할 처리
- 토큰 정보 기반 지능적 분할 전략 구현
- 병렬 API 호출을 통한 빠른 리뷰 처리
- 분할된 결과들의 간단한 병합 (고도화된 합성은 CR-19에서 구현)

## 🎯 Linear 이슈 정보

**CR-18: multiturn review 실행 로직 구현**
- 우선순위: High (2)
- 추정: 2 Points  
- 상태: In Review
- 마감일: 2025-08-07

**요구사항:**
- user prompt를 나누어서 system prompt와 함께 보내는 로직 구현
- context limit을 안 넘도록 분산해서 보냄
- user_prompt를 보낼 때 overlap 필요한지 판단
- 병렬 처리 필요 (빠른 리뷰 처리를 위함)

## 🏗️ 아키텍처 설계

### 현재 워크플로우
```
ReviewRequest -> PromptGenerator -> ReviewPromptWithFileContent -> BaseGateway.review_code -> ReviewResult
                                                                              ↓ (context limit error)
                                                                         Exception 발생
```

### 새로운 Multiturn 워크플로우
```
ReviewRequest -> PromptGenerator -> ReviewPromptWithFileContent -> BaseGateway.review_code
                                                                              ↓ (context limit error)
                                                                   MultiturnReviewExecutor
                                                                              ↓
                                                        PromptSplitter (토큰 기반 분할)
                                                                              ↓
                                                        병렬 API 호출 (multiple BaseGateway.review_code)
                                                                              ↓
                                                        간단한 결과 병합 (CR-19에서 고도화)
                                                                              ↓
                                                                        최종 ReviewResult
```

## 🗂️ 구현 대상 파일

### 수정 대상 파일

#### `selvage/cli.py`
**위치:** L391-398  
**현재 코드:**
```python
if error_response.is_context_limit_error():
    console.error(
        f"컨텍스트 제한 초과: {error_response.error_message}\n"
        f"향후 Multiturn 리뷰 기능으로 자동 재시도될 예정입니다."
    )
    # TODO: Multiturn 리뷰 구현 후 여기서 재시도
    raise Exception(
        f"Context limit exceeded: {error_response.error_message}"
    )
```

**수정 후:**
```python
if error_response.is_context_limit_error():
    console.info("컨텍스트 제한 초과 감지, Multiturn 리뷰 모드로 전환합니다.")
    
    # Multiturn 리뷰 실행 (이미 생성된 review_prompt 사용)
    multiturn_executor = MultiturnReviewExecutor()
    review_result = multiturn_executor.execute_multiturn_review(
        review_prompt=review_prompt,  # L383에서 이미 생성된 프롬프트 사용
        error_response=error_response,
        llm_gateway=llm_gateway
    )
    
    return review_result.review_response, review_result.estimated_cost
```

### 신규 생성 파일

#### `selvage/src/multiturn/__init__.py`
- MultiturnReviewExecutor, PromptSplitter 클래스 export

#### `selvage/src/multiturn/multiturn_review_executor.py`
- 메인 실행 로직 담당
- 프롬프트 분할, 병렬 처리, 결과 합성 조율

#### `selvage/src/multiturn/prompt_splitter.py`  
- 토큰 정보 기반 프롬프트 분할 로직
- Gemini 등 토큰 정보 미제공 provider 대응


## 🔧 핵심 컴포넌트 인터페이스

### 1. MultiturnReviewExecutor

```python
class MultiturnReviewExecutor:
    """Multiturn Review 메인 실행기"""
    
    def execute_multiturn_review(
        self, 
        review_prompt: ReviewPromptWithFileContent,
        error_response: ErrorResponse,
        llm_gateway: BaseGateway
    ) -> ReviewResult:
        """
        Context limit 초과 시 프롬프트를 분할하여 병렬 처리 후 결과 합성
        
        Args:
            review_prompt: 이미 생성된 리뷰 프롬프트 (cli.py:L383에서 생성)
            error_response: Context limit 에러 정보 (토큰 정보 포함)
            llm_gateway: LLM API 호출 게이트웨이
            
        Returns:
            ReviewResult: 합성된 최종 리뷰 결과
        """
        # Pseudo code:
        # 1. 토큰 정보 추출 (actual_tokens, max_tokens)
        # 2. user_prompts 분할 (system_prompt는 공통 사용)
        # 3. 병렬 API 호출
        # 4. 결과 간단 병합 (상세 합성은 CR-19에서 구현)
        pass
```

### 2. PromptSplitter

```python
class PromptSplitter:
    """프롬프트 분할 담당 클래스"""
    
    def split_user_prompts(
        self,
        user_prompts: list[UserPromptWithFileContent],
        actual_tokens: int | None,
        max_tokens: int | None,
        overlap: int = 1
    ) -> list[list[UserPromptWithFileContent]]:
        """
        토큰 정보를 기반으로 user_prompts를 분할
        
        Args:
            user_prompts: 분할할 사용자 프롬프트 목록
            actual_tokens: 실제 사용한 토큰 수 (error_response에서 추출)
            max_tokens: 최대 허용 토큰 수 (error_response에서 추출)
            overlap: 분할된 청크간 겹치는 파일 개수 (기본값: 1)
            
        Returns:
            분할된 user_prompts 그룹들의 목록
            
        분할 전략:
        - 토큰 정보 있음: actual_tokens과 max_tokens 비율로 계산하여 분할
        - 토큰 정보 없음: 임의로 반으로 분할 (Gemini 등)
        - overlap 적용: 각 청크에 overlap 개수만큼 이전 청크의 마지막 파일들 포함
        """
        pass
    
    def _calculate_split_ratio(self, actual_tokens: int, max_tokens: int) -> int:
        """분할 비율 계산"""
        pass
    
    def _apply_overlap(
        self, 
        chunks: list[list[UserPromptWithFileContent]], 
        overlap: int
    ) -> list[list[UserPromptWithFileContent]]:
        """분할된 청크에 overlap 적용"""
        pass
```


## 💡 구현 세부사항

### 토큰 정보 추출 로직

```python
def extract_token_info(error_response: ErrorResponse) -> tuple[int | None, int | None]:
    """
    ErrorResponse에서 토큰 정보 추출
    
    Returns:
        (actual_tokens, max_tokens) 튜플
        토큰 정보가 없으면 (None, None) 반환
    """
    actual_tokens = error_response.raw_error.get("actual_tokens")
    max_tokens = error_response.raw_error.get("max_tokens")
    
    return (
        int(actual_tokens) if actual_tokens else None,
        int(max_tokens) if max_tokens else None
    )
```

### 분할 전략

#### 토큰 정보 기반 분할
```python
# 예시: actual_tokens=150000, max_tokens=100000인 경우
split_ratio = math.ceil(actual_tokens / (max_tokens * 0.8))  # 여유분 20% 확보
# split_ratio = 2 (2개로 분할)

# user_prompts를 split_ratio 개수만큼 균등 분할
chunks = []
chunk_size = len(user_prompts) // split_ratio
for i in range(0, len(user_prompts), chunk_size):
    chunks.append(user_prompts[i:i + chunk_size])

# overlap 적용
overlap = 1
if overlap > 0 and len(chunks) > 1:
    for i in range(1, len(chunks)):
        # 이전 청크의 마지막 overlap 개수만큼 현재 청크 앞에 추가
        prev_chunk = chunks[i-1]
        if len(prev_chunk) >= overlap:
            overlap_items = prev_chunk[-overlap:]
            chunks[i] = overlap_items + chunks[i]
```

#### 토큰 정보 미제공 시 기본 분할
```python
# Gemini 등 토큰 정보를 제공하지 않는 경우
# 임의로 반으로 분할
mid_point = len(user_prompts) // 2
chunk1 = user_prompts[:mid_point]
chunk2 = user_prompts[mid_point:]
chunks = [chunk1, chunk2]

# overlap 적용
overlap = 1
if overlap > 0 and len(chunk1) >= overlap:
    overlap_items = chunk1[-overlap:]
    chunk2 = overlap_items + chunk2
    chunks = [chunk1, chunk2]
```

### 병렬 처리 구현

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def parallel_review(
    self, 
    split_prompts: list[list[UserPromptWithFileContent]],
    system_prompt: SystemPrompt,
    llm_gateway: BaseGateway
) -> list[ReviewResult]:
    """
    분할된 프롬프트들을 병렬로 처리
    """
    async def review_single_chunk(user_prompts_chunk: list[UserPromptWithFileContent]):
        review_prompt = ReviewPromptWithFileContent(
            system_prompt=system_prompt,
            user_prompts=user_prompts_chunk
        )
        return llm_gateway.review_code(review_prompt)
    
    # 병렬 실행
    tasks = [review_single_chunk(chunk) for chunk in split_prompts]
    results = await asyncio.gather(*tasks)
    
    return results
```


## 🧪 테스트 전략

### 단위 테스트

#### `test_prompt_splitter.py`
- 토큰 정보 기반 분할 로직 테스트
- 토큰 정보 없을 때 기본 분할 테스트
- overlap 파라미터별 분할 결과 테스트 (overlap=0,1,2)
- 분할 비율 계산 로직 테스트


#### `test_multiturn_review_executor.py`
- 전체 워크플로우 테스트
- 에러 처리 테스트

### 통합 테스트

#### `test_multiturn_integration.py`
- 실제 context limit 초과 상황 모의
- CLI에서 multiturn review 트리거 테스트
- 병렬 처리 성능 테스트

## 📊 성능 고려사항

### 병렬 처리 최적화
- 동시 API 호출 수 제한 (rate limit 고려)
- 실패한 요청의 재시도 로직
- 타임아웃 처리

### 메모리 사용량
- 대용량 diff 처리 시 메모리 효율성
- 분할된 결과의 임시 저장 전략

### 비용 최적화  
- 불필요한 중복 처리 방지
- 합성 단계의 토큰 사용량 최소화

## 🚀 구현 순서

1. **Phase 1: 핵심 클래스 구현**
   - PromptSplitter 기본 로직
   - MultiturnReviewExecutor 프레임워크

2. **Phase 2: CLI 통합**
   - `selvage/cli.py` 수정
   - 기본 동작 검증

3. **Phase 3: 고도화**
   - 병렬 처리 최적화
   - 에러 처리 강화
   - 성능 튜닝

4. **Phase 4: 테스트 및 검증**
   - 단위 테스트 작성
   - 통합 테스트 작성
   - 실제 환경에서 검증

## 📋 체크리스트

- [ ] `selvage/src/multiturn/` 패키지 생성
- [ ] MultiturnReviewExecutor 클래스 구현
- [ ] PromptSplitter 클래스 구현  
- [ ] CLI 통합 (`selvage/cli.py` 수정)
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 작성
- [ ] 실제 context limit 상황에서 동작 검증
- [ ] 성능 및 비용 최적화
- [ ] 문서화 업데이트

## 🔗 관련 이슈

- **Linear CR-18**: multiturn review 실행 로직 구현
- **Linear CR-19**: synthesize 로직 구현 (후속 이슈)
- **Linear CR-17**: 토큰 검증 방식 개선 (선행 작업)