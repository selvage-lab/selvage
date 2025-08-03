# Change Log

## [0.1.4] - 2025-08-03

### Added

#### feat: context extract 기능 구현

**핵심 기능**

##### 컨텍스트 추출 개선

- **Tree-sitter 기반 smart context extractor 도입**: AST 분석을 통해 변경 라인이 속하는 가장 작은 코드 블록과 파일에 존재하는 dependency statement (import, require, define 등)를 자동 추출
  - **다중 언어 지원**: Python, JavaScript/TypeScript, Java/Kotlin 언어에 대한 전문적인 컨텍스트 추출 지원
  - **Smart Context 적용 조건**: 전체 파일 대비 변경 라인이 20% 이하일 때 사용되며, 그 이상일 때는 전체 파일 컨텍스트 사용
- **Fallback 컨텍스트 추출기**: 지원하지 않는 언어(C, C#, Go, Swift 등)에 대해서는 정규표현식 기반 패턴 매칭으로 컨텍스트 추출

**추가 개선사항**

- **시스템 프롬프트 개선**: 시스템 프롬프트 업그레이드하여 더 정확한 컨텍스트 기반 코드 리뷰 제공
- **무의미한 변경 필터링**: 빈 라인, 주석, 전처리기 지시문 등 무의미한 변경사항을 자동으로 필터링하여 리뷰 품질 향상
